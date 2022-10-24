import xml.etree.ElementTree as ET
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
    STARTUP_ODM_XML_EXTENSIONS,
    STARTUP_UNIT_DEFINITIONS,
)


class OdmXmlExporterTest(TestCase):
    TEST_DB_NAME = "odmxmlexporter"

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
        db.cypher_query(STARTUP_ODM_XML_EXTENSIONS)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def test_get_odm_xml(self):
        response = self.test_client.get(
            "concepts/odms/metadata/xmls?targetUid=odm_template1&targetType=template&exportTo=v1",
            headers={"content-type": "application/xml"},
        )

        expected_xml = ET.fromstring(
            """<?xml version="1.0" encoding="utf-8"?>
                <ODM xmlns:odm="http://www.cdisc.org/ns/odm/v1.3" xmlns:osb="namespace2" xmlns:prefix="namespace1" ODMVersion="1.3.2"
                FileType="Snapshot" FileOID="OID.1653902417076" CreationDateTime="2022-09-22T08:02:21.594676" Granularity="All">
                    <Study OID="name1-odm_template1">
                        <GlobalVariables>
                            <StudyName>name1</StudyName>
                            <StudyDescription>name1</StudyDescription>
                        </GlobalVariables>
                        <BasicDefinitions>
                            <MeasurementUnit OID="name1" Name="term_root1_uid">
                                <Symbol>
                                    <TranslatedText xml:lang="en" osb:version="0.1">name1</TranslatedText>
                                </Symbol>
                            </MeasurementUnit>
                        </BasicDefinitions>
                        <MetaDataVersion OID="MDV.0.1" Name="MDV.0.1" Description="Draft version">
                            <FormDef OID="oid1" Name="name1" Repeating="Yes" osb:version="1.0">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <ItemGroupRef CollectionExceptionConditionOID="oid2"
                                ItemGroupOID="oid1" Mandatory="Yes" osb:locked="No" OrderNumber="1" />
                            </FormDef>
                            <ItemGroupDef OID="oid1" Name="name1" Repeating="No" Purpose="purpose1" SASDatasetName="sas_dataset_name1"
                            Domain="code_submission_value1:preferred_term1|code_submission_value2:preferred_term2" osb:version="1.0">
                                <osb:DomainColor>code_submission_value1:#bfffff;</osb:DomainColor>
                                <osb:DomainColor>code_submission_value2:#ffff96;</osb:DomainColor>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <ItemRef CollectionExceptionConditionOID="oid1" ItemOID="oid1"
                                Mandatory="Yes" osb:sdv="No" osb:locked="No" OrderNumber="1" />
                           </ItemGroupDef>
                            <ItemDef OID="oid1" Name="name1" DataType="datatype1" Length="1" SASFieldName="sasfieldname1"
                            SDSVarName="sdsvarname1" Origin="origin1" osb:version="1.0">
                                <Question>
                                    <TranslatedText xml:lang="en" osb:version="1.0">name1</TranslatedText>
                                </Question>
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <Alias Name="name1" Context="context1" osb:version="0.1" />
                                <CodeListRef CodeListOID="submission_value1@oid1" />
                                <MeasurementUnitRef MeasurementUnitOID="name1" />
                            </ItemDef>
                            <ConditionDef Name="name1" OID="oid1" osb:version="1.0">
                                <Description>
                                    <TranslatedText xml:lang="en" osb:version="1.0">description1</TranslatedText>
                                </Description>
                                <FormalExpression Context="context1" osb:version="0.1">expression1</FormalExpression>
                            </ConditionDef>
                            <CodeList OID="submission_value1@oid1" Name="codelist_root1" DataType="string" SASFormatName="submission_value1">
                                <CodeListItem osb:OID="term1" CodedValue="code_submission_value1">
                                    <Decode>
                                        <TranslatedText xml:lang="en">preferred_term1</TranslatedText>
                                    </Decode>
                                </CodeListItem>
                                <CodeListItem OID="uid1" CodedValue="code_submission_value1">
                                    <Decode>
                                        <TranslatedText xml:lang="en">preferred_term1</TranslatedText>
                                    </Decode>
                                </CodeListItem>
                            </CodeList>
                        </MetaDataVersion>
                    </Study>
                </ODM>"""
        )
        actual_xml = ET.fromstring(response.content)

        namespaces = {"osb": "namespace2"}

        expected_xml.set("FileOID", actual_xml.get("FileOID"))
        expected_xml.set("CreationDateTime", actual_xml.get("CreationDateTime"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "application/xml")

        self.assertEqual(set(actual_xml.items()), set(expected_xml.items()))
        self.assertEqual(
            set(actual_xml.find("Study").items()),
            set(expected_xml.find("Study").items()),
        )
        self.assertEqual(
            set(actual_xml.find("Study").find("MetaDataVersion").items()),
            set(expected_xml.find("Study").find("MetaDataVersion").items()),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study").find("MetaDataVersion").find("FormDef").items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("FormDef")
            .find("Description")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("FormDef")
            .find("Description")
            .find("TranslatedText")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("Alias")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("Alias")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("ItemGroupRef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("FormDef")
                .find("ItemGroupRef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemGroupDef")
            .find("osb:DomainColor", namespaces)
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemGroupDef")
            .find("osb:DomainColor", namespaces)
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .find("Alias")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .find("Alias")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .find("ItemRef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemGroupDef")
                .find("ItemRef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study").find("MetaDataVersion").find("ItemDef").items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Question")
                .find("TranslatedText")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Question")
                .find("TranslatedText")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemDef")
            .find("Question")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemDef")
            .find("Question")
            .find("TranslatedText")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemDef")
            .find("Description")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("ItemDef")
            .find("Description")
            .find("TranslatedText")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Alias")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("Alias")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("CodeListRef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("CodeListRef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("MeasurementUnitRef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ItemDef")
                .find("MeasurementUnitRef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .find("Description")
                .find("TranslatedText")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("ConditionDef")
            .find("Description")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("ConditionDef")
            .find("Description")
            .find("TranslatedText")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .find("FormalExpression")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("ConditionDef")
                .find("FormalExpression")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("ConditionDef")
            .find("FormalExpression")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("ConditionDef")
            .find("FormalExpression")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .find("CodeListItem")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .find("CodeListItem")
                .items()
            ),
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .find("CodeListItem")
                .find("Decode")
                .find("TranslatedText")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("MetaDataVersion")
                .find("CodeList")
                .find("CodeListItem")
                .find("Decode")
                .find("TranslatedText")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("MetaDataVersion")
            .find("CodeList")
            .find("CodeListItem")
            .find("Decode")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("MetaDataVersion")
            .find("CodeList")
            .find("CodeListItem")
            .find("Decode")
            .find("TranslatedText")
            .text,
        )
        self.assertEqual(
            set(
                actual_xml.find("Study")
                .find("BasicDefinitions")
                .find("MeasurementUnit")
                .items()
            ),
            set(
                expected_xml.find("Study")
                .find("BasicDefinitions")
                .find("MeasurementUnit")
                .items()
            ),
        )
        self.assertEqual(
            actual_xml.find("Study")
            .find("BasicDefinitions")
            .find("MeasurementUnit")
            .find("Symbol")
            .find("TranslatedText")
            .text,
            expected_xml.find("Study")
            .find("BasicDefinitions")
            .find("MeasurementUnit")
            .find("Symbol")
            .find("TranslatedText")
            .text,
        )
