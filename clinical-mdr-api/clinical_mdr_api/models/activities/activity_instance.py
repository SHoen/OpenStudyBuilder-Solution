from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence, TypeVar

from pydantic import Field

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.activities.activity import (
    ActivityBase,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concept import ConceptInput
from clinical_mdr_api.models.ct_term import SimpleTermModel

_AggregateRootType = TypeVar("_AggregateRootType", bound=ActivityInstanceAR)


class ActivityInstance(ActivityBase):
    @classmethod
    def _get_term_model(
        cls, item: ConceptVO, uid_attribute: str, name_attribute: str
    ) -> Optional[SimpleTermModel]:
        uid_value = getattr(item, uid_attribute)
        if uid_value is None:
            return None
        return SimpleTermModel(termUid=uid_value, name=getattr(item, name_attribute))

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: _AggregateRootType,
        find_activity_hierarchy_by_uid: Callable[[str], Optional[ActivityAR]],
        find_activity_subgroup_by_uid: Callable[[str], Optional[ActivitySubGroupAR]],
        find_activity_group_by_uid: Callable[[str], Optional[ActivityGroupAR]],
    ) -> "ActivityInstance":

        activity_subgroup_uids = [
            find_activity_hierarchy_by_uid(activity_uid).concept_vo.activity_sub_group
            for activity_uid in activity_ar.concept_vo.activity_uids
        ]
        activity_group_uids = [
            find_activity_subgroup_by_uid(subgroup_uid).concept_vo.activity_group
            for subgroup_uid in activity_subgroup_uids
        ]
        sdtmVariable = cls._get_term_model(
            activity_ar.concept_vo, "sdtm_variable_uid", "sdtm_variable_name"
        )
        sdtmSubcat = cls._get_term_model(
            activity_ar.concept_vo, "sdtm_subcat_uid", "sdtm_subcat_name"
        )
        sdtmCat = cls._get_term_model(
            activity_ar.concept_vo, "sdtm_cat_uid", "sdtm_cat_name"
        )
        sdtmDomain = cls._get_term_model(
            activity_ar.concept_vo, "sdtm_domain_uid", "sdtm_domain_name"
        )
        specimen = cls._get_term_model(
            activity_ar.concept_vo, "specimen_uid", "specimen_name"
        )

        return cls(
            uid=activity_ar.uid,
            type=activity_ar.concept_vo.activity_type,
            name=activity_ar.name,
            nameSentenceCase=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            topicCode=activity_ar.concept_vo.topic_code,
            adamParamCode=activity_ar.concept_vo.adam_param_code,
            legacyDescription=activity_ar.concept_vo.legacy_description,
            sdtmVariable=sdtmVariable,
            sdtmSubcat=sdtmSubcat,
            sdtmCat=sdtmCat,
            sdtmDomain=sdtmDomain,
            activities=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity,
                        find_activity_by_uid=find_activity_hierarchy_by_uid,
                    )
                    for activity in activity_ar.concept_vo.activity_uids
                ],
                key=lambda item: item.name,
            ),
            activitySubgroups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_subgroup,
                        find_activity_by_uid=find_activity_subgroup_by_uid,
                    )
                    for activity_subgroup in activity_subgroup_uids
                ],
                key=lambda item: item.name,
            ),
            activityGroups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_group,
                        find_activity_by_uid=find_activity_group_by_uid,
                    )
                    for activity_group in activity_group_uids
                ],
                key=lambda item: item.name,
            ),
            specimen=specimen,
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

    type: Optional[str] = Field(
        None, title="type", description="The subtype of ActivityInstance"
    )
    topicCode: str = Field(
        ...,
        title="topicCode",
        description="",
    )
    adamParamCode: str = Field(
        ...,
        title="adamParamCode",
        description="",
    )
    legacyDescription: Optional[str] = Field(
        None,
        title="legacyDescription",
        description="",
    )
    sdtmVariable: Optional[SimpleTermModel] = Field(
        ...,
        title="sdtmVariable",
        description="",
    )
    sdtmSubcat: Optional[SimpleTermModel] = Field(
        ...,
        title="sdtmSubcat",
        description="",
    )
    sdtmCat: Optional[SimpleTermModel] = Field(
        ...,
        title="sdtmCat",
        description="",
    )
    sdtmDomain: Optional[SimpleTermModel] = Field(
        ...,
        title="sdtmDomain",
        description="",
    )
    activities: Sequence[ActivityHierarchySimpleModel] = Field(
        ...,
        title="activities",
        description="List of activity unique identifiers",
    )
    activitySubgroups: Sequence[ActivityHierarchySimpleModel] = Field(
        ...,
        title="activitySubgroups",
        description="List of activity sub group unique identifiers",
    )
    activityGroups: Sequence[ActivityHierarchySimpleModel] = Field(
        ...,
        title="activityGroups",
        description="List of activity group unique identifiers",
    )
    specimen: Optional[SimpleTermModel] = Field(
        ...,
        title="specimen",
        description="",
    )
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


class ActivityInstanceCreateInput(ConceptInput):
    name: str = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    nameSentenceCase: Optional[str] = Field(
        None,
        title="nameSentenceCase",
        description="",
    )
    topicCode: Optional[str] = Field(
        None,
        title="topicCode",
        description="",
    )
    adamParamCode: Optional[str] = Field(
        None,
        title="adamParamCode",
        description="",
    )
    legacyDescription: Optional[str] = Field(
        None,
        title="legacyDescription",
        description="",
    )
    sdtmVariable: Optional[str] = Field(
        None,
        title="sdtmVariable",
        description="",
    )
    sdtmSubcat: Optional[str] = Field(
        None,
        title="sdtmSubcat",
        description="",
    )
    sdtmCat: Optional[str] = Field(
        None,
        title="sdtmCat",
        description="",
    )
    sdtmDomain: Optional[str] = Field(
        None,
        title="sdtmDomain",
        description="",
    )
    activities: Optional[Sequence[str]] = Field(
        None,
        title="activity",
        description="",
    )
    libraryName: str


class ActivityInstanceEditInput(ConceptInput):
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
    topicCode: Optional[str] = Field(
        None,
        title="topicCode",
        description="",
    )
    adamParamCode: Optional[str] = Field(
        None,
        title="adamParamCode",
        description="",
    )
    legacyDescription: Optional[str] = Field(
        None,
        title="legacyDescription",
        description="",
    )
    sdtmVariable: Optional[str] = Field(
        None,
        title="sdtmVariable",
        description="",
    )
    sdtmSubcat: Optional[str] = Field(
        None,
        title="sdtmSubcat",
        description="",
    )
    sdtmCat: Optional[str] = Field(
        None,
        title="sdtmCat",
        description="",
    )
    sdtmDomain: Optional[str] = Field(
        None,
        title="sdtmDomain",
        description="",
    )
    specimen: Optional[str] = Field(
        None,
        title="specimen",
        description="",
    )
    activities: Optional[Sequence[str]] = Field(
        None,
        title="activity",
        description="",
    )
    changeDescription: str = Field(..., title="changeDescription", description="")


class ActivityInstanceVersion(ActivityInstance):
    """
    Class for storing ActivityInstance and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
