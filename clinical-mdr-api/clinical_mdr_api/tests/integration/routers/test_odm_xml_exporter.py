import xml.etree.ElementTree as ET
from json import loads
from unittest import TestCase

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.data.odm_xml import (
    export_form,
    export_item,
    export_item_group,
    export_template,
    export_with_csv,
    export_with_extension,
)
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
    STARTUP_ODM_XML_EXTENSION_TAGS,
    STARTUP_ODM_XML_EXTENSIONS,
    STARTUP_UNIT_DEFINITIONS,
)
from clinical_mdr_api.tests.utils.utils import xml_diff


class OdmXmlExporterTest(TestCase):
    TEST_DB_NAME = "odmxmlexporter"
    CONTENT_TYPE = "application/xml"

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
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)
        db.cypher_query(STARTUP_ODM_XML_EXTENSION_TAGS)
        db.cypher_query(STARTUP_ODM_XML_EXPORTER)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_get_odm_xml_template(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_template1&target_type=template&stylesheet=file.xsl",
        )

        expected_xml = ET.fromstring(export_template)
        actual_xml = ET.fromstring(response.content)

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_get_odm_xml_form(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_form1&target_type=form&stylesheet=file.xsl",
        )

        expected_xml = ET.fromstring(export_form)
        actual_xml = ET.fromstring(response.content)

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_get_odm_xml_item_group(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_item_group1&target_type=item_group&stylesheet=file.xsl",
        )

        expected_xml = ET.fromstring(export_item_group)
        actual_xml = ET.fromstring(response.content)

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_get_odm_xml_item(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_item1&target_type=item&stylesheet=file.xsl",
        )

        expected_xml = ET.fromstring(export_item)
        actual_xml = ET.fromstring(response.content)

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        assert '<?xml-stylesheet type="text/xsl" href="file.xsl"?>' in response.text
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_get_odm_xml_with_allowed_extensions(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_template1&target_type=template&allowed_extensions=prefix",
        )

        expected_xml = ET.fromstring(export_with_extension)
        actual_xml = ET.fromstring(response.content)
        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_get_odm_xml_with_mapper_csv(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_type=template&target_uid=odm_template1",
            files={
                "mapper": (
                    "mapper.csv",
                    "type,parent,from_name,to_name,to_alias,from_alias,alias_context\n"
                    "attribute,,osb:instruction,CompletionInstructions,,,\n"
                    "attribute,*,osb:sponsorInstruction,ImplementationNotes,,,\n"
                    "attribute,,CompletionInstructions,,true,,\n"
                    "attribute,*,ImplementationNotes,,true,,\n"
                    "attribute,FormDef,osb:version,ov,,,\n"
                    "tag,,ItemRef,osb:ItemRef,,,\n"
                    "tag,FormDef,ItemGroupRef,osb:ItemGroupRef,,,\n"
                    "tag,*,MeasurementUnitRef,osb:measurementUnitRef,,,\n"
                    "tag,*,osb:DomainColor,DomainColor,,,",
                    "text/csv",
                )
            },
        )

        expected_xml = ET.fromstring(export_with_csv)
        actual_xml = ET.fromstring(response.content)

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), self.CONTENT_TYPE)

        xml_diff(expected_xml, actual_xml)

    def test_throw_exception_if_target_type_is_not_supported(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=study&target_type=study",
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)

        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(rs["message"], "Requested target type not supported.")

    def test_throw_exception_if_mapper_is_non_csv(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_template1&target_type=template",
            files={
                "mapper": (
                    "mapper.json",
                    "type,parent,from_name,to_name,to_alias\n"
                    "attribute,,osb:instruction,CompletionInstructions,\n",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(rs["message"], "Only CSV format is supported.")

    def test_throw_exception_if_csv_header_missing(self):
        response = self.test_client.post(
            "concepts/odms/metadata/xmls/export?target_uid=odm_template1&target_type=template",
            files={
                "mapper": (
                    "mapper.csv",
                    "parent,from_name,to_name,to_alias\n"
                    ",osb:instruction,CompletionInstructions,\n",
                    "text/csv",
                )
            },
        )

        self.assertEqual(response.status_code, 400)
        rs = loads(response.content)
        self.assertEqual(rs["type"], "BusinessLogicException")
        self.assertEqual(
            rs["message"],
            "These headers must be present: ['alias_context', 'from_alias', 'from_name', 'parent', 'to_alias', 'to_name', 'type']",
        )
