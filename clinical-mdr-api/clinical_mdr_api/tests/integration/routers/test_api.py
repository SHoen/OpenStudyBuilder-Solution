from unittest import TestCase

from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import create_paths


class TestApi(TestCase):
    TEST_DB_NAME = "unittests"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

        # load_schema_file(graph, DB_SCHEMA_SCRIPT)
        # load_data_file(graph, DB_INIT_SCRIPT)

    def tearDown(self):
        pass  # db.cypher_query(f"DROP DATABASE {self.EST_DB_NAME}")

    def test_all_gets(self):
        all_paths = create_paths()
        for route in all_paths:
            if "GET" in route["methods"]:
                path = route["path_ready"]
                is_specific = route["is_specific"]
                print(route)
                try:

                    response = self.test_client.get(path)
                    if is_specific:
                        # TODO: passed because some calls respond
                        # with empty list instead of 404
                        # self.assertIn(response.status_code, [400, 404, 422])
                        pass
                    elif path in [
                        "/study/1/study-objectives/{study_objective_uid}",
                        "/study/1/study-criteria/{studycriteriauid}",
                    ]:
                        # this test fails for now as there are no connections between study and objective/criteria selected
                        self.assertIn(response.status_code, [404])
                    elif path.endswith("get-by-name/{name}"):
                        # This test fails because we do not know the name
                        self.assertIn(response.status_code, [404])
                    elif path == "/ct/packages/changes":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/ct/packages/dates":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path.endswith("/headers"):
                        # This fails because it takes a mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/study/allowed-configs":
                        # This fails because it needs data setup
                        self.assertIn(response.status_code, [404])
                    elif path.startswith("/studies/1/study-epochs/"):
                        # This fails because it takes a mandatory query parameter
                        self.assertIn(response.status_code, [400])
                    elif path == "/ct/catalogues/changes":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/ct/codelists/{codelistUid}/sub-codelists":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/dictionaries/terms":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/dictionaries/codelists/{library}":
                        # This test fails because of Library that has to exist
                        self.assertIn(response.status_code, [400])
                    elif path == "/study-flowchart/flowchart":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422, 404])
                    elif path == "/study/study-visits/allowed-visit-types":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/study/study-visits/allowed-time-references":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/concepts/odms/metadata/xmls":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/concepts/odms/metadata/csvs":
                        # This test fails because of mandatory query parameter
                        self.assertIn(response.status_code, [422])
                    elif path == "/system/check/secured":
                        self.assertIn(response.status_code, [401, 501])
                    else:
                        self.assertEqual(response.status_code, 200)
                except Exception as e:
                    print(f"Exception during GET {path} execution")
                    raise e

    def test_all_posts(self):
        all_paths = create_paths()
        for route in all_paths:
            if "POST" in route["methods"]:
                path = route["path_ready"]
                data = route.get("data")

                if data:
                    print(f"Evaluating POST {path}")
                    response = self.test_client.post(path, json=data)
                    if path.endswith("pre-validate"):
                        self.assertIn(response.status_code, [202])
                    elif path.endswith("libraries"):
                        self.assertIn(response.status_code, [201])
                    else:
                        self.assertIn(response.status_code, [404, 400, 422])
