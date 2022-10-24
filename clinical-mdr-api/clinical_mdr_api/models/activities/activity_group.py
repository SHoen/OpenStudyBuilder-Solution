from typing import Dict

from pydantic import Field

from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.models.activities.activity import (
    ActivityBase,
    ActivityCommonInput,
)
from clinical_mdr_api.models.library import Library


class ActivityGroup(ActivityBase):
    @classmethod
    def from_activity_ar(cls, activity_group_ar: ActivityGroupAR) -> "ActivityGroup":
        return cls(
            uid=activity_group_ar.uid,
            name=activity_group_ar.name,
            nameSentenceCase=activity_group_ar.concept_vo.name_sentence_case,
            definition=activity_group_ar.concept_vo.definition,
            abbreviation=activity_group_ar.concept_vo.abbreviation,
            libraryName=Library.from_library_vo(activity_group_ar.library).name,
            startDate=activity_group_ar.item_metadata.start_date,
            endDate=activity_group_ar.item_metadata.end_date,
            status=activity_group_ar.item_metadata.status.value,
            version=activity_group_ar.item_metadata.version,
            changeDescription=activity_group_ar.item_metadata.change_description,
            userInitials=activity_group_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in activity_group_ar.get_possible_actions()]
            ),
        )


class ActivityGroupInput(ActivityCommonInput):
    pass


class ActivityGroupEditInput(ActivityGroupInput):
    changeDescription: str = Field(None, title="changeDescription", description="")


class ActivityGroupCreateInput(ActivityGroupInput):
    libraryName: str


class ActivityGroupVersion(ActivityGroupInput):
    """
    Class for storing ActivityGroup and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
