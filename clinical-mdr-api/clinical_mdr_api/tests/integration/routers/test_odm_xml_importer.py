import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER,
    STARTUP_UNIT_DEFINITIONS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class OdmXmlImporterTest(api.APITest):
    TEST_DB_NAME = "odmxmlimporter"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query("MERGE (library:Library {name:'Sponsor', is_editable:true})")
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "odm_xml_importer.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
        ]
