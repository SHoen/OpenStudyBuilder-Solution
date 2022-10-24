from unittest import TestCase

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM,
    STARTUP_ODM_ALIASES,
    STARTUP_ODM_CONDITIONS,
    STARTUP_ODM_FORMAL_EXPRESSIONS,
    STARTUP_ODM_FORMS,
    STARTUP_ODM_ITEM_GROUPS,
    STARTUP_ODM_ITEMS,
    STARTUP_ODM_TEMPLATES,
    STARTUP_ODM_XML_EXPORTER,
    STARTUP_UNIT_DEFINITIONS,
)


class OdmCsvExporterTest(TestCase):
    TEST_DB_NAME = "odmxmlexporter"
    HEADERS = {"content-type": "text/csv"}

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ODM_FORMAL_EXPRESSIONS)
        db.cypher_query(STARTUP_ODM_CONDITIONS)
        db.cypher_query(STARTUP_ODM_ALIASES)
        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_UNIT_DEFINITIONS)
        db.cypher_query(STARTUP_ODM_ITEMS)
        db.cypher_query(STARTUP_ODM_ITEM_GROUPS)
        db.cypher_query(STARTUP_ODM_FORMS)
        db.cypher_query(STARTUP_ODM_TEMPLATES)
        db.cypher_query(STARTUP_ODM_XML_EXPORTER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_get_odm_template(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=odm_template1&targetType=template",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint:disable=line-too-long
            == '"Template_Name","Template_Version","Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","yes","1.0","name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_form(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=odm_form1&targetType=form",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint:disable=line-too-long
            == '"Form_Name","Form_Repeating","Form_Version","ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","yes","1.0","name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_item_group(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=odm_item_group1&targetType=item-group",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint:disable=line-too-long
            == '"ItemGroup_Name","ItemGroup_Version","Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","1.0","name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_get_odm_item(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=odm_item1&targetType=item",
            headers=self.HEADERS,
        )

        assert response.status_code == 200
        assert (
            response.text
            # pylint:disable=line-too-long
            == '"Item_Name","Item_Datatype","Item_Version","Item_Units","Item_Codelist","Item_Terms"\n"name1","datatype1","1.0","name1","name1","code_submission_value1"\n'
        )

    def test_odm_template_not_found(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=wrong&targetType=template",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_form_not_found(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=wrong&targetType=form",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_item_group_not_found(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=wrong&targetType=item-group",
            headers=self.HEADERS,
        )

        assert response.status_code == 404

    def test_odm_item_not_found(self):
        response = self.test_client.get(
            "concepts/odms/metadata/csvs?targetUid=wrong&targetType=item",
            headers=self.HEADERS,
        )

        assert response.status_code == 404
