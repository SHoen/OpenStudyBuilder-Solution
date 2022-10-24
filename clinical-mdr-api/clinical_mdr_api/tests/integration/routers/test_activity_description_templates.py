import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models.activity_description_template import (
    ActivityDescriptionTemplateCreateInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.activity_description_templates import (
    ActivityDescriptionTemplateService,
)
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_DICTIONARY_CODELISTS_CYPHER,
    STARTUP_DICTIONARY_TERMS_CYPHER,
    STARTUP_PARAMETERS_CYPHER,
    library_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ActivityDescriptionTemplatesTest(api.APITest):
    TEST_DB_NAME = "unittestsats"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_CODELISTS_CYPHER)
        db.cypher_query(STARTUP_DICTIONARY_TERMS_CYPHER)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)

    def testFiltering(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        import clinical_mdr_api.services.libraries as library_service

        self.library = library_service.create(**library_data)
        Service = ActivityDescriptionTemplateService
        Service().create(
            ActivityDescriptionTemplateCreateInput(
                libraryName=library_data["name"],
                name="test",
                activitySubGroupUids=["activity_sub_group_root1"],
                activityGroupUids=["activity_group_root1"],
            )
        )
        self.filtering_common_test_scenario(
            test_client=self.test_client,
            path_root="/activity-description-templates",
            filter_field_name="name",
            wildcard_filter_field_name=self.library["name"],
        )

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_description_template.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid"]


class ActivityDescriptionTemplatesNegativeTest(api.APITest):
    TEST_DB_NAME = "unittestsats"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=False)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_description_template_negative.json")
    ]

    def post_test(self):
        def check_activity_description_templates_empty():
            repos = MetaRepository()
            data = list(repos.activity_description_template_repository.find_all())
            self.assertListEqual(data, [])

        check_activity_description_templates_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


class ActivityDescriptionTemplatesVersioningTest(api.APITest):
    TEST_DB_NAME = "unittestsatsver"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_description_template_versioning.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid", "content-length"]
