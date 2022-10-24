from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.concepts.activities.categoric_finding import (
    CategoricFindingAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.activities.activity import ActivityHierarchySimpleModel
from clinical_mdr_api.models.activities.finding import (
    Finding,
    FindingCreateInput,
    FindingEditInput,
    FindingVersion,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel


class CategoricFinding(Finding):
    categoricResponseValue: Optional[SimpleTermModel]
    categoricResponseList: Optional[SimpleTermModel]

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: CategoricFindingAR,
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_activity_hierarchy_by_uid: Callable[[str], Optional[ActivityAR]],
        find_activity_subgroup_by_uid: Callable[[str], Optional[ActivitySubGroupAR]],
        find_activity_group_by_uid: Callable[[str], Optional[ActivityGroupAR]],
    ) -> "CategoricFinding":

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
            valueSasDisplayFormat=activity_ar.concept_vo.value_sas_display_format,
            specimen=specimen,
            testCode=SimpleTermModel.from_ct_code(
                c_code=activity_ar.concept_vo.test_code_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            categoricResponseValue=SimpleTermModel.from_ct_code(
                c_code=activity_ar.concept_vo.categoric_response_value_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            categoricResponseList=SimpleTermModel.from_ct_code(
                c_code=activity_ar.concept_vo.categoric_response_list_uid,
                find_term_by_uid=find_term_by_uid,
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


class CategoricFindingCreateInput(FindingCreateInput):
    categoricResponseValue: Optional[str] = None
    categoricResponseList: Optional[str] = None


class CategoricFindingEditInput(FindingEditInput):
    categoricResponseValue: Optional[str]
    categoricResponseList: Optional[str]


class CategoricFindingVersion(FindingVersion, CategoricFinding):
    pass
