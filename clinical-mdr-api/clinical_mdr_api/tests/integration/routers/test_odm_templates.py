import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import STARTUP_ODM_FORMS

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmTemplateTest(api.APITest):
    TEST_DB_NAME = "odmtemplates"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMS)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_templates.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
        ]


class OdmTemplateNegativeTest(api.APITest):
    TEST_DB_NAME = "odmtemplates"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMS)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_templates_negative.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
            "time",
        ]
