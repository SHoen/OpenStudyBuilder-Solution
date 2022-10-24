import csv
from typing import Dict, List

from fastapi import FastAPI
from fastapi.routing import APIRoute
from neomodel.core import db

# Helpers
from starlette.routing import Mount

from clinical_mdr_api.config import (
    DEFAULT_STUDY_FIELD_CONFIG_FILE,
    STUDY_ENDPOINT_TP_NAME,
)

# Models
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
    Library,
)
from clinical_mdr_api.models.configuration import CTConfigPostInput
from clinical_mdr_api.models.study import Study
from clinical_mdr_api.models.utils import camel_case_data
from clinical_mdr_api.services._meta_repository import MetaRepository

# Services/repositories
from clinical_mdr_api.services.configuration import CTConfigService
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

library_data = {"name": "Test library", "is_editable": True}

template_data = {
    "name": "Test_Name_Template",
    "library": library_data,
    "libraryName": "Test library",
    "editableInstance": True,
}

criteria_template_data = template_data
criteria_template_data["typeUid"] = "C25532"

DATA_MAP = {"objective-templates": template_data, "libraries": library_data}

STARTUP_ODM_CONDITIONS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1", sponsor_instruction: "sponsorInstruction1"})
MERGE (odm_description_root1)-[ld:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l:LATEST]->(odm_description_value1)
SET ld = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_condition_root1:ConceptRoot:OdmConditionRoot {uid: "odm_condition1"})
MERGE (odm_condition_value1:ConceptValue:OdmConditionValue {oid: "oid1", name: "name1"})
MERGE (odm_condition_root1)-[ld1:LATEST_FINAL]->(odm_condition_value1)
MERGE (odm_condition_root1)-[l1:LATEST]->(odm_condition_value1)
SET ld1 = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_condition_root2:ConceptRoot:OdmConditionRoot {uid: "odm_condition2"})
MERGE (odm_condition_value2:ConceptValue:OdmConditionValue {oid: "oid2", name: "name2"})
MERGE (odm_condition_root2)-[ld2:LATEST_FINAL]->(odm_condition_value2)
MERGE (odm_condition_root2)-[l2:LATEST]->(odm_condition_value2)
SET ld2 = final_properties

MERGE (odm_condition_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
MERGE (odm_condition_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)

"""

STARTUP_ODM_FORMAL_EXPRESSIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root1:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression1"})
MERGE (odm_formal_expression_value1:ConceptValue:OdmFormalExpressionValue {context: "context1", expression: "expression1"})
MERGE (odm_formal_expression_root1)-[ld1:LATEST_DRAFT]->(odm_formal_expression_value1)
MERGE (odm_formal_expression_root1)-[l1:LATEST]->(odm_formal_expression_value1)
SET ld1 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root2:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression2"})
MERGE (odm_formal_expression_value2:ConceptValue:OdmFormalExpressionValue {context: "context2", expression: "expression2"})
MERGE (odm_formal_expression_root2)-[ld2:LATEST_DRAFT]->(odm_formal_expression_value2)
MERGE (odm_formal_expression_root2)-[l2:LATEST]->(odm_formal_expression_value2)
SET ld2 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_formal_expression_root3:ConceptRoot:OdmFormalExpressionRoot {uid: "odm_formal_expression3"})
MERGE (odm_formal_expression_value3:ConceptValue:OdmFormalExpressionValue {context: "context1", expression: "expression1"})
MERGE (odm_formal_expression_root3)-[ld3:LATEST_DRAFT]->(odm_formal_expression_value3)
MERGE (odm_formal_expression_root3)-[l3:LATEST]->(odm_formal_expression_value3)
SET ld3 = draft_properties
"""

STARTUP_ODM_DESCRIPTIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1", sponsor_instruction: "sponsorInstruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_DRAFT]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
SET ld1 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root2:ConceptRoot:OdmDescriptionRoot {uid: "odm_description2"})
MERGE (odm_description_value2:ConceptValue:OdmDescriptionValue {name: "name2", language: "language2", description: "description2", instruction: "instruction2", sponsor_instruction: "sponsorInstruction2"})
MERGE (odm_description_root2)-[ld2:LATEST_DRAFT]->(odm_description_value2)
MERGE (odm_description_root2)-[l2:LATEST]->(odm_description_value2)
SET ld2 = draft_properties
"""

STARTUP_ODM_ALIASES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_alias_root1:ConceptRoot:OdmAliasRoot {uid: "odm_alias1"})
MERGE (odm_alias_value1:ConceptValue:OdmAliasValue {context: "context1", name: "name1"})
MERGE (odm_alias_root1)-[ld1:LATEST_DRAFT]->(odm_alias_value1)
MERGE (odm_alias_root1)-[l1:LATEST]->(odm_alias_value1)
SET ld1 = draft_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_alias_root2:ConceptRoot:OdmAliasRoot {uid: "odm_alias2"})
MERGE (odm_alias_value2:ConceptValue:OdmAliasValue {context: "context2", name: "name2"})
MERGE (odm_alias_root2)-[ld2:LATEST_DRAFT]->(odm_alias_value2)
MERGE (odm_alias_root2)-[l2:LATEST]->(odm_alias_value1)
SET ld2 = draft_properties
"""

STARTUP_CT_TERM_WITHOUT_CATALOGUE = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_TERM]->(TermRoot:CTTermRoot {concept_id: "concept_id1", uid: "term1"})
MERGE (TermRoot)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot:CTTermAttributesRoot)
MERGE (TermAttrValue:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot)-[lf1:LATEST_FINAL]->(TermAttrValue)
MERGE (TermAttrRoot)-[:LATEST]->(TermAttrValue)

MERGE (TermRoot)-[:HAS_NAME_ROOT]->(TermNameRoot:CTTermNameRoot)
MERGE (TermNameValue:CTTermNameValue {name: "name1", name_sentence_case: "name_sentence_case1"})
MERGE (TermNameRoot)-[lf2:LATEST_FINAL]->(TermNameValue)
MERGE (TermNameRoot)-[:LATEST]->(TermNameValue)
SET lf1 = final_properties
SET lf2 = final_properties
"""

STARTUP_CT_TERM = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_CATALOGUE]->(Catalogue:CTCatalogue {name:"SDTM CT"})
MERGE (Library)-[:CONTAINS_CODELIST]->(CodelistRoot:CTCodelistRoot {uid: "codelist_root1"})
MERGE (Catalogue)-[:HAS_CODELIST]->(CodelistRoot)
MERGE (Library)-[:CONTAINS_TERM]->(TermRoot1:CTTermRoot {concept_id: "concept_id1", uid: "term1"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot1)
MERGE (TermRoot1)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot1:CTTermAttributesRoot)
MERGE (TermAttrValue1:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot1)-[lf1:LATEST_FINAL]->(TermAttrValue1)
MERGE (TermAttrRoot1)-[:LATEST]->(TermAttrValue1)
SET lf1 = final_properties

MERGE (TermRoot1)-[:HAS_NAME_ROOT]->(TermNameRoot1:CTTermNameRoot)
MERGE (TermNameRoot1)-[:LATEST]->(TermNameValue1:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (TermNameRoot1)-[lf2:LATEST_FINAL]->(TermNameValue1)
SET lf2 = final_properties

MERGE (Library)-[:CONTAINS_TERM]->(TermRoot2:CTTermRoot {concept_id: "concept_id2", uid: "term2"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot2)
MERGE (TermRoot2)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot2:CTTermAttributesRoot)
MERGE (TermAttrValue2:CTTermAttributesValue {code_submission_value: "code_submission_value2", concept_id: "concept_id2", definition: "definition2", preferred_term: "preferred_term2", synonyms: "synonyms2"})
MERGE (TermAttrRoot2)-[lf3:LATEST_FINAL]->(TermAttrValue2)
MERGE (TermAttrRoot2)-[:LATEST]->(TermAttrValue2)
SET lf3 = final_properties

MERGE (TermRoot2)-[:HAS_NAME_ROOT]->(TermNameRoot2:CTTermNameRoot)
MERGE (TermNameRoot2)-[:LATEST]->(TermNameValue2:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (TermNameRoot2)-[lf4:LATEST_FINAL]->(TermNameValue2)
SET lf4 = final_properties
"""

STARTUP_UNIT_DEFINITIONS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties,
{
start_date: datetime(),
user_initials: "Dictionary Codelist Test"
} AS has_term_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit_definition_root1"})
MERGE (unit_def_value:ConceptValue:UnitDefinitionValue { name:"name1", unit_ct_uid: "unit1-ct-uid", convertible_unit: true, display_unit: true, master_unit: true, si_unit: true, us_conventional_unit: true, unit_dimension_uid: "unit1-dimension", legacy_code: "unit1-legacy-code", molecular_weight_conv_expon: 0, conversion_factor_to_master: 1.0 })
MERGE (unit_def_root)-[ld1:LATEST_DRAFT]-(unit_def_value)
MERGE (unit_def_root)-[l1:LATEST]->(unit_def_value)
SET ld1 = draft_properties

MERGE (codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1)
MERGE (codelist_value1:DictionaryCodelistValue {name:"name1"})
MERGE (codelist_root1)-[lf1:LATEST_FINAL]->(codelist_value1)
MERGE (codelist_root1)-[l2:LATEST]->(codelist_value1)
SET lf1 = final_properties

MERGE (codelist_root1)-[has_term1:HAS_TERM]->(term_root1:DictionaryTermRoot:UCUMTermRoot {uid:"term_root1_uid"})
-[:LATEST]->(term_value1:DictionaryTermValue:UCUMTermValue {
name:"name1", dictionary_id:"dictionary_id1", name_sentence_case:"Name1", abbreviation:"abbreviation1", definition:"definition1"})

MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root1)
MERGE (term_root1)-[lf2:LATEST_FINAL]->(term_value1)
SET lf2 = final_properties
SET has_term1 = has_term_properties
MERGE (unit_def_value)-[hut1:HAS_UCUM_TERM]->(term_root1)

MERGE (library)-[:CONTAINS_TERM]->(cttr:CTTermRoot {uid: "C25532_name1", concept_id: "C25532"})
MERGE (cttr)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)
MERGE (unit_def_value)-[hcu1:HAS_CT_UNIT]->(cttr)
MERGE (cttnr)-[:LATEST]->(cttnv:CTTermNameValue {name: "name1", name_sentence_case: "name1"})
MERGE (cttnr)-[latest_final1:LATEST_FINAL]->(cttnv)
MERGE (cttnr)-[has_version1:HAS_VERSION]->(cttnv)
SET latest_final1 = final_properties
SET has_version1 = final_properties
"""

STARTUP_ODM_ITEM_GROUPS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
SET ld1 = final_properties

MERGE (item_group_root1:ConceptRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MERGE (item_group_value1:ConceptValue:OdmItemGroupValue {oid: "oid1", name: "name1", repeating: false, is_reference_data: "is_reference_data1", sas_dataset_name: "sas_dataset_name1", origin: "origin1", purpose: "purpose1", comment: "comment1"})
MERGE (library)-[r0:CONTAINS_CONCEPT]->(item_group_root1)
MERGE (item_group_root1)-[r1:LATEST_FINAL]->(item_group_value1)
MERGE (item_group_root1)-[:LATEST]->(item_group_value1)
MERGE (item_group_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r1 = final_properties

MERGE (item_group_root2:ConceptRoot:OdmItemGroupRoot {uid: "odm_item_group2"})
MERGE (item_group_value2:ConceptValue:OdmItemGroupValue {oid: "oid2", name: "name2", repeating: false, is_reference_data: "is_reference_data2", sas_dataset_name: "sas_dataset_name2", origin: "origin2", purpose: "purpose2", comment: "comment2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_group_root2)
MERGE (item_group_root2)-[r2:LATEST_FINAL]->(item_group_value2)
MERGE (item_group_root2)-[:LATEST]->(item_group_value2)
MERGE (item_group_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r2 = final_properties

WITH *
MATCH (ct_term_root1:CTTermRoot {uid: "term1"})
MATCH (ct_term_root2:CTTermRoot {uid: "term2"})
MERGE (item_group_root1)-[:HAS_SDTM_DOMAIN]->(ct_term_root1)
MERGE (item_group_root1)-[:HAS_SDTM_DOMAIN]->(ct_term_root2)
MERGE (item_group_root2)-[:HAS_SDTM_DOMAIN]->(ct_term_root1)
"""

STARTUP_ODM_ITEMS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
SET ld1 = final_properties

MERGE (item_root1:ConceptRoot:OdmItemRoot {uid: "odm_item1"})
MERGE (item_value1:ConceptValue:OdmItemValue {oid: "oid1", name: "name1", datatype: "datatype1", length: 1, significant_digits: 1, sas_field_name: "sasfieldname1", sds_var_name: "sdsvarname1", origin: "origin1", comment: "comment1"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_root1)
MERGE (item_root1)-[r1:LATEST_FINAL]->(item_value1)
MERGE (item_root1)-[:LATEST]->(item_value1)
MERGE (item_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r1 = final_properties

MERGE (item_root2:ConceptRoot:OdmItemRoot {uid: "odm_item2"})
MERGE (item_value2:ConceptValue:OdmItemValue {oid: "oid2", name: "name2", datatype: "datatype2", length: 2, significant_digits: 2, sas_field_name: "sasfieldname2", sds_var_name: "sdsvarname2", origin: "origin2", comment: "comment2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(item_root2)
MERGE (item_root2)-[r2:LATEST_FINAL]->(item_value2)
MERGE (item_root2)-[:LATEST]->(item_value2)
MERGE (item_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r2 = final_properties
"""

STARTUP_ODM_FORMS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (library)-[:CONTAINS_CONCEPT]->(odm_description_root1:ConceptRoot:OdmDescriptionRoot {uid: "odm_description1"})
MERGE (odm_description_value1:ConceptValue:OdmDescriptionValue {name: "name1", language: "ENG", description: "description1", instruction: "instruction1"})
MERGE (odm_description_root1)-[ld1:LATEST_FINAL]->(odm_description_value1)
MERGE (odm_description_root1)-[l1:LATEST]->(odm_description_value1)
SET ld1 = final_properties

MERGE (odm_form_root1:ConceptRoot:OdmFormRoot {uid: "odm_form1"})
MERGE (odm_form_value1:ConceptValue:OdmFormValue {oid: "oid1", name: "name1", repeating: true})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_form_root1)
MERGE (odm_form_root1)-[r1:LATEST_FINAL]->(odm_form_value1)
MERGE (odm_form_root1)-[:LATEST]->(odm_form_value1)
MERGE (odm_form_root1)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r1 = final_properties

MERGE (odm_form_root2:ConceptRoot:OdmFormRoot {uid: "odm_form2"})
MERGE (odm_form_value2:ConceptValue:OdmFormValue {oid: "oid2", name: "name2", repeating: true})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_form_root2)
MERGE (odm_form_root2)-[r2:LATEST_FINAL]->(odm_form_value2)
MERGE (odm_form_root2)-[:LATEST]->(odm_form_value2)
MERGE (odm_form_root2)-[:HAS_DESCRIPTION]->(odm_description_root1)
SET r2 = final_properties
"""

STARTUP_ODM_TEMPLATES = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (TemplateRoot:ConceptRoot:OdmTemplateRoot {uid: "odm_template1"})
MERGE (TemplateValue:ConceptValue:OdmTemplateValue {oid: "oid1", name: "name1", effective_date: date(), retired_date: date(), description: "description"})
MERGE (library)-[:CONTAINS_CONCEPT]->(TemplateRoot)
MERGE (TemplateRoot)-[r1:LATEST_FINAL]->(TemplateValue)
MERGE (TemplateRoot)-[r2:LATEST]->(TemplateValue)
SET r1 = final_properties
"""

STARTUP_ODM_XML_EXPORTER = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (Library:Library {name:"Sponsor", is_editable:true})
MERGE (Library)-[:CONTAINS_CATALOUGE]->(Catalogue:CTCatalogue {name:"SDTM CT"})

WITH *
MATCH (oa:OdmAliasRoot {uid: "odm_alias1"})
MATCH (ofr:OdmFormRoot {uid: "odm_form1"})
MATCH (oigr:OdmItemGroupRoot {uid: "odm_item_group1"})
MATCH (oir:OdmItemRoot {uid: "odm_item1"})
MERGE (ofr)-[:HAS_ALIAS]->(oa)
MERGE (oigr)-[:HAS_ALIAS]->(oa)
MERGE (oir)-[:HAS_ALIAS]->(oa)

WITH *
MATCH (ItemRoot:OdmItemRoot {uid: "odm_item1"})
MATCH (UnitRoot:UnitDefinitionRoot {uid: "unit_definition_root1"})
MERGE (ItemRoot)-[:HAS_UNIT_DEFINITION]->(UnitRoot)

MERGE (CodelistRoot:CTCodelistRoot {uid: "codelist_root1"})
MERGE (Library)-[:CONTAINS_CODELIST]->(CodelistRoot)
MERGE (Catalogue)-[:HAS_CODELIST]->(CodelistRoot)
MERGE (ItemRoot)-[:HAS_CODELIST]->(CodelistRoot)

WITH *
MATCH (CTTerm:CTTermRoot {uid: "term1"})
MERGE (ItemRoot)-[:HAS_CODELIST_TERM]->(CTTerm)

MERGE (CodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(CodelistAttrRoot:CTCodelistAttributesRoot)
MERGE (CodelistAttrValue:CTCodelistAttributesValue {name:"name1", definition:"definition1", preferred_term: "preferred_term1", synonyms: "synonyms1", submission_value: "submission_value1", extensible:false})
MERGE (CodelistAttrRoot)-[lf1:LATEST_FINAL]->(CodelistAttrValue)
MERGE (CodelistAttrRoot)-[:LATEST]->(CodelistAttrValue)
SET lf1 = final_properties

MERGE (Library)-[:CONTAINS_TERM]->(TermRoot:CTTermRoot {concept_id: "concept_id1", uid: "uid1"})
MERGE (CodelistRoot)-[:HAS_TERM]->(TermRoot)
MERGE (TermRoot)-[:HAS_ATTRIBUTES_ROOT]->(TermAttrRoot:CTTermAttributesRoot)
MERGE (TermAttrValue:CTTermAttributesValue {code_submission_value: "code_submission_value1", concept_id: "concept_id1", definition: "definition1", preferred_term: "preferred_term1", synonyms: "synonyms1"})
MERGE (TermAttrRoot)-[lf2:LATEST_FINAL]->(TermAttrValue)
MERGE (TermAttrRoot)-[:LATEST]->(TermAttrValue)
SET lf2 = final_properties

WITH *
MATCH (ConditionRoot1:OdmConditionRoot {uid: "odm_condition1"})
MATCH (ConditionRoot2:OdmConditionRoot {uid: "odm_condition2"})
MATCH (FormalExpression:OdmFormalExpressionRoot {uid: "odm_formal_expression1"})
MERGE (ConditionRoot1)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)
MERGE (ConditionRoot2)-[:HAS_FORMAL_EXPRESSION]->(FormalExpression)

WITH *
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MATCH (ItemRoot:OdmItemRoot {uid: "odm_item1"})
MERGE (ItemGroupRoot)-[:ITEM_REF {order_number: "1", mandatory: true, sdv: false, locked: false, collection_exception_condition_oid: "oid1", method_oid: "oid1"}]->(ItemRoot)

WITH *
MATCH (FormRoot:OdmFormRoot {uid: "odm_form1"})
MATCH (ItemGroupRoot:OdmItemGroupRoot {uid: "odm_item_group1"})
MERGE (FormRoot)-[:ITEM_GROUP_REF {order_number: "1", mandatory: true, locked: false, collection_exception_condition_oid: "oid2", method_oid: "oid2"}]->(ItemGroupRoot)

WITH *
MATCH (TemplateRoot:OdmTemplateRoot {uid: "odm_template1"})
MATCH (FormRoot:OdmFormRoot {uid: "odm_form1"})
MERGE (TemplateRoot)-[:FORM_REF {order_number: "1", mandatory: true, locked: false, collection_exception_condition_oid: "oid1"}]->(FormRoot)
"""

STARTUP_ODM_XML_EXTENSIONS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

MERGE (odm_xml_extension_root1:ConceptRoot:OdmXmlExtensionRoot {uid: "odm_xml_extension1"})
MERGE (odm_xml_extension_value1:ConceptValue:OdmXmlExtensionValue {name: "nameOne", prefix: "prefix", namespace: "namespace1"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_root1)
MERGE (odm_xml_extension_root1)-[r1:LATEST_FINAL]->(odm_xml_extension_value1)
MERGE (odm_xml_extension_root1)-[:LATEST]->(odm_xml_extension_value1)
SET r1 = final_properties

MERGE (odm_xml_extension_root2:ConceptRoot:OdmXmlExtensionRoot {uid: "odm_xml_extension2"})
MERGE (odm_xml_extension_value2:ConceptValue:OdmXmlExtensionValue {name: "OSB", prefix: "osb", namespace: "namespace2"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_root2)
MERGE (odm_xml_extension_root2)-[r2:LATEST_FINAL]->(odm_xml_extension_value2)
MERGE (odm_xml_extension_root2)-[:LATEST]->(odm_xml_extension_value2)
SET r2 = final_properties
"""

STARTUP_ODM_XML_EXTENSION_TAGS = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

WITH *
MATCH (odm_xml_extension_root:ConceptRoot:OdmXmlExtensionRoot {uid: "odm_xml_extension1"})

MERGE (odm_xml_extension_tag_root1:ConceptRoot:OdmXmlExtensionTagRoot {uid: "odm_xml_extension_tag1"})
MERGE (odm_xml_extension_tag_value1:ConceptValue:OdmXmlExtensionTagValue {name: "nameOne"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_tag_root1)
MERGE (odm_xml_extension_tag_root1)-[r1:LATEST_FINAL]->(odm_xml_extension_tag_value1)
MERGE (odm_xml_extension_tag_root1)-[:LATEST]->(odm_xml_extension_tag_value1)
MERGE (odm_xml_extension_root)-[:HAS_XML_EXTENSION_TAG]->(odm_xml_extension_tag_root1)
SET r1 = final_properties

MERGE (odm_xml_extension_tag_root2:ConceptRoot:OdmXmlExtensionTagRoot {uid: "odm_xml_extension_tag2"})
MERGE (odm_xml_extension_tag_value2:ConceptValue:OdmXmlExtensionTagValue {name: "nameTwo"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_tag_root2)
MERGE (odm_xml_extension_tag_root2)-[r2:LATEST_FINAL]->(odm_xml_extension_tag_value2)
MERGE (odm_xml_extension_tag_root2)-[:LATEST]->(odm_xml_extension_tag_value2)
MERGE (odm_xml_extension_root)-[:HAS_XML_EXTENSION_TAG]->(odm_xml_extension_tag_root2)
SET r2 = final_properties
"""

STARTUP_ODM_XML_EXTENSION_ATTRIBUTES = """
WITH  {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})

WITH *
MATCH (odm_xml_extension_root:ConceptRoot:OdmXmlExtensionRoot {uid: "odm_xml_extension1"})
MATCH (odm_xml_extension_tag_root:OdmXmlExtensionTagRoot {uid:"odm_xml_extension_tag1"})

MERGE (odm_xml_extension_attribute_root1:ConceptRoot:OdmXmlExtensionAttributeRoot {uid: "odm_xml_extension_attribute1"})
MERGE (odm_xml_extension_attribute_value1:ConceptValue:OdmXmlExtensionAttributeValue {name: "nameOne"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_attribute_root1)
MERGE (odm_xml_extension_attribute_root1)-[r1:LATEST_FINAL]->(odm_xml_extension_attribute_value1)
MERGE (odm_xml_extension_attribute_root1)-[:LATEST]->(odm_xml_extension_attribute_value1)
MERGE (odm_xml_extension_tag_root)-[:HAS_XML_EXTENSION_ATTRIBUTE {value: "value1"}]->(odm_xml_extension_attribute_root1)
SET r1 = final_properties

MERGE (odm_xml_extension_attribute_root2:ConceptRoot:OdmXmlExtensionAttributeRoot {uid: "odm_xml_extension_attribute2"})
MERGE (odm_xml_extension_attribute_value2:ConceptValue:OdmXmlExtensionAttributeValue {name: "nameTwo"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_attribute_root2)
MERGE (odm_xml_extension_attribute_root2)-[r2:LATEST_FINAL]->(odm_xml_extension_attribute_value2)
MERGE (odm_xml_extension_attribute_root2)-[:LATEST]->(odm_xml_extension_attribute_value2)
MERGE (odm_xml_extension_tag_root)-[:HAS_XML_EXTENSION_ATTRIBUTE {value: "value2"}]->(odm_xml_extension_attribute_root2)
SET r2 = final_properties

MERGE (odm_xml_extension_attribute_root3:ConceptRoot:OdmXmlExtensionAttributeRoot {uid: "odm_xml_extension_attribute3"})
MERGE (odm_xml_extension_attribute_value3:ConceptValue:OdmXmlExtensionAttributeValue {name: "nameThree"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_attribute_root3)
MERGE (odm_xml_extension_attribute_root3)-[r4:LATEST_FINAL]->(odm_xml_extension_attribute_value3)
MERGE (odm_xml_extension_attribute_root3)-[:LATEST]->(odm_xml_extension_attribute_value3)
MERGE (odm_xml_extension_root)-[:HAS_XML_EXTENSION_ATTRIBUTE {value: "value3"}]->(odm_xml_extension_attribute_root3)
SET r4 = final_properties

MERGE (odm_xml_extension_attribute_root4:ConceptRoot:OdmXmlExtensionAttributeRoot {uid: "odm_xml_extension_attribute4"})
MERGE (odm_xml_extension_attribute_value4:ConceptValue:OdmXmlExtensionAttributeValue {name: "nameFour"})
MERGE (library)-[:CONTAINS_CONCEPT]->(odm_xml_extension_attribute_root4)
MERGE (odm_xml_extension_attribute_root4)-[r5:LATEST_FINAL]->(odm_xml_extension_attribute_value4)
MERGE (odm_xml_extension_attribute_root4)-[:LATEST]->(odm_xml_extension_attribute_value4)
MERGE (odm_xml_extension_root)-[:HAS_XML_EXTENSION_ATTRIBUTE {value: "value4"}]->(odm_xml_extension_attribute_root4)
SET r5 = final_properties
"""

STARTUP_CRITERIA = """
WITH
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
// Create codelist
MERGE (cdisc:Library {name:"CDISC", is_editable: True})
MERGE (catalogue:CTCatalogue {name:"SDTM CT"})
MERGE (cdisc)-[:CONTAINS_CATALOGUE]->(catalogue)
MERGE (cdisc)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (catalogue)-[:HAS_CODELIST]-(codelist_root)
// Create Inclusion criteria term
CREATE (cdisc)-[:CONTAINS_TERM]->(incr:CTTermRoot {uid: "C25532"})-[:HAS_NAME_ROOT]->
(incnr:CTTermNameRoot)-[:LATEST]->(incnv:CTTermNameValue {
name: "INCLUSION CRITERIA",
name_sentence_case: "Inclusion Criteria"})
MERGE (incnr)-[incnrel:LATEST_FINAL]->(incnv)
SET incnrel = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(incr)
CREATE (incar:CTTermAttributesRoot)-[:LATEST]->(incav:CTTermAttributesValue {
code_submission_value: "Inclusion Criteria",
definition: "Inclusion Criteria",
preferred_term: "Inclusion Criteria"})
MERGE (incr)-[:HAS_ATTRIBUTES_ROOT]->(incar)-[incarel:LATEST_FINAL]->(incav)
SET incarel = final_properties
// Create Exclusion criteria term
CREATE (cdisc)-[:CONTAINS_TERM]->(excr:CTTermRoot {uid: "C25370"})-[:HAS_NAME_ROOT]->
(excnr:CTTermNameRoot)-[:LATEST]->(excnv:CTTermNameValue {
name: "EXCLUSION CRITERIA",
name_sentence_case: "Exclusion Criteria"})
MERGE (excnr)-[excnrel:LATEST_FINAL]->(excnv)
SET excnrel = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(excr)
CREATE (excar:CTTermAttributesRoot)-[:LATEST]->(excav:CTTermAttributesValue {
code_submission_value: "Exclusion Criteria",
definition: "Exclusion Criteria",
preferred_term: "Exclusion Criteria"})
MERGE (excr)-[:HAS_ATTRIBUTES_ROOT]->(excar)-[excarel:LATEST_FINAL]->(excav)
SET excarel = final_properties
"""

STARTUP_TIME_POINTS = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MATCH (lib {name:"Sponsor"})
MERGE (lib)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"UnitDefinition_000001"})-[:LATEST]-
(unit_def_value:ConceptValue:UnitDefinitionValue {
name:"name_1",
unit_ct_uid: "unit1-ct-uid",
convertible_unit: true,
display_unit: true,
master_unit: true,
si_unit: true,
us_conventional_unit: true,
unit_dimension_uid: "unit1-dimension",
legacy_code: "unit1-legacy-code",
molecular_weight_conv_expon: 0,
conversion_factor_to_master: 1.0
})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties
MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root:ConceptRoot:SimpleConceptRoot:NumericValueRoot {uid:"NumericValue_000001"})-[:LATEST]-(numeric_value_value:ConceptValue:SimpleConceptValue:NumericValue {
name:"1.23",
value:1.23})
MERGE (numeric_value_root)-[numeric_value_final1:LATEST_FINAL]-(numeric_value_value)
SET numeric_value_final1 = final_properties
MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root2:ConceptRoot:SimpleConceptRoot:NumericValueRoot {uid:"NumericValue_000002"})-[:LATEST]-(numeric_value_value2:ConceptValue:SimpleConceptValue:NumericValue {
name:"3.21",
value:3.21})
MERGE (numeric_value_root2)-[numeric_value_final2:LATEST_FINAL]-(numeric_value_value2)
SET numeric_value_final2 = final_properties
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"CTCodelistRoot_000001"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue {name:"codelist_name"})
CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
MERGE (editable_lib:Library{ name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr)-[has_term:HAS_TERM]->(term_root:CTTermRoot {uid:"CTTermRoot_000001"})-[:HAS_NAME_ROOT]->
    (term_ver_root:CTTermNameRoot)-[:LATEST]-(term_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
set has_term.order = 1
set lf.change_description = "Approved version"
set lf.start_date = datetime()
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"
"""

STARTUP_NUMERIC_VALUES_WITH_UNITS = """
MERGE (lib:Library{name:"Sponsor", is_editable:true})

WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MATCH (lib {name:"Sponsor"})
MERGE (lib)-[:CONTAINS_CONCEPT]->(unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"UnitDefinition_000001"})-[:LATEST]-
(unit_def_value:ConceptValue:UnitDefinitionValue {
name:"name_1",
unit_ct_uid: "unit1-ct-uid",
convertible_unit: true,
display_unit: true,
master_unit: true,
si_unit: true,
us_conventional_unit: true,
unit_dimension_uid: "unit1-dimension",
legacy_code: "unit1-legacy-code",
molecular_weight_conv_expon: 0,
conversion_factor_to_master: 1.0
})

MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties

MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root:ConceptRoot:SimpleConceptRoot:NumericValueRoot:NumericValueWithUnitRoot {uid:"NumericValueWithUnit_000001"})-[:LATEST]-(numeric_value_value:ConceptValue:SimpleConceptValue:NumericValue:NumericValueWithUnitValue {
name:"1.23 [UnitDefinition_000001]",
value:1.23})
MERGE (numeric_value_root)-[numeric_value_final1:LATEST_FINAL]-(numeric_value_value)
MERGE (numeric_value_value)-[:HAS_UNIT_DEFINITION]->(unit_def_root)
SET numeric_value_final1 = final_properties

MERGE (lib)-[:CONTAINS_CONCEPT]->(numeric_value_root2:ConceptRoot:SimpleConceptRoot:NumericValueRoot:NumericValueWithUnitRoot {uid:"NumericValueWithUnit_000002"})-[:LATEST]-(numeric_value_value2:ConceptValue:SimpleConceptValue:NumericValue:NumericValueWithUnitValue {
name:"3.21 [UnitDefinition_000001]",
value:3.21})
MERGE (numeric_value_root2)-[numeric_value_final2:LATEST_FINAL]-(numeric_value_value2)
MERGE (numeric_value_value2)-[:HAS_UNIT_DEFINITION]->(unit_def_root)
SET numeric_value_final2 = final_properties

"""

STARTUP_ACTIVITY_INSTANCES_CT_INIT = """
WITH
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"CDISC", is_editable: false})
MERGE (catalogue:CTCatalogue {name:"SDTM"})
MERGE (library)-[:CONTAINS_CATALOGUE]->(catalogue)
MERGE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (catalogue)-[:HAS_CODELIST]-(codelist_root)
CREATE (library)-[:CONTAINS_TERM]->(sdtm_variable1:CTTermRoot {uid: "sdtm_variable_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root1:CTTermNameRoot)-[:LATEST]->(term_ver_value1:CTTermNameValue {
name: "sdtm_variable_name1",
name_sentence_case: "sdtm_variable_name1"})
MERGE (term_ver_root1)-[latest_final1:LATEST_FINAL]->(term_ver_value1)
SET latest_final1 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_variable1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_subcat1:CTTermRoot {uid: "sdtm_subcat_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root2:CTTermNameRoot)-[:LATEST]->(term_ver_value2:CTTermNameValue {
name: "sdtm_subcat_name1",
name_sentence_case: "sdtm_subcat_name1"})
MERGE (term_ver_root2)-[latest_final2:LATEST_FINAL]->(term_ver_value2)
SET latest_final2 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_subcat1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_cat1:CTTermRoot {uid: "sdtm_cat_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root3:CTTermNameRoot)-[:LATEST]->(term_ver_value3:CTTermNameValue {
name: "sdtm_cat_name1",
name_sentence_case: "sdtm_cat_name1"})
MERGE (term_ver_root3)-[latest_final3:LATEST_FINAL]->(term_ver_value3)
SET latest_final3 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_cat1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_domain1:CTTermRoot {uid: "sdtm_domain_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root4:CTTermNameRoot)-[:LATEST]->(term_ver_value4:CTTermNameValue {
name: "sdtm_domain_name1",
name_sentence_case: "sdtm_domain_name1"})
MERGE (term_ver_root4)-[latest_final4:LATEST_FINAL]->(term_ver_value4)
SET latest_final4 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_domain1)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_variable2:CTTermRoot {uid: "sdtm_variable_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root5:CTTermNameRoot)-[:LATEST]->(term_ver_value5:CTTermNameValue {
name: "sdtm_variable_name2",
name_sentence_case: "sdtm_variable_name2"})
MERGE (term_ver_root5)-[latest_final5:LATEST_FINAL]->(term_ver_value5)
SET latest_final5 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_variable2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_subcat2:CTTermRoot {uid: "sdtm_subcat_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root6:CTTermNameRoot)-[:LATEST]->(term_ver_value6:CTTermNameValue {
name: "sdtm_subcat_name2",
name_sentence_case: "sdtm_subcat_name2"})
MERGE (term_ver_root6)-[latest_final6:LATEST_FINAL]->(term_ver_value6)
SET latest_final6 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_subcat2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_cat2:CTTermRoot {uid: "sdtm_cat_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root7:CTTermNameRoot)-[:LATEST]->(term_ver_value7:CTTermNameValue {
name: "sdtm_cat_name2",
name_sentence_case: "sdtm_cat_name2"})
MERGE (term_ver_root7)-[latest_final7:LATEST_FINAL]->(term_ver_value7)
SET latest_final7 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_cat2)

CREATE (library)-[:CONTAINS_TERM]->(sdtm_domain2:CTTermRoot {uid: "sdtm_domain_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root8:CTTermNameRoot)-[:LATEST]->(term_ver_value8:CTTermNameValue {
name: "sdtm_domain_name2",
name_sentence_case: "sdtm_domain_name2"})
MERGE (term_ver_root8)-[latest_final8:LATEST_FINAL]->(term_ver_value8)
SET latest_final8 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(sdtm_domain2)

CREATE (library)-[:CONTAINS_TERM]->(specimen1:CTTermRoot {uid: "specimen_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root9:CTTermNameRoot)-[:LATEST]->(term_ver_value9:CTTermNameValue {
name: "specimen_name1",
name_sentence_case: "specimen_name_sentence_case1"})
MERGE (term_ver_root9)-[latest_final9:LATEST_FINAL]->(term_ver_value9)
SET latest_final9 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(specimen1)

CREATE (library)-[:CONTAINS_TERM]->(specimen2:CTTermRoot {uid: "specimen_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root10:CTTermNameRoot)-[:LATEST]->(term_ver_value10:CTTermNameValue {
name: "specimen_name2",
name_sentence_case: "specimen_name_sentence_case2"})
MERGE (term_ver_root10)-[latest_final10:LATEST_FINAL]->(term_ver_value10)
SET latest_final10 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(specimen2)

CREATE (library)-[:CONTAINS_TERM]->(test_code1:CTTermRoot {uid: "test_code_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root11:CTTermNameRoot)-[:LATEST]->(term_ver_value11:CTTermNameValue {
name: "test_code_name1",
name_sentence_case: "test_code_name_sentence_case1"})
MERGE (term_ver_root11)-[latest_final11:LATEST_FINAL]->(term_ver_value11)
SET latest_final11 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(test_code1)

CREATE (library)-[:CONTAINS_TERM]->(test_code2:CTTermRoot {uid: "test_code_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root12:CTTermNameRoot)-[:LATEST]->(term_ver_value12:CTTermNameValue {
name: "test_code_name2",
name_sentence_case: "test_code_name_sentence_case2"})
MERGE (term_ver_root12)-[latest_final12:LATEST_FINAL]->(term_ver_value12)
SET latest_final12 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(test_code2)

CREATE (library)-[:CONTAINS_TERM]->(unit_dimension1:CTTermRoot {uid: "unit_dimension_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root13:CTTermNameRoot)-[:LATEST]->(term_ver_value13:CTTermNameValue {
name: "unit_dimension_name1",
name_sentence_case: "unit_dimension_name_sentence_case1"})
MERGE (term_ver_root13)-[latest_final13:LATEST_FINAL]->(term_ver_value13)
SET latest_final13 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(unit_dimension1)

CREATE (library)-[:CONTAINS_TERM]->(unit_dimension2:CTTermRoot {uid: "unit_dimension_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root14:CTTermNameRoot)-[:LATEST]->(term_ver_value14:CTTermNameValue {
name: "unit_dimension_name2",
name_sentence_case: "unit_dimension_name_sentence_case2"})
MERGE (term_ver_root14)-[latest_final14:LATEST_FINAL]->(term_ver_value14)
SET latest_final14 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(unit_dimension2)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_value1:CTTermRoot {uid: "categoric_response_value_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root15:CTTermNameRoot)-[:LATEST]->(term_ver_value15:CTTermNameValue {
name: "categoric_response_value_name1",
name_sentence_case: "categoric_response_value_name_sentence_case1"})
MERGE (term_ver_root15)-[latest_final15:LATEST_FINAL]->(term_ver_value15)
SET latest_final15 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_value1)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_value2:CTTermRoot {uid: "categoric_response_value_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root16:CTTermNameRoot)-[:LATEST]->(term_ver_value16:CTTermNameValue {
name: "categoric_response_value_name2",
name_sentence_case: "categoric_response_value_name_sentence_case2"})
MERGE (term_ver_root16)-[latest_final16:LATEST_FINAL]->(term_ver_value16)
SET latest_final16 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_value2)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_list1:CTTermRoot {uid: "categoric_response_list_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root17:CTTermNameRoot)-[:LATEST]->(term_ver_value17:CTTermNameValue {
name: "categoric_response_list_name1",
name_sentence_case: "categoric_response_list_name_sentence_case1"})
MERGE (term_ver_root17)-[latest_final17:LATEST_FINAL]->(term_ver_value17)
SET latest_final17 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_list1)

CREATE (library)-[:CONTAINS_TERM]->(categoric_response_list2:CTTermRoot {uid: "categoric_response_list_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root18:CTTermNameRoot)-[:LATEST]->(term_ver_value18:CTTermNameValue {
name: "categoric_response_list_name2",
name_sentence_case: "categoric_response_list_name_sentence_case2"})
MERGE (term_ver_root18)-[latest_final18:LATEST_FINAL]->(term_ver_value18)
SET latest_final18 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(categoric_response_list2)

CREATE (library)-[:CONTAINS_TERM]->(dose_frequency1:CTTermRoot {uid: "dose_frequency_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root19:CTTermNameRoot)-[:LATEST]->(term_ver_value19:CTTermNameValue {
name: "dose_frequency_name1",
name_sentence_case: "dose_frequency_name_sentence_case1"})
MERGE (term_ver_root19)-[latest_final19:LATEST_FINAL]->(term_ver_value19)
SET latest_final19 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_frequency1)

CREATE (library)-[:CONTAINS_TERM]->(dose_frequency2:CTTermRoot {uid: "dose_frequency_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root20:CTTermNameRoot)-[:LATEST]->(term_ver_value20:CTTermNameValue {
name: "dose_frequency_name2",
name_sentence_case: "dose_frequency_name_sentence_case2"})
MERGE (term_ver_root20)-[latest_final20:LATEST_FINAL]->(term_ver_value20)
SET latest_final20 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_frequency2)

CREATE (library)-[:CONTAINS_TERM]->(dose_unit1:CTTermRoot {uid: "dose_unit_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root21:CTTermNameRoot)-[:LATEST]->(term_ver_value21:CTTermNameValue {
name: "dose_unit_name1",
name_sentence_case: "dose_unit_name_sentence_case1"})
MERGE (term_ver_root21)-[latest_final21:LATEST_FINAL]->(term_ver_value21)
SET latest_final21 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_unit1)

CREATE (library)-[:CONTAINS_TERM]->(dose_unit2:CTTermRoot {uid: "dose_unit_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root22:CTTermNameRoot)-[:LATEST]->(term_ver_value22:CTTermNameValue {
name: "dose_unit_name2",
name_sentence_case: "dose_unit_name_sentence_case2"})
MERGE (term_ver_root22)-[latest_final22:LATEST_FINAL]->(term_ver_value22)
SET latest_final22 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dose_unit2)

CREATE (library)-[:CONTAINS_TERM]->(dosage_form1:CTTermRoot {uid: "dosage_form_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root23:CTTermNameRoot)-[:LATEST]->(term_ver_value23:CTTermNameValue {
name: "dosage_form_name1",
name_sentence_case: "dosage_form_name_sentence_case1"})
MERGE (term_ver_root23)-[latest_final23:LATEST_FINAL]->(term_ver_value23)
SET latest_final23 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dosage_form1)

CREATE (library)-[:CONTAINS_TERM]->(dosage_form2:CTTermRoot {uid: "dosage_form_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root24:CTTermNameRoot)-[:LATEST]->(term_ver_value24:CTTermNameValue {
name: "dosage_form_name2",
name_sentence_case: "dosage_form_name_sentence_case2"})
MERGE (term_ver_root24)-[latest_final24:LATEST_FINAL]->(term_ver_value24)
SET latest_final24 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dosage_form2)

CREATE (library)-[:CONTAINS_TERM]->(route_of_administration1:CTTermRoot {uid: "route_of_administration_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root25:CTTermNameRoot)-[:LATEST]->(term_ver_value25:CTTermNameValue {
name: "route_of_administration_name1",
name_sentence_case: "route_of_administration_name_sentence_case1"})
MERGE (term_ver_root25)-[latest_final25:LATEST_FINAL]->(term_ver_value25)
SET latest_final25 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(route_of_administration1)

CREATE (library)-[:CONTAINS_TERM]->(route_of_administration2:CTTermRoot {uid: "route_of_administration_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root26:CTTermNameRoot)-[:LATEST]->(term_ver_value26:CTTermNameValue {
name: "route_of_administration_name2",
name_sentence_case: "route_of_administration_name_sentence_case2"})
MERGE (term_ver_root26)-[latest_final26:LATEST_FINAL]->(term_ver_value26)
SET latest_final26 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(route_of_administration2)

CREATE (library)-[:CONTAINS_TERM]->(delivery_device1:CTTermRoot {uid: "delivery_device_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root27:CTTermNameRoot)-[:LATEST]->(term_ver_value27:CTTermNameValue {
name: "delivery_device_name1",
name_sentence_case: "delivery_device_name_sentence_case1"})
MERGE (term_ver_root27)-[latest_final27:LATEST_FINAL]->(term_ver_value27)
SET latest_final27 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(delivery_device1)

CREATE (library)-[:CONTAINS_TERM]->(delivery_device2:CTTermRoot {uid: "delivery_device_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root28:CTTermNameRoot)-[:LATEST]->(term_ver_value28:CTTermNameValue {
name: "delivery_device_name2",
name_sentence_case: "delivery_device_name_sentence_case2"})
MERGE (term_ver_root28)-[latest_final28:LATEST_FINAL]->(term_ver_value28)
SET latest_final28 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(delivery_device2)

CREATE (library)-[:CONTAINS_TERM]->(dispenser1:CTTermRoot {uid: "dispenser_uid1"})-[:HAS_NAME_ROOT]->
(term_ver_root29:CTTermNameRoot)-[:LATEST]->(term_ver_value29:CTTermNameValue {
name: "dispenser_name1",
name_sentence_case: "dispenser_name_sentence_case1"})
MERGE (term_ver_root29)-[latest_final29:LATEST_FINAL]->(term_ver_value29)
SET latest_final29 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dispenser1)

CREATE (library)-[:CONTAINS_TERM]->(dispenser2:CTTermRoot {uid: "dispenser_uid2"})-[:HAS_NAME_ROOT]->
(term_ver_root30:CTTermNameRoot)-[:LATEST]->(term_ver_value30:CTTermNameValue {
name: "dispenser_name2",
name_sentence_case: "dispenser_name_sentence_case2"})
MERGE (term_ver_root30)-[latest_final30:LATEST_FINAL]->(term_ver_value30)
SET latest_final30 = final_properties
CREATE (codelist_root)-[:HAS_TERM]->(dispenser2)
"""
STARTUP_ACTIVITY_INSTANCES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (activity_hierarchy_root1:ActivityRoot {uid:"activity_root1"})-[:LATEST]->(activity_hierarchy_value1)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root1:ConceptRoot:ActivityInstanceRoot:TemplateParameterValueRoot:ReminderRoot {uid:"activity_instance_root1"})
-[:LATEST]->(activity_instance_value1:ConceptValue:ActivityInstanceValue:TemplateParameterValue:ReminderValue {
name:"name1",
name_sentence_case:"name_sentence_case1",
definition:"definition1",
abbreviation:"abbv",
topic_code:"topic_code1",
adam_param_code:"adam_param_code1",
legacy_description:"legacy_description1"
})-[:IN_HIERARCHY]->(activity_hierarchy_value1)
MERGE (activity_instance_root1)-[latest_final1:LATEST_FINAL]->(activity_instance_value1)
SET latest_final1 = final_properties
MERGE (sdtm_variable1:CTTermRoot {uid:"sdtm_variable_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:TABULATED_IN]->(sdtm_variable1)
MERGE (sdtm_subcat1:CTTermRoot {uid:"sdtm_subcat_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_SUBCAT]->(sdtm_subcat1)
MERGE (sdtm_cat1:CTTermRoot {uid:"sdtm_cat_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_CAT]->(sdtm_cat1)
MERGE (sdtm_domain1:CTTermRoot {uid:"sdtm_domain_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_DOMAIN]->(sdtm_domain1)
MERGE (specimen1:CTTermRoot {uid:"specimen_uid1"})
MERGE (activity_instance_value1)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SPECIMEN]->(specimen1)

MERGE (activity_hierarchy_root2:ActivityRoot {uid:"activity_root2"})-[:LATEST]->(activity_hierarchy_value2)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root2:ConceptRoot:ActivityInstanceRoot:TemplateParameterValueRoot:ReminderRoot {uid:"activity_instance_root2"})
-[:LATEST]->(activity_instance_value2:ConceptValue:ActivityInstanceValue:TemplateParameterValue:ReminderValue {
name:"name2",
name_sentence_case:"name_sentence_case2",
definition:"definition2",
abbreviation:"abbv",
topic_code:"topic_code2",
adam_param_code:"adam_param_code2",
legacy_description:"legacy_description2"
})-[:IN_HIERARCHY]->(activity_hierarchy_value2)
MERGE (activity_instance_root2)-[latest_draft2:LATEST_FINAL]->(activity_instance_value2)
SET latest_draft2 = draft_properties
MERGE (sdtm_variable2:CTTermRoot {uid:"sdtm_variable_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:TABULATED_IN]->(sdtm_variable2)
MERGE (sdtm_subcat2:CTTermRoot {uid:"sdtm_subcat_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_SUBCAT]->(sdtm_subcat2)
MERGE (sdtm_cat2:CTTermRoot {uid:"sdtm_cat_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_CAT]->(sdtm_cat2)
MERGE (sdtm_domain2:CTTermRoot {uid:"sdtm_domain_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SDTM_DOMAIN]->(sdtm_domain2)
MERGE (specimen2:CTTermRoot {uid:"specimen_uid2"})
MERGE (activity_instance_value2)-[:DEFINED_BY]->(:ActivityDefinition:ConceptRoot:ActivityItem)-[:HAS_SPECIMEN]->(specimen2)
"""

STARTUP_ACTIVITY_INSTANCES_TOPICCDDEF = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime('2021-10-01T12:00:00.0+0200'),
end_date: datetime('2021-10-03T12:00:00.0+0200'),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties,
{
change_description: "Approved version",
start_date: datetime('2021-10-03T12:00:00.0+0200'),
status: "Final",
user_initials: "TODO initials",
version: "2.0"
} AS final2_properties

MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (activity_root1:ActivityRoot {uid:"activity_root1"})-[:LATEST]->(activity_value1)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root1:ConceptRoot:ActivityInstanceRoot:FindingRoot:NumericFindingRoot {uid:"activity_instance_root1"})
-[:LATEST]->(new_activity_instance_value1:ConceptValue:ActivityInstanceValue:FindingValue:NumericFindingValue {
name:"new_name1",
name_sentence_case:"name_sentence_case1",
definition:"definition1",
abbreviation:"abbv",
topic_code:"topic_code1",
adam_param_code:"adam_param_code1",
legacy_description:"legacy_description1",
molecular_weight:1.0,
value_sas_display_format:"string"
})-[:IN_HIERARCHY]->(activity_value1)
MERGE (activity_instance_root1)-[latest_final2:LATEST_FINAL]->(new_activity_instance_value1)

MERGE (activity_instance_root1)-[latest_final1:HAS_VERSION]->(activity_instance_value1:ConceptValue:
ActivityInstanceValue:FindingValue:NumericFindingValue {
name:"name1"})
MERGE (activity_instance_value1)-[:IN_HIERARCHY]->(activity_value1)
SET activity_instance_value1=new_activity_instance_value1
SET activity_instance_value1.molecular_weight = 0.0
SET activity_instance_value1.name="name1"
SET latest_final1 = final_properties
SET latest_final2 = final2_properties



MERGE (activity_root2:ActivityRoot {uid:"activity_root2"})-[:LATEST]->(activity_value2)
MERGE (library)-[:CONTAINS_CONCEPT]->(
activity_instance_root2:ConceptRoot:ActivityInstanceRoot:InterventionRoot:CompoundDosingRoot {uid:"activity_instance_root2"})
-[:LATEST]->(activity_instance_value2:ConceptValue:ActivityInstanceValue:InterventionValue:CompoundDosingValue {
name:"name2",
name_sentence_case:"name_sentence_case2",
definition:"definition2",
abbreviation:"abbv",
topic_code:"topic_code2",
adam_param_code:"adam_param_code2",
legacy_description:"legacy_description2"
})-[:IN_HIERARCHY]->(activity_value2)
MERGE (activity_instance_root2)-[latest_final3:LATEST_FINAL]->(activity_instance_value2)
SET latest_final3 = final2_properties

"""

STARTUP_ACTIVITY_GROUPS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_group_root1:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root1"})
-[:LATEST]->(activity_group_value1:ConceptValue:ActivityGroupValue {
name:"name1",
name_sentence_case:"name_sentence_case1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_group_root1)-[latest_final1:LATEST_FINAL]->(activity_group_value1)
SET latest_final1 = final_properties

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_group_root2:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root2"})
-[:LATEST]->(activity_group_value2:ConceptValue:ActivityGroupValue {
name:"name2",
name_sentence_case:"name_sentence_case2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_group_root2)-[latest_draft2:LATEST_FINAL]->(activity_group_value2)
SET latest_draft2 = draft_properties
"""
STARTUP_ACTIVITY_SUB_GROUPS = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_sub_group_root1:ConceptRoot:ActivitySubGroupRoot {uid:"activity_sub_group_root1"})
-[:LATEST]->(activity_sub_group_value1:ConceptValue:ActivitySubGroupValue {
name:"name1",
name_sentence_case:"name_sentence_case1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_sub_group_root1)-[latest_final1:LATEST_FINAL]->(activity_sub_group_value1)
SET latest_final1 = final_properties

MERGE (activity_group_root1:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root1"})
-[:LATEST]->(activity_group_value1:ConceptValue:ActivityGroupValue)
MERGE (activity_sub_group_value1)-[:IN_GROUP]->(activity_group_value1)


MERGE (library)-[:CONTAINS_CONCEPT]->(activity_sub_group_root2:ConceptRoot:ActivitySubGroupRoot {uid:"activity_sub_group_root2"})
-[:LATEST]->(activity_sub_group_value2:ConceptValue:ActivitySubGroupValue {
name:"name2",
name_sentence_case:"name_sentence_case2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_sub_group_root2)-[latest_draft2:LATEST_FINAL]->(activity_sub_group_value2)
SET latest_draft2 = draft_properties

MERGE (activity_group_root2:ConceptRoot:ActivityGroupRoot {uid:"activity_group_root2"})
-[:LATEST]->(activity_group_value2:ConceptValue:ActivityGroupValue)
MERGE (activity_sub_group_value2)-[:IN_GROUP]->(activity_group_value2)
"""
STARTUP_ACTIVITIES = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
MERGE (library:Library {name:"Sponsor", is_editable:true})
MERGE (library)-[:CONTAINS_CONCEPT]->(activity_root1:ConceptRoot:ActivityRoot {uid:"activity_root1"})
-[:LATEST]->(activity_value1:ConceptValue:ActivityValue {
name:"name1",
name_sentence_case:"name_sentence_case1",
definition:"definition1",
abbreviation:"abbv"
})
MERGE (activity_root1)-[latest_final1:LATEST_FINAL]->(activity_value1)
SET latest_final1 = final_properties
MERGE (activity_sub_group_root1:ConceptRoot:ActivitySubGroupRoot {uid:"activity_sub_group_root1"})
-[:LATEST]->(activity_sub_group_value1:ConceptValue:ActivitySubGroupValue)
MERGE (activity_value1)-[:IN_SUB_GROUP]->(activity_sub_group_value1)

MERGE (library)-[:CONTAINS_CONCEPT]->(activity_root2:ConceptRoot:ActivityRoot {uid:"activity_root2"})
-[:LATEST]->(activity_value2:ConceptValue:ActivityValue {
name:"name2",
name_sentence_case:"name_sentence_case2",
definition:"definition2",
abbreviation:"abbv"
})
MERGE (activity_root2)-[latest_draft2:LATEST_FINAL]->(activity_value2)
SET latest_draft2 = draft_properties
MERGE (activity_sub_group_root2:ConceptRoot:ActivitySubGroupRoot {uid:"activity_sub_group_root2"})
-[:LATEST]->(activity_sub_group_value2:ConceptValue:ActivitySubGroupValue)
MERGE (activity_value2)-[:IN_SUB_GROUP]->(activity_sub_group_value2)
"""
STARTUP_DICTIONARY_CODELISTS_CYPHER = """
// SNOMED Library with two codelists
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"SNOMED", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"name1"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
SET latest_final1 = final_properties

MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root2:DictionaryCodelistRoot {uid:"codelist_root2_uid"})
-[:LATEST]->(codelist_value2:DictionaryCodelistValue {name:"name2"})
MERGE (codelist_root2)-[latest_draft2:LATEST_DRAFT]->(codelist_value2)
SET latest_draft2 = draft_properties


// UNII Library with UNII codelist
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"UNII", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_unii_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"UNII"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
SET latest_final1 = final_properties



// MED-RT Library with PClass codelist
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties
CREATE (library:Library {name:"MED-RT", is_editable:true})
MERGE (library)-[:CONTAINS_DICTIONARY_CODELIST]->(codelist_root1:DictionaryCodelistRoot {uid:"codelist_pclass_uid"})
-[:LATEST]->(codelist_value1:DictionaryCodelistValue:TemplateParameter {name:"PClass"})
MERGE (codelist_root1)-[latest_final1:LATEST_FINAL]->(codelist_value1)
SET latest_final1 = final_properties

"""
STARTUP_DICTIONARY_TERMS_CYPHER = """
WITH  {
change_description: "New draft version",
start_date: datetime(),
status: "Draft",
user_initials: "TODO initials",
version: "0.1"
} AS draft_properties,
{
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties,
{
start_date: datetime(),
user_initials: "Dictionary Codelist Test"
} AS has_term_properties
MATCH (library:Library {name:"SNOMED"})
MERGE (codelist_root1:DictionaryCodelistRoot {uid:"codelist_root1_uid"})
MERGE (codelist_root1)-[has_term1:HAS_TERM]->(term_root1:DictionaryTermRoot:SnomedTermRoot {uid:"term_root1_uid"})
-[:LATEST]->(term_value1:DictionaryTermValue:SnomedTermValue {
name:"name1", dictionary_id:"dictionary_id1", name_sentence_case:"Name1", abbreviation:"abbreviation1", definition:"definition1"})
MERGE (codelist_root1)-[has_term4:HAS_TERM]->(term_root4:DictionaryTermRoot:SnomedTermRoot {uid:"term_root4_uid"})
-[:LATEST]->(term_value4:DictionaryTermValue:SnomedTermValue {
name:"name4", dictionary_id:"dictionary_id4", name_sentence_case:"Name4", abbreviation:"abbreviation4", definition:"definition4"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root1)
MERGE (term_root1)-[latest_final1:LATEST_FINAL]->(term_value1)
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root4)
MERGE (term_root4)-[latest_final2:LATEST_FINAL]->(term_value4)
SET latest_final1 = final_properties
SET has_term1 = has_term_properties
SET latest_final2 = final_properties
SET has_term4 = has_term_properties

MERGE (codelist_root2:DictionaryCodelistRoot {uid:"codelist_root2_uid"})
MERGE (codelist_root2)-[has_term2:HAS_TERM]->(term_root2:DictionaryTermRoot:SnomedTermRoot {uid:"term_root2_uid"})
-[:LATEST]->(term_value2:DictionaryTermValue:SnomedTermValue {
name:"name2", dictionary_id:"dictionary_id2", name_sentence_case:"Name2", abbreviation:"abbreviation2", definition:"definition2"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root2)
MERGE (term_root2)-[latest_draft2:LATEST_DRAFT]->(term_value2)
SET latest_draft2 = draft_properties
SET has_term2 = has_term_properties

MERGE (codelist_root2)-[has_term3:HAS_TERM]->(term_root3:DictionaryTermRoot:SnomedTermRoot {uid:"term_root3_uid"})
-[:LATEST]->(term_value3:DictionaryTermValue:SnomedTermValue {
name:"name3", dictionary_id:"dictionary_id3", name_sentence_case:"Name3", abbreviation:"abbreviation3", definition:"definition3"})
MERGE (library)-[:CONTAINS_DICTIONARY_TERM]->(term_root3)
MERGE (term_root3)-[latest_draft3:LATEST_DRAFT]->(term_value3)
MERGE (term_root3)-[latest_final3:LATEST_FINAL]->(term_value3)
SET latest_draft3 = draft_properties
SET latest_final3 = final_properties
SET has_term3 = has_term_properties
"""
STARTUP_CT_CATALOGUE_CYPHER = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS new_props
MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:HAS_CODELIST]->
(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(codelist_attr_root_to_update:CTCodelistAttributesRoot)-[final1:LATEST_FINAL]->(:CTCodelistAttributesValue
{name:"old_name", extensible:false})
SET final1 = old_props
MERGE (catalogue)-[:HAS_CODELIST]->(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(codelist_attr_to_delete)-[final2:LATEST_FINAL]->(:CTCodelistAttributesValue 
{name:"old_name", extensible:false})
SET final2=old_props
MERGE (codelist_to_update)-[:HAS_TERM]->(term_to_update:CTTermRoot {uid:"updated_term_uid"})
-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root_to_update:CTTermAttributesRoot)-[final3:LATEST_FINAL]->(:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
SET final3 = old_props
MERGE (codelist_to_delete)-[:HAS_TERM]->(:CTTermRoot {uid:"deleted_term_uid"})
-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[final4:LATEST_FINAL]->(:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
SET final4=old_props

MERGE (codelist_attr_root_to_update)-[final5:LATEST_FINAL]->(:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition"})
SET final5=new_props
MERGE (catalogue)-[:HAS_CODELIST]->(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})-[:HAS_ATTRIBUTES_ROOT]->
(:CTCodelistAttributesRoot)-[final6:LATEST_FINAL]->(:CTCodelistAttributesValue 
{name:"new_name", definition:"codelist_added"})
SET final6=new_props
MERGE (term_attr_root_to_update)-[final7:LATEST_FINAL]->(:CTTermAttributesValue 
{name_submission_value:"new_submission_value", definition:"new_definition"})
SET final7=new_props
MERGE (codelist_to_add)-[:HAS_TERM]->(:CTTermRoot {uid:"added_term_uid"})-
[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[final8:LATEST_FINAL]->(:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})
SET final8=new_props
"""

STARTUP_CT_PACKAGE_CYPHER = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS new_props
MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:CONTAINS_PACKAGE]->(old_package:CTPackage{
uid:"old_package_uid",
name:"old_package",
effective_date:date("2020-03-27"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
user_initials:"initials"
})
MERGE (catalogue)-[:CONTAINS_PACKAGE]->(new_package:CTPackage{
uid:"new_package_uid", 
name:"new_package", 
effective_date:date("2020-06-26"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
user_initials:"initials"
})

MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist1:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"old_name", extensible:false})<-[final1:LATEST_FINAL]-(codelist_attr_root_to_update:CTCodelistAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})
SET final1 = old_props
MERGE (codelist_to_update)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[final2:LATEST_FINAL]->(:CTCodelistNameValue)
SET final2=old_props
MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist2:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"old_name", extensible:false})<-[final3:LATEST_FINAL]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})
SET final3=old_props
MERGE (package_codelist1)-[contains_term:CONTAINS_TERM]->(package_term1:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final4:LATEST_FINAL]-(term_attr_root_to_update:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(term_to_update:CTTermRoot {uid:"updated_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
SET final4=old_props
MERGE (package_term1)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value:CTTermAttributesValue 
{name_submission_value:"not_modified_submission_value", preferred_term:"not_modified_preferred_term"})<-[final5:LATEST_FINAL]-(:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(not_modified_term:CTTermRoot {uid:"not_modified_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
SET final5=old_props
MERGE (package_codelist2)-[:CONTAINS_TERM]->(package_term2:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final6:LATEST_FINAL]-(:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"deleted_term_uid"})<-[:HAS_TERM]-(codelist_to_delete)
SET final6=old_props

MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist3:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition"})<-[final7:LATEST_FINAL]-(codelist_attr_root_to_update)
SET final7 = new_props
MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist4:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"new_name", definition:"codelist_added"})<-[final8:LATEST_FINAL]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})
SET final8 = new_props
MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term3:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{name_submission_value:"new_submission_value", definition:"new_definition"})<-[final9:LATEST_FINAL]-(term_attr_root_to_update)
SET final9 = new_props
MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term5:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value)
MERGE (package_codelist4)-[:CONTAINS_TERM]->(package_term4:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue
{name_submission_value:"old_submission_value", preferred_term:"old_preferred_term"})<-[final10:LATEST_FINAL]-(:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"added_term_uid"})<-[:HAS_TERM]-(codelist_to_add)
SET final10 = new_props
"""

STARTUP_CT_PACKAGE_CYPHER_CDISC_CT = """
WITH  {
change_description: "Approved version",
start_date: datetime("2020-03-27T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS old_props,
{
change_description: "Approved version",
start_date: datetime("2020-06-26T00:00:00"),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS new_props

MERGE (cat:CTCatalogue {name: "catalogue2"})-[:CONTAINS_PACKAGE] -> (package1:CTPackage{
uid:"package1_uid",name:"package1",effective_date:date("2020-06-26")})
-[:CONTAINS_CODELIST]->(p_codelist1:CTPackageCodelist {uid:"package1_uid_cdlist_code1"})
-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"codelist_name1", extensible:false, submission_value:"submission_value1", definition: "definition1", 
preferred_term:"codelist_pref_term1", synonyms:apoc.text.split("synonym1",",")})
MERGE (p_codelist1)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id", code_submission_value:"code_submission_value",definition:"definition",
preferred_term:"pref_term",synonyms:apoc.text.split("syn1,syn2",",")})

MERGE (cat2:CTCatalogue {name: "catalogue3"})-[:CONTAINS_PACKAGE] -> (package2:CTPackage{
uid:"package2_uid",name:"package2",effective_date:date("2020-06-26")})
-[:CONTAINS_CODELIST]->(p_codelist2:CTPackageCodelist {uid:"package2_uid_cdlist_code2"})
-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"codelist_name2", extensible:false, submission_value:"submission_value2", definition: "definition2", 
preferred_term:"codelist_pref_term2", synonyms:apoc.text.split("synonym2",",")})
MERGE (p_codelist2)-[:CONTAINS_TERM]->(:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id2", code_submission_value:"code_submission_value2",definition:"definition2",
preferred_term:"pref_term2",synonyms:apoc.text.split("syn1,syn2",",")})

MERGE (catalogue:CTCatalogue {name:"catalogue"})-[:CONTAINS_PACKAGE]->(old_package:CTPackage{
uid:"old_package_uid",
name:"old_package",
effective_date:date("2020-03-27"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
user_initials:"initials"
})
MERGE (catalogue)-[:CONTAINS_PACKAGE]->(new_package:CTPackage{
uid:"new_package_uid", 
name:"new_package", 
effective_date:date("2020-06-26"), 
label:"label",
href:"href",
description:"description",
source:"source",
registration_status:"status",
import_date:datetime("2020-03-27T00:00:00Z"),
user_initials:"initials"
})

MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist1:CTPackageCodelist {uid:"old_package_uid_codelist_code1"})-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"old_name1", extensible:false, submission_value:"old_submission_value1", definition:"old_definition1", preferred_term:"old_pref_term1", synonyms:apoc.text.split("syn1,syn2",",")})
<-[final1:LATEST_FINAL]-(codelist_attr_root_to_update:CTCodelistAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_update:CTCodelistRoot {uid:"updated_codelist_uid"})
SET final1 = old_props
MERGE (codelist_to_update)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[final2:LATEST_FINAL]->(:CTCodelistNameValue)
SET final2=old_props
MERGE (old_package)-[:CONTAINS_CODELIST]->(package_codelist2:CTPackageCodelist {uid:"old_package_uid_codelist_code2"})-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"old_name2", extensible:false, submission_value:"old_submission_value2", definition: "old_definition2", preferred_term:"old_pref_term2", synonyms:apoc.text.split("synonym",",")})
<-[final3:LATEST_FINAL]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_delete:CTCodelistRoot {uid:"deleted_codelist_uid"})
SET final3=old_props
MERGE (package_codelist1)-[contains_term:CONTAINS_TERM]->(package_term1:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id1", code_submission_value:"code_submission_value1",definition:"definition1",
preferred_term:"pref_term1",synonyms:apoc.text.split("syn1,syn2",",")})<-[final4:LATEST_FINAL]-(term_attr_root_to_update:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(term_to_update:CTTermRoot {uid:"updated_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
SET final4=old_props
//MERGE (package_term1)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value:CTTermAttributesValue 
//{name_submission_value:"not_modified_submission_value", preferred_term:"not_modified_preferred_term"})<-[final5:LATEST_FINAL]-(:CTTermAttributesRoot)
//<-[:HAS_ATTRIBUTES_ROOT]-(not_modified_term:CTTermRoot {uid:"not_modified_term_uid"})<-[:HAS_TERM]-(codelist_to_update)
//SET final5=old_props
MERGE (package_codelist2)-[:CONTAINS_TERM]->(package_term2:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id2", code_submission_value:"code_submission_value2",
definition:"definition2",preferred_term:"pref_term2",synonyms:apoc.text.split("syn",",")})<-[final6:LATEST_FINAL]-(:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"deleted_term_uid"})<-[:HAS_TERM]-(codelist_to_delete)
SET final6=old_props

MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist3:CTPackageCodelist {uid:"new_package_uid_codelist_code3"})-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"new_name", definition: "new_definition", extensible:true, submission_value:"new_submission_value", preferred_term:"new_pref_term1"})
<-[final7:LATEST_FINAL]-(codelist_attr_root_to_update)
SET final7 = new_props
MERGE (new_package)-[:CONTAINS_CODELIST]->(package_codelist4:CTPackageCodelist {uid:"new_package_uid_codelist_code4"})-[:CONTAINS_ATTRIBUTES]->(:CTCodelistAttributesValue 
{name:"new_name", submission_value:"new_submission_value",definition:"codelist_added", extensible:false, preferred_term:"new_pref_term", synonyms:apoc.text.split("syn1,syn2,syn3",",")})
<-[final8:LATEST_FINAL]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(codelist_to_add:CTCodelistRoot {uid:"added_codelist_uid"})
SET final8 = new_props
MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term3:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue 
{concept_id:"concept_id3", code_submission_value:"code_submission_value3",definition:"definition3",preferred_term:"pref_term3"})
<-[final9:LATEST_FINAL]-(term_attr_root_to_update)
SET final9 = new_props
//MERGE (package_codelist3)-[:CONTAINS_TERM]->(package_term5:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(not_modified_term_value)
MERGE (package_codelist4)-[:CONTAINS_TERM]->(package_term4:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]->(:CTTermAttributesValue
{concept_id:"concept_id4", code_submission_value:"code_submission_value4",
definition:"definition4",preferred_term:"pref_term4",synonyms:apoc.text.split("syn1,syn2,syn3",",")})<-[final10:LATEST_FINAL]-(:CTTermAttributesRoot)
<-[:HAS_ATTRIBUTES_ROOT]-(:CTTermRoot {uid:"added_term_uid"})<-[:HAS_TERM]-(codelist_to_add)
SET final10 = new_props

"""
STARTUP_CT_CODELISTS_ATTRIBUTES_CYPHER = """
MERGE (cr:CTCodelistRoot {uid: "ct_codelist_root1"})
MERGE (cr)-[:HAS_ATTRIBUTES_ROOT]->(car:CTCodelistAttributesRoot)-
    [:LATEST]->(cav:CTCodelistAttributesValue {name: "codelist attributes value1",
                                               submission_value: "codelist submission value1",
                                               preferred_term: "codelist preferred term",
                                               definition: "codelist definition",
                                               extensible: false})
MERGE (:CTTermRoot {uid:"ct_term_root1"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr)
MERGE (car)-[hv:HAS_VERSION]->(cav)
MERGE (car)-[lf:LATEST_FINAL]->(cav)
set lf.change_description = "Approved version"
set lf.start_date = datetime("2020-06-26T00:00:00")
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"
set hv.change_description = "Initial version"
set hv.start_date = datetime("2020-03-27T00:00:00")
set hv.end_date = datetime("2020-06-26T00:00:00")
set hv.status = "Draft"
set hv.user_initials = "TODO initials"
set hv.version = "0.1"
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr2:CTCodelistRoot {uid: "ct_codelist_root2"})
MERGE (cr2)-[:HAS_ATTRIBUTES_ROOT]->(car2:CTCodelistAttributesRoot)-[:LATEST]->
    (cav2:CTCodelistAttributesValue {name: "codelist attributes value2",
                                    submission_value: "codelist submission value2",
                                    preferred_term: "codelist preferred term",
                                    definition: "codelist definition",
                                    extensible: false})
MERGE (cc)-[:HAS_CODELIST]->(cr2)
MERGE (car2)-[hv2:HAS_VERSION]->(cav2)
MERGE (car2)-[lf2:LATEST_FINAL]->(cav2)
MERGE (car2)-[ld2:LATEST_DRAFT]->(cav2)
set lf2.change_description = "Approved version"
set lf2.start_date = datetime("2020-03-27T00:00:00")
set lf2.end_date = datetime("2020-06-26T00:00:00")
set lf2.status = "Final"
set lf2.user_initials = "TODO initials"
set lf2.version = "1.0"
set ld2.change_description = "latest draft"
set ld2.start_date = datetime("2020-06-26T00:00:00")
set ld2.status = "Draft"
set ld2.user_initials = "TODO initials"
set ld2.version = "1.1"
set hv2.change_description = "Initial version"
set hv2.start_date = datetime("2020-03-27T00:00:00")
set hv2.end_date = datetime("2020-06-26T00:00:00")
set hv2.status = "Draft"
set hv2.user_initials = "TODO initials"
set hv2.version = "0.1"
MERGE (lib2:Library{name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr3:CTCodelistRoot {uid: "ct_codelist_root3"})
MERGE (cr3)-[:HAS_ATTRIBUTES_ROOT]->(car3:CTCodelistAttributesRoot)-[:LATEST]->
    (cav3:CTCodelistAttributesValue {name: "codelist attributes value3",
                                    submission_value: "codelist submission value3",
                                    preferred_term: "codelist preferred term",
                                    definition: "codelist definition",
                                    extensible: false})
MERGE (cc)-[:HAS_CODELIST]->(cr3)
MERGE (car3)-[ld3:LATEST_DRAFT]->(cav3)
set ld3.change_description = "latest draft"
set ld3.start_date = datetime("2020-06-26T00:00:00")
set ld3.status = "Draft"
set ld3.user_initials = "TODO initials"
set ld3.version = "0.1"


MERGE (cr3)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->(cnv:CTCodelistNameValue {name: "codelist_name_value"})
MERGE (cnr)-[hv3:HAS_VERSION]->(cnv)
MERGE (cnr)-[lf3:LATEST_FINAL]->(cnv)
set lf3.change_description = "Approved version"
set lf3.start_date = datetime("2020-06-26T00:00:00")
set lf3.status = "Final"
set lf3.user_initials = "TODO initials"
set lf3.version = "1.0"
set hv3.change_description = "Initial version"
set hv3.start_date = datetime("2020-03-27T00:00:00")
set hv3.end_date = datetime("2020-06-26T00:00:00")
set hv3.status = "Draft"
set hv3.user_initials = "TODO initials"
set hv3.version = "0.1"
MERGE (lib)-[:CONTAINS_CODELIST]->(cr3)
"""

STARTUP_CT_CODELISTS_NAME_CYPHER = """
MERGE (cr:CTCodelistRoot {uid: "ct_codelist_root1"})
MERGE (cr)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "tp_codelist_name_value"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr)
MERGE (cnr)-[hv:HAS_VERSION]->(cnv)
MERGE (cnr)-[lf:LATEST_FINAL]->(cnv)
set lf.change_description = "Approved version"
set lf.start_date = datetime("2020-06-26T00:00:00")
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"
set hv.change_description = "Initial version"
set hv.start_date = datetime("2020-03-27T00:00:00")
set hv.end_date = datetime("2020-06-26T00:00:00")
set hv.status = "Draft"
set hv.user_initials = "TODO initials"
set hv.version = "0.1"
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cr2:CTCodelistRoot {uid: "ct_codelist_root2"})
MERGE (cr2)-[:HAS_NAME_ROOT]->(cnr2:CTCodelistNameRoot)-[:LATEST]->
    (cnv2:CTCodelistNameValue {name: "not_tp_codelist_name_value"})
MERGE (cc)-[:HAS_CODELIST]->(cr2)
MERGE (cnr2)-[hv2:HAS_VERSION]->(cnv2)
MERGE (cnr2)-[lf2:LATEST_FINAL]->(cnv2)
MERGE (cnr2)-[ld2:LATEST_DRAFT]->(cnv2)
set lf2.change_description = "Approved version"
set lf2.start_date = datetime("2020-03-27T00:00:00")
set lf2.end_date = datetime("2020-06-26T00:00:00")
set lf2.status = "Final"
set lf2.user_initials = "TODO initials"
set lf2.version = "1.0"
set ld2.change_description = "latest draft"
set ld2.start_date = datetime("2020-06-26T00:00:00")
set ld2.status = "Draft"
set ld2.user_initials = "TODO initials"
set ld2.version = "1.1"
set hv2.change_description = "Initial version"
set hv2.start_date = datetime("2020-03-27T00:00:00")
set hv2.end_date = datetime("2020-06-26T00:00:00")
set hv2.status = "Draft"
set hv2.user_initials = "TODO initials"
set hv2.version = "0.1"
MERGE (lib2:Library{name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr3:CTCodelistRoot {uid: "ct_codelist_root3"})
MERGE (cr3)-[:HAS_NAME_ROOT]->(cnr3:CTCodelistNameRoot)-[:LATEST]->
    (cnv3:CTCodelistNameValue {name: "codelist_name_value"})
MERGE (cc)-[:HAS_CODELIST]->(cr3)
MERGE (cnr3)-[ld3:LATEST_DRAFT]->(cnv3)
set ld3.change_description = "latest draft"
set ld3.start_date = datetime("2020-06-26T00:00:00")
set ld3.status = "Draft"
set ld3.user_initials = "TODO initials"
set ld3.version = "0.1"
MERGE (lib)-[:CONTAINS_CODELIST]->(cr3)
"""

STARTUP_CT_TERM_ATTRIBUTES_CYPHER = """
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"editable_cr"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL{change_description: "Approved version",start_date: datetime(),status: "Final",user_initials: "TODO initials",version : "1.0"}]->(codelist_ver_value:CTCodelistNameValue)
MERGE (cr)-[:HAS_ATTRIBUTES_ROOT]->(car:CTCodelistAttributesRoot)-[:LATEST]->(cav:CTCodelistAttributesValue {name: "codelist attributes value1", submission_value: "codelist submission value1", preferred_term: "codelist preferred term", definition: "codelist definition", extensible: false})

CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
MERGE (car)-[hv1:HAS_VERSION]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
set lf1.change_description = "Approved version"
set lf1.start_date = datetime("2020-06-26T00:00:00")
set lf1.status = "Final"
set lf1.user_initials = "TODO initials"
set lf1.version = "1.0"
set hv1.change_description = "Initial version"
set hv1.start_date = datetime("2020-03-27T00:00:00")
set hv1.end_date = datetime("2020-06-26T00:00:00")
set hv1.status = "Draft"
set hv1.user_initials = "TODO initials"
set hv1.version = "0.1"

MERGE (editable_lib:Library{name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cc)-[:HAS_CODELIST]->(cr2:CTCodelistRoot {uid:"non_editable_cr"})
MERGE (non_editable_lib:Library{ name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr)-[has_term1:HAS_TERM]->(term_root:CTTermRoot {uid:"term_root_final"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root:CTTermAttributesRoot)-[:LATEST]-(term_ver_value:CTTermAttributesValue 
        {code_submission_value: "code_submission_value1", name_submission_value:"name_submission_value1", 
        preferred_term:"preferred_term", definition:"definition"})
MERGE (term_root)-[:HAS_NAME_ROOT]->(term_name_ver_root:CTTermNameRoot)-[:LATEST]-(term_name_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[hv2:HAS_VERSION]->(term_ver_value)
MERGE (term_ver_root)-[lf2:LATEST_FINAL]->(term_ver_value)
MERGE (term_name_ver_root)-[latest_final:LATEST_FINAL]->(term_name_ver_value)
set has_term1.order = 1
set lf2.change_description = "Approved version"
set lf2.start_date = datetime()
set lf2.status = "Final"
set lf2.user_initials = "TODO initials"
set lf2.version = "1.0"
set latest_final.change_description = "Approved version"
set latest_final.start_date = datetime()
set latest_final.status = "Final"
set latest_final.user_initials = "TODO initials"
set latest_final.version = "1.0"
set hv2.change_description = "Initial version"
set hv2.start_date = datetime()
set hv2.end_date = datetime()
set hv2.status = "Draft"
set hv2.user_initials = "TODO initials"
set hv2.version = "0.1"

MERGE (cr)-[has_term2:HAS_TERM]->(term_root2:CTTermRoot {uid:"term_root_draft"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root2:CTTermAttributesRoot)-[:LATEST]-(term_ver_value2:CTTermAttributesValue 
        {code_submission_value: "code_submission_value2", name_submission_value:"name_submission_value2", preferred_term:"preferred_term", definition:"definition"})
MERGE (term_ver_root2)-[ld:LATEST_DRAFT]->(term_ver_value2)
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root2)
set has_term2.order = 2
set ld.change_description = "latest draft"
set ld.start_date = datetime()
set ld.status = "Draft"
set ld.user_initials = "TODO initials"
set ld.version = "0.1"

MERGE (cr2)-[has_term3:HAS_TERM]->(term_root3:CTTermRoot {uid:"term_root_final_non_edit"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root3:CTTermAttributesRoot)-[:LATEST]-(term_ver_value3:CTTermAttributesValue 
        {code_submission_value: "code_submission_value3", name_submission_value:"name_submission_value3", preferred_term:"preferred_term", definition:"definition"})
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root3)
MERGE (term_ver_root3)-[hv3:HAS_VERSION]->(term_ver_value3)
MERGE (term_ver_root3)-[lf3:LATEST_FINAL]->(term_ver_value3)
set has_term3.order = 3
set lf3.change_description = "Approved version"
set lf3.start_date = datetime()
set lf3.status = "Final"
set lf3.user_initials = "TODO initials"
set lf3.version = "1.0"
set hv3.change_description = "Initial version"
set hv3.start_date = datetime()
set hv3.end_date = datetime()
set hv3.status = "Draft"
set hv3.user_initials = "TODO initials"
set hv3.version = "0.1"

MERGE (cr2)-[has_term4:HAS_TERM]->(term_root4:CTTermRoot {uid:"term_root_draft_non_edit"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root4:CTTermAttributesRoot)-[:LATEST]-(term_ver_value4:CTTermAttributesValue 
        {code_submission_value: "code_submission_value4", name_submission_value:"name_submission_value4", preferred_term:"preferred_term", definition:"definition"})
MERGE (term_ver_root4)-[ld2:LATEST_DRAFT]->(term_ver_value4)
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root4)
set has_term4.order = 4
set ld2.change_description = "latest draft"
set ld2.start_date = datetime()
set ld2.status = "Draft"
set ld2.user_initials = "TODO initials"
set ld2.version = "0.1"
"""

STARTUP_CT_TERM_NAME_CYPHER = """
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(cr:CTCodelistRoot {uid:"editable_cr"})-[:HAS_NAME_ROOT]
->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue {name:"Objective Level"})
CREATE (codelist_ver_root)-[:LATEST]->(codelist_ver_value)
MERGE (editable_lib:Library{ name:"Sponsor", is_editable:true})
MERGE (editable_lib)-[:CONTAINS_CODELIST]->(cr)

MERGE (cc)-[:HAS_CODELIST]->(cr2:CTCodelistRoot {uid:"non_editable_cr"})
MERGE (non_editable_lib:Library{ name:"CDISC", is_editable:false})-[:CONTAINS_CODELIST]->(cr2)

MERGE (cr)-[has_term:HAS_TERM]->(term_root:CTTermRoot {uid:"term_root_final"})-[:HAS_NAME_ROOT]->
    (term_ver_root:CTTermNameRoot)-[:LATEST]-(term_ver_value:CTTermNameValue 
        {name:"term_value_name1", name_sentence_case:"term_value_name_sentence_case"})
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[hv:HAS_VERSION]->(term_ver_value)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
set has_term.order = 1
set lf.change_description = "Approved version"
set lf.start_date = datetime()
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"
set hv.change_description = "Initial version"
set hv.start_date = datetime()
set hv.end_date = datetime()
set hv.status = "Draft"
set hv.user_initials = "TODO initials"
set hv.version = "0.1"

MERGE (cr)-[has_term2:HAS_TERM]->(term_root2:CTTermRoot {uid:"term_root_draft"})-[:HAS_NAME_ROOT]->
    (term_ver_root2:CTTermNameRoot)-[:LATEST]-(term_ver_value2:CTTermNameValue 
        {name:"term_value_name2", name_sentence_case:"term_value_name_sentence_case"})
MERGE (term_ver_root2)-[ld:LATEST_DRAFT]->(term_ver_value2)
MERGE (term_root2)-[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[ld_attributes:LATEST_DRAFT]->
(term_attributes_value:CTTermAttributesValue { 
                code_submission_value: "codeSubmissionValue",
                name_submission_value: "nameSubmissionValue",
                preferred_term: "nciPreferredName",
                definition: "definition"})
MERGE (term_attributes_root)-[:LATEST]->(term_attributes_value)
MERGE (editable_lib)-[:CONTAINS_TERM]->(term_root2)
set has_term2.order = 2
set has_term2.start_date=datetime()
set has_term2.user_initials='cttest'
set ld.change_description = "latest draft"
set ld.start_date = datetime()
set ld.status = "Draft"
set ld.user_initials = "TODO initials"
set ld.version = "0.1"
set ld_attributes.change_description = "latest draft"
set ld_attributes.start_date = datetime()
set ld_attributes.status = "Draft"
set ld_attributes.user_initials = "TODO initials"
set ld_attributes.version = "0.1"

MERGE (cr2)-[has_term3:HAS_TERM]->(term_root3:CTTermRoot {uid:"term_root_final_non_edit"})-[:HAS_NAME_ROOT]->
    (term_ver_root3:CTTermNameRoot)-[:LATEST]-(term_ver_value3:CTTermNameValue 
        {name:"term_value_name3", name_sentence_case:"term_value_name_sentence_case"})
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root3)
MERGE (term_ver_root3)-[hv2:HAS_VERSION]->(term_ver_value3)
MERGE (term_ver_root3)-[lf2:LATEST_FINAL]->(term_ver_value3)
set has_term3.order = 3
set lf2.change_description = "Approved version"
set lf2.start_date = datetime()
set lf2.status = "Final"
set lf2.user_initials = "TODO initials"
set lf2.version = "1.0"
set hv2.change_description = "Initial version"
set hv2.start_date = datetime()
set hv2.end_date = datetime()
set hv2.status = "Draft"
set hv2.user_initials = "TODO initials"
set hv2.version = "0.1"

MERGE (cr2)-[has_term4:HAS_TERM]->(term_root4:CTTermRoot {uid:"term_root_draft_non_edit"})-[:HAS_NAME_ROOT]->
    (term_ver_root4:CTTermNameRoot)-[:LATEST]-(term_ver_value4:CTTermNameValue 
        {name:"term_value_name4", name_sentence_case:"term_value_name_sentence_case"})
MERGE (term_ver_root4)-[ld2:LATEST_DRAFT]->(term_ver_value4)
MERGE (non_editable_lib)-[:CONTAINS_TERM]->(term_root4)
set has_term4.order = 4
set ld2.change_description = "latest draft"
set ld2.start_date = datetime()
set ld2.status = "Draft"
set ld2.user_initials = "TODO initials"
set ld2.version = "0.1"
"""

STARTUP_PARAMETERS_CYPHER = f"""
MERGE (intervention:TemplateParameter {{name: 'Intervention'}})
MERGE (pr1:TemplateParameterValueRoot {{uid: 'Intervention-99991'}})-[:LATEST_FINAL]->(:TemplateParameterValue {{name: 'human insulin'}})
MERGE (intervention)-[:HAS_VALUE]->(pr1)
MERGE (pr2:TemplateParameterValueRoot {{uid: 'Intervention-99992'}})-[:LATEST_FINAL]->(:TemplateParameterValue {{name: 'Metformin'}})
MERGE (intervention)-[:HAS_VALUE]->(pr2)

MERGE (indication:TemplateParameter {{name: 'Indication'}})
MERGE (pr3:TemplateParameterValueRoot {{uid: 'Indication-99991'}})-[:LATEST_FINAL]->(:TemplateParameterValue {{name: 'type 2 diabetes'}})
MERGE (indication)-[:HAS_VALUE]->(pr3)
MERGE (pr4:TemplateParameterValueRoot {{uid: 'Indication-99992'}})-[:LATEST_FINAL]->(:TemplateParameterValue {{name: 'coronary heart disease'}})
MERGE (indication)-[:HAS_VALUE]->(pr4)
MERGE (pr5:TemplateParameterValueRoot {{uid: 'Indication-99993'}})-[:LATEST_FINAL]->(:TemplateParameterValue {{name: 'breathing problems'}})
MERGE (indication)-[:HAS_VALUE]->(pr5)

//Study Endpoint
MERGE (endpoint:TemplateParameter {{name: '{STUDY_ENDPOINT_TP_NAME}'}})
"""

STARTUP_STUDY_FIELD_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
CREATE (p2:Project {description: "Description DEF", name: "Project DEF", project_number: "456", uid :"project_uid_2"})
CREATE (c)-[:HOLDS_PROJECT]->(p2)
"""

STARTUP_STUDY_PROTOCOL_TITLE_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "EudractId", value: "2019-123456-42"})
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "InvestigationalNewDrugApplicationNumberInd", value: "ind-number-777"})
MERGE (sv)-[:HAS_TEXT_FIELD]->(:StudyField:StudyTextField {field_name: "StudyShortTitle", value: "Study short title"})
MERGE (cp:ClinicalProgramme{uid: "ClinicalProgramme_000001"})
    SET cp.name="Test CP"
MERGE (p:Project{uid: "Project_000001"})
    SET p.description="description", p.name="name", p.project_number="project_number"
MERGE (cp)-[:HOLDS_PROJECT]->(p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)

// Compound
CREATE (cr:ConceptRoot:CompoundRoot:TemplateParameterValueRoot {uid : "TemplateParameter_000001"})
CREATE (cv:ConceptValue:CompoundValue:TemplateParameterValue {definition: "definition", is_sponsor_compound: true, is_name_inn: true, name: "name", user_initials: "user_initials"})
MERGE (cr)-[lat:LATEST]->(cv)
MERGE (cr)-[lf:LATEST_FINAL]->(cv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})-[:CONTAINS_CONCEPT]->(cr)
MERGE (n:TemplateParameter {name : "Compound"})-[:HAS_VALUE]->(cr)
set lf.change_description = "Approved version"
set lf.start_date = datetime()
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"

// Compound Alias
CREATE (car:ConceptRoot:CompoundAliasRoot:TemplateParameterValueRoot {uid : "TemplateParameter_000002"})
CREATE (cav:ConceptValue:CompoundAliasValue:TemplateParameterValue {definition: "definition", name: "name", user_initials: "user_initials"})
MERGE (car)-[lat1:LATEST]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
MERGE (cav)-[:IS_COMPOUND]->(cr)
MERGE (lib)-[:CONTAINS_CONCEPT]->(car)
MERGE (:TemplateParameter {name : "CompoundAlias"})-[:HAS_VALUE]->(car)
set lf1.change_description = "Approved version"
set lf1.start_date = datetime()
set lf1.status = "Final"
set lf1.user_initials = "TODO initials"
set lf1.version = "1.0"
MERGE (cav)-[:IS_COMPOUND]->(cr)

MERGE (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound:StudySelection)-[:HAS_SELECTED_COMPOUND]->(cav)
set sc.order = 1
set sc.uid = "StudyCompound_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(sc)
set sa.date = datetime()
set sa.user_initials = "TODO user initials"

WITH sc
MATCH (term_root:CTTermRoot {uid: "term_root_final"})
MERGE (sc)-[:HAS_TYPE_OF_TREATMENT]->(term_root)
"""

STARTUP_STUDY_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
SET ld.start_date=datetime("2021-09-27"), ld.status="DRAFT"
MERGE (sr)-[lv:HAS_VERSION]->(sv)
SET lv.start_date=datetime("2021-09-27"), lv.status="DRAFT"
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
"""

STARTUP_STUDY_OBJECTIVE_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (ot:ObjectiveTemplateRoot)-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue {name :"objective_1", name_plain : "objective_1"})
MERGE (ot2:ObjectiveTemplateRoot)-[relt2:LATEST_FINAL]->(otv2:ObjectiveTemplateValue {name :"objective_2", name_plain : "objective_2"})
MERGE (ot3:ObjectiveTemplateRoot)-[relt3:LATEST_FINAL]->(otv3:ObjectiveTemplateValue {name :"objective_3", name_plain : "objective_3"})
MERGE (ot4:ObjectiveTemplateRoot)-[relt4:LATEST_FINAL]->(otv4:ObjectiveTemplateValue {name :"objective_4", name_plain : "objective_4"})
MERGE (ot4)-[:LATEST]->(otv4)
MERGE (or:ObjectiveRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue {name :"objective_1", name_plain : "objective_1"})
MERGE (or)-[:HAS_VERSION]->(ov)
MERGE (or)-[:LATEST]->(ov)
MERGE (or2:ObjectiveRoot)-[rel2:LATEST_FINAL]->(ov2:ObjectiveValue {name :"objective_2", name_plain : "objective_2"})
MERGE (or2)-[:HAS_VERSION]->(ov2)
MERGE (or2)-[:LATEST]->(ov2)
MERGE (or3:ObjectiveRoot)-[rel3:LATEST_DRAFT]->(ov3:ObjectiveValue {name :"objective_3", name_plain : "objective_3"})
MERGE (or3)-[:HAS_VERSION]->(ov3)
MERGE (or3)-[:LATEST]->(ov3)
MERGE (or4:ObjectiveRoot)-[rel4:LATEST_RETIRED]->(ov4:ObjectiveValue {name :"objective_5", name_plain : "objective_5"})
MERGE (or4)-[:LATEST]->(ov4)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or) 
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (ot2)-[:HAS_OBJECTIVE]->(or2)
MERGE (ot3)-[:HAS_OBJECTIVE]->(or3)
MERGE (ot4)-[:HAS_OBJECTIVE]->(or4)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot4)
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or2)
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or3)
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or4)
set ot.editable_instance = False
set ot2.editable_instance = False
set ot3.editable_instance = False
set ot4.editable_instance = False
set relt.change_description="Approved version"
set relt.start_date= datetime()
set relt.status = "Final"
set relt.user_initials = "TODO Initials"
set relt.version = "1.0"
set relt2.change_description="Approved version"
set relt2.start_date= datetime()
set relt2.status = "Final"
set relt2.user_initials = "TODO Initials"
set relt2.version = "1.0"
set relt3.change_description="Approved version"
set relt3.start_date= datetime()
set relt3.status = "Final"
set relt3.user_initials = "TODO Initials"
set relt3.version = "1.0"
set relt4.change_description="Approved version"
set relt4.start_date= datetime()
set relt4.status = "Final"
set relt4.user_initials = "TODO Initials"
set relt4.version = "1.0"

set rel.change_description="Approved version"
set rel.start_date= datetime()
set rel.status = "Final"
set rel.user_initials = "TODO Initials"
set rel.version = "1.0"
set rel2.change_description="Approved version"
set rel2.start_date= datetime()
set rel2.status = "Final"
set rel2.user_initials = "TODO Initials"
set rel2.version = "1.0"
set rel3.change_description="Initial version"
set rel3.start_date= datetime()
set rel3.status = "Draft"
set rel3.user_initials = "TODO Initials"
set rel3.version = "0.1"

set rel4.change_description="Retired version"
set rel4.start_date= datetime()
set rel4.status = "Retired"
set rel4.user_initials = "TODO Initials"
set rel4.version = "1.0"
"""

STARTUP_STUDY_ENDPOINT_CYPHER = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
SET unit_final2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot)-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue {name :"objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot)
set ot.editable_instance = False
set relt = final_properties

set rel = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.user_initials = "TODO user initials"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot)-[endRelt:LATEST_FINAL]->(etv:EndpointTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot)-[endRel:LATEST_FINAL]->(ev:EndpointValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (lib)-[:CONTAINS_ENDPOINT]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et)
set et.editable_instance = False
set endRelt = final_properties
set endRel = final_properties

MERGE (et2:EndpointTemplateRoot)-[endRelt2:LATEST_FINAL]->(etv2:EndpointTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et2)
set et2.editable_instance = False
set endRelt2 = final_properties

MERGE (tt:TimeframeTemplateRoot)-[timRelt:LATEST_FINAL]->(ttv:TimeframeTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot)-[timRel:LATEST_FINAL]->(tv:TimeframeValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (lib)-[:CONTAINS_TIMEFRAME]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_TIMEFRAME_TEMPLATE]->(tt)
set tt.editable_instance = False
set timRelt = final_properties
set timRel = final_properties
WITH timRel

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1

MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"SDTM CT"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)
"""

STARTUP_STUDY_LIST_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot)-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (lib:Library{name:"Sponsor", is_editable:true})-[:CONTAINS_OBJECTIVE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot)
set ot.editable_instance = False
set relt.change_description="Approved version"
set relt.start_date= datetime()
set relt.status = "Final"
set relt.user_initials = "TODO Initials"
set relt.version = "1.0"

set rel.change_description="Approved version"
set rel.start_date= datetime()
set rel.status = "Final"
set rel.user_initials = "TODO Initials"
set rel.version = "1.0"

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.user_initials = "TODO user initials"


MERGE (et:EndpointTemplateRoot)-[endRelt:LATEST_FINAL]->(etv:EndpointTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot)-[endRel:LATEST_FINAL]->(ev:EndpointValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (lib)-[:CONTAINS_ENDPOINT]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et)
set et.editable_instance = False
set endRelt.change_description="Approved version"
set endRelt.start_date= datetime()
set endRelt.status = "Final"
set endRelt.user_initials = "TODO Initials"
set endRelt.version = "1.0"

set endRel.change_description="Approved version"
set endRel.start_date= datetime()
set endRel.status = "Final"
set endRel.user_initials = "TODO Initials"
set endRel.version = "1.0"

MERGE (sv)-[:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint:StudySelection)-[:HAS_SELECTED_ENDPOINT]->(ev)
set se.order = 1
set se.uid = "StudyEndpoint_000001"
CREATE (saa:StudyAction:Create)-[:AFTER]->(se)
set saa.date = datetime()
set saa.user_initials = "TODO user initials"

MERGE (cp:ClinicalProgramme{uid: "ClinicalProgramme_000001"})
    SET cp.name="Test CP"
MERGE (p:Project{uid: "Project_000001"})
    SET p.description="description", p.name="name", p.project_number="project_number"
MERGE (cp)-[:HOLDS_PROJECT]->(p)-[:HAS_FIELD]->(sf:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
"""

STARTUP_STUDY_COMPOUND_CYPHER = """
MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv

// Compound
CREATE (cr:ConceptRoot:CompoundRoot:TemplateParameterValueRoot {uid : "TemplateParameter_000001"})
CREATE (cv:ConceptValue:CompoundValue:TemplateParameterValue {definition: "definition", is_sponsor_compound: true, is_name_inn: true, name: "name", user_initials: "user_initials"})
MERGE (cr)-[lat:LATEST]->(cv)
MERGE (cr)-[lf:LATEST_FINAL]->(cv)
MERGE (cr)-[hvc:HAS_VERSION]->(cv)
MERGE (lib:Library{name:"Sponsor", is_editable:true})-[:CONTAINS_CONCEPT]->(cr)
MERGE (n:TemplateParameter {name : "Compound"})-[:HAS_VALUE]->(cr)
set lf.change_description = "Approved version"
set lf.start_date = datetime()
set lf.status = "Final"
set lf.user_initials = "TODO initials"
set lf.version = "1.0"
set hvc.change_description = "Initial version"
set hvc.start_date = datetime()
set hvc.end_date = datetime()
set hvc.status = "Draft"
set hvc.user_initials = "TODO initials"
set hvc.version = "0.1"

// Compound Alias
CREATE (car:ConceptRoot:CompoundAliasRoot:TemplateParameterValueRoot {uid : "TemplateParameter_000002"})
CREATE (cav:ConceptValue:CompoundAliasValue:TemplateParameterValue {definition: "definition", name: "name", user_initials: "user_initials"})
MERGE (car)-[lat1:LATEST]->(cav)
MERGE (car)-[lf1:LATEST_FINAL]->(cav)
MERGE (cav)-[:IS_COMPOUND]->(cr)
MERGE (lib)-[:CONTAINS_CONCEPT]->(car)
MERGE (:TemplateParameter {name : "CompoundAlias"})-[:HAS_VALUE]->(car)
set lf1.change_description = "Approved version"
set lf1.start_date = datetime()
set lf1.status = "Final"
set lf1.user_initials = "TODO initials"
set lf1.version = "1.0"

// Pharmaceutical dosage form
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000003"})
MERGE (cv)-[:HAS_DOSAGE_FORM]->(term_root)

// Route of administration
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000002"})
MERGE (cv)-[:HAS_ROUTE_OF_ADMINISTRATION]->(term_root)

// Delivery device
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000005"})
MERGE (cv)-[:HAS_DELIVERY_DEVICE]->(term_root)

// Dispenser
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "CTTerm_000004"})
MERGE (cv)-[:HAS_DISPENSER]->(term_root)

// Dose frequency
WITH (cv)
MATCH (term_root:CTTermRoot {uid: "dose_frequency_uid1"})
MERGE (cv)-[:HAS_DOSE_FREQUENCY]->(term_root)

// Strength
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_STRENGTH_VALUE]->(term_root)

// Half-life
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_HALF_LIFE]->(term_root)

// Dose value
WITH (cv)
MATCH (term_root:NumericValueWithUnitRoot {uid: "NumericValueWithUnit_000001"})
MERGE (cv)-[:HAS_DOSE_VALUE]->(term_root)

// Lag-time
// WITH (cv)
// MATCH (term_root:NumericValueWithUnitRoot {uid: "LagTime_000001"})
// MERGE (cv)-[:HAS_LAG_TIME]->(term_root)




"""

STARTUP_STUDY_COMPOUND_DOSING_CYPHER = """
MATCH (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
MATCH (est:CTTermRoot {uid: "ElementSubTypeTermUid_1"})
MERGE (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement:StudySelection)-[:HAS_ELEMENT_SUBTYPE]->(est)
set se.order = 1
set se.uid = "StudyElement_000001"
set se.name = "Element_Name_1"
set se.shortName = "Element_Short_Name_1"
set se.code = "Code1"
set se.description = "Description"
CREATE (sa1:StudyAction:Create)-[:AFTER]->(se)
set sa1.date = datetime()
set sa1.user_initials = "TODO user initials"

WITH sv
MATCH (cav:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot {uid: "TemplateParameter_000002"})
MERGE (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound:StudySelection)-[:HAS_SELECTED_COMPOUND]->(cav)
set sc.order = 1
set sc.uid = "StudyCompound_000001"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sc)
set sa2.date = datetime()
set sa2.user_initials = "TODO user initials"

WITH sc
MATCH (term_root:CTTermRoot {uid: "CTTerm_000001"})
MERGE (sc)-[:HAS_TYPE_OF_TREATMENT]->(term_root)
"""

STARTUP_STUDY_CRITERIA_CYPHER = """
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH p

MATCH (incl:CTTermRoot {uid: "C25532"}), (excl:CTTermRoot {uid: "C25370"})
MERGE (library:Library{name: "Sponsor", is_editable: True})
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:0})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (incl)<-[:HAS_TYPE]-(ctr1:CriteriaTemplateRoot {uid: "incl_criteria_1"})-[relt:LATEST_FINAL]->(ctv1:CriteriaTemplateValue {name : "incl_criteria_1", guidance_text: "Guidance text", name_plain : "incl_criteria_1"})
MERGE (incl)<-[:HAS_TYPE]-(ctr2:CriteriaTemplateRoot {uid: "incl_criteria_2"})-[relt2:LATEST_FINAL]->(ctv2:CriteriaTemplateValue {name : "incl_criteria_2", name_plain : "incl_criteria_2"})
MERGE (incl)<-[:HAS_TYPE]-(ctr3:CriteriaTemplateRoot {uid: "incl_criteria_3"})-[relt3:LATEST_FINAL]->(ctv3:CriteriaTemplateValue {name : "incl_criteria_3", name_plain : "incl_criteria_3"})
MERGE (incl)<-[:HAS_TYPE]-(ctr4:CriteriaTemplateRoot {uid: "incl_criteria_4"})-[relt4:LATEST_FINAL]->(ctv4:CriteriaTemplateValue {name : "incl_criteria_4", name_plain : "incl_criteria_4"})
MERGE (ctr1)-[:LATEST]->(ctv1)
MERGE (ctr2)-[:LATEST]->(ctv2)
MERGE (ctr3)-[:LATEST]->(ctv3)
MERGE (ctr4)-[:LATEST]->(ctv4)
set ctr1.editable_instance=False
set ctr2.editable_instance=False
set ctr3.editable_instance=False
set ctr4.editable_instance=False
set relt.change_description="Approved version"
set relt.start_date= datetime()
set relt.status = "Final"
set relt.user_initials = "TODO Initials"
set relt.version = "1.0"
set relt2.change_description="Approved version"
set relt2.start_date= datetime()
set relt2.status = "Final"
set relt2.user_initials = "TODO Initials"
set relt2.version = "1.0"
set relt3.change_description="Approved version"
set relt3.start_date= datetime()
set relt3.status = "Final"
set relt3.user_initials = "TODO Initials"
set relt3.version = "1.0"
set relt4.change_description="Approved version"
set relt4.start_date= datetime()
set relt4.status = "Final"
set relt4.user_initials = "TODO Initials"
set relt4.version = "1.0"
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr1)
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr2)
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr3)
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr4)
MERGE (excl)<-[:HAS_TYPE]-(ctr5:CriteriaTemplateRoot {uid: "excl_criteria_1"})-[relt5:LATEST_FINAL]->(ctv5:CriteriaTemplateValue {name :"excl_criteria_1", name_plain : "excl_criteria_1"})
MERGE (excl)<-[:HAS_TYPE]-(ctr6:CriteriaTemplateRoot {uid: "excl_criteria_2"})-[relt6:LATEST_FINAL]->(ctv6:CriteriaTemplateValue {name :"excl_criteria_2", name_plain : "excl_criteria_2"})
MERGE (ctr5)-[:LATEST]->(ctv5)
MERGE (ctr6)-[:LATEST]->(ctv6)
set ctr5.editable_instance=False
set ctr6.editable_instance=False
set relt5.change_description="Approved version"
set relt5.start_date= datetime()
set relt5.status = "Final"
set relt5.user_initials = "TODO Initials"
set relt5.version = "1.0"
set relt6.change_description="Approved version"
set relt6.start_date= datetime()
set relt6.status = "Final"
set relt6.user_initials = "TODO Initials"
set relt6.version = "1.0"
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr5)
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr6)
"""


STARTUP_STUDY_ACTIVITY_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue)
"""

STARTUP_SINGLE_STUDY_CYPHER = """
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv
"""

REMOVE_TRIGGERS = """
CALL apoc.trigger.removeAll();
"""

CREATE_BASE_TEMPLATE_PARAMETER_TREE = f"""
        // activity
        MERGE (activity:TemplateParameter {{name: "Activity"}})
        // activity sub group
        MERGE (activity_sub_group:TemplateParameter {{name: "ActivitySubGroup"}})
        // activity group
        MERGE (activity_group:TemplateParameter {{name: "ActivityGroup"}})
        // activity-instance
        MERGE (activity_instance:TemplateParameter {{name: "ActivityInstance"}})

        // reminders
        MERGE (reminder:TemplateParameter {{name: "Reminder"}})
        MERGE (reminder)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // interventions
        MERGE (interventions:TemplateParameter {{name: "Intervention"}})
        MERGE (interventions)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (compoundDosing:TemplateParameter {{name: "CompoundDosing"}})
        MERGE (compoundDosing)-[:HAS_PARENT_PARAMETER]->(interventions)
        MERGE (compoundAlias:TemplateParameter {{name: "CompoundAlias"}})
        MERGE (compoundAlias)-[:HAS_PARENT_PARAMETER]->(compoundDosing)
        
        // special-purposes
        MERGE (special_purposes:TemplateParameter {{name: "SpecialPurpose"}})
        MERGE (special_purposes)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        
        // findings
        MERGE (findings:TemplateParameter {{name: "Finding"}})
        MERGE (findings)-[:HAS_PARENT_PARAMETER]->(activity_instance)
        MERGE (categoricFinding:TemplateParameter {{name: "CategoricFinding"}})
        MERGE (categoricFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (ratingScale:TemplateParameter {{name: "RatingScale"}})
        MERGE (ratingScale)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (laboratoryActivity:TemplateParameter {{name: "LaboratoryActivity"}})
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(categoricFinding)
        MERGE (numericFinding:TemplateParameter {{name: "NumericFinding"}})
        MERGE (numericFinding)-[:HAS_PARENT_PARAMETER]->(findings)
        MERGE (laboratoryActivity)-[:HAS_PARENT_PARAMETER]->(numericFinding)
        MERGE (textualFinding:TemplateParameter {{name: "TextualFinding"}})
        MERGE (textualFinding)-[:HAS_PARENT_PARAMETER]->(findings)

        // events
        MERGE (events:TemplateParameter {{name: "Event"}})
        MERGE (events)-[:HAS_PARENT_PARAMETER]->(activity_instance)

        //simple concepts
        MERGE (simple_concepts:TemplateParameter {{name:"SimpleConcept"}})
        MERGE (numeric_values:TemplateParameter {{name:"NumericValue"}})
        MERGE (numeric_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (numeric_value_with_unit:TemplateParameter {{name:"NumericValueWithUnit"}})
        MERGE (numeric_value_with_unit)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (text_values:TemplateParameter {{name:"TextValue"}})
        MERGE (text_values)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (visit_names:TemplateParameter {{name:"VisitName"}})
        MERGE (visit_names)-[:HAS_PARENT_PARAMETER]->(text_values)
        MERGE (study_days:TemplateParameter {{name:"StudyDay"}})
        MERGE (study_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_weeks:TemplateParameter {{name:"StudyWeek"}})
        MERGE (study_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_days:TemplateParameter {{name:"StudyDurationDays"}})
        MERGE (study_duration_days)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (study_duration_weeks:TemplateParameter {{name:"StudyDurationWeeks"}})
        MERGE (study_duration_weeks)-[:HAS_PARENT_PARAMETER]->(numeric_values)
        MERGE (time_points:TemplateParameter {{name:"TimePoint"}})
        MERGE (time_points)-[:HAS_PARENT_PARAMETER]->(simple_concepts)
        MERGE (lag_time:TemplateParameter {{name:"LagTime"}})
        MERGE (lag_time)-[:HAS_PARENT_PARAMETER]->(numeric_values)

        //Study Endpoint
        MERGE (endpoint:TemplateParameter {{name: '{STUDY_ENDPOINT_TP_NAME}'}})
"""

CREATE_NA_TEMPLATE_PARAMETER = """
   MERGE (r:TemplateParameterValueRoot{uid: "NA"})
    WITH r
    OPTIONAL MATCH (r)-[x:HAS_VERSION|LATEST|LATEST_FINAL]->()
    DELETE x
    WITH r
    MERGE (r)-[:LATEST]->(v:TemplateParameterValue{name: "NA"})
    MERGE (r)-[:LATEST_FINAL{change_description: "initial version", start_date: datetime(), end_date: datetime(), status: "Final", user_initials: "import-procedure", version: "1.0"}]->(v)
    MERGE (r)-[:HAS_VERSION{change_description: "initial version", start_date: datetime(), end_date: datetime(), status: "Final", user_initials: "import-procedure", version: "1.0"}]->(v)
    WITH r
    MATCH (n:TemplateParameter) 
    MERGE (n)-[:HAS_VALUE]->(r)
    """


def get_codelist_with_term_cypher(
    name: str,
    codelist_name: str = "tp_codelist_name_value",
    codelist_uid: str = "ct_codelist_root1",
    term_uid: str = "term_root_final",
) -> str:
    return """
WITH {
  change_description: "Approved version",
  start_date: datetime("2020-06-26T00:00:00"),
  status: "Final",
  user_initials: "TODO initials",
  version: "1.0"
} AS final_version_props
MERGE (clr:CTCodelistRoot {uid: "%(codelist_uid)s"})
MERGE (clr)-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "%(codelist_name)s"})
MERGE (cc:CTCatalogue {name: "SDTM CT"})-[:HAS_CODELIST]->(clr)
MERGE (cnr)-[cl_lf:LATEST_FINAL]->(cnv)
set cl_lf = final_version_props
MERGE (lib:Library {name: "Sponsor", is_editable: true})
MERGE (lib)-[:CONTAINS_CODELIST]->(clr)

MERGE (clr)-[has_term1:HAS_TERM]->(term_root:CTTermRoot {uid:"%(term_uid)s"})-[:HAS_ATTRIBUTES_ROOT]->
    (term_ver_root:CTTermAttributesRoot)-[:LATEST]-(term_ver_value:CTTermAttributesValue
        {code_submission_value: "code_submission_value1", name_submission_value:"name_submission_value1",
        preferred_term:"preferred_term", definition:"definition"})
MERGE (term_root)-[:HAS_NAME_ROOT]->(term_name_ver_root:CTTermNameRoot)-[:LATEST]-(term_name_ver_value:CTTermNameValue
        {name: "%(name)s", name_sentence_case:"term_value_name_sentence_case"})
MERGE (lib)-[:CONTAINS_TERM]->(term_root)
MERGE (term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value)
set lf = final_version_props
MERGE (term_name_ver_root)-[tnvr_lf:LATEST_FINAL]->(term_name_ver_value)
set tnvr_lf = final_version_props
""" % {
        "name": name,
        "codelist_name": codelist_name,
        "codelist_uid": codelist_uid,
        "term_uid": term_uid,
    }


STARTUP_STUDY_ARM_CYPHER = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
SET unit_final2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot)-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot)
set ot.editable_instance = False
set relt = final_properties

set rel = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.user_initials = "TODO user initials"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot)-[endRelt:LATEST_FINAL]->(etv:EndpointTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot)-[endRel:LATEST_FINAL]->(ev:EndpointValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (lib)-[:CONTAINS_ENDPOINT]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et)
set et.editable_instance = False
set endRelt = final_properties
set endRel = final_properties

MERGE (et2:EndpointTemplateRoot)-[endRelt2:LATEST_FINAL]->(etv2:EndpointTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et2)
set et2.editable_instance = False
set endRelt2 = final_properties

MERGE (tt:TimeframeTemplateRoot)-[timRelt:LATEST_FINAL]->(ttv:TimeframeTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot)-[timRel:LATEST_FINAL]->(tv:TimeframeValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (lib)-[:CONTAINS_TIMEFRAME]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_TIMEFRAME_TEMPLATE]->(tt)
set tt.editable_instance = False
set timRelt = final_properties
set timRel = final_properties
WITH timRel

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1

MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"SDTM CT"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)
"""


STARTUP_STUDY_ELEMENT_CYPHER = """
WITH {
change_description: "Approved version",
start_date: datetime(),
status: "Final",
user_initials: "TODO initials",
version: "1.0"
} AS final_properties

MERGE (l:Library {name:"CDISC", is_editable:false})
MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"catalogue_name"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"
MERGE (p:Project)
SET p.description = "Description ABC",
    p.name = "Project ABC",
    p.project_number = "123",
    p.uid = "project_uid"
CREATE (c)-[:HOLDS_PROJECT]->(p)
WITH final_properties, p

MERGE (unit_def_root:ConceptRoot:UnitDefinitionRoot {uid:"unit 1"})-[:LATEST]-(unit_def_value:ConceptValue:UnitDefinitionValue {name:"name 1"})
MERGE (unit_def_root)-[unit_final1:LATEST_FINAL]-(unit_def_value)
SET unit_final1 = final_properties
MERGE (unit_def_root2:ConceptRoot:UnitDefinitionRoot {uid:"unit 2"})-[:LATEST]-(unit_def_value2:ConceptValue:UnitDefinitionValue {name:"name 2"})
MERGE (unit_def_root2)-[unit_final2:LATEST_FINAL]-(unit_def_value2)
SET unit_final2 = final_properties
MERGE (sr:StudyRoot {uid: "study_root"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id", study_number:"0"})
MERGE (p)-[:HAS_FIELD]->(:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "TODO Initials"
set ld = hv

MERGE (ot:ObjectiveTemplateRoot)-[relt:LATEST_FINAL]->(otv:ObjectiveTemplateValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or:ObjectiveRoot)-[rel:LATEST_FINAL]->(ov:ObjectiveValue {name : "objective_1", name_plain : "objective_1"})
MERGE (or)-[:LATEST]->(ov)
MERGE (lib:Library{name:"Sponsor", is_editable:true})
MERGE (lib)-[:CONTAINS_OBJECTIVE]->(or)
MERGE (ot)-[:HAS_OBJECTIVE]->(or)
MERGE (lib)-[:CONTAINS_OBJECTIVE_TEMPLATE]->(ot)
set ot.editable_instance = False
set relt = final_properties

set rel = final_properties

MERGE (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective:StudySelection)-[:HAS_SELECTED_OBJECTIVE]->(ov)
set so.order = 1
set so.uid = "StudyObjective_000001"
CREATE (sa:StudyAction:Create)-[:AFTER]->(so)
set sa.date = datetime()
set sa.user_initials = "TODO user initials"

// Set counter for study objective UID 
MERGE (:Counter:StudyObjectiveCounter {count: 1, counterId:'StudyObjectiveCounter'})

MERGE (et:EndpointTemplateRoot)-[endRelt:LATEST_FINAL]->(etv:EndpointTemplateValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er:EndpointRoot)-[endRel:LATEST_FINAL]->(ev:EndpointValue {name : "endpoint_1", name_plain : "endpoint_1"})
MERGE (er)-[:LATEST]->(ev)
MERGE (et)-[:LATEST]->(etv)
MERGE (lib)-[:CONTAINS_ENDPOINT]->(er)
MERGE (et)-[:HAS_ENDPOINT]->(er)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et)
set et.editable_instance = False
set endRelt = final_properties
set endRel = final_properties

MERGE (et2:EndpointTemplateRoot)-[endRelt2:LATEST_FINAL]->(etv2:EndpointTemplateValue {name : "endpoint_template_2", name_plain : "endpoint_template_2"})
MERGE (et2)-[:LATEST]->(etv2)
MERGE (lib)-[:CONTAINS_ENDPOINT_TEMPLATE]->(et2)
set et2.editable_instance = False
set endRelt2 = final_properties

MERGE (tt:TimeframeTemplateRoot)-[timRelt:LATEST_FINAL]->(ttv:TimeframeTemplateValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr:TimeframeRoot)-[timRel:LATEST_FINAL]->(tv:TimeframeValue {name : "timeframe_1", name_plain : "timeframe_1"})
MERGE (tr)-[:LATEST]->(tv)
MERGE (tt)-[:LATEST]->(ttv)
MERGE (lib)-[:CONTAINS_TIMEFRAME]->(tr)
MERGE (tt)-[:HAS_TIMEFRAME]->(tr)
MERGE (lib)-[:CONTAINS_TIMEFRAME_TEMPLATE]->(tt)
set tt.editable_instance = False
set timRelt = final_properties
set timRel = final_properties
WITH timRel

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MERGE (termroot)<-[has_term:HAS_TERM]-(codelistroot:CTCodelistRoot {uid: "ct_codelist_root_endpoint"})-[:HAS_NAME_ROOT]->(cnr:CTCodelistNameRoot)-[:LATEST_FINAL]->
    (cnv:TemplateParameter:CTCodelistNameValue {name: "Endpoint Level"})
set has_term.order = 1

MERGE (catalogue:CTCatalogue {uid:"CTCatalogue_000001", name:"SDTM CT"})
MERGE (catalogue)-[:HAS_CODELIST]->(codelistroot)
"""


STARTUP_STUDY_BRANCH_ARM_CYPHER = """
MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000001"})
set sar.order = 1
set sar.name = "StudyArm_000001"
set sar.short_name = "StudyArm_000001"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sar)
set sa2.date = datetime()
set sa2.user_initials = "TODO user initials"
MERGE (sr)-[:AUDIT_TRAIL]->(sa2)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 1, counterId:'StudyArmCounter'})

WITH sv

MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MATCH (sar:StudyArm {uid:"StudyArm_000001"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

WITH sv


MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000002"})
set sar.order = 2
set sar.name = "StudyArm_000002"
set sar.short_name = "StudyArm_000002"
CREATE (sa2:StudyAction:Create)-[:AFTER]->(sar)
set sa2.date = datetime()
set sa2.user_initials = "TODO user initials"
MERGE (sr)-[:AUDIT_TRAIL]->(sa2)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 2, counterId:'StudyArmCounter2'})

WITH sv
MATCH (termroot:CTTermRoot {uid:"term_root_final_non_edit"})
MATCH (sar:StudyArm {uid:"StudyArm_000002"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

WITH sv

MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)
MERGE (sv)-[:HAS_STUDY_ARM]->(sar:StudyArm:StudySelection{uid : "StudyArm_000003"})
set sar.order = 3
set sar.name = "StudyArm_000003"
set sar.short_name = "StudyArm_000003"
CREATE (sa3:StudyAction:Create)-[:AFTER]->(sar)
set sa3.date = datetime()
set sa3.user_initials = "TODO user initials"
MERGE (sr)-[:AUDIT_TRAIL]->(sa3)
// Set counter for study arm UID 
MERGE (:Counter:StudyArmCounter {count: 3, counterId:'StudyArmCounter3'})

WITH sv
MATCH (termroot:CTTermRoot {uid:"term_root_final"})
MATCH (sar:StudyArm {uid:"StudyArm_000003"})
CREATE (sar)-[:HAS_ARM_TYPE]->(termroot)

"""

STARTUP_PROJECTS_CYPHER = """
MERGE (c:ClinicalProgramme)
SET c.name = "CP",
    c.uid = "cp_001"

CREATE (p1:Project)
SET p1.name = "Project 1",
    p1.description = "Description 1",
    p1.project_number = "PRJ-001",
    p1.uid = "project_uid1"
CREATE (c)-[:HOLDS_PROJECT]->(p1)

CREATE (p2:Project)
SET p2.name = "Project 2",
    p2.description = "Description 2",
    p2.project_number = "PRJ-002",
    p2.uid = "project_uid2"
CREATE (c)-[:HOLDS_PROJECT]->(p2)
"""


def get_path(path):
    if "{uid}" in path:
        path.replace("{uid}", "1234")
    return path


def is_specific(path):
    if any(
        x in path
        for x in (
            "{uid}",
            "{cataloguename}",
            "{codelistuid}",
            "{termuid}",
            "{study_number}",
        )
    ):
        return True
    return False


def create_stub(path, methods):
    if is_specific(path):
        patel = path.split("/")
        path = path.replace("{codelistuid}", "1")
        path = path.replace("{cataloguename}", "1")
        path = path.replace("{termuid}", "1")
        path = path.replace("{study_number}", "1")
        if patel[-1] != "{uid}":
            pass
        retval = {
            "id": 1,
            "path_spec": path,
            "path_ready": path.replace("{uid}", "1"),
            "is_specific": True,
            "methods": methods,
        }
    else:
        retval = {"path_ready": path, "is_specific": False, "methods": methods}
    prefix = path.split("/")[1]
    retval["data"] = DATA_MAP.get(prefix, {})
    return retval


def create_paths():
    from clinical_mdr_api.main import app

    return _create_paths(app)


def _create_paths(app: FastAPI, path_prefix="") -> List[Dict[str, any]]:
    paths = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            st = create_stub(path_prefix + route.path, route.methods)
            paths.append(st)
        elif isinstance(route, Mount):
            paths += _create_paths(route.app, route.path)
    return paths


def inject_base_data() -> Study:
    """
    The data included as generic base data is the following
    - names specified below
    * Clinical Programme - ClinicalProgramme
    * Project - Project
    * Study - study_root
    * Libraries :
        * CDISC - non editable
        * Sponsor - editable
        * SNOMED - editable
    * Catalogues :
        * SDTM CT
    Returns created Study object
    """

    # Inject generic base data
    ## Parent objects for study
    clinical_programme = TestUtils.create_clinical_programme(name="CP")
    project = TestUtils.create_project(
        name="Project ABC",
        project_number="123",
        description="Base project",
        clinical_programme_uid=clinical_programme.uid,
    )

    ## Libraries
    TestUtils.create_library("CDISC", True)
    TestUtils.create_library("Sponsor", True)
    TestUtils.create_library("SNOMED", True)
    with db.write_transaction:
        sdtm = CTCatalogue(name="SDTM CT").save()
        cdisc = Library.nodes.get(name="CDISC")
        sdtm.contains_catalogue.connect(cdisc)

    ## Study snapshot definition
    ## It needs CDISC Library and SDTM CT catalogue
    initialize_study_field_config()

    ## Study
    study = TestUtils.create_study("123", "study_root", project.projectNumber)

    # TODO : Add optionally callable methods to add other data, for instance
    ## CT data
    ### Random codelists
    ### Random terms
    ### Random dict
    ## Syntax templates

    return study


def initialize_study_field_config():
    config_service = CTConfigService(
        user_id="TEST_IMPORT", meta_repository=MetaRepository()
    )
    with open(DEFAULT_STUDY_FIELD_CONFIG_FILE, encoding="UTF-8") as f:
        r = csv.DictReader(f)
        for line in r:
            data = camel_case_data(line)
            if data.get("configuredCodelistUid") != "":
                db.cypher_query(
                    """
                MATCH (library:Library {name:"CDISC"})
                MATCH (catalogue:CTCatalogue {name:"SDTM CT"})
                CREATE (library)-[:CONTAINS_CODELIST]->(codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                (codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue {
                name: $uid + 'name',
                name_sentence_case: $uid + 'name'})
                CREATE (codelist_ver_root)-[:LATEST_FINAL {
                version:"1.0",
                status:"Final",
                change_description:"test",
                user_initials:"test",
                start_date:datetime()}]->(codelist_ver_value)
                CREATE (catalogue)-[:HAS_CODELIST]->(codelist_root)
                """,
                    {"uid": data.get("configuredCodelistUid")},
                )
            elif data.get("configuredTermUid") != "":
                db.cypher_query(
                    """
                MATCH (library:Library {name:"CDISC"})
                MATCH (catalogue:CTCatalogue {name:"SDTM CT"})
                // common codelist for all terms that we create for tests
                MERGE (codelist_root:CTCodelistRoot{uid:"CTCodelist_Config"})
                CREATE (library)-[:CONTAINS_TERM]->(term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->
                (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue {
                name: $uid + 'name',
                name_sentence_case: $uid + 'name'})
                CREATE (term_ver_root)-[:LATEST_FINAL {
                version:"1.0",
                status:"Final",
                change_description:"test",
                user_initials:"test",
                start_date:datetime()}]->(term_ver_value)
                CREATE (codelist_root)-[:HAS_TERM]->(term_root)
                MERGE (catalogue)-[:HAS_CODELIST]->(codelist_root)
                """,
                    {"uid": data.get("configuredTermUid")},
                )
            ct_config_post_input = CTConfigPostInput(**data)
            config_service.post(ct_config_post_input)
