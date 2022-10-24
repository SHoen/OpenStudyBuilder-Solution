import abc
from typing import Optional, Sequence, TypeVar, cast

from neomodel import core, db
from pydantic import BaseModel

from clinical_mdr_api.domain._utils import extract_parameters
from clinical_mdr_api.domain.library.library_ar import LibraryAR
from clinical_mdr_api.domain.library.object import (
    ParametrizedTemplateARBase,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domain.library.parameter_value import (  # noqa: E501
    ComplexParameterValue,
    NumericParameterValueVO,
    ParameterValueEntryVO,
    SimpleParameterValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
    TemplateVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.library.template_parameters_repository import (
    TemplateParameterRepository,
)
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    InternalErrorException,
    NotFoundException,
    ValidationException,
)
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.services._utils import process_complex_parameters
from clinical_mdr_api.services.generic_template_service import (
    GenericLibraryItemServiceBase,  # type: ignore
)

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericObjectService(GenericLibraryItemServiceBase[_AggregateRootType], abc.ABC):
    """
    This class is generic library object service. It can provide services for any type
    of object derived from templates. Supports generic versioning proces with exception that
    it not allows to create new version after it is approved.

    Configuration options:
    aggregate_class - a class of Aggregate root that supports selected object
    repository_interface - repository interface for selected object
    template_repository_interface - repository for template object that selected object is created from
    templateUidProperty - name of template uid property from pydantic models supporting selected object
    templateNameProperty - template name property that service is supposed to return with pydantic object
    """

    aggregate_class: type
    repository_interface: type
    template_repository_interface: type
    templateUidProperty: str
    templateNameProperty: str
    parametrized_template_vo_class: type = ParametrizedTemplateVO
    _allowed_parameters = None

    @property
    def template_repository(self) -> GenericRepository:
        """
        gets template object repository based on interface
        """
        return self.template_repository_interface()

    def _get_parameter_value(self, uid: str) -> str:
        """
        Return parameter value based on uid
        """
        params = []
        for p in self._allowed_parameters:
            params.extend(p["values"])
        params_dict = {item["uid"]: item for item in params}
        return params_dict.get(uid, {}).get("name")

    def create_ar_from_input_values(
        self,
        template,
        generate_uid_callback=None,
        study_uid: Optional[str] = None,
        include_study_endpoints: Optional[bool] = False,
    ) -> _AggregateRootType:
        parameter_values = self._create_parameter_entries(
            template,
            study_uid=study_uid,
            include_study_endpoints=include_study_endpoints,
        )
        template_uid = getattr(template, self.templateUidProperty)
        template_vo = self.parametrized_template_vo_class.from_input_values_2(
            template_uid=template_uid,
            parameter_values=parameter_values,
            name_override=getattr(template, "nameOverride", None),
            get_final_template_vo_by_template_uid_callback=self._get_template_vo_by_template_uid,
            is_instance_editable_callback=self.template_repository.is_template_instance_editable,
        )

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

        item = self.aggregate_class.from_input_values(
            author=self.user_initials,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback
            if generate_uid_callback is None
            else generate_uid_callback,
        )
        return item

    def create(self, template: BaseModel, preview=False) -> BaseModel:
        """
        Supports create object action.
        When the preview parameter is set to true, don't create the object, just preview it.
        """
        # TODO: something to get typing work
        # This function is not decorated with db.transaction as internal transactions
        # are handled manually by "with" statement.
        item = None
        try:

            # Transaction that is performing initial save
            with db.transaction:
                item = self.create_ar_from_input_values(template)
                rep = self.repository

                if item is None:
                    raise InternalErrorException(
                        "Unable to create template instance AR object."
                    )

                if rep.check_exists_by_name(item.name):
                    raise BusinessLogicException("The specified object already exists.")
                if not preview:
                    self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item_ar=item)
        except core.DoesNotExist as exc:
            raise NotFoundException(
                f"The library with the name='{template.libraryName}' could not be found."
            ) from exc
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

    def _get_template_vo_by_template_uid(
        self, template_uid: str
    ) -> Optional[TemplateVO]:
        """
        Helper function getting template for given template uid.
        """
        template_ar = self.template_repository.find_by_uid_2(
            template_uid, status=LibraryItemStatus.FINAL
        )
        return template_ar.template_value if template_ar is not None else None

    @db.transaction
    def find_by(self, name: str):
        item = self.repository.find_by(name=name)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def edit_draft(self, uid, template: BaseModel):
        """
        Supports edit draft action
        """
        # TODO: do sth for better typing
        try:
            item: ParametrizedTemplateARBase = self._find_by_uid_or_raise_not_found(
                uid, for_update=True
            )
            parameter_values = self._create_parameter_entries(
                template, template_uid=item.template_uid
            )

            try:
                template_vo = self.parametrized_template_vo_class.from_input_values_2(
                    template_uid=item.template_uid,
                    parameter_values=parameter_values,
                    get_final_template_vo_by_template_uid_callback=self._get_template_vo_by_template_uid,
                )
            except ValueError as e:
                raise ValidationException(e.args[0]) from e
            item.edit_draft(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        """
        Create new version is not allowed for objects derived from templates.
        Only cascading update can do that
        """
        raise NotImplementedError("You cannot create new version")

    @db.transaction
    def get_parameters(
        self,
        uid: str,
        study_uid: Optional[str] = None,
        include_study_endpoints: Optional[bool] = False,
    ):
        try:
            parameter_repository = TemplateParameterRepository()
            item = self._find_by_uid_or_raise_not_found(uid)
            parameters = self.template_repository.get_parameters_including_values(
                item.template_uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
            )
            return process_complex_parameters(parameters, parameter_repository)
        except core.DoesNotExist as exc:
            raise NotFoundException(
                f"The object  with uid='{uid}' could not be found."
            ) from exc

    def _create_parameter_entries(
        self,
        template,
        template_uid: Optional[str] = None,
        study_uid: Optional[str] = None,
        include_study_endpoints: Optional[bool] = False,
    ) -> Sequence[ParameterValueEntryVO]:
        """
        Creates sequence of Parameter Value Entries that is used in aggregate. These contain:
        parameter name, conjunctions, uids, and values of parameters
        """
        if template_uid is None:
            template_uid = getattr(template, self.templateUidProperty)
        parameter_values = []
        self._allowed_parameters = (
            self.template_repository.get_parameters_including_values(
                template_uid,
                study_uid=study_uid,
                include_study_endpoints=include_study_endpoints,
            )
        )
        parameter: TemplateParameterMultiSelectInput
        idx = 0
        for _, allowed_parameter in enumerate(self._allowed_parameters):
            if allowed_parameter.get(
                "definition"
            ):  # What is this check? Is this a different way of writing allowed_parameter != CTTerm?
                param_names = extract_parameters(allowed_parameter["template"])
                params = []
                for param_name in param_names:
                    parameter = template.parameterValues[idx]
                    if param_name != "NumericValue":
                        tp = SimpleParameterValueVO(
                            uid=parameter.values[0].uid, value=parameter.values[0].name
                        )
                    else:
                        tp = NumericParameterValueVO(
                            uid="", value=template.parameterValues[idx].value
                        )
                    idx += 1
                    params.append(tp)
                parameter_values.append(
                    ComplexParameterValue(
                        uid=allowed_parameter.get("definition"),
                        parameter_template=allowed_parameter["template"],
                        parameters=params,
                    )
                )
            else:
                parameter = template.parameterValues[idx]
                uids = []

                if len(parameter.values) == 0:
                    # If we have an empty paremeter value selection, send an empty list with default type fro the allowed parameters.
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
                        parameter_name=allowed_parameter[
                            "name"
                        ],  # Item is used out of context of the for-loop
                        conjunction=parameter.conjunction,
                        parameters=uids,
                    )
                    parameter_values.append(pve)
                    idx += 1
                else:
                    # Else, iterate over the provided values, store them and their type dynamically.
                    for item in parameter.values:
                        pv = SimpleParameterValueVO.from_input_values(
                            value_by_uid_lookup_callback=self._get_parameter_value,
                            uid=item.uid,
                        )
                        uids.append(pv)
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
                        # pylint:disable=undefined-loop-variable
                        parameter_name=item.type,
                        conjunction=parameter.conjunction,
                        parameters=uids,
                    )
                    parameter_values.append(pve)
                    idx += 1
        return parameter_values
