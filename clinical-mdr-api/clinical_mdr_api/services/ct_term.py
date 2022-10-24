from typing import Optional, Sequence, TypeVar

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.controlled_terminology.utils import TermParentType
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models import CTTerm, CTTermCreateInput, CTTermNameAndAttributes
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import normalize_string

_AggregateRootType = TypeVar("_AggregateRootType")


class CTTermService:
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    @db.transaction
    def create(self, term_input: CTTermCreateInput) -> CTTerm:
        """
        Method creates CTTermAttributesAR and saves that object to the database.
        When saving CTTermAttributesAR - CTTermRoot node is created that will become a root node for
        CTTermAttributes and CTTermName nodes.
        The uid for the CTTermRoot is assigned when the CTTermAttributesAR is being created.
        Created CTTermRoot uid is then passed to the CTTermNameAR.
        The uid of CTTermRoot node is used by CTTermName repository to create a
        relationship from CTTermRoot to CTTermName node when saving a CTTermNameAR.
        :param term_input:
        :return term:CTTerm
        """

        if (
            term_input.libraryName is not None
            and not self._repos.library_repository.library_exists(
                normalize_string(term_input.libraryName)
            )
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
            ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                author=self.user_initials,
                ct_term_attributes_vo=CTTermAttributesVO.from_input_values(
                    codelist_uid=term_input.codelistUid,
                    catalogue_name=term_input.catalogueName,
                    code_submission_value=term_input.codeSubmissionValue,
                    name_submission_value=term_input.nameSubmissionValue,
                    preferred_term=term_input.nciPreferredName,
                    definition=term_input.definition,
                    codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                    catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                    term_exists_by_name_callback=self._repos.ct_term_attributes_repository.term_specific_exists_by_name,
                    term_exists_by_code_submission_value_callback=(
                        self._repos.ct_term_attributes_repository.term_attributes_exists_by_code_submission_value
                    ),
                ),
                library=library_vo,
                generate_uid_callback=self._repos.ct_term_attributes_repository.generate_uid,
            )

            self._repos.ct_term_attributes_repository.save(ct_term_attributes_ar)

            ct_term_name_ar = CTTermNameAR.from_input_values(
                author=self.user_initials,
                ct_term_name_vo=CTTermNameVO.from_input_values(
                    codelist_uid=term_input.codelistUid,
                    catalogue_name=term_input.catalogueName,
                    name=term_input.sponsorPreferredName,
                    name_sentence_case=term_input.sponsorPreferredNameSentenceCase,
                    order=term_input.order,
                    codelist_exists_callback=self._repos.ct_codelist_attribute_repository.codelist_exists,
                    catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                ),
                library=library_vo,
                generate_uid_callback=lambda: ct_term_attributes_ar.uid,
            )

            self._repos.ct_term_name_repository.save(ct_term_name_ar)

        except ValueError as value_error:
            raise exceptions.ValidationException(value_error.args[0])

        return CTTerm.from_ct_term_ars(ct_term_name_ar, ct_term_attributes_ar)

    def get_all_terms(
        self,
        codelist_uid: Optional[str],
        codelist_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTTermNameAndAttributes]:

        self.enforce_codelist_package_library(
            codelist_uid, codelist_name, library, package
        )

        all_aggregated_terms = (
            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
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
        )

        all_aggregated_terms.items = [
            CTTermNameAndAttributes.from_ct_term_ars(
                ct_term_name_ar=term_name_ar, ct_term_attributes_ar=term_attributes_ar
            )
            for term_name_ar, term_attributes_ar in all_aggregated_terms.items
        ]

        return all_aggregated_terms

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

        header_values = self._repos.ct_term_aggregated_repository.get_distinct_headers(
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

    def add_parent(
        self, term_uid: str, parent_uid: str, relationship_type: str
    ) -> CTTerm:
        if not self._repos.ct_term_name_repository.term_exists(
            normalize_string(term_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTTermRoot identified by provided termuid ({term_uid})"
            )
        if not self._repos.ct_term_name_repository.term_exists(
            normalize_string(parent_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTTermRoot identified by provided termuid ({parent_uid})"
            )

        relationship_type = relationship_type.lower()
        if relationship_type == "type":
            rel_type = TermParentType.PARENT_TYPE
        elif relationship_type == "subtype":
            rel_type = TermParentType.PARENT_SUB_TYPE
        elif relationship_type == "valid_for_epoch":
            rel_type = TermParentType.VALID_FOR_EPOCH_TYPE
        else:
            raise exceptions.BusinessLogicException(
                f"The following type ({relationship_type}) is not valid relationship type."
            )

        try:
            self._repos.ct_term_attributes_repository.add_parent(
                term_uid=term_uid, parent_uid=parent_uid, relationship_type=rel_type
            )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )

    def remove_parent(
        self, term_uid: str, parent_uid: str, relationship_type: str
    ) -> CTTerm:

        if not self._repos.ct_term_name_repository.term_exists(
            normalize_string(term_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTTermRoot identified by provided termuid ({term_uid})"
            )
        if not self._repos.ct_term_name_repository.term_exists(
            normalize_string(parent_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTTermRoot identified by provided termuid ({parent_uid})"
            )

        if relationship_type == "type":
            rel_type = TermParentType.PARENT_TYPE
        elif relationship_type == "subtype":
            rel_type = TermParentType.PARENT_SUB_TYPE
        else:
            raise exceptions.BusinessLogicException(
                f"The following type ({relationship_type}) is not valid relationship type."
            )

        try:
            self._repos.ct_term_attributes_repository.remove_parent(
                term_uid=term_uid, parent_uid=parent_uid, relationship_type=rel_type
            )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )

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

    def set_new_order(self, term_uid: str, codelist_uid: str, new_order: int) -> CTTerm:

        if not self._repos.ct_codelist_name_repository.codelist_exists(
            normalize_string(codelist_uid)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no CTCodelistRoot identified by provided codelistuid ({codelist_uid})"
            )

        ct_term_name_ar = self._repos.ct_term_name_repository.find_by_uid(
            term_uid, for_update=True
        )

        if ct_term_name_ar is None:
            raise exceptions.BusinessLogicException(
                f"There is no CTTermRoot identified by provided termuid ({term_uid})"
            )

        ct_term_name_ar.set_new_order(codelist_uid=codelist_uid, new_order=new_order)

        self._repos.ct_term_name_repository.save(ct_term_name_ar)

        ct_term_attributes_ar = self._repos.ct_term_attributes_repository.find_by_uid(
            term_uid=term_uid
        )
        return CTTerm.from_ct_term_ars(
            ct_term_name_ar=ct_term_name_ar, ct_term_attributes_ar=ct_term_attributes_ar
        )
