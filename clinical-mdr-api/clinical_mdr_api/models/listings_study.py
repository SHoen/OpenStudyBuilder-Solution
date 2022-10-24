from typing import Any, Callable, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    HighLevelStudyDesignVO,
    StudyPopulationVO,
)
from clinical_mdr_api.models.study import (
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    StudyPopulationJsonModel,
)
from clinical_mdr_api.models.utils import BaseModel


class SimpleListingCTModel(BaseModel):
    @classmethod
    def from_ct_code(
        cls, ct_uid: str, find_term_by_uid: Callable[[str], Optional[Any]]
    ) -> Optional["SimpleListingCTModel"]:
        simple_listing_ct_model = None
        if ct_uid is not None:
            term = find_term_by_uid(ct_uid)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_listing_ct_model = cls(
                        id=getattr(term.ct_term_vo, "concept_id"),
                        code=getattr(term.ct_term_vo, "code_submission_value"),
                        name=getattr(term.ct_term_vo, "name_submission_value"),
                    )
                elif hasattr(term, "dictionary_term_vo"):
                    # library = DictionaryTerm.from_dictionary_term_ar(term).libraryName
                    # print("Library: ", library)
                    # if library == "SNOMED":
                    #     simple_listing_ct_model = cls(
                    #     id=getattr(term.dictionary_term_vo, "dictionary_id"),
                    #     name=getattr(term.dictionary_term_vo, "definition"))
                    # else:
                    simple_listing_ct_model = cls(
                        id=getattr(term.dictionary_term_vo, "dictionary_id"),
                        name=getattr(term.dictionary_term_vo, "name"),
                    )
            else:
                simple_listing_ct_model = cls(term_id=ct_uid, name=None)
        else:
            simple_listing_ct_model = None
        return simple_listing_ct_model

    id: Optional[str] = Field(
        None,
        title="concept id: c code for CDISC CT, dictionary id for dictionary codes",
        description="",
    )
    code: Optional[str] = Field(
        None,
        title="code: submission code for CDISC CT, this doesnot exists for dictionary codes",
        description="",
    )

    name: Optional[str] = Field(
        None,
        title="name: submission name for CDISC CT, name for dictionary codes",
        description="",
    )


class RegistryIdentifiersListingModel(RegistryIdentifiersJsonModel):
    class Config:
        title = "Registry identifiers model for listing"
        description = "Registry identifiers model for listing."

    ctGovIdNullValueCode: Optional[SimpleListingCTModel] = None
    eudractIdNullValueCode: Optional[SimpleListingCTModel] = None
    universalTrialNumberUTNNullValueCode: Optional[SimpleListingCTModel] = None
    japaneseTrialRegistryIdJAPICNullValueCode: Optional[SimpleListingCTModel] = None
    investigationalNewDrugApplicationNumberINDNullValueCode: Optional[
        SimpleListingCTModel
    ] = None

    @classmethod
    def from_study_registry_identifiers_vo_to_listing(
        cls,
        registry_identifiers_vo: RegistryIdentifiersVO,
        find_term_by_uid: Callable[[str], Optional[CTTermAttributesAR]],
    ) -> "RegistryIdentifiersListingModel":
        return cls(
            ctGovId=registry_identifiers_vo.ct_gov_id,
            ctGovIdNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=registry_identifiers_vo.ct_gov_id_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            eudractId=registry_identifiers_vo.eudract_id,
            eudractIdNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=registry_identifiers_vo.eudract_id_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            universalTrialNumberUTN=registry_identifiers_vo.universal_trial_number_UTN,
            universalTrialNumberUTNNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=registry_identifiers_vo.universal_trial_number_UTN_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            japaneseTrialRegistryIdJAPIC=registry_identifiers_vo.japanese_trial_registry_id_JAPIC,
            japaneseTrialRegistryIdJAPICNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=registry_identifiers_vo.japanese_trial_registry_id_JAPIC_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            investigationalNewDrugApplicationNumberIND=registry_identifiers_vo.investigational_new_drug_application_number_IND,
            investigationalNewDrugApplicationNumberINDNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=registry_identifiers_vo.investigational_new_drug_application_number_IND_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyTypeListingModel(HighLevelStudyDesignJsonModel):
    class Config:
        title = "Study Type model for listing"
        description = "Study Type model for listing"

    studyTypeCode: Optional[SimpleListingCTModel] = None
    studyTypeNullValueCode: Optional[SimpleListingCTModel] = None

    trialTypesCodes: Optional[Sequence[SimpleListingCTModel]] = None
    trialTypesNullValueCode: Optional[SimpleListingCTModel] = None

    trialPhaseCode: Optional[SimpleListingCTModel] = None
    trialPhaseNullValueCode: Optional[SimpleListingCTModel] = None

    isExtensionTrialNullValueCode: Optional[SimpleListingCTModel] = None

    isAdaptiveDesignNullValueCode: Optional[SimpleListingCTModel] = None

    studyStopRulesNullValueCode: Optional[SimpleListingCTModel] = None

    confirmedResponseMinimumDuration: Optional[str] = None
    confirmedResponseMinimumDurationNullValueCode: Optional[SimpleListingCTModel] = None

    postAuthIndicatorNullValueCode: Optional[SimpleListingCTModel] = None

    @classmethod
    def from_high_level_study_design_vo_to_listing(
        cls,
        high_level_study_design_vo: Optional[HighLevelStudyDesignVO],
        find_term_by_uid: Callable[[str], Optional[CTTermAttributesAR]],
    ) -> Optional["StudyTypeListingModel"]:
        if high_level_study_design_vo is None:
            return None
        return cls(
            studyTypeCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.study_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            studyTypeNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.study_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialTypesCodes=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=trial_type_code, find_term_by_uid=find_term_by_uid
                )
                for trial_type_code in high_level_study_design_vo.trial_type_codes
            ],
            trialTypesNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.trial_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialPhaseCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.trial_phase_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialPhaseNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.trial_phase_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            isExtensionTrial=high_level_study_design_vo.is_extension_trial,
            isExtensionTrialNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.is_extension_trial_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            isAdaptiveDesign=high_level_study_design_vo.is_adaptive_design,
            isAdaptiveDesignNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.is_adaptive_design_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            studyStopRules=high_level_study_design_vo.study_stop_rules,
            studyStopRulesNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.study_stop_rules_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            confirmedResponseMinimumDuration=high_level_study_design_vo.confirmed_response_minimum_duration,
            confirmedResponseMinimumDurationNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            postAuthIndicator=high_level_study_design_vo.post_auth_indicator,
            postAuthIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=high_level_study_design_vo.post_auth_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyPopulationListingModel(StudyPopulationJsonModel):
    class Config:
        title = "Study population model for listing"
        description = "Study population model for listing"

    therapeuticAreasCodes: Optional[Sequence[SimpleListingCTModel]] = None
    therapeuticAreasNullValueCode: Optional[SimpleListingCTModel] = None

    diseaseConditionsOrIndicationsCodes: Optional[Sequence[SimpleListingCTModel]] = None
    diseaseConditionsOrIndicationsNullValueCode: Optional[SimpleListingCTModel] = None

    diagnosisGroupsCodes: Optional[Sequence[SimpleListingCTModel]] = None
    diagnosisGroupsNullValueCode: Optional[SimpleListingCTModel] = None

    sexOfParticipantsCode: Optional[SimpleListingCTModel] = None
    sexOfParticipantsNullValueCode: Optional[SimpleListingCTModel] = None

    rareDiseaseIndicatorNullValueCode: Optional[SimpleListingCTModel] = None

    healthySubjectIndicatorNullValueCode: Optional[SimpleListingCTModel] = None

    plannedMinimumAgeOfSubjects: Optional[str] = None
    plannedMinimumAgeOfSubjectsNullValueCode: Optional[SimpleListingCTModel] = None

    plannedMaximumAgeOfSubjects: Optional[str] = None
    plannedMaximumAgeOfSubjectsNullValueCode: Optional[SimpleListingCTModel] = None

    stableDiseaseMinimumDuration: Optional[str] = None
    stableDiseaseMinimumDurationNullValueCode: Optional[SimpleListingCTModel] = None

    pediatricStudyIndicatorNullValueCode: Optional[SimpleListingCTModel] = None

    pediatricPostmarketStudyIndicatorNullValueCode: Optional[
        SimpleListingCTModel
    ] = None

    pediatricInvestigationPlanIndicatorNullValueCode: Optional[
        SimpleListingCTModel
    ] = None

    relapseCriteriaNullValueCode: Optional[SimpleListingCTModel] = None

    numberOfExpectedSubjectsNullValueCode: Optional[SimpleListingCTModel] = None

    @classmethod
    def from_study_population_vo_to_listing(
        cls,
        study_population_vo: Optional[StudyPopulationVO],
        find_term_by_uid: Callable[[str], Optional[CTTermAttributesAR]],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> Optional["StudyPopulationListingModel"]:
        if study_population_vo is None:
            return None
        return cls(
            therapeuticAreasCodes=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=therapeutic_area_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for therapeutic_area_code in study_population_vo.therapeutic_area_codes
            ],
            therapeuticAreasNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.therapeutic_area_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            diseaseConditionsOrIndicationsCodes=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=disease_or_indication_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for disease_or_indication_code in study_population_vo.disease_condition_or_indication_codes
            ],
            diseaseConditionsOrIndicationsNullValueCode=(
                SimpleListingCTModel.from_ct_code(
                    ct_uid=study_population_vo.disease_condition_or_indication_null_value_code,
                    find_term_by_uid=find_term_by_uid,
                )
            ),
            diagnosisGroupsCodes=[
                SimpleListingCTModel.from_ct_code(
                    ct_uid=diagnosis_group_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for diagnosis_group_code in study_population_vo.diagnosis_group_codes
            ],
            diagnosisGroupsNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.diagnosis_group_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sexOfParticipantsCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.sex_of_participants_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sexOfParticipantsNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.sex_of_participants_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            rareDiseaseIndicator=study_population_vo.rare_disease_indicator,
            rareDiseaseIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.rare_disease_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            healthySubjectIndicator=study_population_vo.healthy_subject_indicator,
            healthySubjectIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.healthy_subject_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plannedMinimumAgeOfSubjects=study_population_vo.planned_minimum_age_of_subjects,
            plannedMinimumAgeOfSubjectsNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.planned_minimum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plannedMaximumAgeOfSubjects=study_population_vo.planned_maximum_age_of_subjects,
            plannedMaximumAgeOfSubjectsNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.planned_maximum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stableDiseaseMinimumDuration=study_population_vo.stable_disease_minimum_duration,
            stableDiseaseMinimumDurationNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.stable_disease_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricStudyIndicator=study_population_vo.pediatric_study_indicator,
            pediatricStudyIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.pediatric_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricPostmarketStudyIndicator=study_population_vo.pediatric_postmarket_study_indicator,
            pediatricPostmarketStudyIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.pediatric_postmarket_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricInvestigationPlanIndicator=study_population_vo.pediatric_investigation_plan_indicator,
            pediatricInvestigationPlanIndicatorNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.pediatric_investigation_plan_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            relapseCriteria=study_population_vo.relapse_criteria,
            relapseCriteriaNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.relapse_criteria_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            numberOfExpectedSubjects=study_population_vo.number_of_expected_subjects,
            numberOfExpectedSubjectsNullValueCode=SimpleListingCTModel.from_ct_code(
                ct_uid=study_population_vo.number_of_expected_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )
