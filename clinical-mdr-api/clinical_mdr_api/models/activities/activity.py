from datetime import datetime
from typing import Callable, Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.models.concept import Concept, ConceptInput
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class ActivityHierarchySimpleModel(BaseModel):
    @classmethod
    def from_activity_uid(
        cls, uid: str, find_activity_by_uid: Callable[[str], Optional[ConceptARBase]]
    ) -> Optional["ActivityHierarchySimpleModel"]:

        if uid is not None:
            activity = find_activity_by_uid(uid)

            if activity is not None:
                simple_activity_model = cls(uid=uid, name=activity.concept_vo.name)
            else:
                simple_activity_model = cls(uid=uid, name=None)
        else:
            simple_activity_model = None
        return simple_activity_model

    uid: str = Field(
        ...,
        title="uid",
        description="",
    )
    name: Optional[str] = Field(None, title="name", description="")


class ActivityBase(Concept):
    startDate: datetime
    endDate: Optional[datetime] = None
    status: str
    version: str
    changeDescription: str
    userInitials: str
    possibleActions: List[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the ActivityInstances. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class Activity(ActivityBase):
    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: ActivityAR,
        find_activity_subgroup_by_uid: Callable[[str], Optional[ActivitySubGroupAR]],
        find_activity_group_by_uid: Callable[[str], Optional[ActivityGroupAR]],
    ) -> "Activity":
        activity_group_uid = find_activity_subgroup_by_uid(
            activity_ar.concept_vo.activity_sub_group
        ).concept_vo.activity_group
        return cls(
            uid=activity_ar.uid,
            name=activity_ar.name,
            nameSentenceCase=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            activitySubGroup=ActivityHierarchySimpleModel.from_activity_uid(
                uid=activity_ar.concept_vo.activity_sub_group,
                find_activity_by_uid=find_activity_subgroup_by_uid,
            ),
            activityGroup=ActivityHierarchySimpleModel.from_activity_uid(
                uid=activity_group_uid,
                find_activity_by_uid=find_activity_group_by_uid,
            ),
            libraryName=Library.from_library_vo(activity_ar.library).name,
            startDate=activity_ar.item_metadata.start_date,
            endDate=activity_ar.item_metadata.end_date,
            status=activity_ar.item_metadata.status.value,
            version=activity_ar.item_metadata.version,
            changeDescription=activity_ar.item_metadata.change_description,
            userInitials=activity_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in activity_ar.get_possible_actions()]
            ),
        )

    activitySubGroup: Optional[ActivityHierarchySimpleModel]
    activityGroup: Optional[ActivityHierarchySimpleModel]


class ActivityCommonInput(ConceptInput):
    name: Optional[str] = Field(
        None,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    nameSentenceCase: Optional[str] = Field(
        None,
        title="nameSentenceCase",
        description="",
    )


class ActivityInput(ActivityCommonInput):
    activitySubGroup: Optional[str] = None


class ActivityEditInput(ActivityInput):
    changeDescription: str = Field(None, title="changeDescription", description="")


class ActivityCreateInput(ActivityInput):
    libraryName: str


class ActivityVersion(Activity):
    """
    Class for storing Activity and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
