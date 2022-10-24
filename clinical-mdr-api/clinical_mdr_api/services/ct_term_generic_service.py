import abc
from datetime import datetime
from typing import Any, Generic, Optional, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import calculate_diffs, normalize_string

_AggregateRootType = TypeVar("_AggregateRootType")


class CTTermGenericService(Generic[_AggregateRootType], abc.ABC):
    @abc.abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> CTTermGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @db.transaction
    def get_all_ct_terms(
        self,
        codelist_uid: Optional[str] = None,
        codelist_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:

        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        all_ct_terms = self.repository.find_all(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library=library,
            package=package,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
        )

        all_ct_terms.items = [
            self._transform_aggregate_root_to_pydantic_model(ct_term_ar)
            for ct_term_ar in all_ct_terms.items
        ]

        return all_ct_terms

    def get_distinct_values_for_header(
        self,
        codelist_uid: Optional[str],
        codelist_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ) -> Sequence:
        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        header_values = self.repository.get_distinct_headers(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library=library,
            package=package,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )

        return header_values

    @db.transaction
    def get_term_attributes_by_codelist_uids(
        self, codelist_uids: Sequence[str]
    ) -> BaseModel:
        items, prop_names = self.repository.get_term_attributes_by_codelist_uids(
            codelist_uids
        )

        return [dict(zip(prop_names, item)) for item in items]

    @db.transaction
    def get_by_uid(
        self,
        term_uid: str,
        version: Optional[str] = None,
        at_specific_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> BaseModel:

        item = self._find_by_uid_or_raise_not_found(
            term_uid=term_uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        term_uid: str,
        version: Optional[str] = None,
        at_specific_date: Optional[datetime] = None,
        status: Optional[str] = None,
        for_update: Optional[bool] = False,
    ) -> _AggregateRootType:
        codelist_status = None
        if status is not None:
            status = status.lower()
            if status == "final":
                codelist_status = LibraryItemStatus.FINAL
            elif status == "draft":
                codelist_status = LibraryItemStatus.DRAFT
            elif status == "retired":
                codelist_status = LibraryItemStatus.RETIRED
        item = self.repository.find_by_uid(
            term_uid=term_uid,
            at_specific_date=at_specific_date,
            version=version,
            status=codelist_status,
            for_update=for_update,
        )
        if item is None:
            raise exceptions.NotFoundException(
                f"{self.aggregate_class.__name__} with uid {term_uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def get_version_history(self, term_uid) -> Sequence[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions(term_uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.aggregate_class.__name__} with uid {term_uid} does not exist."
                )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(codelist_ar).dict()
                for codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create_new_version(self, term_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
            item.create_new_version(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def edit_draft(self, term_uid: str, term_input: BaseModel) -> BaseModel:
        raise NotImplementedError()

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
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        try:
            item.inactivate(author=self.user_initials)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def reactivate_retired(self, term_uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)

        try:
            item.reactivate(author=self.user_initials)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def soft_delete(self, term_uid: str) -> None:
        try:
            item = self._find_by_uid_or_raise_not_found(term_uid, for_update=True)
            item.soft_delete()
            self.repository.save(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    def enforce_codelist_package_library(
        self,
        codelist_uid: Optional[str],
        codelist_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
    ) -> None:
        if (
            codelist_uid is not None
            and not self._repos.ct_codelist_attribute_repository.codelist_exists(
                normalize_string(codelist_uid)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTCodelistRoot identified by provided codelist uid ({codelist_uid})"
            )
        if (
            codelist_name is not None
            and not self._repos.ct_codelist_name_repository.codelist_specific_exists_by_name(
                normalize_string(codelist_name)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTCodelistNameValue node identified by provided codelist name ({codelist_name})"
            )
        if library is not None and not self._repos.library_repository.library_exists(
            normalize_string(library)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({library})"
            )
        if (
            package is not None
            and not self._repos.ct_package_repository.package_exists(
                normalize_string(package)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no package identified by provided package name ({package})"
            )
