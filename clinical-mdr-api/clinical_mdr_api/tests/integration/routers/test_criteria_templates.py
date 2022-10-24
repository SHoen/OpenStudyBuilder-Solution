import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models.criteria_template import CriteriaTemplateCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.criteria_templates import CriteriaTemplateService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CRITERIA,
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class CriteriaTemplatesTest(api.APITest):
    TEST_DB_NAME = "unittestscts"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_CRITERIA)
        db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def testFiltering(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CRITERIA)
        Service = CriteriaTemplateService
        Service().create(
            CriteriaTemplateCreateInput(
                libraryName="CDISC", name="test", typeUid="C25532"
            )
        )
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            filter_field_name="name",
            path_root="/criteria-templates",
            wildcard_filter_field_name="CDISC",
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "criteria_template.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid"]


class CriteriaTemplatesNegativeTest(api.APITest):
    TEST_DB_NAME = "unittestscts"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=False)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "criteria_template_negative.json")
    ]

    def post_test(self):
        def check_criteria_templates_empty():
            repos = MetaRepository()
            data = list(repos.criteria_template_repository.find_all())
            self.assertListEqual(data, [])

        check_criteria_templates_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


class CriteriaTemplatesVersioningTest(api.APITest):
    TEST_DB_NAME = "unittestsctsver"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_CRITERIA)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "criteria_template_versioning.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid", "content-length"]
