import random
import string
import unittest
from datetime import datetime, timedelta
from typing import Any, Callable, Iterable, List, Mapping, Optional, Sequence, Union

import pytest

# from pytest_mock import MockerFixture
from hypothesis import HealthCheck, assume, given, settings
from hypothesis.strategies import sampled_from

from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.tests.unit.domain.utils import (
    random_c_code_sequence,
    random_int,
    random_opt_c_code,
    random_opt_str,
    random_str,
    random_str_sequence,
)


def _dict() -> Mapping[str, Any]:
    return {}


def random_valid_duration_object() -> str:
    duration_units = ["Day", "Hour", "Month", "Week", "Year"]
    duration_unit = random.choice(duration_units)
    value = random.randint(0, 100)
    return "P" + str(value) + duration_unit[0]


initialize_ct_data_map = {
    "NullValueCodes": [("A good reason", "NullValue1"), ("A bad reason", "NullValue2")],
    "StudyType": [
        ("C129000", "Patient Registry Study"),
        ("C98722", "Expanded Access Study"),
        ("C98388", "Interventional Study"),
        ("C16084", "Observational Study"),
    ],
    "TrialIntentType": [
        ("C49654", "Cure Study"),
        ("C49655", "Adverse Effect Mitigation Study"),
        ("C49657", "Prevention Study"),
        ("C15245", "Health Services Research"),
        ("C71485", "Screening Study"),
        ("C71486", "Supportive Care Study"),
    ],
    "TrialType": [
        ("C49653", "Diagnosis Study"),
        ("C39493", "Pharmacoeconomic Study"),
        ("C161477", "Position Effect Trial"),
        ("C158284", "Alcohol Effect Study"),
        ("C158285", "Device-Drug Interaction Study"),
        ("C161480", "Water Effect Trial"),
        ("C49656", "Therapy Trial"),
    ],
    "TrialPhase": [
        ("C15603", "Phase IV Trial"),
        ("C49688", "Phase IIb Trial"),
        ("C15601", "Phase II Trial"),
        ("C47865", "Phase V Trial"),
        ("C15693", "Phase I/II Trial"),
        ("C15694", "Phase II/III Trial"),
        ("C48660", "Not Applicable"),
        ("C49686", "Phase IIa Trial"),
    ],
    "StudyStopRules": ("C49698", "Study Stop Rule"),
    "IsExtensionTrial": ("C139274", "Extension Trial Indicator"),
    "IsAdaptiveDesign": ("C146995", "Adaptive Study Design Indicator"),
    "PostAuthIndicator": ("C139275", "Post Authorization Safety Study Indicator"),
    "TherapeuticAreas": [
        (random_str(), "Therapeutic Area1"),
        (random_str(), "Therapeutic Area2"),
        (random_str(), "Therapeutic Area3"),
        (random_str(), "Therapeutic Area4"),
        (random_str(), "Therapeutic Area5"),
    ],
    "DiseaseConditionOrIndications": [
        (random_str(), "DiseaseConditionOrIndication1"),
        (random_str(), "DiseaseConditionOrIndication2"),
        (random_str(), "DiseaseConditionOrIndication3"),
        (random_str(), "DiseaseConditionOrIndication4"),
        (random_str(), "DiseaseConditionOrIndication5"),
    ],
    "DiagnosisGroups": [
        (random_str(), "DiagnosisGroup1"),
        (random_str(), "DiagnosisGroup2"),
        (random_str(), "DiagnosisGroup3"),
        (random_str(), "DiagnosisGroup4"),
        (random_str(), "DiagnosisGroup5"),
    ],
    "SexOfParticipants": [("C16576", "Female"), ("C20197", "Male"), ("C49636", "Both")],
    "StableDiseaseMinimumDuration": ("C98783", "Stable Disease Minimum Duration"),
    "RareDiseaseIndicator": ("C126070", "Rare Disease Indicator"),  # SDTM catalogue
    "HealthySubjectIndicator": (
        "C98737",
        "Healthy Subject Indicator",
    ),  # SDTM catalogue
    "PlannedMinimumAgeOfSubject": (
        "C49693",
        "Planned Minimum Age of Subjects",
    ),  # SDTM catalogue
    "PlannedMaximumAgeOfSubject": (
        "C49694",
        "Planned Maximum Age of Subjects",
    ),  # SDTM catalogue
    "PediatricStudyIndicator": (
        "C123632",
        "Pediatric Study Indicator",
    ),  # SDTM catalogue
    "PediatricPostmarketStudyIndicator": (
        "C123631",
        "Pediatric Postmarket Study Indicator",
    ),  # SDTM catalogue
    "PediatricInvestigationPlanIndicator": (
        "C126059",
        "EMA Decision Number for Pediatric Investigation Plan",
    ),
    # SDTM catalogue
    "RelapseCriteria": ("C117961", "Relapse Criteria"),
    "InterventionType": [
        ("C127574", "MJDIAEVS"),
        ("C122086", "Augmentation Pressure Point P2"),
        ("C127558", "Cusp Tethering Indicator"),
        ("C127589", "Pulmonic Valve Regurgitant Jet Width"),
        ("C127570", "Mean Blood Flow Velocity"),
        ("C127535", "Annular a' Velocity"),
        ("C147156", "Pressure Half Time"),
    ],
    "AddOnToExistingTreatments": ("C49703", "ADDON"),  # SDTM catalogue
    "ControlType": [
        ("C120841", "Dose Response Control"),
        ("C41132", "None"),
        ("C49648", "Placebo Control"),
        ("C49649", "Active Control"),
    ],
    "InterventionModel": [
        ("C82638", "Factorial Study"),
        ("C142568", "Group Sequential Design"),
        ("C82637", "Crossover Study"),
        ("C82639", "Parallel Study"),
        ("C82640", "Single Group Study"),
    ],
    "IsTrialRandomised": ("C25196", "Randomization"),  # SDTM catalogue
    "StratificationFactor": ("C16153", "Stratification Factors"),  # SDTM catalogue
    "TrialBlindingSchema": [
        ("C15228", "Double Blind Study"),
        ("C49659", "Open Label Study"),
        ("C156592", "OPEN LABEL TO TREATMENT AND DOUBLE BLIND TO IMP DOSE"),
        ("C28233", "Single Blind Study"),
    ],
    "PlannedStudyLength": ("C49697", "Trial Length"),  # SDTM catalogue
    "ConfirmedResponseMinimumDuration": (
        "C98715",
        "ConfirmedResponseMinimumDuration",
    ),  # SDTM catalogue
    "DrugStudyIndication": ("C123630", "DrugStudyIndication"),  # SDTM catalogue
    "DeviceStudyIndication": ("C123629", "DeviceStudyIndication"),  # SDTM catalogue
    "StudyTitle": ("C49802", "Trial Title"),  # SDTM catalogue
}


def random_valid_study_population(
    *,
    condition: Callable[[StudyPopulationVO], bool] = (lambda _: True),
    max_tries: int = 100,
) -> StudyPopulationVO:
    count = 0
    while count < max_tries:
        use_therapeutic_area = random.choice([True, False])
        therapeutic_area_codes = tuple(
            [random.choice(initialize_ct_data_map["TherapeuticAreas"])[0]]
            + list(random_c_code_sequence(initialize_ct_data_map["TherapeuticAreas"]))
            if use_therapeutic_area
            else []
        )
        therapeutic_area_null_value_code = (
            None
            if use_therapeutic_area
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_diagnosis_group = random.choice([True, False])
        diagnosis_group_codes = (
            [random.choice(initialize_ct_data_map["DiagnosisGroups"])[0]]
            + list(random_c_code_sequence(initialize_ct_data_map["DiagnosisGroups"]))
            if use_diagnosis_group
            else []
        )
        diagnosis_group_null_value_code = (
            None
            if use_diagnosis_group
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_disease_condition_or_indication = random.choice([True, False])
        disease_condition_or_indication_codes = (
            [random.choice(initialize_ct_data_map["DiseaseConditionOrIndications"])[0]]
            + list(random_c_code_sequence(initialize_ct_data_map["DiagnosisGroups"]))
            if use_disease_condition_or_indication
            else []
        )
        disease_condition_or_indication_null_value_code = (
            None
            if use_disease_condition_or_indication
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_sex_of_participants = random.choice([True, False])
        sex_of_participants_code = (
            random.choice(initialize_ct_data_map["SexOfParticipants"])[0]
            if use_sex_of_participants
            else None
        )
        sex_of_participants_null_value_code = (
            None
            if use_sex_of_participants
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_healthy_subject_indicator = random.choice([True, False])
        healthy_subject_indicator = (
            random.choice([True, False]) if use_healthy_subject_indicator else None
        )
        healthy_subject_indicator_null_value_code = (
            None
            if use_healthy_subject_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_rare_disease_indicator = random.choice([True, False])
        rare_disease_indicator = (
            random.choice([True, False]) if use_rare_disease_indicator else None
        )
        rare_disease_indicator_null_value_code = (
            None
            if use_rare_disease_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_planned_minimum_age_of_subjects = random.choice([True, False])
        planned_minimum_age_of_subjects = (
            random_valid_duration_object()
            if use_planned_minimum_age_of_subjects
            else None
        )
        planned_minimum_age_of_subjects_null_value_code = (
            None
            if use_planned_minimum_age_of_subjects
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_planned_maximum_age_of_subjects = random.choice([True, False])
        planned_maximum_age_of_subjects = (
            random_valid_duration_object()
            if use_planned_maximum_age_of_subjects
            else None
        )
        planned_maximum_age_of_subjects_null_value_code = (
            None
            if use_planned_maximum_age_of_subjects
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_stable_disease_minimum_duration = random.choice([True, False])
        stable_disease_minimum_duration = (
            random_valid_duration_object()
            if use_stable_disease_minimum_duration
            else None
        )
        stable_disease_minimum_duration_null_value_code = (
            None
            if use_stable_disease_minimum_duration
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_pediatric_study_indicator = random.choice([True, False])
        pediatric_study_indicator = (
            random.choice([True, False]) if use_pediatric_study_indicator else None
        )
        pediatric_study_indicator_null_value_code = (
            None
            if use_pediatric_study_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_pediatric_postmarket_study_indicator = random.choice([True, False])
        pediatric_postmarket_study_indicator = (
            random.choice([True, False])
            if use_pediatric_postmarket_study_indicator
            else None
        )
        pediatric_postmarket_study_indicator_null_value_code = (
            None
            if use_pediatric_postmarket_study_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_pediatric_investigation_plan_indicator = random.choice([True, False])
        pediatric_investigation_plan_indicator = (
            random.choice([True, False])
            if use_pediatric_investigation_plan_indicator
            else None
        )
        pediatric_investigation_plan_indicator_null_value_code = (
            None
            if use_pediatric_investigation_plan_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_relapse_criteria = random.choice([True, False])
        relapse_criteria = random_str() if use_relapse_criteria else None
        relapse_criteria_null_value_code = (
            None
            if use_relapse_criteria
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_number_of_expected_subjects = random.choice([True, False])
        number_of_expected_subjects = (
            random_int() if use_number_of_expected_subjects else None
        )
        number_of_expected_subjects_null_value_code = (
            None
            if use_number_of_expected_subjects
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )
        result = StudyPopulationVO.from_input_values(
            therapeutic_area_codes=therapeutic_area_codes,
            therapeutic_area_null_value_code=therapeutic_area_null_value_code,
            disease_condition_or_indication_codes=disease_condition_or_indication_codes,
            disease_condition_or_indication_null_value_code=disease_condition_or_indication_null_value_code,
            diagnosis_group_codes=diagnosis_group_codes,
            diagnosis_group_null_value_code=diagnosis_group_null_value_code,
            sex_of_participants_code=sex_of_participants_code,
            sex_of_participants_null_value_code=sex_of_participants_null_value_code,
            healthy_subject_indicator=healthy_subject_indicator,
            healthy_subject_indicator_null_value_code=healthy_subject_indicator_null_value_code,
            rare_disease_indicator=rare_disease_indicator,
            rare_disease_indicator_null_value_code=rare_disease_indicator_null_value_code,
            planned_minimum_age_of_subjects=planned_minimum_age_of_subjects,
            planned_minimum_age_of_subjects_null_value_code=planned_minimum_age_of_subjects_null_value_code,
            planned_maximum_age_of_subjects=planned_maximum_age_of_subjects,
            planned_maximum_age_of_subjects_null_value_code=planned_maximum_age_of_subjects_null_value_code,
            stable_disease_minimum_duration=stable_disease_minimum_duration,
            stable_disease_minimum_duration_null_value_code=stable_disease_minimum_duration_null_value_code,
            pediatric_study_indicator=pediatric_study_indicator,
            pediatric_study_indicator_null_value_code=pediatric_study_indicator_null_value_code,
            pediatric_postmarket_study_indicator=pediatric_postmarket_study_indicator,
            pediatric_postmarket_study_indicator_null_value_code=pediatric_postmarket_study_indicator_null_value_code,
            pediatric_investigation_plan_indicator=pediatric_investigation_plan_indicator,
            pediatric_investigation_plan_indicator_null_value_code=pediatric_investigation_plan_indicator_null_value_code,
            relapse_criteria=relapse_criteria,
            relapse_criteria_null_value_code=relapse_criteria_null_value_code,
            number_of_expected_subjects=number_of_expected_subjects,
            number_of_expected_subjects_null_value_code=number_of_expected_subjects_null_value_code,
        )

        if condition(result):
            return result

        count += 1

    raise TimeoutError(
        f"Cannot find random data which satisfy given condition (after {count} tries)"
    )


class TestStudyPopulation(unittest.TestCase):
    def test__validate__valid_data__success(self):

        # given
        for test_data in [random_valid_study_population() for _ in range(0, 1000)]:
            with self.subTest():
                # when
                test_data.validate()

                # then
                # nothing (i.e. no exception)

    def test__validate__both_value_and_null_value_provided__failure(self):

        series_of_data_with_both_value_and_null_value_provided_for_one_of_values = [
            random.choice(
                [
                    _.fix_some_values(
                        therapeutic_area_codes=[random_str()],
                        therapeutic_area_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        disease_condition_or_indication_codes=[random_str()],
                        disease_condition_or_indication_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        diagnosis_group_codes=[random_str()],
                        diagnosis_group_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        sex_of_participants_code=random_str(),
                        sex_of_participants_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        rare_disease_indicator=random.choice([True, False]),
                        rare_disease_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        healthy_subject_indicator=random.choice([True, False]),
                        healthy_subject_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        planned_minimum_age_of_subjects=random_valid_duration_object(),
                        planned_minimum_age_of_subjects_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        planned_maximum_age_of_subjects=random_valid_duration_object(),
                        planned_maximum_age_of_subjects_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_study_indicator=random.choice([True, False]),
                        pediatric_study_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_postmarket_study_indicator=random.choice(
                            [True, False]
                        ),
                        pediatric_postmarket_study_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_investigation_plan_indicator=random.choice(
                            [True, False]
                        ),
                        pediatric_investigation_plan_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        relapse_criteria=random_str(),
                        relapse_criteria_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        number_of_expected_subjects=random_int(),
                        number_of_expected_subjects_null_value_code=random_str(),
                    ),
                ]
            )
            for _ in [random_valid_study_population() for _ in range(0, 1000)]
        ]

        # given
        for (
            test_data
        ) in series_of_data_with_both_value_and_null_value_provided_for_one_of_values:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate()

    def test__validate__invalid_therapeutic_area_code__failure(self):

        # given
        for test_data in [
            random_valid_study_population().fix_some_values(
                therapeutic_area_codes=[random_str()],
                therapeutic_area_null_value_code=None,
            )
            for _ in range(0, 10)
        ]:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate(
                        therapeutic_area_exists_callback=(lambda _: False)
                    )

    def test__validate__invalid_disease_condition_or_indication_code__failure(self):

        # given
        for test_data in [
            random_valid_study_population().fix_some_values(
                disease_condition_or_indication_codes=[random_str()],
                disease_condition_or_indication_null_value_code=None,
            )
            for _ in range(0, 10)
        ]:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate(
                        disease_condition_or_indication_exists_callback=(
                            lambda _: False
                        )
                    )

    def test__validate__invalid_diagnostic_group_code__failure(self):

        # given
        for test_data in [
            random_valid_study_population().fix_some_values(
                diagnosis_group_codes=[random_str()],
                diagnosis_group_null_value_code=None,
            )
            for _ in range(0, 10)
        ]:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate(
                        diagnosis_group_exists_callback=(lambda _: False)
                    )

    def test__validate__invalid_sex_of_participants_code__failure(self):

        # given
        for test_data in [
            random_valid_study_population().fix_some_values(
                sex_of_participants_code=random_str(),
                sex_of_participants_null_value_code=None,
            )
            for _ in range(0, 10)
        ]:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate(
                        sex_of_participants_exists_callback=(lambda _: False)
                    )

    def test__validate__invalid_null_value_code_provided__failure(self):

        series_of_data_with_one_of_null_value_provided = [
            random.choice(
                [
                    _.fix_some_values(
                        therapeutic_area_codes=(),
                        therapeutic_area_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        disease_condition_or_indication_codes=[],
                        disease_condition_or_indication_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        diagnosis_group_codes=[],
                        diagnosis_group_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        sex_of_participants_code=None,
                        sex_of_participants_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        rare_disease_indicator=None,
                        rare_disease_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        healthy_subject_indicator=None,
                        healthy_subject_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        planned_minimum_age_of_subjects=None,
                        planned_minimum_age_of_subjects_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        planned_maximum_age_of_subjects=None,
                        planned_maximum_age_of_subjects_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_study_indicator=None,
                        pediatric_study_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_postmarket_study_indicator=None,
                        pediatric_postmarket_study_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        pediatric_investigation_plan_indicator=None,
                        pediatric_investigation_plan_indicator_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        relapse_criteria=None,
                        relapse_criteria_null_value_code=random_str(),
                    ),
                    _.fix_some_values(
                        number_of_expected_subjects=None,
                        number_of_expected_subjects_null_value_code=random_str(),
                    ),
                ]
            )
            for _ in [random_valid_study_population() for _ in range(0, 1000)]
        ]

        # given
        for test_data in series_of_data_with_one_of_null_value_provided:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_data.validate(null_value_exists_callback=(lambda _: False))


def random_valid_id_metadata(
    *,
    condition: Optional[Callable[[StudyIdentificationMetadataVO], bool]] = None,
    fixed_values: Optional[Mapping[str, Any]] = None,
    max_tries: int = 100,
) -> StudyIdentificationMetadataVO:
    if fixed_values is None:
        fixed_values = _dict()

    def fixed_or_default(field_name: str, default_val: Any) -> Any:
        return fixed_values[field_name] if field_name in fixed_values else default_val

    def random_study_number() -> str:
        choice = [str(_) for _ in range(0, 10)]
        return (
            random.choice(choice)
            + random.choice(choice)
            + random.choice(choice)
            + random.choice(choice)
        )

    count: int = 0
    while True:

        result = StudyIdentificationMetadataVO(
            study_number=fixed_or_default("study_number", random_study_number()),
            study_acronym=fixed_or_default("study_acronym", random_opt_str()),
            project_number=fixed_or_default("project_number", random_opt_str()),
            # tested in separate file test_registry_identifier
            registry_identifiers=RegistryIdentifiersVO(
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
        )
        if condition is None or condition(result):
            return result
        count = count + 1
        if count >= max_tries:
            raise TimeoutError(
                f"Cannot find random data which satisfy given condition (after {count} tries)"
            )


def random_valid_id_metadata_sequence(
    count: int,
    *,
    condition: Optional[Callable[[StudyIdentificationMetadataVO], bool]] = None,
    max_tries: int = 100,
) -> Sequence[StudyIdentificationMetadataVO]:
    return [
        random_valid_id_metadata(condition=condition, max_tries=max_tries)
        for _ in range(0, count)
    ]


class TestIdentificationMetadataVO(unittest.TestCase):
    def test__study_id__results(self):
        # test data in form of tuples
        # (study_number, study_acronym, study_id_prefix, ct_gov_id, eudract_id, study_status, locked_version_number,
        #       project_number)
        test_tuples = [
            ("study-num", "study-acronym", "id-prefix", "proj-num"),
            ("s-num", None, None, None),
            (None, "study-acronym", None, None),
            (None, None, "id-prefix", None),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                # given
                id_metadata = StudyIdentificationMetadataVO(
                    study_number=test_tuple[0],
                    study_acronym=test_tuple[1],
                    _study_id_prefix=test_tuple[2],
                    project_number=test_tuple[3],
                    registry_identifiers=RegistryIdentifiersVO(
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
                )
                # when
                study_id = id_metadata.study_id

                # then
                if (
                    id_metadata.study_number is None
                    or id_metadata.study_id_prefix is None
                ):
                    self.assertIsNone(study_id)
                else:
                    self.assertEqual(
                        study_id,
                        f"{id_metadata.study_id_prefix}-{id_metadata.study_number}",
                    )

    def test__validate__non_up_to_four_digit_study_number__failure(self):
        study_numbers = ["56856", "study-number", ""]

        for study_number in study_numbers:
            with self.subTest():
                # given
                study_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                    study_number=study_number,
                    project_number=None,
                    study_acronym=None,
                    registry_identifiers=RegistryIdentifiersVO(
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
                )

                # then
                with self.assertRaises(ValueError):
                    # when
                    study_id_metadata.validate()

    def test__validate__four_digit_study_number__success(self):
        # given
        study_numbers = ["5685", "911", "11", "5"]
        for study_number in study_numbers:
            study_id_metadata = StudyIdentificationMetadataVO.from_input_values(
                study_number=study_number,
                project_number=None,
                study_acronym=None,
                registry_identifiers=RegistryIdentifiersVO(
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
            )

            # when
            study_id_metadata.validate()

            # then
            # nothing (just no exceptions)

    def test__validate__neither_study_number_nor_study_acronym__failure(self):

        for id_metadata in [
            _.fix_some_values(study_acronym=None, study_number=None)
            for _ in random_valid_id_metadata_sequence(100)
        ]:
            with self.subTest(id_metadata=id_metadata):
                # given
                assert (
                    id_metadata.study_number is None
                    and id_metadata.study_acronym is None
                )

                # then
                with self.assertRaises(ValueError):
                    # when
                    id_metadata.validate(project_exists_callback=(lambda _: True))

    def test__validate__wrong_project_number__failure(self):
        def has_project_number_and_validates_when_it_is_ok(
            id_m: StudyIdentificationMetadataVO,
        ) -> bool:
            if id_m.project_number is None:
                return False
            try:
                id_m.validate(project_exists_callback=(lambda _: True))
            except ValueError:
                return False
            return True

        for id_metadata in random_valid_id_metadata_sequence(
            count=100, condition=has_project_number_and_validates_when_it_is_ok
        ):
            with self.subTest(id_metadata=id_metadata):
                # given
                assert has_project_number_and_validates_when_it_is_ok(id_metadata)

                # then
                with self.assertRaises(ValueError):
                    # when
                    id_metadata.validate(project_exists_callback=(lambda _: False))

    def test__validate__has_study_number_or_study_acronym_and_correct_project_number_if_provided__success(
        self,
    ):
        def has_study_number_or_study_acronym(
            id_m: StudyIdentificationMetadataVO,
        ) -> bool:
            return id_m.study_number is not None or id_m.study_acronym is not None

        for id_metadata in random_valid_id_metadata_sequence(
            count=100, condition=has_study_number_or_study_acronym
        ):
            with self.subTest(id_metadata=id_metadata):
                # given
                assert has_study_number_or_study_acronym(id_metadata)

                # when
                id_metadata.validate(project_exists_callback=(lambda _: True))
                id_metadata.validate(project_exists_callback=None)

                # then
                # nothing we're just happy no exception raised


def random_valid_high_level_study_design(
    *,
    condition: Callable[[HighLevelStudyDesignVO], bool] = (lambda _: True),
    fixed_values: Optional[Mapping[str, Any]] = None,
    max_tries: int = 100,
) -> HighLevelStudyDesignVO:
    if fixed_values is None:
        fixed_values = _dict()
    count: int = 0

    def fixed_or_default(field_name: str, default_val: Any) -> Any:
        return fixed_values[field_name] if field_name in fixed_values else default_val

    while True:
        use_study_type = random.choice([True, False])
        study_type_code = (
            random.choice(initialize_ct_data_map["StudyType"])[0]
            if use_study_type
            else None
        )
        study_type_null_value_code = (
            None
            if use_study_type
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_trial_type = random.choice([True, False])
        trial_type_codes = (
            [random.choice(initialize_ct_data_map["TrialType"])[0]]
            + list(random_c_code_sequence(initialize_ct_data_map["TrialType"]))
            if use_trial_type
            else []
        )
        trial_type_null_value_code = (
            None
            if use_trial_type
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_trial_phase = random.choice([True, False])
        trial_phase_code = (
            random.choice(initialize_ct_data_map["TrialPhase"])[0]
            if use_trial_phase
            else None
        )
        trial_phase_null_value_code = (
            None
            if use_trial_phase
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_is_extension_trial = random.choice([True, False])
        is_extension_trial = (
            random.choice([True, False]) if use_is_extension_trial else None
        )
        is_extension_trial_null_value_code = (
            None
            if use_is_extension_trial
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_is_adaptive_design = random.choice([True, False])
        is_adaptive_design = (
            random.choice([True, False]) if use_is_adaptive_design else None
        )
        is_adaptive_design_null_value_code = (
            None
            if use_is_adaptive_design
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_study_stop_rules = random.choice([True, False])
        study_stop_rules = random_str() if use_study_stop_rules else None
        study_stop_rules_null_value_code = (
            None
            if use_study_stop_rules
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_confirmed_response = random.choice([True, False])
        confirmed_response_minimum_duration = (
            f"P{random.randint(1, 100)}Y" if use_confirmed_response else None
        )
        confirmed_response_minimum_duration_null_value_code = (
            None
            if use_confirmed_response
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_post_auth_indicator = random.choice([True, False])
        post_auth_indicator = (
            random.choice([True, False]) if use_post_auth_indicator else None
        )
        post_auth_indicator_null_value_code = (
            None
            if use_post_auth_indicator
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        result = HighLevelStudyDesignVO(
            study_type_code=fixed_or_default("study_type_code", study_type_code),
            study_stop_rules=fixed_or_default("study_stop_rules", study_stop_rules),
            is_adaptive_design=fixed_or_default(
                "is_adaptive_design", is_adaptive_design
            ),
            trial_phase_code=fixed_or_default("trial_phase_code", trial_phase_code),
            is_extension_trial=fixed_or_default(
                "is_extension_trial", is_extension_trial
            ),
            trial_type_codes=fixed_or_default("trial_type_codes", trial_type_codes),
            trial_phase_null_value_code=fixed_or_default(
                "trial_phase_null_value_code", trial_phase_null_value_code
            ),
            is_extension_trial_null_value_code=fixed_or_default(
                "is_extension_trial_null_value_code", is_extension_trial_null_value_code
            ),
            trial_type_null_value_code=fixed_or_default(
                "trial_type_null_value_code", trial_type_null_value_code
            ),
            is_adaptive_design_null_value_code=fixed_or_default(
                "is_adaptive_design_null_value_code", is_adaptive_design_null_value_code
            ),
            study_type_null_value_code=fixed_or_default(
                "study_type_null_value_code", study_type_null_value_code
            ),
            study_stop_rules_null_value_code=fixed_or_default(
                "study_stop_rules_null_value_code", study_stop_rules_null_value_code
            ),
            confirmed_response_minimum_duration=fixed_or_default(
                "confirmed_response_minimum_duration",
                confirmed_response_minimum_duration,
            ),
            confirmed_response_minimum_duration_null_value_code=fixed_or_default(
                "confirmed_response_minimum_duration_null_value_code",
                confirmed_response_minimum_duration_null_value_code,
            ),
            post_auth_indicator=fixed_or_default(
                "post_auth_indicator", post_auth_indicator
            ),
            post_auth_indicator_null_value_code=fixed_or_default(
                "post_auth_indicator_null_value_code",
                post_auth_indicator_null_value_code,
            ),
        )
        if condition(result):
            return result
        count = count + 1
        if count >= max_tries:
            raise TimeoutError(
                f"Cannot find random data which satisfy given condition (after {count} tries)"
            )


def random_valid_high_level_study_design_sequence(
    count: int,
    condition: Callable[[HighLevelStudyDesignVO], bool] = (lambda _: True),
    generators: Optional[Mapping[str, Any]] = None,
    max_tries: int = 100,
) -> Iterable[HighLevelStudyDesignVO]:
    if generators is None:
        generators = _dict()

    for _ in range(0, count):
        fixed_values = {}
        for field in generators.keys():
            fixed_values[field] = (
                generators[field]()
                if callable(generators[field])
                else generators[field]
            )
        yield random_valid_high_level_study_design(
            condition=condition, max_tries=max_tries, fixed_values=fixed_values
        )


def random_valid_study_description_sequence(count: int) -> Iterable[StudyDescriptionVO]:
    for _ in range(0, count):
        yield random_valid_study_description()


@given(
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
    sampled_from(["invalid-code", None]),
)
def test__high_level_study_design__validate__invalid_null_value_code_failure(
    study_type_null_value_code,
    trial_phase_null_value_code,
    trial_type_null_value_code,
    is_adaptive_design_null_value_code,
    is_extension_trial_null_value_code,
    study_stop_rules_null_value_code,
    confirmed_response_minimum_duration_null_value_code,
    post_auth_indicator_null_value_code,
):
    assume(
        not (
            study_type_null_value_code is None
            and trial_phase_null_value_code is None
            and trial_type_null_value_code is None
            and is_adaptive_design_null_value_code is None
            and is_extension_trial_null_value_code is None
            and study_stop_rules_null_value_code is None
            and confirmed_response_minimum_duration_null_value_code is None
            and post_auth_indicator_null_value_code is None
        )
    )

    # given
    high_level_study_design = HighLevelStudyDesignVO.from_input_values(
        study_type_code=None,
        study_type_null_value_code=study_type_null_value_code,
        trial_type_codes=[],
        trial_type_null_value_code=trial_type_null_value_code,
        trial_phase_code=None,
        trial_phase_null_value_code=trial_phase_null_value_code,
        is_adaptive_design=None,
        is_adaptive_design_null_value_code=is_adaptive_design_null_value_code,
        is_extension_trial=None,
        is_extension_trial_null_value_code=is_extension_trial_null_value_code,
        study_stop_rules=None,
        study_stop_rules_null_value_code=study_stop_rules_null_value_code,
        confirmed_response_minimum_duration=None,
        confirmed_response_minimum_duration_null_value_code=confirmed_response_minimum_duration_null_value_code,
        post_auth_indicator=None,
        post_auth_indicator_null_value_code=post_auth_indicator_null_value_code,
    )

    # then
    with pytest.raises(ValueError):
        # when
        high_level_study_design.validate(
            null_value_exists_callback=(
                lambda null_value_code: null_value_code != "invalid-code"
            )
        )


@settings(
    max_examples=int(max(10, settings.default.max_examples / 10)),
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)
@given(
    sampled_from([None, "code"]),
    sampled_from([None, "code"]),
    sampled_from([None, "code"]),
    sampled_from([None, "code"]),
    sampled_from([[], ["code"]]),
    sampled_from([None, "code"]),
    sampled_from([None, True, False]),
    sampled_from([None, "code"]),
    sampled_from([None, True, False]),
    sampled_from([None, "code"]),
    sampled_from([None, "stop rules"]),
    sampled_from([None, "code"]),
    sampled_from([None, "code"]),
    sampled_from([None, "code"]),
    sampled_from([None, True, False]),
    sampled_from([None, "code"]),
)
def test__high_level_study_design_vo__validate__valid_data__success(
    study_type_code,
    study_type_null_value_code,
    trial_phase_code,
    trial_phase_null_value_code,
    trial_type_codes,
    trial_type_null_value_code,
    is_adaptive_design,
    is_adaptive_design_null_value_code,
    is_extension_trial,
    is_extension_trial_null_value_code,
    study_stop_rules,
    study_stop_rules_null_value_code,
    confirmed_response,
    confirmed_response_null_value_code,
    post_auth_indicator,
    post_auth_indicator_null_value_code,
):
    assume(study_type_code is None or study_type_null_value_code is None)
    assume(trial_phase_code is None or trial_phase_null_value_code is None)
    assume(trial_type_codes == [] or trial_type_null_value_code is None)
    assume(confirmed_response is None or confirmed_response_null_value_code is None)
    assume(is_adaptive_design is None or is_adaptive_design_null_value_code is None)
    assume(is_extension_trial is None or is_extension_trial_null_value_code is None)
    assume(study_stop_rules is None or study_stop_rules_null_value_code is None)
    assume(post_auth_indicator is None or post_auth_indicator_null_value_code is None)

    # given
    high_level_study_design = HighLevelStudyDesignVO.from_input_values(
        study_type_code=study_type_code,
        study_type_null_value_code=study_type_null_value_code,
        trial_type_codes=trial_type_codes,
        trial_type_null_value_code=trial_type_null_value_code,
        trial_phase_code=trial_phase_code,
        trial_phase_null_value_code=trial_phase_null_value_code,
        is_adaptive_design=is_adaptive_design,
        is_adaptive_design_null_value_code=is_adaptive_design_null_value_code,
        is_extension_trial=is_extension_trial,
        is_extension_trial_null_value_code=is_extension_trial_null_value_code,
        study_stop_rules=study_stop_rules,
        study_stop_rules_null_value_code=study_stop_rules_null_value_code,
        confirmed_response_minimum_duration=confirmed_response,
        confirmed_response_minimum_duration_null_value_code=confirmed_response_null_value_code,
        post_auth_indicator=post_auth_indicator,
        post_auth_indicator_null_value_code=post_auth_indicator_null_value_code,
    )

    # when
    high_level_study_design.validate()


class TestStudyDescriptionVO(unittest.TestCase):
    def test__validate__create_success(self):
        # given
        test_sequence = list(random_valid_study_description_sequence(count=10))

        for test_item in test_sequence:
            with self.subTest():
                # then
                test_item.validate(
                    study_number="study_number",
                    study_title_exists_callback=(lambda _, study_number: False),
                    study_short_title_exists_callback=(lambda _, study_number: False),
                )

    def test__validate__create_existing_study_title__failure(self):
        # given
        test_sequence = list(random_valid_study_description_sequence(count=10))

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    test_item.validate(
                        study_number="study_number",
                        study_title_exists_callback=(lambda _, study_number: True),
                        study_short_title_exists_callback=(
                            lambda _, study_number: True
                        ),
                    )


class TestHighLevelStudyDesignVO(unittest.TestCase):
    def test__validate__otherwise_valid_with_invalid_null_value_present__failure(self):
        def valid_with_some_null_value(_: HighLevelStudyDesignVO) -> bool:
            return _.is_valid() and (
                _.study_type_null_value_code is not None
                or _.trial_type_null_value_code is not None
                or _.study_stop_rules_null_value_code is not None
                or _.is_adaptive_design_null_value_code is not None
                or _.is_extension_trial_null_value_code is not None
                or _.trial_phase_null_value_code is not None
            )

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=100, condition=valid_with_some_null_value
            )
        )

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: False),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_study_stop_rules_and_its_null_value_present__failure(self):

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=10, condition=(lambda _: _.is_valid())
            )
        )
        test_sequence = [
            _.fix_some_values(
                study_stop_rules=random_str(),
                study_stop_rules_null_value_code=random_str(),
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_is_adaptive_design_and_its_null_value_present__failure(
        self,
    ):

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=10, condition=(lambda _: _.is_valid())
            )
        )
        test_sequence = [
            _.fix_some_values(
                is_adaptive_design=random.choice([True, False]),
                is_adaptive_design_null_value_code=random_str(),
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_is_extension_trial_and_its_null_value_present__failure(
        self,
    ):

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=10, condition=(lambda _: _.is_valid())
            )
        )
        test_sequence = [
            _.fix_some_values(
                is_extension_trial=random.choice([True, False]),
                is_extension_trial_null_value_code=random_str(),
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_trial_types_and_its_null_value_present__failure(self):

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=10, condition=(lambda _: _.is_valid())
            )
        )
        test_sequence = [
            _.fix_some_values(
                trial_type_codes=list(random_str_sequence()) + [random_str()],
                trial_type_null_value_code=random_str(),
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_trial_phase_and_its_null_value_present__failure(self):

        # given
        test_sequence = list(
            random_valid_high_level_study_design_sequence(
                count=10, condition=(lambda _: _.is_valid())
            )
        )
        test_sequence = [
            _.fix_some_values(
                trial_phase_code=random_str(), trial_phase_null_value_code=random_str()
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__both_study_type_and_study_type_null_value_present__failure(
        self,
    ):

        # given
        test_sequence = random_valid_high_level_study_design_sequence(
            count=10, condition=(lambda _: _.is_valid())
        )
        test_sequence = [
            _.fix_some_values(
                study_type_code=random_str(), study_type_null_value_code=random_str()
            )
            for _ in test_sequence
        ]

        for test_item in test_sequence:
            with self.subTest():
                # then
                with self.assertRaises(ValueError):
                    # when
                    test_item.validate(
                        null_value_exists_callback=(lambda _: True),
                        study_type_exists_callback=(lambda _: True),
                        trial_type_exists_callback=(lambda _: True),
                        trial_intent_type_exists_callback=(lambda _: True),
                        trial_phase_exists_callback=(lambda _: True),
                    )

    def test__validate__neither_main_nor_null_values__success(self):

        # given
        test_sequence = random_valid_high_level_study_design_sequence(
            count=1,
            generators={
                "study_type_code": None,
                "trial_type_codes": [],
                "trial_intent_type_codes": [],
                "trial_phase_code": None,
                "is_extension_trial": None,
                "is_adaptive_design": None,
                "study_stop_rules": None,
                "study_type_null_value_code": None,
                "study_stop_rules_null_value_code": None,
                "is_adaptive_design_null_value_code": None,
                "is_extension_trial_null_value_code": None,
                "trial_intent_type_null_value_code": None,
                "trial_type_null_value_code": None,
                "trial_phase_null_value_code": None,
            },
        )

        for test_item in test_sequence:
            with self.subTest():
                # when
                test_item.validate(
                    null_value_exists_callback=(lambda _: True),
                    study_type_exists_callback=(lambda _: True),
                    trial_type_exists_callback=(lambda _: True),
                    trial_intent_type_exists_callback=(lambda _: True),
                    trial_phase_exists_callback=(lambda _: True),
                )

                # then
                # nothing (just no exceptions)

    def test__validate__no_main_values__success(self):

        # given
        test_sequence = random_valid_high_level_study_design_sequence(
            count=100,
            generators={
                "study_type_code": None,
                "trial_type_codes": [],
                "trial_intent_type_codes": [],
                "trial_phase_code": None,
                "is_extension_trial": None,
                "is_adaptive_design": None,
                "study_stop_rules": None,
            },
        )

        for test_item in test_sequence:
            with self.subTest():
                # when
                test_item.validate(
                    null_value_exists_callback=(lambda _: True),
                    study_type_exists_callback=(lambda _: True),
                    trial_type_exists_callback=(lambda _: True),
                    trial_intent_type_exists_callback=(lambda _: True),
                    trial_phase_exists_callback=(lambda _: True),
                )

                # then
                # nothing (just no exceptions)

    def test__validate__no_null_values__success(self):

        # given
        test_sequence = random_valid_high_level_study_design_sequence(
            count=100,
            generators={
                "study_type_null_value_code": None,
                "study_stop_rules_null_value_code": None,
                "is_adaptive_design_null_value_code": None,
                "is_extension_trial_null_value_code": None,
                "trial_intent_type_null_value_code": None,
                "trial_type_null_value_code": None,
                "trial_phase_null_value_code": None,
            },
        )

        for test_item in test_sequence:
            with self.subTest():
                # when
                test_item.validate(
                    null_value_exists_callback=(lambda _: True),
                    study_type_exists_callback=(lambda _: True),
                    trial_type_exists_callback=(lambda _: True),
                    trial_intent_type_exists_callback=(lambda _: True),
                    trial_phase_exists_callback=(lambda _: True),
                )

                # then
                # nothing (just no exceptions)

    def test__init__with_mutable_iterables__changed_to_tuples(self):
        # given
        study_type_code: Optional[str] = random_str()
        trial_type_codes: Iterable[str] = [random_str(), random_str()]
        trial_phase_code: Optional[str] = random_str()
        is_extension_trial: Optional[bool] = None
        is_adaptive_design: Optional[bool] = None
        study_stop_rules: Optional[str] = "some rules"
        confirmed_response = random_str()

        # when
        high_level_study_design = HighLevelStudyDesignVO(
            study_type_code=study_type_code,
            study_stop_rules=study_stop_rules,
            trial_type_codes=trial_type_codes,
            is_adaptive_design=is_adaptive_design,
            is_extension_trial=is_extension_trial,
            trial_phase_code=trial_phase_code,
            study_type_null_value_code=None,
            is_adaptive_design_null_value_code=None,
            study_stop_rules_null_value_code=None,
            trial_type_null_value_code=None,
            is_extension_trial_null_value_code=None,
            trial_phase_null_value_code=None,
            confirmed_response_minimum_duration=confirmed_response,
            confirmed_response_minimum_duration_null_value_code=None,
        )

        # then
        self.assertIsInstance(high_level_study_design.trial_type_codes, list)
        self.assertEqual(
            list(high_level_study_design.trial_type_codes), trial_type_codes
        )
        self.assertIsInstance(
            high_level_study_design.confirmed_response_minimum_duration, str
        )
        self.assertEqual(
            high_level_study_design.confirmed_response_minimum_duration,
            confirmed_response,
        )

    def test__validate__invalid_trial_phase_code__failure(self):
        def has_trial_phase_code_and_is_otherwise_valid(
            d: HighLevelStudyDesignVO,
        ) -> bool:
            if d.trial_phase_code is None:
                return False
            try:
                d.validate(trial_phase_exists_callback=(lambda _: True))
            except ValueError:
                return False
            return True

        for high_level_study_design in random_valid_high_level_study_design_sequence(
            10, has_trial_phase_code_and_is_otherwise_valid
        ):
            with self.subTest(high_level_study_design=high_level_study_design):
                # given
                assert has_trial_phase_code_and_is_otherwise_valid(
                    high_level_study_design
                )

                # then
                with self.assertRaises(ValueError):
                    # when
                    high_level_study_design.validate(
                        trial_phase_exists_callback=(lambda _: False)
                    )

    def test__validate__invalid_study_type_code__failure(self):
        def has_study_type_code_and_is_otherwise_valid(
            d: HighLevelStudyDesignVO,
        ) -> bool:
            if d.study_type_code is None:
                return False
            try:
                d.validate(study_type_exists_callback=(lambda _: True))
            except ValueError:
                return False
            return True

        for high_level_study_design in random_valid_high_level_study_design_sequence(
            10, has_study_type_code_and_is_otherwise_valid
        ):
            with self.subTest(high_level_study_design=high_level_study_design):
                # given
                assert has_study_type_code_and_is_otherwise_valid(
                    high_level_study_design
                )

                # then
                with self.assertRaises(ValueError):
                    # when
                    high_level_study_design.validate(
                        study_type_exists_callback=(lambda _: False)
                    )


def random_ver_metadata(
    condition: Optional[Callable[[StudyVersionMetadataVO], bool]] = None,
    max_tries: int = 100,
) -> StudyVersionMetadataVO:
    count: int = 0
    while True:
        result = StudyVersionMetadataVO(
            locked_version_info=random_opt_str(),
            locked_version_author=random_opt_str(),
            version_timestamp=random.choice(
                [None, datetime.today() + timedelta(days=random.randint(-1000, 1000))]
            ),
            study_status=random.choice(
                [StudyStatus.DRAFT, StudyStatus.RELEASED, StudyStatus.LOCKED]
            ),
            locked_version_number=random.choice([None, random.randint(-100, 100)]),
        )
        if condition is None or condition(result):
            return result
        count = count + 1
        if count >= max_tries:
            raise TimeoutError(
                f"Cannot find random data which satisfy given condition (after {count} tries)"
            )


def random_ver_metadata_sequence(
    count: int,
    condition: Optional[Callable[[StudyVersionMetadataVO], bool]] = None,
    max_tries: int = 100,
) -> Sequence[StudyVersionMetadataVO]:
    return [random_ver_metadata(condition, max_tries) for _ in range(0, count)]


def random_study_metadata(
    condition: Optional[Callable[[StudyMetadataVO], bool]] = None, max_tries: int = 100
) -> StudyMetadataVO:
    count: int = 0
    while True:
        result = StudyMetadataVO(
            high_level_study_design=random_valid_high_level_study_design(),
            ver_metadata=random_ver_metadata(),
            id_metadata=random_valid_id_metadata(),
            study_population=random_valid_study_population(),
            study_intervention=random_valid_study_intervention(),
            study_description=random_valid_study_description(),
        )
        if condition is None or condition(result):
            return result
        count = count + 1
        if count >= max_tries:
            raise TimeoutError(
                f"Cannot find random data which satisfy given condition (after {count} tries)"
            )


def random_study_metadata_sequence(
    count: int,
    condition: Optional[Callable[[StudyMetadataVO], bool]] = None,
    max_tries: int = 1000,
) -> Sequence[StudyMetadataVO]:
    return [random_study_metadata(condition, max_tries) for _ in range(0, count)]


def random_valid_study_description() -> StudyDescriptionVO:
    study_title = "".join(
        random.choice(string.ascii_uppercase + string.digits + " ") for _ in range(40)
    )
    study_short_title = "".join(
        random.choice(string.ascii_uppercase + string.digits + " ") for _ in range(40)
    )
    return StudyDescriptionVO.from_input_values(
        study_title, study_short_title=study_short_title
    )


def random_valid_study_intervention(
    *,
    condition: Callable[[StudyInterventionVO], bool] = (lambda _: True),
    max_tries: int = 100,
) -> StudyInterventionVO:
    count = 0
    while count < max_tries:
        use_intervention_type = random.choice([True, False])
        intervention_type_code = (
            random.choice(initialize_ct_data_map["InterventionType"])[0]
            if use_intervention_type
            else None
        )
        intervention_type_null_value_code = (
            None
            if use_intervention_type
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_add_on_to_existing_treatments = random.choice([True, False])
        add_on_to_existing_treatments = (
            random.choice([True, False]) if use_add_on_to_existing_treatments else None
        )
        add_on_to_existing_treatments_null_value_code = (
            None
            if use_add_on_to_existing_treatments
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_control_type = random.choice([True, False])
        control_type_code = (
            random.choice(initialize_ct_data_map["ControlType"])[0]
            if use_control_type
            else None
        )
        control_type_null_value_code = (
            None
            if use_control_type
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_intervention_model = random.choice([True, False])
        intervention_model_code = (
            random.choice(initialize_ct_data_map["InterventionModel"])[0]
            if use_intervention_model
            else None
        )
        intervention_model_null_value_code = (
            None
            if use_intervention_model
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_is_trial_randomised = random.choice([True, False])
        is_trial_randomised = (
            random.choice([True, False]) if use_is_trial_randomised else None
        )
        is_trial_randomised_null_value_code = (
            None
            if use_is_trial_randomised
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_stratification_factor = random.choice([True, False])
        stratification_factor = random_str() if use_stratification_factor else None
        stratification_factor_null_value_code = (
            None
            if use_stratification_factor
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_trial_blinding_schema_code = random.choice([True, False])
        trial_blinding_schema_code = (
            random.choice(initialize_ct_data_map["TrialBlindingSchema"])[0]
            if use_trial_blinding_schema_code
            else None
        )
        trial_blinding_schema_null_value_code = (
            None
            if use_trial_blinding_schema_code
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_planned_study_length = random.choice([True, False])
        planned_study_length = (
            random_valid_duration_object() if use_planned_study_length else None
        )
        planned_study_length_null_value_code = (
            None
            if use_planned_study_length
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_drug_study_indication = random.choice([True, False])
        drug_study_indication = (
            random.choice([True, False]) if use_drug_study_indication else None
        )
        drug_study_indication_null_value_code = (
            None
            if use_drug_study_indication
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_device_study_indication = random.choice([True, False])
        device_study_indication = (
            random.choice([True, False]) if use_device_study_indication else None
        )
        device_study_indication_null_value_code = (
            None
            if use_device_study_indication
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        use_trial_intent_type = random.choice([True, False])
        trial_intent_type_codes = (
            [random.choice(initialize_ct_data_map["TrialIntentType"])[0]]
            + list(random_c_code_sequence(initialize_ct_data_map["TrialIntentType"]))
            if use_trial_intent_type
            else []
        )
        trial_intent_type_null_value_code = (
            None
            if use_trial_intent_type
            else random_opt_c_code(initialize_ct_data_map["NullValueCodes"])
        )

        result = StudyInterventionVO.from_input_values(
            intervention_type_code=intervention_type_code,
            intervention_type_null_value_code=intervention_type_null_value_code,
            add_on_to_existing_treatments=add_on_to_existing_treatments,
            add_on_to_existing_treatments_null_value_code=add_on_to_existing_treatments_null_value_code,
            control_type_code=control_type_code,
            control_type_null_value_code=control_type_null_value_code,
            intervention_model_code=intervention_model_code,
            intervention_model_null_value_code=intervention_model_null_value_code,
            is_trial_randomised=is_trial_randomised,
            is_trial_randomised_null_value_code=is_trial_randomised_null_value_code,
            stratification_factor=stratification_factor,
            stratification_factor_null_value_code=stratification_factor_null_value_code,
            trial_blinding_schema_code=trial_blinding_schema_code,
            trial_blinding_schema_null_value_code=trial_blinding_schema_null_value_code,
            planned_study_length=planned_study_length,
            planned_study_length_null_value_code=planned_study_length_null_value_code,
            drug_study_indication=drug_study_indication,
            device_study_indication=device_study_indication,
            drug_study_indication_null_value_code=drug_study_indication_null_value_code,
            device_study_indication_null_value_code=device_study_indication_null_value_code,
            trial_intent_type_codes=trial_intent_type_codes,
            trial_intent_type_null_value_code=trial_intent_type_null_value_code,
        )

        if condition(result):
            return result

        count += 1

    raise TimeoutError(
        f"Cannot find random data which satisfy given condition (after {count} tries)"
    )


class TestStudyMetadataVO(unittest.TestCase):
    def test__validate__all_components_valid__success(self):
        # test data in form of tuples
        # (study_number, study_acronym, study_id_prefix, ct_gov_id, eudract_id, study_status, locked_version_number,
        #       project_number, version_info, version_author)

        def all_components_valid(_: StudyMetadataVO) -> bool:
            try:
                _.id_metadata.validate()
                _.ver_metadata.validate()
                _.high_level_study_design.validate()
                _.study_intervention.validate()
            except ValueError:
                return False
            return True

        for study_metadata in random_study_metadata_sequence(10, all_components_valid):
            with self.subTest(study_metadata=study_metadata):
                # given
                assert all_components_valid(study_metadata)

                # when
                study_metadata.validate()

    def test__validate__some_components_invalid__failure(self):
        def is_valid(
            _: Union[
                StudyIdentificationMetadataVO,
                StudyVersionMetadataVO,
                HighLevelStudyDesignVO,
            ]
        ) -> bool:
            try:
                _.validate()
            except ValueError:
                return False
            return True

        def is_invalid(_):
            return not is_valid(_)

        def combine_sequences(
            id_metadata_sequence: Sequence[StudyIdentificationMetadataVO],
            ver_metadata_sequence: Sequence[StudyVersionMetadataVO],
            high_level_study_design_sequence: Sequence[HighLevelStudyDesignVO],
            study_population_sequence: Sequence[StudyPopulationVO],
            study_intervention_sequence: Sequence[StudyInterventionVO],
            study_description_sequence: Sequence[StudyDescriptionVO],
        ) -> Sequence[StudyMetadataVO]:
            return [
                StudyMetadataVO(
                    id_metadata=id_metadata_sequence[i],
                    ver_metadata=ver_metadata_sequence[i],
                    high_level_study_design=high_level_study_design_sequence[i],
                    study_population=study_population_sequence[i],
                    study_intervention=study_intervention_sequence[i],
                    study_description=study_description_sequence[i],
                )
                for i in range(0, len(id_metadata_sequence))
            ]

        test_sequence: List[StudyMetadataVO] = []
        valid_id_metadata_sequence = random_valid_id_metadata_sequence(count=10)
        invalid_id_metadata_sequence = [
            _.fix_some_values(study_number=None, study_acronym=None)
            for _ in valid_id_metadata_sequence
        ]

        valid_ver_metadata_sequence = random_ver_metadata_sequence(10, is_valid)
        invalid_ver_metadata_sequence = random_ver_metadata_sequence(10, is_invalid)

        valid_high_level_study_design_sequence = list(
            random_valid_high_level_study_design_sequence(10)
        )
        invalid_high_level_study_design_sequence = [
            _.fix_some_values(
                study_type_code=random_str(), study_type_null_value_code=random_str()
            )
            for _ in valid_high_level_study_design_sequence
        ]

        valid_study_population_sequence = [
            random_valid_study_population() for _ in range(0, 10)
        ]
        invalid_study_population_sequence = [
            _.fix_some_values(
                therapeutic_area_codes=[random_str()],
                therapeutic_area_null_value_code=random_str(),
            )
            for _ in valid_study_population_sequence
        ]

        valid_study_intervention_sequence = [
            random_valid_study_intervention() for _ in range(0, 10)
        ]
        invalid_study_intervention_sequence = [
            _.fix_some_values(
                intervention_type_code=random_str(),
                intervention_type_null_value_code=random_str(),
            )
            for _ in valid_study_intervention_sequence
        ]

        valid_study_description_sequence = [
            random_valid_study_description() for _ in range(0, 10)
        ]

        # invalid high level study design
        test_sequence.extend(
            combine_sequences(
                valid_id_metadata_sequence,
                valid_ver_metadata_sequence,
                invalid_high_level_study_design_sequence,
                valid_study_population_sequence,
                valid_study_intervention_sequence,
                valid_study_description_sequence,
            )
        )

        # invalid id metadata
        test_sequence.extend(
            combine_sequences(
                invalid_id_metadata_sequence,
                valid_ver_metadata_sequence,
                valid_high_level_study_design_sequence,
                valid_study_population_sequence,
                valid_study_intervention_sequence,
                valid_study_description_sequence,
            )
        )

        # invalid ver metadata
        test_sequence.extend(
            combine_sequences(
                valid_id_metadata_sequence,
                invalid_ver_metadata_sequence,
                valid_high_level_study_design_sequence,
                valid_study_population_sequence,
                valid_study_intervention_sequence,
                valid_study_description_sequence,
            )
        )

        # invalid study population
        test_sequence.extend(
            combine_sequences(
                valid_id_metadata_sequence,
                valid_ver_metadata_sequence,
                valid_high_level_study_design_sequence,
                invalid_study_population_sequence,
                valid_study_intervention_sequence,
                valid_study_description_sequence,
            )
        )

        # invalid study intervention
        test_sequence.extend(
            combine_sequences(
                valid_id_metadata_sequence,
                valid_ver_metadata_sequence,
                valid_high_level_study_design_sequence,
                valid_study_population_sequence,
                invalid_study_intervention_sequence,
                valid_study_description_sequence,
            )
        )

        for study_metadata in test_sequence:
            with self.subTest(study_metadata=study_metadata):
                # given
                # study_metadata

                # then
                with self.assertRaises(ValueError):
                    # when
                    study_metadata.validate()
