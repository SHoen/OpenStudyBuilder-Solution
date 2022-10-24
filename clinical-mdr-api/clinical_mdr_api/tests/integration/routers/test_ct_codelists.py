import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
    STARTUP_CT_CODELISTS_NAME_CYPHER,
    STARTUP_CT_TERM_WITHOUT_CATALOGUE,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CTCodelistNameTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def testFiltering(self):
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            filter_field_name="catalogueName",
            path_root="/ct/codelists/names",
            wildcard_filter_field_name="CT",
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_codelist_name.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class CTCodelistNameTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "ct_codelist_name_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "userInitials"]


class CTCodelistAttributesTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_WITHOUT_CATALOGUE)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_codelist_attributes.json")]

    def ignored_fields(self):
        return ["codelistUid", "startDate", "endDate", "userInitials"]


class CTCodelistAttributesTestNegativeTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "ct_codelist_attributes_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "userInitials"]


class CTCodelistConcurrencyTest(api.APITest):
    TEST_DB_NAME = "cttests.codelists"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_CT_CODELISTS_NAME_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "ct_codelist_concurrency.json")]

    def is_check_headers_needed(self):
        return True

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "time",
            "userInitials",
            "traceresponse",
            "content-length",
            "content-type",
        ]
