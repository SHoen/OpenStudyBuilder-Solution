import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class TimeframeTemplatesTest(api.APITest):
    TEST_DB_NAME = "timeframetemplates"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

        from clinical_mdr_api.domain_repositories.models.generic import Library

        lib = Library(name="Test library", is_editable=True)
        lib.save()
        lib2 = Library(name="Test library1", is_editable=False)
        lib2.save()

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "timeframe_template.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid"]

    def post_test(self):
        def check_template_parameters():
            from clinical_mdr_api.domain_repositories.models.template_parameter import (
                TemplateParameter,
            )
            from clinical_mdr_api.domain_repositories.templates.timeframe_template_repository import (  # noqa: E501
                TimeframeTemplateRepository,
            )

            tp = TemplateParameter.nodes.get_or_none(name="Intervention")
            self.assertIsNotNone(tp)
            data = TimeframeTemplateRepository().find_all()
            if len(data) == 2:
                ttroot = (
                    TimeframeTemplateRepository()
                    .find_by_uid_2(data[0].uid, for_update=True)
                    .repository_closure_data[0]
                )
                tp = ttroot.has_parameters.all()
                self.assertEqual(len(tp), 1)

        check_template_parameters()


class TimeframeTemplatesNegativeTest(TimeframeTemplatesTest):
    TEST_DB_NAME = "timeframetemplates"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        from clinical_mdr_api.domain_repositories.models.generic import Library

        lib = Library(name="Test library", is_editable=True)
        lib.save()
        lib2 = Library(name="Test library1", is_editable=False)
        lib2.save()

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "timeframe_template_negative.json")
    ]

    def post_test(self):
        def check_timeframe_templates_empty():
            from clinical_mdr_api.services.timeframe_templates import (
                TimeframeTemplateService,
            )

            data = TimeframeTemplateService().get_all(total_count=True)
            self.assertEqual(data.total_count, 0)

        check_timeframe_templates_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


class TimeframeTemplatesVersioningTest(TimeframeTemplatesTest):
    TEST_DB_NAME = "timeframetemplates"

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "timeframe_template_versioning.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid", "content-length"]
