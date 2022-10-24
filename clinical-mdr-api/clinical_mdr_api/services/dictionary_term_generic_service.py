from abc import ABC
from typing import Any, Generic, Optional, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.dictionaries.dictionary_term import (
    DictionaryTermAR,
    DictionaryTermVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_repository import (
    DictionaryTermGenericRepository,
)
from clinical_mdr_api.models import DictionaryTerm, DictionaryTermVersion
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
    normalize_string,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class DictionaryTermGenericService(Generic[_AggregateRootType], ABC):
    @classmethod
    def get_input_or_previous_property(
        cls, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    aggregate_class = DictionaryTermAR
    version_class = DictionaryTermVersion
    repository_interface = DictionaryTermGenericRepository
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> DictionaryTermGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        return DictionaryTerm.from_dictionary_term_ar(item_ar)

    def _create_aggregate_root(
        self, term_input: BaseModel, library: LibraryVO
    ) -> _AggregateRootType:
        return DictionaryTermAR.from_input_values(
            author=self.user_initials,
            dictionary_term_vo=DictionaryTermVO.from_input_values(
                codelist_uid=term_input.codelistUid,
                name=term_input.name,
                dictionary_id=term_input.dictionaryId,
                name_sentence_case=term_input.nameSentenceCase,
                abbreviation=term_input.abbreviation,
                definition=term_input.definition,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            term_exists_by_name_callback=self.repository.term_exists_by_name,
        )

    def _edit_aggregate(
        self, item: _AggregateRootType, term_input: BaseModel
    ) -> _AggregateRootType:
        item.edit_draft(
            author=self.user_initials,
            change_description=term_input.changeDescription,
            dictionary_term_vo=DictionaryTermVO.from_input_values(
                codelist_uid=item.dictionary_term_vo.codelist_uid,
                name=term_input.name,
                dictionary_id=term_input.dictionaryId,
                name_sentence_case=term_input.nameSentenceCase,
                abbreviation=term_input.abbreviation,
                definition=term_input.definition,
            ),
            term_exists_by_name_callback=self.repository.term_exists_by_name,
        )
        return item

    @db.transaction
    def get_all_dictionary_terms(
        self,
        codelist_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[DictionaryTerm]:

        items, total_count = self.repository.find_all(
            codelist_uid=codelist_uid,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )

        all_dictionary_terms = GenericFilteringReturn.create(items, total_count)
        all_dictionary_terms.items = [
            self._transform_aggregate_root_to_pydantic_model(dictionary_term_ar)
            for dictionary_term_ar in all_dictionary_terms.items
        ]

        return all_dictionary_terms

    def get_distinct_values_for_header(
        self,
        codelist_uid: str,
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ) -> Sequence[str]:

        # First, check that attributes provided for filtering exist in the return class
        # Properties can be nested => check if root property exists in class
        if not models.utils.isAttributeInModel(
            field_name.split(".")[0], DictionaryTerm
        ):
            raise exceptions.NotFoundException(
                f"Invalid field name specified in the filter dictionary : {field_name}"
            )

        header_values = self.repository.get_distinct_headers(
            codelist_uid=codelist_uid,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        return header_values

    @db.transaction
    def get_by_uid(self, term_uid: str) -> DictionaryTerm:

        item = self._find_by_uid_or_raise_not_found(term_uid=term_uid)
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self, term_uid: str, for_update: Optional[bool] = False
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid_2(uid=term_uid, for_update=for_update)
        if item is None:
            raise exceptions.NotFoundException(
                f"{self.aggregate_class.__name__} with uid {term_uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def get_version_history(self, term_uid: str) -> Sequence[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(term_uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.aggregate_class.__name__} with uid {term_uid} does not exist."
                )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(
                    dictionary_term_ar
                ).dict()
                for dictionary_term_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create(self, term_input: BaseModel) -> BaseModel:
        if not self._repos.dictionary_codelist_generic_repository.codelist_exists(
            normalize_string(term_input.codelistUid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no dictionary codelist identified by provided uid ({term_input.codelistUid})"
            )

        if not self._repos.library_repository.library_exists(
            normalize_string(term_input.libraryName)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({term_input.libraryName})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=term_input.libraryName,
            is_library_editable_callback=(
                lambda name: self._repos.library_repository.find_by_name(
                    name
                ).is_editable
                if self._repos.library_repository.find_by_name(name) is not None
                else None
            ),
        )
        try:
            dictionary_term_ar = self._create_aggregate_root(
                term_input=term_input, library=library_vo
            )
            self.repository.save(dictionary_term_ar)

        except ValueError as value_error:
            raise exceptions.ValidationException(value_error.args[0])

        return self._transform_aggregate_root_to_pydantic_model(dictionary_term_ar)

    @db.transaction
    def create_new_version(self, term_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(
                term_uid=term_uid, for_update=True
            )
            item.create_new_version(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.ValidationException(e.msg)

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(
                term_uid=term_uid, for_update=True
            )
            fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=term_input,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )
            item = self._edit_aggregate(item=item, term_input=term_input)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
        except ValueError as e:
            raise exceptions.ValidationException(e)

    @db.transaction
    def approve(self, term_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(
                term_uid=term_uid, for_update=True
            )
            item.approve(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def inactivate_final(self, term_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
            item.inactivate(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def reactivate_retired(self, term_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
            item.reactivate(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def soft_delete(self, term_uid: str) -> None:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
            item.soft_delete()
            self.repository.save(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
