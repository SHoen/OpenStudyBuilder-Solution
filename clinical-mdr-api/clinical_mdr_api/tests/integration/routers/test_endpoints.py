import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.models import EndpointTemplate
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.endpoint_templates import EndpointTemplateService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    library_data,
    template_data,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class EndpointTest(api.APITest):
    TEST_DB_NAME = "unittestsobjs"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        epdata = template_data.copy()
        epdata["name"] = "Test [Indication]"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**epdata)
        self.ep = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.ep, EndpointTemplate)
        EndpointTemplateService().approve(self.ep.uid)
        self.data["etuid"] = self.ep.uid
        print(self.ep.uid)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoints.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time"]


# @pytest.mark.skip
class EndpointNegativeTest(EndpointTest):
    TEST_DB_NAME = "unittestsobjs"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(name="Test library", is_editable=True)
        etdata = template_data.copy()
        etdata["editableInstance"] = False
        endpoint_template = ep_models.EndpointTemplateCreateInput(**etdata)
        self.et = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.et, EndpointTemplate)
        EndpointTemplateService().approve(self.et.uid)
        self.data["etuid"] = self.et.uid
        etdt = template_data.copy()
        etdt["name"] = "Name not approved"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**etdt)
        self.not_approved_et = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.not_approved_et, EndpointTemplate)
        self.data["etuidna"] = self.not_approved_et.uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoint_negative.json")]

    def post_test(self):
        def check_endpoints_empty():
            repos = MetaRepository()
            data = repos.endpoint_repository.find_all()
            self.assertListEqual(list(data), [])

        check_endpoints_empty()

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


# @pytest.mark.skip
class EndpointVersioningTest(EndpointTest):
    TEST_DB_NAME = "unittestsobjs"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        import clinical_mdr_api.models.endpoint_template as ep_models
        import clinical_mdr_api.services.libraries as library_service
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)
        self.library = library_service.create(**library_data)
        epdata = template_data.copy()
        epdata["name"] = "Test [Indication]"
        endpoint_template = ep_models.EndpointTemplateCreateInput(**epdata)
        self.ep = EndpointTemplateService().create(endpoint_template)
        assert isinstance(self.ep, EndpointTemplate)
        EndpointTemplateService().approve(self.ep.uid)
        self.data["etuid"] = self.ep.uid

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "endpoint_versioning.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "path", "uid"]
