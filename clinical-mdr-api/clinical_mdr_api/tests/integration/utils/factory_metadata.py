from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.study import (
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
    StudyVersionMetadataJsonModel,
)
from clinical_mdr_api.services.study import StudyService


def input_metadata_in_study(study_uid):
    study_service = StudyService(user="some_user")
    study_service.patch(
        uid=study_uid,
        dry=False,
        study_patch_request=generate_study_patch_request(),
    )


def generate_id_metadata() -> StudyIdentificationMetadataJsonModel:
    ri_data = RegistryIdentifiersJsonModel(
        ctGovId="some ct gov id",
        ctGovIdNullValueCode=None,
        eudractId="some eudtact id",
        eudractIdNullValueCode=None,
        universalTrialNumberUTN="some utn id",
        universalTrialNumberUTNNullValueCode=None,
        japaneseTrialRegistryIdJAPIC="some japic id",
        japaneseTrialRegistryIdJAPICNullValueCode=None,
        investigationalNewDrugApplicationNumberIND="some ind id",
        investigationalNewDrugApplicationNumberINDNullValueCode=None,
    )

    return StudyIdentificationMetadataJsonModel(registryIdentifiers=ri_data)


def generate_ver_metadata() -> StudyVersionMetadataJsonModel:
    result = StudyVersionMetadataVO(study_status=StudyStatus.DRAFT)
    return StudyVersionMetadataJsonModel.from_study_version_metadata_vo(result)


def generate_high_level_study_design() -> HighLevelStudyDesignJsonModel:
    return HighLevelStudyDesignJsonModel(
        studyTypeCode=None,
        studyTypeNullValueCode=None,
        trialTypesCodes=None,
        trialTypesNullValueCode=None,
        trialPhaseCode=None,
        trialPhaseNullValueCode=None,
        isExtensionTrial=None,
        isExtensionTrialNullValueCode=None,
        isAdaptiveDesign=None,
        isAdaptiveDesignNullValueCode=None,
        studyStopRules="some stop rule",
        studyStopRulesNullValueCode=None,
        confirmedResponseMinimumDuration=None,
        confirmedResponseMinimumDurationNullValueCode=None,
        postAuthIndicator="True",
        postAuthIndicatorNullValueCode=None,
    )


def generate_study_population() -> StudyPopulationJsonModel:
    return StudyPopulationJsonModel(
        therapeuticAreasCodes=None,
        therapeuticAreasNullValueCode=None,
        diseaseConditionsOrIndicationsCodes=None,
        diseaseConditionsOrIndicationsNullValueCode=None,
        diagnosisGroupsCodes=None,
        diagnosisGroupsNullValueCode=None,
        sexOfParticipantsCode=None,
        sexOfParticipantsNullValueCode=None,
        rareDiseaseIndicator=None,
        rareDiseaseIndicatorNullValueCode=None,
        healthySubjectIndicator=None,
        healthySubjectIndicatorNullValueCode=None,
        plannedMinimumAgeOfSubjects=None,
        plannedMinimumAgeOfSubjectsNullValueCode=None,
        plannedMaximumAgeOfSubjects=None,
        plannedMaximumAgeOfSubjectsNullValueCode=None,
        stableDiseaseMinimumDuration=None,
        stableDiseaseMinimumDurationNullValueCode=None,
        pediatricStudyIndicator=None,
        pediatricStudyIndicatorNullValueCode=None,
        pediatricPostmarketStudyIndicator=False,
        pediatricPostmarketStudyIndicatorNullValueCode=None,
        pediatricInvestigationPlanIndicator=True,
        pediatricInvestigationPlanIndicatorNullValueCode=None,
        relapseCriteria="some criteria",
        relapseCriteriaNullValueCode=None,
    )


def generate_study_metadata() -> StudyMetadataJsonModel:
    return StudyMetadataJsonModel(
        identificationMetadata=generate_id_metadata(),
        versionMetadata=generate_ver_metadata(),
        highLevelStudyDesign=generate_high_level_study_design(),
        studyPopulation=generate_study_population(),
    )


def generate_study_patch_request() -> StudyPatchRequestJsonModel:
    return StudyPatchRequestJsonModel(currentMetadata=generate_study_metadata())
