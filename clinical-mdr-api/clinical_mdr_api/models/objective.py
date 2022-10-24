from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.library.objectives import ObjectiveAR
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.objective_template import ObjectiveTemplateNameUid
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
)
from clinical_mdr_api.models.utils import BaseModel


class Objective(BaseModel):
    uid: Optional[str] = None
    name: Optional[str] = None
    namePlain: Optional[str] = None

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None

    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the objective. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    objectiveTemplate: Optional[ObjectiveTemplateNameUid]
    parameterValues: Optional[List[MultiTemplateParameterValue]] = Field(
        None,
        description="Holds the parameter values that are used within the objective. The values are ordered as they occur in the objective name.",
    )
    library: Optional[Library] = None

    studyCount: Optional[int] = Field(
        None, description="Count of studies referencing objective"
    )

    @classmethod
    def from_objective_ar(cls, objective_ar: ObjectiveAR) -> "Objective":
        parameter_values: List[MultiTemplateParameterValue] = []
        for position, parameter in enumerate(objective_ar.get_parameters()):
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
            uid=objective_ar.uid,
            name=objective_ar.name,
            namePlain=objective_ar.name_plain,
            startDate=objective_ar.item_metadata.start_date,
            endDate=objective_ar.item_metadata.end_date,
            status=objective_ar.item_metadata.status.value,
            version=objective_ar.item_metadata.version,
            changeDescription=objective_ar.item_metadata.change_description,
            userInitials=objective_ar.item_metadata.user_initials,
            possibleActions=sorted(
                {_.value for _ in objective_ar.get_possible_actions()}
            ),
            objectiveTemplate=ObjectiveTemplateNameUid(
                name=objective_ar.template_name,
                namePlain=objective_ar.template_name_plain,
                uid=objective_ar.template_uid,
            ),
            library=Library.from_library_vo(objective_ar.library),
            studyCount=objective_ar.study_count,
            parameterValues=parameter_values,
        )


class ObjectiveVersion(Objective):
    """
    Class for storing Objectives and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )


class ObjectiveParameterInput(BaseModel):
    parameterValues: List[TemplateParameterMultiSelectInput] = Field(
        None,
        title="parameterValues",
        description="An ordered list of selected parameter values that are used to replace the parameters of the objective template.",
    )


class ObjectiveEditInput(ObjectiveParameterInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ObjectiveCreateInput(ObjectiveParameterInput):
    objectiveTemplateUid: str = Field(
        ...,
        title="objectiveTemplateUid",
        description="The unique id of the objective template that is used as the basis for the new objective.",
    )
    nameOverride: Optional[str] = Field(
        None,
        title="name",
        description="Optionally, a name to override the name inherited from the template.",
    )
    libraryName: str = Field(
        None,
        title="libraryName",
        description="If specified: The name of the library to which the objective will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true. \n\n"
        "If not specified: The library of the objective template will be used.",
    )
