from typing import Callable, Dict, Optional

from pydantic import Field

from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.activities.activity import (
    ActivityBase,
    ActivityCommonInput,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.library import Library


class ActivitySubGroup(ActivityBase):
    @classmethod
    def from_activity_ar(
        cls,
        activity_sub_group_ar: ActivitySubGroupAR,
        find_activity_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> "ActivitySubGroup":
        return cls(
            uid=activity_sub_group_ar.uid,
            name=activity_sub_group_ar.name,
            nameSentenceCase=activity_sub_group_ar.concept_vo.name_sentence_case,
            definition=activity_sub_group_ar.concept_vo.definition,
            abbreviation=activity_sub_group_ar.concept_vo.abbreviation,
            activityGroup=ActivityHierarchySimpleModel.from_activity_uid(
                uid=activity_sub_group_ar.concept_vo.activity_group,
                find_activity_by_uid=find_activity_by_uid,
            ),
            libraryName=Library.from_library_vo(activity_sub_group_ar.library).name,
            startDate=activity_sub_group_ar.item_metadata.start_date,
            endDate=activity_sub_group_ar.item_metadata.end_date,
            status=activity_sub_group_ar.item_metadata.status.value,
            version=activity_sub_group_ar.item_metadata.version,
            changeDescription=activity_sub_group_ar.item_metadata.change_description,
            userInitials=activity_sub_group_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in activity_sub_group_ar.get_possible_actions()]
            ),
        )

    activityGroup: ActivityHierarchySimpleModel


class ActivitySubGroupInput(ActivityCommonInput):
    activityGroup: Optional[str] = None


class ActivitySubGroupEditInput(ActivitySubGroupInput):
    changeDescription: str = Field(None, title="changeDescription", description="")


class ActivitySubGroupCreateInput(ActivitySubGroupInput):
    libraryName: str


class ActivitySubGroupVersion(ActivitySubGroup):
    """
    Class for storing ActivitySubGroup and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
