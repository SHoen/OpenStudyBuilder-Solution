import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models.endpoint_template import EndpointTemplateCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.endpoint_templates import EndpointTemplateService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class EndpointTemplatesTest(api.APITest):
    TEST_DB_NAME = "unittestsets"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)

    def testFiltering(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        import clinical_mdr_api.services.libraries as library_service

        self.library = library_service.create(**library_data)
        Service = EndpointTemplateService
        Service().create(
            EndpointTemplateCreateInput(libraryName=library_data["name"], name="test")
        )
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            path_root="/endpoint-templates",
            filter_field_name="name",
            wildcard_filter_field_name=self.library["name"],
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoint_template.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid"]


class EndpointTemplatesNegativeTest(api.APITest):
    TEST_DB_NAME = "unittestsets"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=False)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "endpoint_template_negative.json")
    ]

    def post_test(self):
        def check_endpoint_templates_empty():
            repos = MetaRepository()
            data = repos.endpoint_template_repository.find_all()
            self.assertListEqual(list(data), [])

        check_endpoint_templates_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


class EndpointTemplatesVersioningTest(api.APITest):
    TEST_DB_NAME = "unittestsets"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "endpoint_template_versioning.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid"]
