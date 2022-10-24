from typing import Optional, Sequence, TypeVar

from neomodel import db
from starlette.requests import Request

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models import (
    CTCodelist,
    CTCodelistCreateInput,
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import normalize_string

_AggregateRootType = TypeVar("_AggregateRootType")


class CTCodelistService:
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"
        self._repos = MetaRepository(self.user_initials)

    def __del__(self):
        self._repos.close()

    def get_codelist_etag(self, request: Request) -> str:
        codelist_uid = request.path_params["codelistuid"]
        attributes_etag = (
            self._repos.ct_codelist_attribute_repository.get_codelist_etag_value(
                codelist_uid=codelist_uid
            )
        )
        name_etag = self._repos.ct_codelist_name_repository.get_codelist_etag_value(
            codelist_uid=codelist_uid
        )
        return f"{codelist_uid}_{attributes_etag}_{codelist_uid}_{name_etag}"

    @db.transaction
    def create(self, codelistInput: CTCodelistCreateInput) -> CTCodelist:
        """
        Method creates CTCodelistAttributesAR and saves that object to the database.
        When saving CTCodelistAttributesAR - CTCodelistRoot node is created that will become a root node for
        CTCodelistAttributes and CTCodelistName nodes.
        The uid for the CTCodelistRoot is assigned when the CTCodelistAttributesAR is being created.
        Created CTCodelistRoot uid is then passed to the CTCodelistNameAR.
        The uid of CTCodelistRoot node is used by CTCodelistName repository to create a
        relationship from CTCodelistRoot to CTCodelistName node when saving a CTCodelistNameAR.
        If terms are provided then the codelist will be approved and the terms will be connected to the codelist.
        When no terms are provided the codelist is created in draft state.
        :param codelistInput:
        :return codelist:CTCodelist
        """

        if not self._repos.library_repository.library_exists(
            normalize_string(codelistInput.libraryName)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({codelistInput.libraryName})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=codelistInput.libraryName,
            is_library_editable_callback=(
                lambda name: self._repos.library_repository.find_by_name(
                    name
                ).is_editable
                if self._repos.library_repository.find_by_name(name) is not None
                else None
            ),
        )
        try:
            ct_codelist_attributes_ar = CTCodelistAttributesAR.from_input_values(
                author=self.user_initials,
                ct_codelist_attributes_vo=CTCodelistAttributesVO.from_input_values(
                    name=codelistInput.name,
                    parent_codelist_uid=codelistInput.parentCodelistUid,
                    catalogue_name=codelistInput.catalogueName,
                    submission_value=codelistInput.submissionValue,
                    preferred_term=codelistInput.nciPreferredName,
                    definition=codelistInput.definition,
                    extensible=codelistInput.extensible,
                    catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                    codelist_exists_by_uid_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_uid,
                    codelist_exists_by_name_callback=self._repos.ct_codelist_attribute_repository.codelist_specific_exists_by_name,
                    codelist_exists_by_submission_value_callback=(
                        self._repos.ct_codelist_attribute_repository.codelist_attributes_exists_by_submission_value
                    ),
                ),
                library=library_vo,
                generate_uid_callback=self._repos.ct_codelist_attribute_repository.generate_uid,
            )

            if codelistInput.terms:
                ct_codelist_attributes_ar.approve(author=self.user_initials)

            self._repos.ct_codelist_attribute_repository.save(ct_codelist_attributes_ar)

            ct_codelist_name_ar = CTCodelistNameAR.from_input_values(
                author=self.user_initials,
                ct_codelist_name_vo=CTCodelistNameVO.from_input_values(
                    name=codelistInput.sponsorPreferredName,
                    catalogue_name=codelistInput.catalogueName,
                    is_template_parameter=codelistInput.templateParameter,
                    catalogue_exists_callback=self._repos.ct_catalogue_repository.catalogue_exists,
                    codelist_exists_by_name_callback=self._repos.ct_codelist_name_repository.codelist_specific_exists_by_name,
                ),
                library=library_vo,
                generate_uid_callback=lambda: ct_codelist_attributes_ar.uid,
            )

            self._repos.ct_codelist_name_repository.save(ct_codelist_name_ar)

            if codelistInput.terms:
                parent_codelist_uid = (
                    ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
                )

                term_uids = [term.termUid for term in codelistInput.terms]

                if parent_codelist_uid:
                    sub_codelist_with_given_terms = (
                        self.get_sub_codelists_that_have_given_terms(
                            parent_codelist_uid, term_uids
                        )
                    )

                    if sub_codelist_with_given_terms.items:
                        raise exceptions.BusinessLogicException(
                            f"""Sub codelists with these terms already exist.
                            Codelist UIDs ({[item.codelistUid for item in sub_codelist_with_given_terms.items]})"""
                        )

                for term in codelistInput.terms:
                    if (
                        parent_codelist_uid
                        and not len(
                            self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                                filter_by={
                                    "codelistUid": {
                                        "v": [parent_codelist_uid],
                                        "op": "eq",
                                    },
                                    "termUid": {"v": [term.termUid], "op": "eq"},
                                }
                            ).items
                        )
                        > 0
                    ):
                        raise exceptions.BusinessLogicException(
                            f"The term identifed by ({term.termUid}) is not in use by parent codelist identifed by ({parent_codelist_uid})"
                        )

                    ct_codelist_name_ar = (
                        self._repos.ct_codelist_name_repository.find_by_uid(
                            codelist_uid=ct_codelist_attributes_ar.uid
                        )
                    )

                    self._repos.ct_codelist_attribute_repository.add_term(
                        codelist_uid=ct_codelist_attributes_ar.uid,
                        term_uid=term.termUid,
                        author=self.user_initials,
                        order=term.order,
                    )

        except ValueError as value_error:
            raise exceptions.ValidationException(value_error.args[0])

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    def get_all_codelists(
        self,
        catalogue_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:

        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_codelists = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                catalogue_name=catalogue_name,
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

        all_aggregated_codelists.items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar, ct_codelist_attributes_ar
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar in all_aggregated_codelists.items
        ]

        return all_aggregated_codelists

    def get_sub_codelists_that_have_given_terms(
        self,
        codelist_uid: str,
        term_uids: Sequence[str],
        catalogue_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CTCodelistNameAndAttributes]:
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_aggregated_sub_codelists = (
            self._repos.ct_codelist_aggregated_repository.find_all_aggregated_result(
                library=library,
                total_count=total_count,
                sort_by=sort_by,
                filter_by={"parentCodelistUid": {"v": [codelist_uid], "op": "eq"}},
                filter_operator=filter_operator,
                page_number=page_number,
                page_size=page_size,
            )
        )

        uid_of_sub_codelist_with_terms = []

        for sub_codelist in all_aggregated_sub_codelists.items:
            all_aggregated_terms = (
                self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    codelist_uid=sub_codelist[1].uid,
                    codelist_name=None,
                    library=library,
                    package=package,
                    total_count=total_count,
                    sort_by=sort_by,
                    filter_by=filter_by,
                    filter_operator=filter_operator,
                    page_number=page_number,
                    page_size=page_size,
                )
            ).items

            if set(term_uids) == {term[1].uid for term in all_aggregated_terms}:
                uid_of_sub_codelist_with_terms.append(sub_codelist[1].uid)

        all_aggregated_sub_codelists.items = [
            CTCodelistNameAndAttributes.from_ct_codelist_ar(
                ct_codelist_name_ar, ct_codelist_attributes_ar
            )
            for ct_codelist_name_ar, ct_codelist_attributes_ar in all_aggregated_sub_codelists.items
            if ct_codelist_attributes_ar.uid in uid_of_sub_codelist_with_terms
        ]

        return all_aggregated_sub_codelists

    def get_distinct_values_for_header(
        self,
        catalogue_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):
        self.enforce_catalogue_library_package(catalogue_name, library, package)

        header_values = (
            self._repos.ct_codelist_aggregated_repository.get_distinct_headers(
                catalogue_name=catalogue_name,
                library=library,
                package=package,
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )
        )

        return header_values

    @db.transaction
    def add_term(self, codelistuid: str, termUid: str, order: int) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelistuid
            )
        )

        if ct_codelist_attributes_ar is not None:
            if (
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible
            ):
                raise exceptions.BusinessLogicException(
                    f"Codelist identified by {codelistuid} is not extensible"
                )

            parent_codelist_uid = (
                ct_codelist_attributes_ar.ct_codelist_vo.parent_codelist_uid
            )
            if (
                parent_codelist_uid
                and not len(
                    self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                        filter_by={
                            "codelistUid": {
                                "v": [parent_codelist_uid],
                                "op": "eq",
                            },
                            "termUid": {"v": [termUid], "op": "eq"},
                        }
                    ).items
                )
                > 0
            ):
                raise exceptions.BusinessLogicException(
                    f"The term identifed by ({termUid}) is not in use by parent codelist identifed by ({parent_codelist_uid})"
                )

        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelistuid
        )
        try:
            self._repos.ct_codelist_attribute_repository.add_term(
                codelist_uid=codelistuid,
                term_uid=termUid,
                author=self.user_initials,
                order=order,
            )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    @db.transaction
    def remove_term(self, codelistuid: str, termUid: str) -> CTCodelist:
        ct_codelist_attributes_ar = (
            self._repos.ct_codelist_attribute_repository.find_by_uid(
                codelist_uid=codelistuid
            )
        )
        if ct_codelist_attributes_ar is not None:
            if (
                not ct_codelist_attributes_ar.library.is_editable
                and not ct_codelist_attributes_ar.ct_codelist_vo.extensible
            ):
                raise exceptions.BusinessLogicException(
                    f"Codelist identified by {codelistuid} is not extensible"
                )

            child_codelist_uids = (
                ct_codelist_attributes_ar.ct_codelist_vo.child_codelist_uids
            )
            if child_codelist_uids:
                terms = self._repos.ct_term_aggregated_repository.find_all_aggregated_result(
                    filter_by={
                        "codelistUid": {
                            "v": child_codelist_uids,
                            "op": "eq",
                        },
                        "termUid": {"v": [termUid], "op": "eq"},
                    }
                ).items
                if len(terms) > 0:
                    raise exceptions.BusinessLogicException(
                        f"""The term identifed by ({termUid}) is in use by child codelists
                        identifed by {[term[1]._ct_term_attributes_vo.codelist_uid for term in terms]}"""
                    )
        ct_codelist_name_ar = self._repos.ct_codelist_name_repository.find_by_uid(
            codelist_uid=codelistuid
        )

        try:
            self._repos.ct_codelist_attribute_repository.remove_term(
                codelist_uid=codelistuid, term_uid=termUid, author=self.user_initials
            )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        return CTCodelist.from_ct_codelist_ar(
            ct_codelist_name_ar, ct_codelist_attributes_ar
        )

    def enforce_catalogue_library_package(
        self,
        catalogue_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
    ):
        if (
            catalogue_name is not None
            and not self._repos.ct_catalogue_repository.catalogue_exists(
                normalize_string(catalogue_name)
            )
        ):
            raise exceptions.BusinessLogicException(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
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
