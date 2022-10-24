import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_XML_EXTENSION_ATTRIBUTES,
    STARTUP_ODM_XML_EXTENSION_TAGS,
    STARTUP_ODM_XML_EXTENSIONS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmFormTest(api.APITest):
    TEST_DB_NAME = "odmforms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_TAGS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_forms.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
        ]


class OdmFormNegativeTest(api.APITest):
    TEST_DB_NAME = "odmforms"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_TAGS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_forms_negative.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
            "time",
        ]
