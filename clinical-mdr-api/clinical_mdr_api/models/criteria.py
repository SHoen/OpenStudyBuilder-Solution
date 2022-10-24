from datetime import datetime
from typing import Dict, List, Optional, Sequence

from pydantic.fields import Field
from pydantic.main import BaseModel

from clinical_mdr_api.domain.library.criteria import CriteriaAR
from clinical_mdr_api.models.criteria_template import CriteriaTemplateNameUid
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
)


class Criteria(BaseModel):
    uid: str
    name: Optional[str] = None
    namePlain: Optional[str] = None

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None

    possibleActions: Optional[Sequence[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the criteria. "
            "Actions are: None"
        ),
    )

    criteriaTemplate: Optional[CriteriaTemplateNameUid]
    parameterValues: Optional[Sequence[MultiTemplateParameterValue]] = Field(
        None,
        description="Holds the parameter values that are used within the criteria. The values are ordered as they occur in the criteria name.",
    )
    library: Optional[Library] = None

    studyCount: Optional[int] = Field(
        None, description="Count of studies referencing criteria"
    )

    @classmethod
    def from_criteria_ar(cls, criteria_ar: CriteriaAR) -> "Criteria":

        parameter_values: List[MultiTemplateParameterValue] = []
        for position, parameter in enumerate(criteria_ar.get_parameters()):
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
            uid=criteria_ar.uid,
            name=criteria_ar.name,
            namePlain=criteria_ar.name_plain,
            startDate=criteria_ar.item_metadata.start_date,
            endDate=criteria_ar.item_metadata.end_date,
            status=criteria_ar.item_metadata.status.value,
            version=criteria_ar.item_metadata.version,
            changeDescription=criteria_ar.item_metadata.change_description,
            userInitials=criteria_ar.item_metadata.user_initials,
            possibleActions=sorted(
                {_.value for _ in criteria_ar.get_possible_actions()}
            ),
            criteriaTemplate=CriteriaTemplateNameUid(
                name=criteria_ar.template_name,
                namePlain=criteria_ar.name_plain,
                uid=criteria_ar.template_uid,
                guidanceText=criteria_ar.template_guidance_text,
            ),
            library=Library.from_library_vo(criteria_ar.library),
            studyCount=criteria_ar.study_count,
            parameterValues=parameter_values,
        )


class CriteriaVersion(Criteria):
    """
    Class for storing Criteria and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria (e.g. name, startDate, ..)."
        ),
    )


class CriteriaParameterInput(BaseModel):
    parameterValues: List[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameterValues",
        description="An ordered list of selected parameter values that are used to replace the parameters of the criteria template.",
    )


class CriteriaEditInput(CriteriaParameterInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaCreateInput(CriteriaParameterInput):
    criteriaTemplateUid: str = Field(
        ...,
        title="criteriaTemplateUid",
        description="The unique id of the criteria template that is used as the basis for the new criteria.",
    )
    nameOverride: Optional[str] = Field(
        None,
        title="name",
        description="Optionally, a name to override the name inherited from the template.",
    )
    libraryName: str = Field(
        None,
        title="libraryName",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )
