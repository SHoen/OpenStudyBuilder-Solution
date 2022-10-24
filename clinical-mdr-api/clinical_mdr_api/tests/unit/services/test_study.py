import random
import sys
import unittest
from dataclasses import dataclass
from typing import Iterable, Optional
from unittest.mock import PropertyMock, patch

from clinical_mdr_api.config import DEFAULT_STUDY_FIELD_CONFIG_FILE
from clinical_mdr_api.domain.study_definition_aggregate import study_configuration
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.root import StudyDefinitionAR
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    HighLevelStudyDesignVO,
    StudyIdentificationMetadataVO,
    StudyStatus,
)
from clinical_mdr_api.models.study import (
    DurationJsonModel,
    HighLevelStudyDesignJsonModel,
    RegistryIdentifiersJsonModel,
    StudyCreateInput,
    StudyDescriptionJsonModel,
    StudyIdentificationMetadataJsonModel,
    StudyInterventionJsonModel,
    StudyMetadataJsonModel,
    StudyPatchRequestJsonModel,
    StudyPopulationJsonModel,
)
from clinical_mdr_api.models.utils import from_duration_object_to_value_and_unit
from clinical_mdr_api.services._utils import create_duration_object_from_api_input
from clinical_mdr_api.services.study import StudyService
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.controlled_terminology_aggregates.test_ct_term_names import (
    create_random_ct_term_name_ar,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_root import (
    create_random_study,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from clinical_mdr_api.tests.unit.domain_repositories.test_study_definition_repository_base import (
    StudyDefinitionRepositoryFake,
    StudyDefinitionsDBFake,
)
from clinical_mdr_api.tests.unit.services.test_study_description import (
    StudyTitleRepositoryForTestImpl,
)


class UnitDefinitionRepositoryForTestImpl:
    @dataclass(frozen=True)
    class UnitDefinition:
        uid: str
        name: str
        definition: str

    _repo_content = frozenset(
        {
            UnitDefinition("UnitDefinition_000001", "Day", "def1"),
            UnitDefinition("UnitDefinition_000002", "Hour", "def2"),
            UnitDefinition("UnitDefinition_000003", "Month", "def2"),
            UnitDefinition("UnitDefinition_000004", "Week", "def2"),
            UnitDefinition("UnitDefinition_000005", "Year", "def2"),
        }
    )

    def find_by_uid_2(self, code: str) -> Optional[UnitDefinition]:
        results = [_ for _ in self._repo_content if _.uid == code]
        return None if len(results) == 0 else results[0]

    def find_all(self) -> Iterable[UnitDefinition]:
        return self._repo_content, len(self._repo_content)

    def term_exists(self, code: str) -> bool:
        for age_unit in self._repo_content:
            if age_unit.uid == code:
                return True
        return False


class TestStudyService(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.patcher = patch(
            target=study_configuration.__name__ + ".from_database",
            new=lambda: study_configuration.from_file(DEFAULT_STUDY_FIELD_CONFIG_FILE),
        )
        cls.patcher.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.patcher.stop()

    @staticmethod
    def get_field_or_simple_term_uid(field):
        return field if field is None else field.termUid

    @staticmethod
    def get_field_or_unit_def_uid(field):
        return field if field is None else field.uid

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    def test__get_by_uid__plus_study_population__result(
        self,
        ct_term_name_repository_property_mock: PropertyMock,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
    ):
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        for _ in range(0, 100):
            with self.subTest():
                # given
                test_db = StudyDefinitionsDBFake()

                prepare_repo = StudyDefinitionRepositoryFake(test_db)
                sample_study_definition = create_random_study(
                    generate_uid_callback=prepare_repo.generate_uid
                )
                prepare_repo.save(sample_study_definition)
                prepare_repo.close()

                test_repo = StudyDefinitionRepositoryFake(test_db)
                study_definition_repository_property_mock.return_value = test_repo

                # when
                study_service = StudyService(user="PIWQ")
                service_response = study_service.get_by_uid(
                    uid=sample_study_definition.uid,
                    fields="+currentMetadata.studyPopulation",
                )

                # then
                # correct values of high level study design
                _ref_study_population = (
                    sample_study_definition.current_metadata.study_population
                )
                _res_study_population = service_response.currentMetadata.studyPopulation

                self.assertEqual(
                    list(_ref_study_population.therapeutic_area_codes),
                    [
                        self.get_field_or_simple_term_uid(therapeutic_area_code)
                        for therapeutic_area_code in _res_study_population.therapeuticAreasCodes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.therapeutic_area_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.therapeuticAreasNullValueCode
                    ),
                )
                self.assertEqual(
                    list(_ref_study_population.disease_condition_or_indication_codes),
                    [
                        self.get_field_or_simple_term_uid(disease_or_indication_code)
                        for disease_or_indication_code in _res_study_population.diseaseConditionsOrIndicationsCodes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.disease_condition_or_indication_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.diseaseConditionsOrIndicationsNullValueCode
                    ),
                )
                self.assertEqual(
                    list(_ref_study_population.diagnosis_group_codes),
                    [
                        self.get_field_or_simple_term_uid(diagnosis_group_code)
                        for diagnosis_group_code in _res_study_population.diagnosisGroupsCodes
                    ],
                )
                self.assertEqual(
                    _ref_study_population.diagnosis_group_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.diagnosisGroupsNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.sex_of_participants_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.sexOfParticipantsCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.sex_of_participants_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.sexOfParticipantsNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.rare_disease_indicator,
                    _res_study_population.rareDiseaseIndicator,
                )
                self.assertEqual(
                    _ref_study_population.rare_disease_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.rareDiseaseIndicatorNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.healthy_subject_indicator,
                    _res_study_population.healthySubjectIndicator,
                )
                self.assertEqual(
                    _ref_study_population.healthy_subject_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.healthySubjectIndicatorNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.planned_minimum_age_of_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.plannedMinimumAgeOfSubjectsNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.planned_maximum_age_of_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.plannedMaximumAgeOfSubjectsNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_study_indicator,
                    _res_study_population.pediatricStudyIndicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_study_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatricStudyIndicatorNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_postmarket_study_indicator,
                    _res_study_population.pediatricPostmarketStudyIndicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_postmarket_study_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatricPostmarketStudyIndicatorNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.pediatric_investigation_plan_indicator,
                    _res_study_population.pediatricInvestigationPlanIndicator,
                )
                self.assertEqual(
                    _ref_study_population.pediatric_investigation_plan_indicator_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.pediatricInvestigationPlanIndicatorNullValueCode
                    ),
                )
                self.assertEqual(
                    _ref_study_population.number_of_expected_subjects_null_value_code,
                    self.get_field_or_simple_term_uid(
                        _res_study_population.numberOfExpectedSubjectsNullValueCode
                    ),
                )

                if _ref_study_population.planned_minimum_age_of_subjects is None:
                    self.assertIsNone(_res_study_population.plannedMinimumAgeOfSubjects)
                else:
                    self.assertIsNotNone(
                        _res_study_population.plannedMinimumAgeOfSubjects
                    )
                    value, unit = from_duration_object_to_value_and_unit(
                        _ref_study_population.planned_minimum_age_of_subjects,
                        unit_definition_repository_property_mock.find_all,
                    )
                    print("unit", unit)
                    print(
                        "durationunitcode",
                        _res_study_population.plannedMinimumAgeOfSubjects.durationUnitCode,
                    )
                    self.assertEqual(
                        value,
                        _res_study_population.plannedMinimumAgeOfSubjects.durationValue,
                    )
                    self.assertEqual(
                        unit.uid,
                        self.get_field_or_unit_def_uid(
                            _res_study_population.plannedMinimumAgeOfSubjects.durationUnitCode
                        ),
                    )

                if _ref_study_population.planned_maximum_age_of_subjects is None:
                    self.assertIsNone(_res_study_population.plannedMaximumAgeOfSubjects)
                else:
                    self.assertIsNotNone(
                        _res_study_population.plannedMaximumAgeOfSubjects
                    )
                    value, unit = from_duration_object_to_value_and_unit(
                        _ref_study_population.planned_maximum_age_of_subjects,
                        unit_definition_repository_property_mock.find_all,
                    )
                    print("ref_study_population", _ref_study_population)
                    print("unit", unit)
                    print(
                        "durationunitcode",
                        _res_study_population.plannedMaximumAgeOfSubjects.durationUnitCode,
                    )
                    self.assertEqual(
                        value,
                        _res_study_population.plannedMaximumAgeOfSubjects.durationValue,
                    )
                    self.assertEqual(
                        unit.uid,
                        self.get_field_or_unit_def_uid(
                            _res_study_population.plannedMaximumAgeOfSubjects.durationUnitCode
                        ),
                    )

    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__get_by_uid__minus_identification_plus_high_level_study_design__result(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):

        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        study_service = StudyService(user="PIWQ")
        service_response = study_service.get_by_uid(
            uid=sample_study_definition.uid,
            fields=" - currentMetadata . identificationMetadata , "
            " + currentMetadata . highLevelStudyDesign   ",
        )

        # then

        # no id metadata in response
        self.assertIsNone(service_response.currentMetadata.identificationMetadata)
        self.assertNotIn(
            "identificationMetadata", service_response.currentMetadata.__fields_set__
        )

        # correct values of ver metadata
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.study_status.value,
            service_response.currentMetadata.versionMetadata.studyStatus,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.locked_version_number,
            service_response.currentMetadata.versionMetadata.lockedVersionNumber,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.locked_version_info,
            service_response.currentMetadata.versionMetadata.lockedVersionInfo,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.locked_version_author,
            service_response.currentMetadata.versionMetadata.lockedVersionAuthor,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.version_timestamp,
            service_response.currentMetadata.versionMetadata.versionTimestamp,
        )

        # correct values of high level study design
        _ref_high_level_study_design = (
            sample_study_definition.current_metadata.high_level_study_design
        )
        _res_high_level_study_design = (
            service_response.currentMetadata.highLevelStudyDesign
        )

        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.studyTypeNullValueCode
            ),
            _ref_high_level_study_design.study_type_null_value_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.studyTypeCode
            ),
            _ref_high_level_study_design.study_type_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.isExtensionTrialNullValueCode
            ),
            _ref_high_level_study_design.is_extension_trial_null_value_code,
        )
        self.assertEqual(
            _res_high_level_study_design.isExtensionTrial,
            _ref_high_level_study_design.is_extension_trial,
        )
        self.assertEqual(
            _res_high_level_study_design.isAdaptiveDesign,
            _ref_high_level_study_design.is_adaptive_design,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.isAdaptiveDesignNullValueCode
            ),
            _ref_high_level_study_design.is_adaptive_design_null_value_code,
        )
        self.assertEqual(
            _res_high_level_study_design.studyStopRules,
            _ref_high_level_study_design.study_stop_rules,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.studyStopRulesNullValueCode
            ),
            _ref_high_level_study_design.study_stop_rules_null_value_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trialPhaseCode
            ),
            _ref_high_level_study_design.trial_phase_code,
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trialPhaseNullValueCode
            ),
            _ref_high_level_study_design.trial_phase_null_value_code,
        )
        self.assertEqual(
            [
                self.get_field_or_simple_term_uid(trialTypeCode)
                for trialTypeCode in _res_high_level_study_design.trialTypesCodes
            ],
            list(_ref_high_level_study_design.trial_type_codes),
        )
        self.assertEqual(
            self.get_field_or_simple_term_uid(
                _res_high_level_study_design.trialTypesNullValueCode
            ),
            _ref_high_level_study_design.trial_type_null_value_code,
        )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__get_all__minus_identification_plus_high_level_study_design__result(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):

        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definitions = [
            create_random_study(generate_uid_callback=prepare_repo.generate_uid)
            for _ in range(0, 10)
        ]
        for _ in sample_study_definitions:
            prepare_repo.save(_)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_service = StudyService(user="PIWQ")
        service_response = study_service.get_all(
            fields=" - currentMetadata . identificationMetadata , "
            " + currentMetadata . highLevelStudyDesign   "
        ).items

        # then
        self.assertEqual(len(service_response), len(sample_study_definitions))

        self.assertEqual(
            {_.uid for _ in service_response}, {_.uid for _ in sample_study_definitions}
        )

        for sample_study_definition in sample_study_definitions:
            service_response_item = [
                _ for _ in service_response if _.uid == sample_study_definition.uid
            ][0]

            # no id metadata in response
            self.assertIsNone(
                service_response_item.currentMetadata.identificationMetadata
            )
            self.assertNotIn(
                "identificationMetadata",
                service_response_item.currentMetadata.__fields_set__,
            )

            # correct values of ver metadata
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.study_status.value,
                service_response_item.currentMetadata.versionMetadata.studyStatus,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_number,
                service_response_item.currentMetadata.versionMetadata.lockedVersionNumber,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_info,
                service_response_item.currentMetadata.versionMetadata.lockedVersionInfo,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_author,
                service_response_item.currentMetadata.versionMetadata.lockedVersionAuthor,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_timestamp,
                service_response_item.currentMetadata.versionMetadata.versionTimestamp,
            )

            # correct values of high level study design
            _ref_high_level_study_design = (
                sample_study_definition.current_metadata.high_level_study_design
            )
            _res_high_level_study_design = (
                service_response_item.currentMetadata.highLevelStudyDesign
            )

            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.studyTypeNullValueCode
                ),
                _ref_high_level_study_design.study_type_null_value_code,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.studyTypeCode
                ),
                _ref_high_level_study_design.study_type_code,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.isExtensionTrialNullValueCode
                ),
                _ref_high_level_study_design.is_extension_trial_null_value_code,
            )
            self.assertEqual(
                _res_high_level_study_design.isExtensionTrial,
                _ref_high_level_study_design.is_extension_trial,
            )
            self.assertEqual(
                _res_high_level_study_design.isAdaptiveDesign,
                _ref_high_level_study_design.is_adaptive_design,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.isAdaptiveDesignNullValueCode
                ),
                _ref_high_level_study_design.is_adaptive_design_null_value_code,
            )
            self.assertEqual(
                _res_high_level_study_design.studyStopRules,
                _ref_high_level_study_design.study_stop_rules,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.studyStopRulesNullValueCode
                ),
                _ref_high_level_study_design.study_stop_rules_null_value_code,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.trialPhaseCode
                ),
                _ref_high_level_study_design.trial_phase_code,
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.trialPhaseNullValueCode
                ),
                _ref_high_level_study_design.trial_phase_null_value_code,
            )
            self.assertEqual(
                list(
                    self.get_field_or_simple_term_uid(trialType)
                    for trialType in _res_high_level_study_design.trialTypesCodes
                ),
                list(_ref_high_level_study_design.trial_type_codes),
            )
            self.assertEqual(
                self.get_field_or_simple_term_uid(
                    _res_high_level_study_design.trialTypesNullValueCode
                ),
                _ref_high_level_study_design.trial_type_null_value_code,
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__StudyService__create__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()
        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_create_input = StudyCreateInput(studyAcronym="ACRONYM")
        study_service = StudyService(user="PIWQ")

        # when
        study_service.create(study_create_input=study_create_input)

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items
        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_create_input.studyAcronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                study_create_input.studyNumber,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                study_create_input.projectNumber,
            )

    @patch(StudyService.__module__ + ".MetaRepository.ct_term_name_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__StudyService__get_by_uid__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )
        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_service = StudyService(user="PIWQ")
        service_response = study_service.get_by_uid(sample_study_definition.uid)

        # then
        self.assertEqual(
            sample_study_definition.current_metadata.ver_metadata.study_status,
            StudyStatus.DRAFT,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.study_acronym,
            service_response.currentMetadata.identificationMetadata.studyAcronym,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.study_number,
            service_response.currentMetadata.identificationMetadata.studyNumber,
        )
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.project_number,
            service_response.currentMetadata.identificationMetadata.projectNumber,
        )
        self.assertEqual(sample_study_definition.uid, service_response.uid)

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__StudyService__get_all__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definitions = [
            StudyDefinitionAR.from_initial_values(
                generate_uid_callback=prepare_repo.generate_uid,
                initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                    project_number=None,
                    study_acronym=f"ACRONYM-{num}",
                    study_number=None,
                    registry_identifiers=RegistryIdentifiersVO.from_input_values(
                        ct_gov_id=None,
                        eudract_id=None,
                        universal_trial_number_UTN=None,
                        japanese_trial_registry_id_JAPIC=None,
                        investigational_new_drug_application_number_IND=None,
                        ct_gov_id_null_value_code=None,
                        eudract_id_null_value_code=None,
                        universal_trial_number_UTN_null_value_code=None,
                        japanese_trial_registry_id_JAPIC_null_value_code=None,
                        investigational_new_drug_application_number_IND_null_value_code=None,
                    ),
                ),
                study_title_exists_callback=(lambda _, study_number: False),
                study_short_title_exists_callback=(lambda _, study_number: False),
            )
            for num in range(0, 2)
        ]
        for _study_definition in sample_study_definitions:
            prepare_repo.save(_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )
        study_service = StudyService(user="PIWQ")
        service_response = study_service.get_all().items

        # then
        self.assertEqual(len(service_response), len(sample_study_definitions))

        self.assertEqual(
            {_.uid for _ in service_response}, {_.uid for _ in sample_study_definitions}
        )

        for sample_study_definition in sample_study_definitions:
            service_response_item = [
                _ for _ in service_response if _.uid == sample_study_definition.uid
            ][0]
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.study_status.value,
                service_response_item.currentMetadata.versionMetadata.studyStatus,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.study_acronym,
                service_response_item.currentMetadata.identificationMetadata.studyAcronym,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.study_number,
                service_response_item.currentMetadata.identificationMetadata.studyNumber,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.id_metadata.project_number,
                service_response_item.currentMetadata.identificationMetadata.projectNumber,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_number,
                service_response_item.currentMetadata.versionMetadata.lockedVersionNumber,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_info,
                service_response_item.currentMetadata.versionMetadata.lockedVersionInfo,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.locked_version_author,
                service_response_item.currentMetadata.versionMetadata.lockedVersionAuthor,
            )
            self.assertEqual(
                sample_study_definition.current_metadata.ver_metadata.version_timestamp,
                service_response_item.currentMetadata.versionMetadata.versionTimestamp,
            )

    @patch(f"{StudyService.__module__}.MetaRepository.ct_term_name_repository")
    @patch(
        f"{StudyService.__module__}.MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__get_protocol_title__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        ct_term_name_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = create_random_study(
            generate_uid_callback=prepare_repo.generate_uid
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        ct_term_name_repository_property_mock.find_by_uid.return_value = (
            create_random_ct_term_name_ar()
        )

        # When
        study_service = StudyService(user="AZNG")
        result = study_service.get_protocol_title(sample_study_definition.uid)

        # Then
        self.assertEqual(
            sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            result.eudractId,
        )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__high_level_study_design__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            initial_high_level_study_design=HighLevelStudyDesignVO.from_input_values(
                study_type_code=None,
                study_stop_rules_null_value_code=None,
                trial_type_codes=[],
                trial_type_null_value_code=None,
                trial_phase_code=None,
                trial_phase_null_value_code=None,
                is_adaptive_design=False,
                is_adaptive_design_null_value_code=None,
                is_extension_trial=False,
                is_extension_trial_null_value_code=None,
                study_stop_rules="Some important study stop rules.",
                study_type_null_value_code=None,
                confirmed_response_minimum_duration=None,
                confirmed_response_minimum_duration_null_value_code=None,
                post_auth_indicator=None,
                post_auth_indicator_null_value_code=None,
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        high_level_study_design = HighLevelStudyDesignJsonModel(
            studyStopRules="Other study stop rules."
        )
        current_metadata = StudyMetadataJsonModel(
            highLevelStudyDesign=high_level_study_design
        )
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.highLevelStudyDesign is not None

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )

            # we check whether new high_level_study_design is as expected

            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design.fix_some_values(
                    study_stop_rules=(
                        study_patch_request.currentMetadata.highLevelStudyDesign.studyStopRules
                    )
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__id_metadata__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        # patching without registryIdentifiers
        identification_metadata = StudyIdentificationMetadataJsonModel()
        identification_metadata.studyAcronym = "OTHER_ACRONYM"
        current_metadata = StudyMetadataJsonModel(
            identificationMetadata=identification_metadata
        )
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.identificationMetadata is not None

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.project_number_exists.return_value = True

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_patch_request.currentMetadata.identificationMetadata.studyAcronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                sample_study_definition.current_metadata.id_metadata.study_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.ct_gov_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.ct_gov_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
            )
            self.assertEqual(
                # pylint:disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code,
                # pylint:disable=line-too-long
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                sample_study_definition.current_metadata.id_metadata.project_number,
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__id_metadata_registry_identifiers__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        test_db = StudyDefinitionsDBFake()

        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        ri_metadata = RegistryIdentifiersJsonModel()
        ri_metadata.ctGovId = "ct_gov_has_value"
        # removing part data model to ensure we can patch without complete model being submitted
        del ri_metadata.eudractId
        identification_metadata = StudyIdentificationMetadataJsonModel(
            registryIdentifiers=ri_metadata
        )
        current_metadata = StudyMetadataJsonModel(
            identificationMetadata=identification_metadata
        )
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.identificationMetadata is not None
        assert (
            study_patch_request.currentMetadata.identificationMetadata.registryIdentifiers
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.project_number_exists.return_value = True

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            print("STUDY POP", study_definition_ar.current_metadata.study_population)
            print("MODIFIED", sample_study_definition.current_metadata.study_population)
            self.assertEqual(
                study_definition_ar.current_metadata.study_population,
                sample_study_definition.current_metadata.study_population,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                study_patch_request.currentMetadata.identificationMetadata.studyAcronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_number,
                sample_study_definition.current_metadata.id_metadata.study_number,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.study_acronym,
                sample_study_definition.current_metadata.id_metadata.study_acronym,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.eudract_id_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
            )
            self.assertEqual(
                # pylint:disable=line-too-long
                study_definition_ar.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code,
                # pylint:disable=line-too-long
                sample_study_definition.current_metadata.id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata.project_number,
                sample_study_definition.current_metadata.id_metadata.project_number,
            )

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_population__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
        ct_gov_id=None,
    ):
        # given
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=ct_gov_id,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        unit_definitions, _ = unit_definition_test_repo.find_all()
        study_population = StudyPopulationJsonModel(
            plannedMinimumAgeOfSubjects=DurationJsonModel(
                # some positive number
                durationValue=random.randint(0, 100),
                # one of the values in age unit test repo
                durationUnitCode={
                    "uid": random.choice([_.uid for _ in unit_definitions])
                },
            ),
            rareDiseaseIndicator=random.choice([True, False]),
        )
        current_metadata = StudyMetadataJsonModel(studyPopulation=study_population)
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.studyPopulation is not None
        assert (
            study_patch_request.currentMetadata.studyPopulation.plannedMinimumAgeOfSubjects
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        unit_definition_repository_property_mock.find_by_uid_2 = (
            unit_definition_test_repo.find_by_uid_2
        )

        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new high_level_study_design is as expected
            assert (
                study_population.plannedMinimumAgeOfSubjects is not None
            )  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_population,
                sample_study_definition.current_metadata.study_population.fix_some_values(
                    planned_minimum_age_of_subjects=create_duration_object_from_api_input(
                        value=study_population.plannedMinimumAgeOfSubjects.durationValue,
                        unit=(
                            study_population.plannedMinimumAgeOfSubjects.durationUnitCode.uid
                        ),
                        find_duration_name_by_code=lambda _: unit_definition_test_repo.find_by_uid_2(
                            study_population.plannedMinimumAgeOfSubjects.durationUnitCode.uid
                        ),
                    ),
                    rare_disease_indicator=study_population.rareDiseaseIndicator,
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.unit_definition_repository")
    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_intervention__success(
        self,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
        unit_definition_repository_property_mock: PropertyMock,
        ct_gov_id=None,
    ):
        # given
        unit_definition_test_repo = UnitDefinitionRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=ct_gov_id,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()
        unit_definitions, _ = unit_definition_test_repo.find_all()
        study_intervention = StudyInterventionJsonModel(
            plannedStudyLength=DurationJsonModel(
                # some positive number
                durationValue=random.randint(0, 100),
                # one of the values in age unit test repo
                durationUnitCode={
                    "uid": random.choice([_.uid for _ in unit_definitions])
                },
            ),
            isTrialRandomised=random.choice([True, False]),
        )
        current_metadata = StudyMetadataJsonModel(studyIntervention=study_intervention)
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.studyIntervention is not None
        assert (
            study_patch_request.currentMetadata.studyIntervention.plannedStudyLength
            is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        unit_definition_repository_property_mock.find_all.return_value = (
            unit_definition_test_repo.find_all()
        )
        unit_definition_repository_property_mock.find_by_uid_2 = (
            unit_definition_test_repo.find_by_uid_2
        )
        study_definition_repository_property_mock.return_value = test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new high_level_study_design is as expected
            assert (
                study_intervention.plannedStudyLength is not None
            )  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_intervention,
                sample_study_definition.current_metadata.study_intervention.fix_some_values(
                    planned_study_length=create_duration_object_from_api_input(
                        value=study_intervention.plannedStudyLength.durationValue,
                        unit=(
                            study_intervention.plannedStudyLength.durationUnitCode.uid
                        ),
                        find_duration_name_by_code=lambda _: unit_definition_test_repo.find_by_uid_2(
                            study_intervention.plannedStudyLength.durationUnitCode.uid
                        ),
                    ),
                    is_trial_randomised=study_intervention.isTrialRandomised,
                ),
            )

    @patch(StudyService.__module__ + ".MetaRepository.clinical_programme_repository")
    @patch(StudyService.__module__ + ".MetaRepository.project_repository")
    @patch(
        StudyService.__module__ + ".MetaRepository.study_definition_repository",
        new_callable=PropertyMock,
    )
    @patch(
        StudyService.__module__ + ".MetaRepository.study_title_repository",
        new_callable=PropertyMock,
    )
    def test__patch__study_description__success(
        self,
        study_title_repository_mock: PropertyMock,
        study_definition_repository_property_mock: PropertyMock,
        project_repository_property_mock: PropertyMock,
        clinical_programme_repository_property_mock: PropertyMock,
    ):
        # given
        study_title_test_repo = StudyTitleRepositoryForTestImpl()
        test_db = StudyDefinitionsDBFake()
        prepare_repo = StudyDefinitionRepositoryFake(test_db)
        sample_study_definition = StudyDefinitionAR.from_initial_values(
            generate_uid_callback=prepare_repo.generate_uid,
            initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                project_number=None,
                study_acronym="ACRONYM",
                study_number=None,
                registry_identifiers=RegistryIdentifiersVO.from_input_values(
                    ct_gov_id=None,
                    eudract_id=None,
                    universal_trial_number_UTN=None,
                    japanese_trial_registry_id_JAPIC=None,
                    investigational_new_drug_application_number_IND=None,
                    ct_gov_id_null_value_code=None,
                    eudract_id_null_value_code=None,
                    universal_trial_number_UTN_null_value_code=None,
                    japanese_trial_registry_id_JAPIC_null_value_code=None,
                    investigational_new_drug_application_number_IND_null_value_code=None,
                ),
            ),
            study_title_exists_callback=(lambda _, study_number: False),
            study_short_title_exists_callback=(lambda _, study_number: False),
        )
        prepare_repo.save(sample_study_definition)
        prepare_repo.close()

        study_title = random_str()
        study_short_title = random_str()
        study_description = StudyDescriptionJsonModel(
            studyTitle=str(study_title), studyShortTitle=str(study_short_title)
        )
        current_metadata = StudyMetadataJsonModel(studyDescription=study_description)
        study_patch_request = StudyPatchRequestJsonModel(
            currentMetadata=current_metadata
        )

        assert study_patch_request.currentMetadata is not None
        assert study_patch_request.currentMetadata.studyDescription is not None
        assert (
            study_patch_request.currentMetadata.studyDescription.studyTitle is not None
        )

        test_repo = StudyDefinitionRepositoryFake(test_db)

        # mocking repos
        study_definition_repository_property_mock.return_value = test_repo
        study_title_repository_mock.return_value = study_title_test_repo
        project_repository_property_mock.find_by_project_number.return_value = create_random_project(
            clinical_programme_uid=random_str(),
            # pylint:disable=unnecessary-lambda
            generate_uid_callback=lambda: random_str(),
        )
        clinical_programme_repository_property_mock.find_by_uid.return_value = (
            # pylint:disable=unnecessary-lambda
            create_random_clinical_programme(generate_uid_callback=lambda: random_str())
        )

        # when
        study_service = StudyService(user="PIWQ")
        study_service.patch(
            uid=sample_study_definition.uid,
            dry=False,
            study_patch_request=study_patch_request,
        )

        # then
        another_repo_instance = StudyDefinitionRepositoryFake(test_db)
        db_content = another_repo_instance.find_all(
            page_number=1, page_size=sys.maxsize
        ).items

        self.assertEqual(len(db_content), 1)
        for study_definition_ar in db_content:
            self.assertEqual(
                study_definition_ar.current_metadata.ver_metadata.study_status,
                StudyStatus.DRAFT,
            )

            # we check if other parts stay intact
            self.assertEqual(
                study_definition_ar.current_metadata.id_metadata,
                sample_study_definition.current_metadata.id_metadata,
            )
            self.assertEqual(
                study_definition_ar.current_metadata.high_level_study_design,
                sample_study_definition.current_metadata.high_level_study_design,
            )

            # we check whether new study_description is as expected
            assert study_description.studyTitle is not None  # for linter to be happy
            self.assertEqual(
                study_definition_ar.current_metadata.study_description,
                sample_study_definition.current_metadata.study_description.fix_some_values(
                    study_title=study_description.studyTitle,
                    study_short_title=study_description.studyShortTitle,
                ),
            )
