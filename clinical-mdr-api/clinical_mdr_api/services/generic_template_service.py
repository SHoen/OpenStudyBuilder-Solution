import abc
from datetime import datetime
from typing import Generic, Optional, Sequence, Tuple, TypeVar, cast

from neomodel import core, db
from pydantic import BaseModel

from clinical_mdr_api.domain._utils import extract_parameters
from clinical_mdr_api.domain.library.library_ar import LibraryAR
from clinical_mdr_api.domain.library.parameter_value import (
    ParameterValueEntryVO,
    SimpleParameterValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
    TemplateAggregateRootBase,
    TemplateVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.library.generic_template_object_repository import (
    GenericTemplateBasedObjectRepository,
)
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.template_parameters.complex_parameter import (
    ComplexTemplateParameterRepository,
)
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    ConflictErrorException,
    NotFoundException,
    ValidationException,
)
from clinical_mdr_api.models.study import Study
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import MultiTemplateParameterValue
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from clinical_mdr_api.services._utils import (  # type: ignore
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
    process_complex_parameters,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.study import StudyService

_AggregateRootType = TypeVar("_AggregateRootType", bound=TemplateAggregateRootBase)


class GenericLibraryItemServiceBase(Generic[_AggregateRootType], abc.ABC):
    @abc.abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, template: BaseModel) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def edit_draft(self, uid: str, template: BaseModel) -> BaseModel:
        raise NotImplementedError

    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO Initials"
        self._repos = MetaRepository()

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> GenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @property
    def study_repository(self) -> StudyDefinitionRepository:
        return self._repos.study_definition_repository

    def get_by_uid(
        self,
        uid: str,
        return_instantiation_counts: bool = False,
        return_study_count: Optional[bool] = True,
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            uid,
            return_study_count=return_study_count,
            return_instantiation_counts=return_instantiation_counts,
        )
        item = self._transform_aggregate_root_to_pydantic_model(item)
        self._set_groupings(item)
        return item

    @db.transaction
    def get_specific_version(
        self, uid: str, version: str, return_study_count: Optional[bool] = True
    ) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(
            uid, return_study_count=return_study_count, version=version
        )
        item = self._transform_aggregate_root_to_pydantic_model(item)
        self._set_groupings(item)
        return item

    def _find_by_uid_or_raise_not_found(
        self,
        uid: str,
        *,
        version: Optional[str] = None,
        at_specific_date: Optional[datetime] = None,
        status: Optional[LibraryItemStatus] = None,
        for_update: bool = False,
        return_instantiation_counts: bool = False,
        return_study_count: Optional[bool] = True,
    ) -> _AggregateRootType:

        item = self.repository.find_by_uid_2(
            uid,
            for_update=for_update,
            at_specific_date=at_specific_date,
            version=version,
            status=status,
            return_study_count=return_study_count,
            return_instantiation_counts=return_instantiation_counts,
        )
        if item is None:
            raise NotFoundException(
                f"{self.aggregate_class.__name__} with uid {uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def get_all(
        self, status: Optional[str] = None, return_study_count: Optional[bool] = True
    ) -> Sequence[BaseModel]:
        if status is not None:
            all_items = self.repository.find_all(
                status=LibraryItemStatus(status), return_study_count=return_study_count
            )
        else:
            all_items = self.repository.find_all(return_study_count=return_study_count)

        # Transform the items into the model expected by pydantic
        all_items = [
            self._transform_aggregate_root_to_pydantic_model(item) for item in all_items
        ]

        # Finally, set the groupings directly to the pydantic model
        # The groupings are directly transformed into the pydantic model in this method
        for item in all_items:
            self._set_groupings(item)
        return all_items

    def get_distinct_values_for_header(
        self,
        field_name: str,
        status: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):

        all_items = self.get_all(status=status, return_study_count=False)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_releases_referenced_by_any_study(self) -> Sequence[BaseModel]:
        items = self.repository.find_releases_referenced_by_any_study()
        return [
            self._transform_aggregate_root_to_pydantic_model(item) for item in items
        ]

    @db.transaction
    def get_referencing_studies(
        self, uid: str, node_type: core.NodeMeta, fields: Optional[str] = ""
    ) -> Sequence[Study]:
        studies = self.study_repository.find_all_by_library_item_uid(
            uid=uid, library_item_type=node_type, sort_by={"uid": True}
        ).items

        study_service = StudyService(user=self.user_initials)
        return_items = [
            study_service._models_study_from_study_definition_ar(
                study_definition_ar=item,
                find_project_by_project_number=self._repos.project_repository.find_by_project_number,
                find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                fields=fields,
            )
            for item in studies
        ]
        return return_items

    def _parameter_name_exists(self, parameter_name: str) -> bool:
        return self._repos.parameter_repository.parameter_name_exists(parameter_name)

    def _raise_not_found_if_library_does_not_exist_or_return_its_is_editable(
        self, library_name: str
    ) -> bool:
        if self._repos.library_repository.find_by_name(library_name) is None:
            raise NotFoundException(
                f"The library with the name='{library_name}' could not be found."
            )
        return self._repos.library_repository.find_by_name(library_name).is_editable

    @db.transaction
    def approve(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            uses = self.repository.check_usage_count(uid)
            if uses > 0:
                raise ConflictErrorException(
                    f"Template '{item.name}' is used in {uses} instantiations."
                )
            item.approve(author=self.user_initials)
            self.repository.save(item)
            item = self._transform_aggregate_root_to_pydantic_model(item)
            self._set_groupings(item)
            return item
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        # TODO: do sth for better typing
        try:
            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                parameter_name_exists_callback=self._parameter_name_exists,
            )  # noqa: E501
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

            item.create_new_version(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def inactivate_final(self, uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        try:
            item.inactivate(author=self.user_initials)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

        self.repository.save(item)
        item = self._transform_aggregate_root_to_pydantic_model(item)
        self._set_groupings(item)
        return item

    @db.transaction
    def reactivate_retired(self, uid: str) -> BaseModel:
        item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

        try:
            item.reactivate(author=self.user_initials)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

        self.repository.save(item)
        item = self._transform_aggregate_root_to_pydantic_model(item)
        self._set_groupings(item)
        return item

    @db.transaction
    def get_version_history(
        self, uid: str, return_study_count: Optional[bool] = True
    ) -> Sequence[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.get_all_versions_2(
                uid, return_study_count=return_study_count
            )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(_).dict()
                for _ in all_versions
            ]
            data = calculate_diffs(versions, self.version_class)
            for item in data:
                self._set_groupings(item)
            return data
        return []

    @db.transaction
    def get_releases(
        self, uid: str, return_study_count: Optional[bool] = True
    ) -> Sequence[BaseModel]:
        releases = self.repository.find_releases(
            uid=uid, return_study_count=return_study_count
        )
        releases = [
            self._transform_aggregate_root_to_pydantic_model(item) for item in releases
        ]
        for item in releases:
            self._set_groupings(item)
        return releases

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.soft_delete()
            self.repository.save(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    def _set_default_parameter_values(self, item: BaseModel) -> BaseModel:
        """
        This method fetches and sets the default parameter values for a template.
        This method can be template-specific and must be implemented in the template service.
        """
        raise NotImplementedError(
            "Default parameter values handler is not implemented for this service."
        )

    def _set_groupings(self, item: BaseModel) -> None:
        """
        This method fetches and sets the grouping properties to a template.
        These are template-specific and must be implemented in the template-specific service.
        """


class GenericTemplateService(
    GenericLibraryItemServiceBase[_AggregateRootType], abc.ABC
):

    object_repository_interface: type

    @property
    def object_repository(self) -> GenericTemplateBasedObjectRepository:
        return self.object_repository_interface()

    def get_check_exists_callback(self, template: BaseModel):
        if hasattr(template, "studyUid") and template.studyUid:
            return lambda _template_vo: self.repository.check_exists_by_name_in_study(
                name=_template_vo.name, study_uid=template.studyUid
            )
        return lambda _template_vo: self.repository.check_exists_by_name_in_library(
            name=_template_vo.name, library=template.libraryName
        )

    def _create_ar_from_input_values(
        self, template: BaseModel
    ) -> TemplateAggregateRootBase:
        template_vo, library_vo = self._create_template_vo(template)

        # Process item to save
        try:
            item = TemplateAggregateRootBase.from_input_values(
                template_value_exists_callback=self.get_check_exists_callback(
                    template=template
                ),
                author=self.user_initials,
                template=template_vo,
                library=library_vo,
                editable_instance=template.editableInstance,
                generate_uid_callback=self.repository.generate_uid_callback,
            )
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

        return item

    def create(self, template: BaseModel) -> BaseModel:
        # This function is not decorated with db.transaction as internal transactions
        # are handled manually by "with" statement.
        try:
            # Transaction that is performing initial save
            with db.transaction:
                item = self._create_ar_from_input_values(template)

                # Save item
                self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item)
        except core.DoesNotExist as exc:
            raise NotFoundException(
                f"The library with the name='{template.libraryName}' could not be found."
            ) from exc
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    def _create_template_vo(
        self,
        template: BaseModel,
        default_parameter_values: Optional[Sequence[ParameterValueEntryVO]] = None,
    ) -> Tuple[TemplateVO, LibraryVO]:
        # Create TemplateVO
        template_vo = TemplateVO.from_input_values_2(
            template_name=template.name,
            template_guidance_text=template.guidanceText
            if hasattr(template, "guidanceText")
            else None,
            parameter_name_exists_callback=self._parameter_name_exists,
            default_parameter_values=default_parameter_values,
        )

        # Fetch library
        try:
            library_vo = LibraryVO.from_input_values_2(
                library_name=template.libraryName,
                is_library_editable_callback=(
                    lambda name: (
                        cast(
                            LibraryAR, self._repos.library_repository.find_by_name(name)
                        ).is_editable
                        if self._repos.library_repository.find_by_name(name) is not None
                        else None
                    )
                ),
            )
        except ValueError as exc:
            raise NotFoundException(
                f"The library with the name='{template.libraryName}' could not be found."
            ) from exc

        return template_vo, library_vo

    def patch_default_parameter_values(
        self,
        uid: str,
        set_number: int,
        default_parameter_values: Sequence[MultiTemplateParameterValue],
    ) -> BaseModel:
        # Get template AR and use it to parse the default parameter values
        template = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        parsed_default_parameter_values = self._create_default_parameter_entries(
            template_name=template.name,
            default_parameter_values=default_parameter_values,
        )

        # Patch the set of default parameter values
        self.repository.patch_default_parameter_values(
            versioned_object=template,
            parameters=parsed_default_parameter_values,
            set_number=set_number,
        )

        # Finally, get the complete template object and return it
        return self.get_by_uid(uid)

    def _create_default_parameter_entries(
        self,
        template_name: str,
        default_parameter_values: Optional[Sequence[MultiTemplateParameterValue]],
    ) -> Sequence[ParameterValueEntryVO]:
        """
        Creates sequence of Parameter Value Entries that is used in aggregate. These contain:
        parameter name, conjunctions, uids, and values of parameters
        """
        parameter_values = []
        # TODO : Replace the loop on allowed parameters for a loop on the template.parameters
        # Or a loop on parameters where a default value is provided
        parameters = extract_parameters(template_name)
        for i, allowed_parameter in enumerate(parameters):
            uids = []
            conjunction = ""
            parameter_name = ""

            # Find default value for parameter using the "position" property
            parameter: Optional[TemplateParameterMultiSelectInput] = None
            if (
                default_parameter_values is not None
                and len(default_parameter_values) > 0
            ):
                parameter = next(
                    filter(
                        lambda param, i=i: param.position - 1 == i,
                        default_parameter_values,
                    ),
                    None,
                )

            if parameter is None:
                # If we have an empty parameter value selection, send an empty list with default type for the allowed parameters.
                parameter_name = allowed_parameter
            else:
                # Else, iterate over the provided values, store them and their type dynamically.
                for item in parameter.values:
                    pv = SimpleParameterValueVO.from_input_values(
                        value=item.name, uid=item.uid
                    )
                    uids.append(pv)
                parameter_name = parameter.values[0].type
                conjunction = parameter.conjunction

            pve = ParameterValueEntryVO.from_input_values(
                parameter_exists_callback=self._repos.parameter_repository.parameter_name_exists,
                conjunction_exists_callback=lambda _: True,  # TODO: provide proper callback here
                parameter_value_uid_exists_for_parameter_callback=(
                    lambda p_name, v_uid, p_value: (
                        self._repos.parameter_repository.is_parameter_value_uid_valid_for_parameter_name(
                            parameter_value_uid=v_uid,
                            parameter_name=p_name,
                        )
                    )
                ),
                parameter_name=parameter_name,
                conjunction=conjunction,
                parameters=uids,
            )
            parameter_values.append(pve)
        return parameter_values

    @db.transaction
    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

            # fill the missing from the inputs
            fill_missing_values_in_base_model_from_reference_base_model(
                base_model_with_missing_values=template,
                reference_base_model=self._transform_aggregate_root_to_pydantic_model(
                    item
                ),
            )

            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                template_guidance_text=template.guidanceText,
                parameter_name_exists_callback=self._parameter_name_exists,
            )  # noqa: E501

            item.create_new_version(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )
            self.repository.save(item)
            item = self._transform_aggregate_root_to_pydantic_model(item)
            self._set_groupings(item)
            return item
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def approve_cascade(self, uid: str) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            item.approve(author=self.user_initials)
            related_items_uids = self.object_repository.find_item_uids_by_template_uid(
                uid
            )
            related_items = []
            for r_uid in related_items_uids:
                related_item = self.object_repository.find_by_uid_2(
                    r_uid, for_update=True
                )
                assert related_item is not None
                related_items.append(related_item)
            self.repository.save(item)
            related_items = []
            for r_uid in related_items_uids:
                related_item = self.object_repository.find_by_uid_2(
                    r_uid, for_update=True
                )
                assert related_item is not None
                related_item.cascade_update(
                    author=self.user_initials,
                    date=item.item_metadata.start_date,
                    new_template_name=item.name,
                )
                self.object_repository.save(related_item)

            item = self._transform_aggregate_root_to_pydantic_model(item)
            self._set_groupings(item)
            return item

        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def edit_draft(self, uid: str, template: BaseModel) -> BaseModel:
        try:
            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                parameter_name_exists_callback=self._parameter_name_exists,
            )

            item = self._find_by_uid_or_raise_not_found(
                uid, for_update=True, return_study_count=True
            )

            item.edit_draft(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def get_parameters(
        self,
        uid: str,
        study_uid: Optional[str] = None,
        include_study_endpoints: Optional[bool] = False,
    ):
        try:
            parameter_repository_2 = ComplexTemplateParameterRepository()

            parameters = self.repository.get_parameters_including_values(
                template_uid=uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
            )
            return process_complex_parameters(parameters, parameter_repository_2)
        except core.DoesNotExist as exc:
            raise NotFoundException(
                f"The object  with uid='{uid}' could not be found."
            ) from exc

    @db.transaction
    def validate_template_syntax(self, template_name_to_validate: str) -> None:
        try:
            TemplateVO.from_input_values_2(
                template_name=template_name_to_validate,
                parameter_name_exists_callback=self._parameter_name_exists,
            )
        except ValueError as exc:
            raise ValidationException(exc.args[0]) from exc
