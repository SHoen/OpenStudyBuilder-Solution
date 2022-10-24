"""Study model."""
from datetime import datetime
from typing import Callable, Collection, Iterable, List, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.clinical_programme.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.root import StudyDefinitionAR
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.duration import DurationJsonModel
from clinical_mdr_api.models.utils import BaseModel


class RegistryIdentifiersJsonModel(BaseModel):
    class Config:
        title = "RegistryIdentifiersMetadata"
        description = "RegistryIdentifiersMetadata metadata for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    ctGovId: Optional[str] = None
    ctGovIdNullValueCode: Optional[SimpleTermModel] = None
    eudractId: Optional[str] = None
    eudractIdNullValueCode: Optional[SimpleTermModel] = None
    universalTrialNumberUTN: Optional[str] = None
    universalTrialNumberUTNNullValueCode: Optional[SimpleTermModel] = None
    japaneseTrialRegistryIdJAPIC: Optional[str] = None
    japaneseTrialRegistryIdJAPICNullValueCode: Optional[SimpleTermModel] = None
    investigationalNewDrugApplicationNumberIND: Optional[str] = None
    investigationalNewDrugApplicationNumberINDNullValueCode: Optional[
        SimpleTermModel
    ] = None

    @classmethod
    def from_study_registry_identifiers_vo(
        cls,
        registry_identifiers_vo: RegistryIdentifiersVO,
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> "RegistryIdentifiersJsonModel":
        return cls(
            ctGovId=registry_identifiers_vo.ct_gov_id,
            ctGovIdNullValueCode=SimpleTermModel.from_ct_code(
                c_code=registry_identifiers_vo.ct_gov_id_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            eudractId=registry_identifiers_vo.eudract_id,
            eudractIdNullValueCode=SimpleTermModel.from_ct_code(
                c_code=registry_identifiers_vo.eudract_id_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            universalTrialNumberUTN=registry_identifiers_vo.universal_trial_number_UTN,
            universalTrialNumberUTNNullValueCode=SimpleTermModel.from_ct_code(
                c_code=registry_identifiers_vo.universal_trial_number_UTN_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            japaneseTrialRegistryIdJAPIC=registry_identifiers_vo.japanese_trial_registry_id_JAPIC,
            japaneseTrialRegistryIdJAPICNullValueCode=SimpleTermModel.from_ct_code(
                c_code=registry_identifiers_vo.japanese_trial_registry_id_JAPIC_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            investigationalNewDrugApplicationNumberIND=registry_identifiers_vo.investigational_new_drug_application_number_IND,
            investigationalNewDrugApplicationNumberINDNullValueCode=SimpleTermModel.from_ct_code(
                c_code=registry_identifiers_vo.investigational_new_drug_application_number_IND_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyIdentificationMetadataJsonModel(BaseModel):
    class Config:
        title = "StudyIdentificationMetadata"
        description = "Identification metadata for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    studyNumber: Optional[str] = None
    studyAcronym: Optional[str] = None
    projectNumber: Optional[str] = None
    projectName: Optional[str] = None
    clinicalProgrammeName: Optional[str] = None
    studyId: Optional[str] = None
    registryIdentifiers: Optional[RegistryIdentifiersJsonModel] = None

    @classmethod
    def from_study_identification_vo(
        cls,
        study_identification_o: Optional[StudyIdentificationMetadataVO],
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> Optional["StudyIdentificationMetadataJsonModel"]:
        if study_identification_o is None:
            return None
        project_ar = find_project_by_project_number(
            study_identification_o.project_number
        )
        return cls(
            studyNumber=study_identification_o.study_number,
            studyAcronym=study_identification_o.study_acronym,
            projectNumber=study_identification_o.project_number,
            projectName=project_ar.name,
            clinicalProgrammeName=find_clinical_programme_by_uid(
                project_ar.clinical_programme_uid
            ).name,
            studyId=study_identification_o.study_id,
            registryIdentifiers=RegistryIdentifiersJsonModel.from_study_registry_identifiers_vo(
                study_identification_o.registry_identifiers, find_term_by_uid
            ),
        )


class StudyVersionMetadataJsonModel(BaseModel):
    class Config:
        title = "StudyVersionMetadata"
        description = "Version metadata for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    studyStatus: Optional[str] = None
    lockedVersionNumber: Optional[int] = None
    versionTimestamp: Optional[datetime] = None
    lockedVersionAuthor: Optional[str] = None
    lockedVersionInfo: Optional[str] = None

    @classmethod
    def from_study_version_metadata_vo(
        cls, study_version_metadata_vo: Optional[StudyVersionMetadataVO]
    ) -> Optional["StudyVersionMetadataJsonModel"]:
        if study_version_metadata_vo is None:
            return None
        return cls(
            studyStatus=study_version_metadata_vo.study_status.value,
            lockedVersionNumber=study_version_metadata_vo.locked_version_number,
            versionTimestamp=study_version_metadata_vo.version_timestamp,
            lockedVersionAuthor=study_version_metadata_vo.locked_version_author,
            lockedVersionInfo=study_version_metadata_vo.locked_version_info,
        )


class HighLevelStudyDesignJsonModel(BaseModel):
    class Config:
        title = "HighLevelStudyDesign"
        description = "High level study design parameters for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    studyTypeCode: Optional[SimpleTermModel] = None
    studyTypeNullValueCode: Optional[SimpleTermModel] = None

    trialTypesCodes: Optional[Sequence[SimpleTermModel]] = None
    trialTypesNullValueCode: Optional[SimpleTermModel] = None

    trialPhaseCode: Optional[SimpleTermModel] = None
    trialPhaseNullValueCode: Optional[SimpleTermModel] = None

    isExtensionTrial: Optional[bool] = None
    isExtensionTrialNullValueCode: Optional[SimpleTermModel] = None

    isAdaptiveDesign: Optional[bool] = None
    isAdaptiveDesignNullValueCode: Optional[SimpleTermModel] = None

    studyStopRules: Optional[str] = None
    studyStopRulesNullValueCode: Optional[SimpleTermModel] = None

    confirmedResponseMinimumDuration: Optional[DurationJsonModel] = None
    confirmedResponseMinimumDurationNullValueCode: Optional[SimpleTermModel] = None

    postAuthIndicator: Optional[bool] = None
    postAuthIndicatorNullValueCode: Optional[SimpleTermModel] = None

    @classmethod
    def from_high_level_study_design_vo(
        cls,
        high_level_study_design_vo: Optional[HighLevelStudyDesignVO],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> Optional["HighLevelStudyDesignJsonModel"]:
        if high_level_study_design_vo is None:
            return None
        return cls(
            studyTypeCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.study_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            studyTypeNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.study_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialTypesCodes=[
                SimpleTermModel.from_ct_code(
                    c_code=trial_type_code, find_term_by_uid=find_term_by_uid
                )
                for trial_type_code in high_level_study_design_vo.trial_type_codes
            ],
            trialTypesNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.trial_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialPhaseCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.trial_phase_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialPhaseNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.trial_phase_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            isExtensionTrial=high_level_study_design_vo.is_extension_trial,
            isExtensionTrialNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.is_extension_trial_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            isAdaptiveDesign=high_level_study_design_vo.is_adaptive_design,
            isAdaptiveDesignNullValueCode=SimpleTermModel.from_ct_code(
                high_level_study_design_vo.is_adaptive_design_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            studyStopRules=high_level_study_design_vo.study_stop_rules,
            studyStopRulesNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.study_stop_rules_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            confirmedResponseMinimumDuration=(
                DurationJsonModel.from_duration_object(
                    duration=high_level_study_design_vo.confirmed_response_minimum_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if high_level_study_design_vo.confirmed_response_minimum_duration
                is not None
                else None
            ),
            confirmedResponseMinimumDurationNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.confirmed_response_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            postAuthIndicator=high_level_study_design_vo.post_auth_indicator,
            postAuthIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=high_level_study_design_vo.post_auth_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyPopulationJsonModel(BaseModel):
    class Config:
        title = "StudyPopulation"
        description = "Study population parameters for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    therapeuticAreasCodes: Optional[Sequence[SimpleTermModel]] = None
    therapeuticAreasNullValueCode: Optional[SimpleTermModel] = None

    diseaseConditionsOrIndicationsCodes: Optional[Sequence[SimpleTermModel]] = None
    diseaseConditionsOrIndicationsNullValueCode: Optional[SimpleTermModel] = None

    diagnosisGroupsCodes: Optional[Sequence[SimpleTermModel]] = None
    diagnosisGroupsNullValueCode: Optional[SimpleTermModel] = None

    sexOfParticipantsCode: Optional[SimpleTermModel] = None
    sexOfParticipantsNullValueCode: Optional[SimpleTermModel] = None

    rareDiseaseIndicator: Optional[bool] = None
    rareDiseaseIndicatorNullValueCode: Optional[SimpleTermModel] = None

    healthySubjectIndicator: Optional[bool] = None
    healthySubjectIndicatorNullValueCode: Optional[SimpleTermModel] = None

    plannedMinimumAgeOfSubjects: Optional[DurationJsonModel] = None
    plannedMinimumAgeOfSubjectsNullValueCode: Optional[SimpleTermModel] = None

    plannedMaximumAgeOfSubjects: Optional[DurationJsonModel] = None
    plannedMaximumAgeOfSubjectsNullValueCode: Optional[SimpleTermModel] = None

    stableDiseaseMinimumDuration: Optional[DurationJsonModel] = None
    stableDiseaseMinimumDurationNullValueCode: Optional[SimpleTermModel] = None

    pediatricStudyIndicator: Optional[bool] = None
    pediatricStudyIndicatorNullValueCode: Optional[SimpleTermModel] = None

    pediatricPostmarketStudyIndicator: Optional[bool] = None
    pediatricPostmarketStudyIndicatorNullValueCode: Optional[SimpleTermModel] = None

    pediatricInvestigationPlanIndicator: Optional[bool] = None
    pediatricInvestigationPlanIndicatorNullValueCode: Optional[SimpleTermModel] = None

    relapseCriteria: Optional[str] = None
    relapseCriteriaNullValueCode: Optional[SimpleTermModel] = None

    numberOfExpectedSubjects: Optional[int] = None
    numberOfExpectedSubjectsNullValueCode: Optional[SimpleTermModel] = None

    @classmethod
    def from_study_population_vo(
        cls,
        study_population_vo: Optional[StudyPopulationVO],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> Optional["StudyPopulationJsonModel"]:
        if study_population_vo is None:
            return None
        return cls(
            therapeuticAreasCodes=[
                SimpleTermModel.from_ct_code(
                    c_code=therapeutic_area_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for therapeutic_area_code in study_population_vo.therapeutic_area_codes
            ],
            therapeuticAreasNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.therapeutic_area_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            diseaseConditionsOrIndicationsCodes=[
                SimpleTermModel.from_ct_code(
                    c_code=disease_or_indication_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for disease_or_indication_code in study_population_vo.disease_condition_or_indication_codes
            ],
            diseaseConditionsOrIndicationsNullValueCode=(
                SimpleTermModel.from_ct_code(
                    c_code=study_population_vo.disease_condition_or_indication_null_value_code,
                    find_term_by_uid=find_term_by_uid,
                )
            ),
            diagnosisGroupsCodes=[
                SimpleTermModel.from_ct_code(
                    c_code=diagnosis_group_code,
                    find_term_by_uid=find_dictionary_term_by_uid,
                )
                for diagnosis_group_code in study_population_vo.diagnosis_group_codes
            ],
            diagnosisGroupsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.diagnosis_group_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sexOfParticipantsCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.sex_of_participants_code,
                find_term_by_uid=find_term_by_uid,
            ),
            sexOfParticipantsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.sex_of_participants_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            rareDiseaseIndicator=study_population_vo.rare_disease_indicator,
            rareDiseaseIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.rare_disease_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            healthySubjectIndicator=study_population_vo.healthy_subject_indicator,
            healthySubjectIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.healthy_subject_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plannedMinimumAgeOfSubjects=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.planned_minimum_age_of_subjects,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.planned_minimum_age_of_subjects is not None
                else None
            ),
            plannedMinimumAgeOfSubjectsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.planned_minimum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plannedMaximumAgeOfSubjects=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.planned_maximum_age_of_subjects,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.planned_maximum_age_of_subjects is not None
                else None
            ),
            plannedMaximumAgeOfSubjectsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.planned_maximum_age_of_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stableDiseaseMinimumDuration=(
                DurationJsonModel.from_duration_object(
                    duration=study_population_vo.stable_disease_minimum_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_population_vo.stable_disease_minimum_duration is not None
                else None
            ),
            stableDiseaseMinimumDurationNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.stable_disease_minimum_duration_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricStudyIndicator=study_population_vo.pediatric_study_indicator,
            pediatricStudyIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.pediatric_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricPostmarketStudyIndicator=study_population_vo.pediatric_postmarket_study_indicator,
            pediatricPostmarketStudyIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.pediatric_postmarket_study_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            pediatricInvestigationPlanIndicator=study_population_vo.pediatric_investigation_plan_indicator,
            pediatricInvestigationPlanIndicatorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.pediatric_investigation_plan_indicator_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            relapseCriteria=study_population_vo.relapse_criteria,
            relapseCriteriaNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.relapse_criteria_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            numberOfExpectedSubjects=study_population_vo.number_of_expected_subjects,
            numberOfExpectedSubjectsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_population_vo.number_of_expected_subjects_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyInterventionJsonModel(BaseModel):
    class Config:
        title = "StudyIntervention"
        description = "Study interventions parameters for study definition."

    interventionTypeCode: Optional[SimpleTermModel] = None
    interventionTypeNullValueCode: Optional[SimpleTermModel] = None

    addOnToExistingTreatments: Optional[bool] = None
    addOnToExistingTreatmentsNullValueCode: Optional[SimpleTermModel] = None

    controlTypeCode: Optional[SimpleTermModel] = None
    controlTypeNullValueCode: Optional[SimpleTermModel] = None

    interventionModelCode: Optional[SimpleTermModel] = None
    interventionModelNullValueCode: Optional[SimpleTermModel] = None

    isTrialRandomised: Optional[bool] = None
    isTrialRandomisedNullValueCode: Optional[SimpleTermModel] = None

    stratificationFactor: Optional[str] = None
    stratificationFactorNullValueCode: Optional[SimpleTermModel] = None

    trialBlindingSchemaCode: Optional[SimpleTermModel] = None
    trialBlindingSchemaNullValueCode: Optional[SimpleTermModel] = None

    plannedStudyLength: Optional[DurationJsonModel] = None
    plannedStudyLengthNullValueCode: Optional[SimpleTermModel] = None

    drugStudyIndication: Optional[bool] = None
    drugStudyIndicationNullValueCode: Optional[SimpleTermModel] = None

    deviceStudyIndication: Optional[str] = None
    deviceStudyIndicationNullValueCode: Optional[SimpleTermModel] = None

    trialIntentTypesCodes: Optional[Sequence[SimpleTermModel]] = None
    trialIntentTypesNullValueCode: Optional[SimpleTermModel] = None

    @classmethod
    def from_study_intervention_vo(
        cls,
        study_intervention_vo: Optional[StudyInterventionVO],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> Optional["StudyInterventionJsonModel"]:
        if study_intervention_vo is None:
            return None
        return cls(
            interventionTypeCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.intervention_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            interventionTypeNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.intervention_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            addOnToExistingTreatments=study_intervention_vo.add_on_to_existing_treatments,
            addOnToExistingTreatmentsNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.add_on_to_existing_treatments_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            controlTypeCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.control_type_code,
                find_term_by_uid=find_term_by_uid,
            ),
            controlTypeNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.control_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            interventionModelCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.intervention_model_code,
                find_term_by_uid=find_term_by_uid,
            ),
            interventionModelNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.intervention_model_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            isTrialRandomised=study_intervention_vo.is_trial_randomised,
            isTrialRandomisedNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.is_trial_randomised_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            stratificationFactor=study_intervention_vo.stratification_factor,
            stratificationFactorNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.stratification_factor_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialBlindingSchemaCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.trial_blinding_schema_code,
                find_term_by_uid=find_term_by_uid,
            ),
            trialBlindingSchemaNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.trial_blinding_schema_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            plannedStudyLength=(
                DurationJsonModel.from_duration_object(
                    duration=study_intervention_vo.planned_study_length,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_intervention_vo.planned_study_length is not None
                else None
            ),
            plannedStudyLengthNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.planned_study_length_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
            drugStudyIndicator=study_intervention_vo.drug_study_indication,
            drugStudyIndicatorNullValueCode=(
                SimpleTermModel.from_ct_code(
                    c_code=study_intervention_vo.drug_study_indication_null_value_code,
                    find_term_by_uid=find_term_by_uid,
                )
            ),
            deviceStudyIndicator=study_intervention_vo.device_study_indication,
            deviceStudyIndicatorNullValueCode=(
                SimpleTermModel.from_ct_code(
                    c_code=study_intervention_vo.device_study_indication_null_value_code,
                    find_term_by_uid=find_term_by_uid,
                )
            ),
            trialIntentTypesCodes=[
                SimpleTermModel.from_ct_code(
                    c_code=trial_intent_type_code, find_term_by_uid=find_term_by_uid
                )
                for trial_intent_type_code in study_intervention_vo.trial_intent_type_codes
            ],
            trialIntentTypesNullValueCode=SimpleTermModel.from_ct_code(
                c_code=study_intervention_vo.trial_intent_type_null_value_code,
                find_term_by_uid=find_term_by_uid,
            ),
        )


class StudyDescriptionJsonModel(BaseModel):
    class Config:
        title = "StudyDescription"
        description = "Study description for the study definition."

    studyTitle: Optional[str] = None
    studyShortTitle: Optional[str] = None

    @classmethod
    def from_study_description_vo(
        cls, study_description_vo: Optional[StudyDescriptionVO]
    ) -> Optional["StudyDescriptionJsonModel"]:
        if study_description_vo is None:
            return None
        return cls(
            studyTitle=study_description_vo.study_title,
            studyShortTitle=study_description_vo.study_short_title,
        )


class StudyMetadataJsonModel(BaseModel):
    class Config:
        title = "StudyMetadata"
        description = "Study metadata"
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    identificationMetadata: Optional[StudyIdentificationMetadataJsonModel] = None
    versionMetadata: Optional[StudyVersionMetadataJsonModel] = None
    highLevelStudyDesign: Optional[HighLevelStudyDesignJsonModel] = None
    studyPopulation: Optional[StudyPopulationJsonModel] = None
    studyIntervention: Optional[StudyInterventionJsonModel] = None
    studyDescription: Optional[StudyDescriptionJsonModel] = None

    @classmethod
    def from_study_metadata_vo(
        cls,
        study_metadata_vo: StudyMetadataVO,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> "StudyMetadataJsonModel":
        return cls(
            identificationMetadata=StudyIdentificationMetadataJsonModel.from_study_identification_vo(
                study_identification_o=study_metadata_vo.id_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                find_term_by_uid=find_term_by_uid,
            ),
            versionMetadata=StudyVersionMetadataJsonModel.from_study_version_metadata_vo(
                study_version_metadata_vo=study_metadata_vo.ver_metadata
            ),
            highLevelStudyDesign=HighLevelStudyDesignJsonModel.from_high_level_study_design_vo(
                high_level_study_design_vo=study_metadata_vo.high_level_study_design,
                find_term_by_uid=find_term_by_uid,
                find_all_study_time_units=find_all_study_time_units,
            ),
            studyPopulation=StudyPopulationJsonModel.from_study_population_vo(
                study_population_vo=study_metadata_vo.study_population,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uid=find_term_by_uid,
                find_dictionary_term_by_uid=find_dictionary_term_by_uid,
            ),
            studyIntervention=StudyInterventionJsonModel.from_study_intervention_vo(
                study_intervention_vo=study_metadata_vo.study_intervention,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uid=find_term_by_uid,
            ),
            studyDescription=StudyDescriptionJsonModel.from_study_description_vo(
                study_description_vo=study_metadata_vo.study_description
            ),
        )


class StudyPatchRequestJsonModel(BaseModel):
    class Config:
        title = "StudyPatchRequest"
        description = "Identification metadata for study definition."
        # alias_generator = to_lower_camel
        # allow_population_by_field_name = True

    currentMetadata: Optional[StudyMetadataJsonModel] = None


class Study(BaseModel):
    uid: str = Field(
        title="uid",
        description="The unique id of the study.",
    )

    studyNumber: Optional[str] = Field(
        None,
        title="studyNumber",
        description="DEPRECATED. Use field in currentMetadata.identificationMetadata.",
    )

    studyId: Optional[str] = Field(
        None,
        title="studyId",
        description="DEPRECATED. Use field in currentMetadata.identificationMetadata.",
    )

    studyAcronym: Optional[str] = Field(
        None,
        title="studyAcronym",
        description="DEPRECATED. Use field in currentMetadata.identificationMetadata.",
    )

    projectNumber: Optional[str] = Field(
        None,
        title="projectNumber",
        description="DEPRECATED. Use field in currentMetadata.identificationMetadata.",
    )
    studyStatus: str = Field(
        None,
        title="studyStatus",
        description="Current status of given StudyDefinition. "
        "Possible values are: 'DRAFT' or 'LOCKED'.",
    )

    currentMetadata: Optional[StudyMetadataJsonModel] = None

    @classmethod
    def from_study_definition_ar(
        cls,
        study_definition_ar: StudyDefinitionAR,
        find_project_by_project_number: Callable[[str], ProjectAR],
        find_clinical_programme_by_uid: Callable[[str], ClinicalProgrammeAR],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> "Study":
        is_id_metadata_none = (
            True if study_definition_ar.current_metadata.id_metadata is None else None
        )
        return cls(
            uid=study_definition_ar.uid,
            studyNumber=study_definition_ar.current_metadata.id_metadata.study_number
            if not is_id_metadata_none
            else None,
            studyAcronym=study_definition_ar.current_metadata.id_metadata.study_acronym
            if not is_id_metadata_none
            else None,
            projectNumber=study_definition_ar.current_metadata.id_metadata.project_number
            if not is_id_metadata_none
            else None,
            studyId=study_definition_ar.current_metadata.id_metadata.study_id
            if not is_id_metadata_none
            else None,
            studyStatus=study_definition_ar.current_metadata.ver_metadata.study_status.value
            if not is_id_metadata_none
            else None,
            currentMetadata=StudyMetadataJsonModel.from_study_metadata_vo(
                study_metadata_vo=study_definition_ar.current_metadata,
                find_project_by_project_number=find_project_by_project_number,
                find_clinical_programme_by_uid=find_clinical_programme_by_uid,
                find_all_study_time_units=find_all_study_time_units,
                find_term_by_uid=find_term_by_uid,
                find_dictionary_term_by_uid=find_dictionary_term_by_uid,
            ),
        )


class StudyCreateInput(BaseModel):
    # projectUid: str = Field(
    #    ...,
    #    title="projectUid",
    #    description="The unique id of the project that holds the study.",
    # )
    studyNumber: Optional[str] = Field(
        # ...,
        title="studyNumber",
        description="",
    )

    # studyIdPrefix: Optional[str] = Field(
    #     ...,
    #     title="studyIdPrefix",
    #     description="",
    # )

    studyAcronym: Optional[str] = Field(
        # ...,
        title="studyAcronym",
        description="",
    )

    projectNumber: Optional[str] = Field(
        # ...,
        title="projectNumber",
        description="",
    )


class StudyFieldAuditTrailAction(BaseModel):
    section: str = Field(
        None,
        title="section",
        description="The section that the modified study field is in.",
    )

    field: str = Field(
        None,
        title="field",
        description="The name of the study field that was changed.",
    )

    beforeValue: SimpleTermModel = Field(
        None,
        title="beforeValue",
        description="The value of the field before the edit.",
    )

    afterValue: SimpleTermModel = Field(
        None,
        title="afterValue",
        description="The value of the field after the edit.",
    )

    action: str = Field(
        None,
        title="action",
        description="The action taken on the study field. One of (Create, edit, delete...)",
    )


class StudyFieldAuditTrailEntry(BaseModel):
    studyUid: str = Field(
        None,
        title="studyUid",
        description="The unique id of the study.",
    )

    userInitials: str = Field(
        None,
        title="userInitials",
        description="The initials of the user that made the edit.",
    )

    date: str = Field(
        None,
        title="date",
        description="The date that the edit was made.",
    )

    actions: List[StudyFieldAuditTrailAction] = Field(
        None,
        title="actions",
        description="The actions that took place as part of this audit trial entry.",
    )

    @classmethod
    def from_study_field_audit_trail_vo(
        cls,
        study_field_audit_trail_vo: StudyFieldAuditTrailEntryAR,
        sections_selected: Collection[str],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> "StudyFieldAuditTrailEntry":
        actions: List[StudyFieldAuditTrailAction] = [
            StudyFieldAuditTrailAction(
                section=action.section,
                field=action.field_name,
                action=action.action,
                beforeValue=SimpleTermModel.from_ct_code(
                    c_code=action.before_value, find_term_by_uid=find_term_by_uid
                ),
                afterValue=SimpleTermModel.from_ct_code(
                    c_code=action.after_value, find_term_by_uid=find_term_by_uid
                ),
            )
            for action in study_field_audit_trail_vo.actions
            if action.section in sections_selected
        ]
        return cls(
            studyUid=study_field_audit_trail_vo.study_uid,
            actions=actions,
            userInitials=study_field_audit_trail_vo.user_initials,
            date=study_field_audit_trail_vo.date,
        )


class StudyProtocolTitle(BaseModel):
    studyUid: str = Field(
        None,
        title="studyUid",
        description="The unique id of the study.",
    )
    studyTitle: Optional[str] = None
    studyShortTitle: Optional[str] = None
    eudractId: Optional[str] = None
    universalTrialNumberUTN: Optional[str] = None
    trialPhaseCode: Optional[SimpleTermModel] = None
    indNumber: Optional[str] = None
    substanceName: Optional[str] = None

    @classmethod
    def from_study_definition_ar(
        cls,
        study_definition_ar: StudyDefinitionAR,
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> "StudyProtocolTitle":
        return cls(
            studyUid=study_definition_ar.uid,
            studyTitle=study_definition_ar.current_metadata.study_description.study_title,
            studyShortTitle=study_definition_ar.current_metadata.study_description.study_short_title,
            eudractId=study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id,
            universalTrialNumberUTN=study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN,
            trialPhaseCode=SimpleTermModel.from_ct_code(
                c_code=study_definition_ar.current_metadata.high_level_study_design.trial_phase_code,
                find_term_by_uid=find_term_by_uid,
            ),
            indNumber=study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND,
        )
