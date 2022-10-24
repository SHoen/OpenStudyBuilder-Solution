from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.templates.timeframe_templates import TimeframeTemplateAR
from clinical_mdr_api.models.library import ItemCounts, Library
from clinical_mdr_api.models.template_parameter import TemplateParameter
from clinical_mdr_api.models.utils import BaseModel


class TimeframeTemplateName(BaseModel):
    name: Optional[str] = Field(
        None,
        description="""
            The actual value/content. It may include parameters
            referenced by simple strings in square brackets [].
            """,
    )
    namePlain: Optional[str] = Field(
        None,
        description="The plain text version of the name property, stripped of HTML tags",
    )


class TimeframeTemplateNameUid(TimeframeTemplateName):
    uid: str = Field(..., description="The unique id of the timeframe template.")


class TimeframeTemplate(TimeframeTemplateNameUid):
    editableInstance: bool = Field(
        ...,
        description="Indicates if the name of this template's instances can be edited.",
    )
    startDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="""
            Part of the metadata: The point in time when the
            (version of the) timeframe template was created.
            The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00'
            for October 31, 2020 at 6pm in UTC+2 timezone.
            """,
    )
    endDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the timeframe template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    status: Optional[str] = Field(
        None,
        description="The status in which the (version of the) timeframe template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
    )
    version: Optional[str] = Field(
        None,
        description="The version number of the (version of the) timeframe template. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
    )
    changeDescription: Optional[str] = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
    )
    userInitials: Optional[str] = Field(
        None,
        description="The initials of the user that triggered the change of the timeframe template.",
    )

    # TODO use the standard _link/name approach
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the timeframe template. "
            "Actions are: 'approve', 'edit', 'newVersion', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: Optional[List[TemplateParameter]] = Field(
        None, description="Those parameters that are used by the timeframe template."
    )
    library: Optional[Library] = Field(
        None, description=("The library to which the timeframe template belongs.")
    )

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> "TimeframeTemplate":
        return cls(
            uid=timeframe_template_ar.uid,
            editableInstance=timeframe_template_ar.editable_instance,
            name=timeframe_template_ar.name,
            namePlain=timeframe_template_ar.name_plain,
            startDate=timeframe_template_ar.item_metadata.start_date,
            endDate=timeframe_template_ar.item_metadata.end_date,
            status=timeframe_template_ar.item_metadata.status.value,
            version=timeframe_template_ar.item_metadata.version,
            changeDescription=timeframe_template_ar.item_metadata.change_description,
            userInitials=timeframe_template_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in timeframe_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(timeframe_template_ar.library),
            parameters=[
                TemplateParameter(name=_)
                for _ in timeframe_template_ar.template_value.parameter_names
            ],
        )


class TimeframeTemplateWithCount(TimeframeTemplate):
    counts: Optional[ItemCounts] = Field(
        None, description="Optional counts of objective instatiations"
    )

    @classmethod
    def from_timeframe_template_ar(
        cls, timeframe_template_ar: TimeframeTemplateAR
    ) -> "TimeframeTemplateWithCount":
        ot = super().from_timeframe_template_ar(timeframe_template_ar)
        if timeframe_template_ar.counts is not None:
            ot.counts = ItemCounts(
                draft=timeframe_template_ar.counts.count_draft,
                final=timeframe_template_ar.counts.count_final,
                retired=timeframe_template_ar.counts.count_retired,
                total=timeframe_template_ar.counts.count_total,
            )
        return ot


class TimeframeTemplateVersion(TimeframeTemplate):
    """
    Class for storing Timeframe Templates and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the timeframe template (e.g. name, startDate, ..)."
        ),
    )


class TimeframeTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    guidanceText: Optional[str] = Field(
        None, description="Optional guidance text for using the template."
    )


class TimeframeTemplateCreateInput(TimeframeTemplateNameInput):
    libraryName: Optional[str] = Field(
        "Sponsor",
        description="If specified: The name of the library to which the timeframe template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true.",
    )

    editableInstance: Optional[bool] = Field(
        False,
        description="Indicates if the name of this template's instances can be edited. Defaults to False.",
    )


class TimeframeTemplateEditInput(TimeframeTemplateNameInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )
