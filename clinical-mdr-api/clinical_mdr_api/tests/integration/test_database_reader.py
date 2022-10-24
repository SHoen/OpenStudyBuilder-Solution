import unittest

from clinical_mdr_api.config import DEFAULT_STUDY_FIELD_CONFIG_FILE
from clinical_mdr_api.domain.study_definition_aggregate.study_configuration import (
    from_database,
    from_file,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data


class TestConfigurationReaders(unittest.TestCase):
    TEST_DB_NAME = "configreader"

    def setUp(self) -> None:
        inject_and_clear_db(self.TEST_DB_NAME)
        inject_base_data()

    def test__import_and_file__same_results(self):
        data_from_file = from_file(DEFAULT_STUDY_FIELD_CONFIG_FILE)
        data_from_database = from_database()
        data_from_file.sort(key=lambda s: s.study_field_name)
        data_from_database.sort(key=lambda s: s.study_field_name)
        self.assertEqual(data_from_file, data_from_database)
