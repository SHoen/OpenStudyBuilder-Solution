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
    name_plain: Optional[str] = None


class ActivityInstruction(ActivityInstructionNameUid):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    change_description: Optional[str] = None
    user_initials: Optional[str] = None
    activity_instruction_template: Optional[ActivityDescriptionTemplateNameUid]
    parameter_values: Optional[List[MultiTemplateParameterValue]] = Field(
        None,
        description="""Holds the parameter values that are used within the activity
        instruction. The values are ordered as they occur in the activity instruction name.""",
    )
    library: Optional[Library] = None

    study_count: Optional[int] = Field(
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
            name_plain=activity_instruction_ar.name_plain,
            start_date=activity_instruction_ar.item_metadata.start_date,
            end_date=activity_instruction_ar.item_metadata.end_date,
            status=activity_instruction_ar.item_metadata.status.value,
            version=activity_instruction_ar.item_metadata.version,
            change_description=activity_instruction_ar.item_metadata.change_description,
            user_initials=activity_instruction_ar.item_metadata.user_initials,
            activity_instruction_template=ActivityDescriptionTemplateNameUid(
                name=activity_instruction_ar.template_name,
                name_plain=activity_instruction_ar.template_name_plain,
                uid=activity_instruction_ar.template_uid,
            ),
            library=Library.from_library_vo(activity_instruction_ar.library),
            study_count=activity_instruction_ar.study_count,
            parameter_values=parameter_values,
        )


class ActivityInstructionVersion(ActivityInstruction):
    """
    Class for storing Activity Instructions and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the activity instruction (e.g. name, start_date, ..)."
        ),
    )


class ActivityInstructionCreateInput(BaseModel):
    activity_instruction_template_uid: str = Field(
        ...,
        title="activity_instruction_template_uid",
        description="The unique id of the activity instruction template that is used as the basis for the new activity instruction.",
    )
    name_override: Optional[str] = Field(
        None,
        title="name",
        description="Optionally, a name to override the name inherited from the template.",
    )
    parameter_values: List[TemplateParameterMultiSelectInput] = Field(
        ...,
        title="parameter_values",
        description="An ordered list of selected parameter values that are used to replace the parameters of the activity instruction template.",
    )
    library_name: str = Field(
        None,
        title="library_name",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )
