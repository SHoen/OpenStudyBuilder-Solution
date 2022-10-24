from datetime import datetime
from typing import Callable, Dict, List, Optional

from pydantic import Field, conlist

from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.templates.activity_description_template import (
    ActivityDescriptionTemplateAR,
)
from clinical_mdr_api.models.activities.activity import Activity
from clinical_mdr_api.models.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.activities.activity_sub_group import ActivitySubGroup
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.library import ItemCounts, Library
from clinical_mdr_api.models.template_parameter import TemplateParameter
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
)
from clinical_mdr_api.models.utils import BaseModel


class ActivityDescriptionTemplateName(BaseModel):
    name: Optional[str] = Field(
        None,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    namePlain: Optional[str] = Field(
        None,
        description="The plain text version of the name property, stripped of HTML tags",
    )


class ActivityDescriptionTemplateNameUid(ActivityDescriptionTemplateName):
    uid: str = Field(
        ..., description="The unique id of the activity description template."
    )


class ActivityDescriptionTemplate(ActivityDescriptionTemplateNameUid):
    editableInstance: bool = Field(
        ...,
        description="Indicates if the name of this template's instances can be edited.",
    )
    startDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) activity description template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    endDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="""Part of the metadata: The point in time when the version of
        the activity description template was closed (and a new one was created). """
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    status: Optional[str] = Field(
        None,
        description="The status in which the (version of the) activity description template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
    )
    version: Optional[str] = Field(
        None,
        description="The version number of the (version of the) activity description template. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
    )
    changeDescription: Optional[str] = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
    )
    userInitials: Optional[str] = Field(
        None,
        description="The initials of the user that triggered the change of the activity description template.",
    )

    # TODO use the standard _link/name approach
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the activity description template. "
            "Actions are: 'approve', 'edit', 'newVersion', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: Optional[List[TemplateParameter]] = Field(
        None,
        description="Those parameters that are used by the activity description template.",
    )
    defaultParameterValues: Optional[
        Dict[int, List[MultiTemplateParameterValue]]
    ] = Field(
        None,
        description="""Holds the default values for the parameters that are used
        within the template. The values are ordered as they occur in the template's name.""",
    )
    library: Optional[Library] = Field(
        None,
        description=("The library to which the activity description template belongs."),
    )

    # Template groupings
    indications: Optional[List[DictionaryTerm]] = Field(
        None,
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    activities: Optional[List[Activity]] = Field(
        None, description="The activities in scope for the template"
    )
    activityGroups: Optional[List[ActivityGroup]] = Field(
        None, description="The activity groups in scope for the template"
    )
    activitySubGroups: Optional[List[ActivitySubGroup]] = Field(
        None, description="The activity sub groups in scope for the template"
    )

    studyCount: Optional[int] = Field(
        None, description="Count of studies referencing template"
    )

    @classmethod
    def from_activity_description_template_ar(
        cls,
        activity_description_template_ar: ActivityDescriptionTemplateAR,
        find_activity_subgroup_by_uid: Callable[[str], Optional[ActivitySubGroupAR]],
        find_activity_group_by_uid: Callable[[str], Optional[ActivityGroupAR]],
    ) -> "ActivityDescriptionTemplate":
        default_parameter_values: Dict[int, List[MultiTemplateParameterValue]] = {}
        if (
            activity_description_template_ar.template_value.default_parameter_values
            is not None
        ):
            for (
                set_number,
                value_set,
            ) in (
                activity_description_template_ar.template_value.default_parameter_values.items()
            ):
                value_list = []
                for position, parameter in enumerate(value_set):
                    values: List[IndexedTemplateParameterValue] = [
                        IndexedTemplateParameterValue(
                            index=index + 1,
                            uid=parameter_value.uid,
                            name=parameter_value.value,
                            type=parameter.parameter_name,
                        )
                        for index, parameter_value in enumerate(parameter.parameters)
                    ]

                    value_list.append(
                        MultiTemplateParameterValue(
                            conjunction=parameter.conjunction,
                            position=position + 1,
                            values=values,
                        )
                    )
                default_parameter_values[set_number] = value_list

        return cls(
            uid=activity_description_template_ar.uid,
            editableInstance=activity_description_template_ar.editable_instance,
            name=activity_description_template_ar.name,
            namePlain=activity_description_template_ar.name_plain,
            startDate=activity_description_template_ar.item_metadata.start_date,
            endDate=activity_description_template_ar.item_metadata.end_date,
            status=activity_description_template_ar.item_metadata.status.value,
            version=activity_description_template_ar.item_metadata.version,
            changeDescription=activity_description_template_ar.item_metadata.change_description,
            userInitials=activity_description_template_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [
                    _.value
                    for _ in activity_description_template_ar.get_possible_actions()
                ]
            ),
            library=Library.from_library_vo(activity_description_template_ar.library),
            indications=[
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in activity_description_template_ar.indications
            ]
            if activity_description_template_ar.indications
            else None,
            activities=[
                Activity.from_activity_ar(
                    activity,
                    find_activity_subgroup_by_uid,
                    find_activity_group_by_uid,
                )
                for activity in activity_description_template_ar.activities
            ]
            if activity_description_template_ar.activities
            else None,
            activityGroups=[
                ActivityGroup.from_activity_ar(group)
                for group in activity_description_template_ar.activity_groups
            ]
            if activity_description_template_ar.activity_groups
            else None,
            activitySubGroups=[
                ActivitySubGroup.from_activity_ar(group, find_activity_group_by_uid)
                for group in activity_description_template_ar.activity_sub_groups
            ]
            if activity_description_template_ar.activity_sub_groups
            else None,
            studyCount=activity_description_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in activity_description_template_ar.template_value.parameter_names
            ],
            defaultParameterValues=default_parameter_values,
        )


class ActivityDescriptionTemplateWithCount(ActivityDescriptionTemplate):

    counts: Optional[ItemCounts] = Field(
        None, description="Optional counts of activity description instatiations"
    )

    @classmethod
    def from_activity_description_template_ar(
        cls, activity_description_template_ar: ActivityDescriptionTemplateAR, **kwargs
    ) -> "ActivityDescriptionTemplate":
        ot = super().from_activity_description_template_ar(
            activity_description_template_ar, **kwargs
        )
        if activity_description_template_ar.counts is not None:
            ot.counts = ItemCounts(
                draft=activity_description_template_ar.counts.count_draft,
                final=activity_description_template_ar.counts.count_final,
                retired=activity_description_template_ar.counts.count_retired,
                total=activity_description_template_ar.counts.count_total,
            )
        return ot


class ActivityDescriptionTemplateVersion(ActivityDescriptionTemplate):
    """
    Class for storing Activity Description Templates and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the activity description template (e.g. name, startDate, ..)."
        ),
    )


class ActivityDescriptionTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    guidanceText: Optional[str] = Field(
        None, description="Optional guidance text for using the template."
    )


class ActivityDescriptionTemplateCreateInput(ActivityDescriptionTemplateNameInput):
    libraryName: Optional[str] = Field(
        "Sponsor",
        description="If specified: The name of the library to which the activity description template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true.",
    )
    defaultParameterValues: Optional[List[MultiTemplateParameterValue]] = Field(
        None,
        description="Holds the parameter values to be used as default for this template. The values are ordered as they occur in the template name.",
    )

    editableInstance: Optional[bool] = Field(
        False,
        description="Indicates if the name of this template's instances can be edited. Defaults to False.",
    )

    indicationUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    activityUids: Optional[List[str]] = Field(
        None, description="A list of UID of the activities to attach the template to."
    )
    activityGroupUids: conlist(
        str,
        min_items=1,
    )
    activitySubGroupUids: conlist(
        str,
        min_items=1,
    )


class ActivityDescriptionTemplateEditInput(ActivityDescriptionTemplateNameInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ActivityDescriptionTemplateEditGroupingsInput(BaseModel):
    indicationUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    activityUids: Optional[List[str]] = Field(
        None, description="A list of UID of the activities to attach the template to."
    )
    activityGroupUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the activity groups to attach the template to.",
    )
    activitySubGroupUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the activity sub groups to attach the template to.",
    )
