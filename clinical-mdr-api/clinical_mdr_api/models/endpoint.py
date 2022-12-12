from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.library.endpoints import EndpointAR
from clinical_mdr_api.models.endpoint_template import EndpointTemplateNameUid
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    IndexedTemplateParameterValue,
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import MultiTemplateParameterValue
from clinical_mdr_api.models.utils import BaseModel


class Endpoint(BaseModel):
    uid: str
    name: Optional[str] = None
    name_plain: Optional[str] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    change_description: Optional[str] = None
    user_initials: Optional[str] = None

    possible_actions: Optional[Sequence[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the endpoint. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    endpoint_template: Optional[EndpointTemplateNameUid]
    parameter_values: Optional[Sequence[MultiTemplateParameterValue]] = Field(
        None,
        description="Holds the parameter values that are used within the endpoint. The values are ordered as they occur in the endpoint name.",
    )
    # objective: Optional[Objective] = None
    library: Optional[Library] = None

    study_count: Optional[int] = Field(
        None, description="Count of studies referencing endpoint"
    )

    @classmethod
    def from_endpoint_ar(cls, endpoint_ar: EndpointAR) -> "Endpoint":

        parameter_values: List[MultiTemplateParameterValue] = []
        for position, parameter in enumerate(endpoint_ar.get_parameters()):
            values: List[IndexedTemplateParameterValue] = []
            for index, parameter_value in enumerate(parameter.parameters):
                pv = IndexedTemplateParameterValue(
                    index=index + 1,
                    uid=parameter_value.uid,
                    name=parameter_value.value,
                    type=parameter.parameter_name,
                )
                values.append(pv)
            conjunction = parameter.conjunction

            parameter_values.append(
                MultiTemplateParameterValue(
                    conjunction=conjunction, position=position + 1, values=values
                )
            )
        return cls(
            uid=endpoint_ar.uid,
            name=endpoint_ar.name,
            name_plain=endpoint_ar.name_plain,
            start_date=endpoint_ar.item_metadata.start_date,
            end_date=endpoint_ar.item_metadata.end_date,
            status=endpoint_ar.item_metadata.status.value,
            version=endpoint_ar.item_metadata.version,
            change_description=endpoint_ar.item_metadata.change_description,
            user_initials=endpoint_ar.item_metadata.user_initials,
            possible_actions=sorted(
                {_.value for _ in endpoint_ar.get_possible_actions()}
            ),
            endpoint_template=EndpointTemplateNameUid(
                name=endpoint_ar.template_name,
                name_plain=endpoint_ar.template_name_plain,
                uid=endpoint_ar.template_uid,
            ),
            library=Library.from_library_vo(endpoint_ar.library),
            study_count=endpoint_ar.study_count,
            parameter_values=parameter_values,
        )


class EndpointVersion(Endpoint):
    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the endpoint (e.g. name, start_date, ..)."
        ),
    )


class EndpointParameterInput(BaseModel):
    parameter_values: List[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_values",
        description="An ordered list of selected parameter values that are used to replace the parameters of the endpoint template.",
    )


class EndpointEditInput(EndpointParameterInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class EndpointCreateInput(EndpointParameterInput):
    endpoint_template_uid: str = Field(
        ...,
        title="endpoint_template_uid",
        description="The unique id of the endpoint template that is used as the basis for the new endpoint.",
    )
    name_override: Optional[str] = Field(
        None,
        title="name",
        description="Optionally, a name to override the name inherited from the template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the endpoint will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the endpoint template will be used.",
    )
