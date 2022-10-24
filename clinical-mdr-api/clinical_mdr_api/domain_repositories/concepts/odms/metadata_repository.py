from neomodel import db

from clinical_mdr_api.exceptions import NotFoundException


class MetadataRepository:
    CSV_EXPORT_QUERY = """
    CALL apoc.export.csv.query(query, null, {stream:true, params:{target_uid: $target_uid}})
    YIELD data, rows
    RETURN data, rows;"""

    OPTIONAL_FORM_MATCH = """
    OPTIONAL MATCH (OdmTemplateRoot)
    -[:FORM_REF]->(OdmFormRoot:OdmFormRoot)
    -[OdmFormLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmFormValue:OdmFormValue)
    """
    OPTIONAL_ITEM_GROUP_MATCH = """
    OPTIONAL MATCH (OdmFormRoot)
    -[:ITEM_GROUP_REF]->(OdmItemGroupRoot:OdmItemGroupRoot)
    -[OdmItemGroupLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmItemGroupValue:OdmItemGroupValue)
    """
    OPTIONAL_ITEM_MATCH = """
    OPTIONAL MATCH (OdmItemGroupRoot)
    -[:ITEM_REF]->(OdmItemRoot:OdmItemRoot)
    -[OdmItemLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmItemValue:OdmItemValue)
    """
    OPTIONAL_UNIT_DEFINITION_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_UNIT_DEFINITION]->(UnitDefinitionRoot:UnitDefinitionRoot)
    -[:LATEST]->(UnitDefinitionValue:UnitDefinitionValue)
    """
    OPTIONAL_CODELIST_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_CODELIST]->(CTCodelistRoot:CTCodelistRoot)
    -[:HAS_ATTRIBUTES_ROOT]->(CTCodelistAttributesRoot:CTCodelistAttributesRoot)
    -[:LATEST]->(CTCodelistAttributesValue:CTCodelistAttributesValue)
    """
    OPTIONAL_CODELIST_TERM_MATCH = """
    OPTIONAL MATCH (OdmItemRoot)
    -[:HAS_CODELIST_TERM]->(CTTermRoot:CTTermRoot)
    -[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot:CTTermAttributesRoot)
    -[:LATEST]->(CTTermAttributesValue:CTTermAttributesValue)
    """

    TEMPLATE_NAME_RETURN = "OdmTemplateValue.name AS Template_Name"
    TEMPLATE_VERSION_RETURN = "OdmTemplateLatest.version AS Template_Version"
    FORM_NAME_RETURN = "OdmFormValue.name AS Form_Name"
    FORM_REPEATING_RETURN = """
    (CASE WHEN OdmFormValue.repeating IS NULL THEN ''
    WHEN OdmFormValue.repeating THEN  'yes' ELSE 'no' END) AS Form_Repeating
    """
    FORM_VERSION_RETURN = "OdmFormLatest.version AS Form_Version"
    ITEM_GROUP_NAME_RETURN = "OdmItemGroupValue.name AS ItemGroup_Name"
    ITEM_GROUP_VERSION_RETURN = "OdmItemGroupLatest.version AS ItemGroup_Version"
    ITEM_NAME_RETURN = "OdmItemValue.name AS Item_Name"
    ITEM_DATATYPE_RETURN = "OdmItemValue.datatype AS Item_Datatype"
    ITEM_VERSION_RETURN = "OdmItemLatest.version AS Item_Version"
    ITEM_UNIT_RETURN = (
        "apoc.text.join(COLLECT(DISTINCT UnitDefinitionValue.name), '|') as Item_Units"
    )
    ITEM_CODELIST_RETURN = "CTCodelistAttributesValue.name AS Item_Codelist"
    ITEM_TERM_RETURN = "apoc.text.join(COLLECT(DISTINCT CTTermAttributesValue.code_submission_value), '|') as Item_Terms"

    def get_odm_template(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmTemplateRoot:OdmTemplateRoot {{uid: $target_uid}})
                    -[OdmTemplateLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmTemplateValue:OdmTemplateValue)
                    {self.OPTIONAL_FORM_MATCH}
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.TEMPLATE_NAME_RETURN},
                    {self.TEMPLATE_VERSION_RETURN},
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(
                f"ODM Template with uid {target_uid} does not exist."
            )

        return result[0][0]

    def get_odm_form(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmFormRoot:OdmFormRoot {{uid: $target_uid}})-[OdmFormLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmFormValue:OdmFormValue)
                    {self.OPTIONAL_ITEM_GROUP_MATCH}
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.FORM_NAME_RETURN},
                    {self.FORM_REPEATING_RETURN},
                    {self.FORM_VERSION_RETURN},
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(f"ODM Form with uid {target_uid} does not exist.")

        return result[0][0]

    def get_odm_item_group(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmItemGroupRoot:OdmItemGroupRoot {{uid: $target_uid}})
                    -[OdmItemGroupLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmItemGroupValue:OdmItemGroupValue)
                    {self.OPTIONAL_ITEM_MATCH}
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.ITEM_GROUP_NAME_RETURN},
                    {self.ITEM_GROUP_VERSION_RETURN},
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(
                f"ODM Item Group with uid {target_uid} does not exist."
            )

        return result[0][0]

    def get_odm_item(self, target_uid: str):
        query = (
            f"""
                WITH "
                    MATCH (OdmItemRoot:OdmItemRoot {{uid: $target_uid}})-[OdmItemLatest:LATEST_FINAL|LATEST_RETIRED]->(OdmItemValue:OdmItemValue)
                    {self.OPTIONAL_UNIT_DEFINITION_MATCH}
                    {self.OPTIONAL_CODELIST_MATCH}
                    {self.OPTIONAL_CODELIST_TERM_MATCH}

                    RETURN
                    {self.ITEM_NAME_RETURN},
                    {self.ITEM_DATATYPE_RETURN},
                    {self.ITEM_VERSION_RETURN},
                    {self.ITEM_UNIT_RETURN},
                    {self.ITEM_CODELIST_RETURN},
                    {self.ITEM_TERM_RETURN}
                " AS query
            """
            + self.CSV_EXPORT_QUERY
        )
        result, _ = db.cypher_query(query, {"target_uid": target_uid})

        if result[0][1] == 0:
            raise NotFoundException(f"ODM Item with uid {target_uid} does not exist.")

        return result[0][0]
