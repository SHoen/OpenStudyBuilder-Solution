import unittest

from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)

# Goal is to test the business logic of the class


class TestRegistryIdentifiers(unittest.TestCase):
    def test__validate__valid_data__success(self):
        test_tuples = [
            (
                "ct-gov-id",
                "eudract-id",
                "universal-trial-number-UTN",
                "japanese-trial-registry-id-JAPIC",
                "investigational-new-drug-application-number-IND",
                None,
            ),
            ("ct-gov-id", None, None, None, None, None),
            (None, "eudract-id", None, None, None, None),
            (None, None, "universal-trial-number-UTN", None, None, None),
            (None, None, None, "japanese-trial-registry-id-JAPIC", None, None),
            (
                None,
                None,
                None,
                None,
                "investigational-new-drug-application-number-IND",
                None,
            ),
            (None, None, None, None, None, "missing-reason"),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                registry_identifier = RegistryIdentifiersVO(
                    ct_gov_id=test_tuple[0],
                    eudract_id=test_tuple[1],
                    universal_trial_number_UTN=test_tuple[2],
                    japanese_trial_registry_id_JAPIC=test_tuple[3],
                    investigational_new_drug_application_number_IND=test_tuple[4],
                    ct_gov_id_null_value_code=test_tuple[5],
                    eudract_id_null_value_code=test_tuple[5],
                    universal_trial_number_UTN_null_value_code=test_tuple[5],
                    japanese_trial_registry_id_JAPIC_null_value_code=test_tuple[5],
                    investigational_new_drug_application_number_IND_null_value_code=test_tuple[
                        5
                    ],
                )
                registry_identifier.validate()

    def test__validate__valid_data__failure(self):
        test_tuples = [
            (
                "ct-gov-id",
                "eudract-id",
                "universal-trial-number-UTN",
                "japanese-trial-registry-id-JAPIC",
                "investigational-new-drug-application-number-IND",
                "missing-reason",
            ),
            ("ct-gov-id", None, None, None, None, "missing-reason"),
            (None, "eudract-id", None, None, None, "missing-reason"),
            (None, None, "universal-trial-number-UTN", None, None, "missing-reason"),
            (
                None,
                None,
                None,
                "japanese-trial-registry-id-JAPIC",
                None,
                "missing-reason",
            ),
            (
                None,
                None,
                None,
                None,
                "investigational-new-drug-application-number-IND",
                "missing-reason",
            ),
        ]
        for test_tuple in test_tuples:
            with self.subTest(test_tuple=test_tuple):
                registry_identifier = RegistryIdentifiersVO(
                    ct_gov_id=test_tuple[0],
                    eudract_id=test_tuple[1],
                    universal_trial_number_UTN=test_tuple[2],
                    japanese_trial_registry_id_JAPIC=test_tuple[3],
                    investigational_new_drug_application_number_IND=test_tuple[4],
                    ct_gov_id_null_value_code=test_tuple[5],
                    eudract_id_null_value_code=test_tuple[5],
                    universal_trial_number_UTN_null_value_code=test_tuple[5],
                    japanese_trial_registry_id_JAPIC_null_value_code=test_tuple[5],
                    investigational_new_drug_application_number_IND_null_value_code=test_tuple[
                        5
                    ],
                )
                with self.assertRaises(ValueError):
                    registry_identifier.validate()
