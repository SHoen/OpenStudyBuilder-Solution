import abc
from datetime import datetime
from typing import Any, Generic, Optional, Sequence, TypeVar

from neomodel import db
from pydantic import BaseModel
from starlette.requests import Request

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_generic_repository import (
    CTCodelistGenericRepository,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import calculate_diffs, normalize_string

_AggregateRootType = TypeVar("_AggregateRootType")


class CTCodelistGenericService(Generic[_AggregateRootType], abc.ABC):
    @abc.abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    def get_input_or_previous_property(
        self, input_property: Any, previous_property: Any
    ):
        return input_property if input_property is not None else previous_property

    def get_codelist_etag(self, request: Request) -> str:
        codelist_uid = request.path_params["codelistuid"]
        etag = self.repository.get_codelist_etag_value(codelist_uid=codelist_uid)
        return f"{codelist_uid}_{etag}"

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
    def repository(self) -> CTCodelistGenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @db.transaction
    def get_all_ct_codelists(
        self,
        catalogue_name: Optional[str],
        library: Optional[str],
        package: Optional[str],
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:

        self.enforce_catalogue_library_package(catalogue_name, library, package)

        all_ct_codelists = self.repository.find_all(
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

        all_ct_codelists.items = [
            self._transform_aggregate_root_to_pydantic_model(ct_codelist_ar)
            for ct_codelist_ar in all_ct_codelists.items
        ]
        return all_ct_codelists

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
    ) -> Sequence:

        self.enforce_catalogue_library_package(catalogue_name, library, package)

        header_values = self.repository.get_distinct_headers(
            catalogue_name=catalogue_name,
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
    def get_by_uid(
        self,
        codelist_uid: str,
        version: Optional[str] = None,
        at_specific_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> BaseModel:

        item = self._find_by_uid_or_raise_not_found(
            codelist_uid=codelist_uid,
            version=version,
            at_specific_date=at_specific_date,
            status=status,
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        codelist_uid: str,
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
            codelist_uid=codelist_uid,
            at_specific_date=at_specific_date,
            version=version,
            status=codelist_status,
            for_update=for_update,
        )
        if item is None:
            raise exceptions.NotFoundException(
                f"""{self.aggregate_class.__name__} with uid {codelist_uid} does not exist
                or there's no version with requested status or version number."""
            )
        return item

    @db.transaction
    def get_version_history(self, codelist_uid) -> Sequence[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions(codelist_uid)
            if all_versions is None:
                raise exceptions.NotFoundException(
                    f"{self.aggregate_class.__name__} with uid {codelist_uid} does not exist."
                )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(codelist_ar).dict()
                for codelist_ar in all_versions
            ]
            return calculate_diffs(versions, self.version_class)
        return []

    @db.transaction
    def create_new_version(self, codelist_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
            item.create_new_version(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @abc.abstractmethod
    def edit_draft(self, codelist_uid: str, codelist_input: BaseModel) -> BaseModel:
        raise NotImplementedError()

    @db.transaction
    def approve(self, codelist_uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(
                codelist_uid=codelist_uid, for_update=True
            )
            item.approve(author=self.user_initials)
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

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
