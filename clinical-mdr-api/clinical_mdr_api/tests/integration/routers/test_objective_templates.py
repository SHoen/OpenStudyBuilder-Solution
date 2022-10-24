import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models.objective_template import ObjectiveTemplateCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ObjectiveTemplatesTest(api.APITest):
    TEST_DB_NAME = "unittestsots"

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
        Service = ObjectiveTemplateService
        Service().create(
            ObjectiveTemplateCreateInput(libraryName=library_data["name"], name="test")
        )
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            path_root="/objective-templates",
            filter_field_name="name",
            wildcard_filter_field_name=self.library["name"],
        )

    SCENARIO_PATHS = ["clinical_mdr_api/tests/data/scenarios/objective_template.json"]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid"]


# @pytest.mark.skip
class ObjectiveTemplatesNegativeTest(api.APITest):
    TEST_DB_NAME = "unittestsots"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=False)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "objective_template_negative.json")
    ]

    def post_test(self):
        def check_objective_templates_empty():
            repos = MetaRepository()
            data = list(repos.objective_template_repository.find_all())
            self.assertListEqual(data, [])

        check_objective_templates_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


# @pytest.mark.skip
class ObjectiveTemplatesVersioningTest(api.APITest):
    TEST_DB_NAME = "unittestsotsver"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "objective_template_versioning.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid", "content-length"]
