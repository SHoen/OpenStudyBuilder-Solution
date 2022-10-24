from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.library.activity_instructions import ActivityInstructionAR
from clinical_mdr_api.models.activity_description_template import (
    ActivityDescriptionTemplateNameUid,
)
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
)
from clinical_mdr_api.models.utils import BaseModel


class ActivityInstructionNameUid(BaseModel):
    uid: Optional[str] = None
    name: Optional[str] = None
    namePlain: Optional[str] = None


class ActivityInstruction(ActivityInstructionNameUid):
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None
    activityInstructionTemplate: Optional[ActivityDescriptionTemplateNameUid]
    parameterValues: Optional[List[MultiTemplateParameterValue]] = Field(
        None,
        description="""Holds the parameter values that are used within the activity
        instruction. The values are ordered as they occur in the activity instruction name.""",
    )
    library: Optional[Library] = None

    studyCount: Optional[int] = Field(
        None, description="Count of studies referencing activity instruction"
    )

    @classmethod
    def from_activity_instruction_ar(
        cls, activity_instruction_ar: ActivityInstructionAR
    ) -> "ActivityInstruction":
        parameter_values: List[MultiTemplateParameterValue] = []
        for position, parameter in enumerate(activity_instruction_ar.get_parameters()):
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
            uid=activity_instruction_ar.uid,
            name=activity_instruction_ar.name,
            namePlain=activity_instruction_ar.name_plain,
            startDate=activity_instruction_ar.item_metadata.start_date,
            endDate=activity_instruction_ar.item_metadata.end_date,
            status=activity_instruction_ar.item_metadata.status.value,
            version=activity_instruction_ar.item_metadata.version,
            changeDescription=activity_instruction_ar.item_metadata.change_description,
            userInitials=activity_instruction_ar.item_metadata.user_initials,
            activityInstructionTemplate=ActivityDescriptionTemplateNameUid(
                name=activity_instruction_ar.template_name,
                namePlain=activity_instruction_ar.template_name_plain,
                uid=activity_instruction_ar.template_uid,
            ),
            library=Library.from_library_vo(activity_instruction_ar.library),
            studyCount=activity_instruction_ar.study_count,
            parameterValues=parameter_values,
        )


class ActivityInstructionVersion(ActivityInstruction):
    """
    Class for storing Activity Instructions and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the activity instruction (e.g. name, startDate, ..)."
        ),
    )


class ActivityInstructionCreateInput(BaseModel):
    activityInstructionTemplateUid: str = Field(
        ...,
        title="activityInstructionTemplateUid",
        description="The unique id of the activity instruction template that is used as the basis for the new activity instruction.",
    )
    nameOverride: Optional[str] = Field(
        None,
        title="name",
        description="Optionally, a name to override the name inherited from the template.",
    )
    parameterValues: List[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameterValues",
        description="An ordered list of selected parameter values that are used to replace the parameters of the activity instruction template.",
    )
    libraryName: str = Field(
        None,
        title="libraryName",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )
