import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_DESCRIPTIONS,
    STARTUP_ODM_XML_EXTENSION_ATTRIBUTES,
    STARTUP_ODM_XML_EXTENSION_TAGS,
    STARTUP_ODM_XML_EXTENSIONS,
    STARTUP_UNIT_DEFINITIONS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmItemTest(api.APITest):
    TEST_DB_NAME = "odmitems"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_TAGS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_items.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
        ]


class OdmItemNegativeTest(api.APITest):
    TEST_DB_NAME = "odmitems"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_ODM_DESCRIPTIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_TAGS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_ATTRIBUTES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_items_negative.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
            "time",
        ]
