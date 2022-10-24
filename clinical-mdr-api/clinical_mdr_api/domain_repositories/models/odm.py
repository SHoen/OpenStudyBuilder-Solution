from neomodel import (
    BooleanProperty,
    DateProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
)

from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)


class OdmDescriptionValue(ConceptValue):
    language = StringProperty()
    description = StringProperty()
    instruction = StringProperty()
    sponsor_instruction = StringProperty()


class OdmDescriptionRoot(ConceptRoot):
    has_form = RelationshipFrom("OdmFormRoot", "HAS_DESCRIPTION")
    has_item_group = RelationshipFrom("OdmItemGroupRoot", "HAS_DESCRIPTION")
    has_item = RelationshipFrom("OdmItemRoot", "HAS_DESCRIPTION")
    has_condition = RelationshipFrom("OdmConditionRoot", "HAS_DESCRIPTION")
    has_method = RelationshipFrom("OdmMethodRoot", "HAS_DESCRIPTION")
    has_version = RelationshipTo(
        OdmDescriptionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmDescriptionValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmDescriptionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmDescriptionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmDescriptionValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmAliasValue(ConceptValue):
    context = StringProperty()


class OdmAliasRoot(ConceptRoot):
    has_condition = RelationshipFrom("OdmConditionRoot", "HAS_ALIAS")
    has_method = RelationshipFrom("OdmMethodRoot", "HAS_ALIAS")
    has_form = RelationshipFrom("OdmFormRoot", "HAS_ALIAS")
    has_item_group = RelationshipFrom("OdmItemGroupRoot", "HAS_ALIAS")
    has_item = RelationshipFrom("OdmItemRoot", "HAS_ALIAS")
    has_version = RelationshipTo(
        OdmAliasValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmAliasValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmAliasValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmAliasValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmAliasValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmConditionValue(ConceptValue):
    oid = StringProperty()


class OdmConditionRoot(ConceptRoot):
    has_formal_expression = RelationshipTo(
        "OdmFormalExpressionRoot", "HAS_FORMAL_EXPRESSION"
    )
    has_description = RelationshipTo(OdmDescriptionRoot, "HAS_DESCRIPTION")
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS")
    has_version = RelationshipTo(
        OdmConditionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmConditionValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmConditionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmConditionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmConditionValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmMethodValue(ConceptValue):
    oid = StringProperty()
    type = StringProperty()


class OdmMethodRoot(ConceptRoot):
    has_formal_expression = RelationshipTo(
        "OdmFormalExpressionRoot", "HAS_FORMAL_EXPRESSION"
    )
    has_description = RelationshipTo(OdmDescriptionRoot, "HAS_DESCRIPTION")
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS")
    has_version = RelationshipTo(
        OdmMethodValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmMethodValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmMethodValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmMethodValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmMethodValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmFormalExpressionValue(ConceptValue):
    context = StringProperty()
    expression = StringProperty()


class OdmFormalExpressionRoot(ConceptRoot):
    has_condition = RelationshipFrom(OdmConditionRoot, "HAS_FORMAL_EXPRESSION")
    has_method = RelationshipFrom(OdmMethodRoot, "HAS_FORMAL_EXPRESSION")
    has_version = RelationshipTo(
        OdmFormalExpressionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmFormalExpressionValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmItemGroupRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    locked = BooleanProperty()
    collection_exception_condition_oid = StringProperty()


class OdmXmlExtensionRelation(ClinicalMdrRel):
    value = StringProperty()


class OdmFormValue(ConceptValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    sdtm_version = StringProperty()


class OdmFormRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    locked = BooleanProperty()
    collection_exception_condition_oid = StringProperty()


class OdmFormRoot(ConceptRoot):
    form_ref = RelationshipFrom("OdmTemplateRoot", "FORM_REF", model=OdmFormRefRelation)
    has_scope = RelationshipTo(CTTermRoot, "HAS_SCOPE")
    has_description = RelationshipTo(OdmDescriptionRoot, "HAS_DESCRIPTION")
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    item_group_ref = RelationshipTo(
        "OdmItemGroupRoot", "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    has_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    has_xml_extension_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    has_xml_extension_tag_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_TAG_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    # TODO targets_data_model = RelationshipTo(DataModelRoot, "TARGETS_DATA_MODEL")

    has_version = RelationshipTo(OdmFormValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmFormValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmFormValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmFormValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmFormValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmItemRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    data_entry_required = BooleanProperty()
    sdv = BooleanProperty()
    locked = BooleanProperty()
    key_sequence = StringProperty()
    method_oid = StringProperty()
    imputation_method_oid = StringProperty()
    role = StringProperty()
    role_codelist_oid = StringProperty()
    collection_exception_condition_oid = StringProperty()


class OdmItemGroupValue(ConceptValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    is_reference_data = BooleanProperty()
    sas_dataset_name = StringProperty()
    origin = StringProperty()
    purpose = StringProperty()
    locked = BooleanProperty()
    comment = StringProperty()


class OdmItemGroupRoot(ConceptRoot):
    has_description = RelationshipTo(OdmDescriptionRoot, "HAS_DESCRIPTION")
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS")
    has_sdtm_domain = RelationshipTo(CTTermRoot, "HAS_SDTM_DOMAIN")
    has_activity_sub_group = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUB_GROUP"
    )
    item_group_ref = RelationshipFrom(
        OdmFormRoot, "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    item_ref = RelationshipTo("OdmItemRoot", "ITEM_REF", model=OdmItemRefRelation)
    has_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    has_xml_extension_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    has_xml_extension_tag_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_TAG_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    # TODO targets_data_model = RelationshipTo(DataModelRoot, "TARGETS_DATA_MODEL")

    has_version = RelationshipTo(
        OdmItemGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmItemGroupValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmItemGroupValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmItemGroupValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmItemGroupValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmItemTermRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()


class OdmItemUnitDefinitionRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()


class OdmItemValue(ConceptValue):
    oid = StringProperty()
    prompt = StringProperty()
    datatype = StringProperty()
    length = IntegerProperty()
    significant_digits = IntegerProperty()
    sas_field_name = StringProperty()
    sds_var_name = StringProperty()
    origin = StringProperty()
    comment = StringProperty()


class OdmItemRoot(ConceptRoot):
    has_description = RelationshipTo(OdmDescriptionRoot, "HAS_DESCRIPTION")
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS")
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=OdmItemUnitDefinitionRelationship,
    )
    has_codelist = RelationshipTo(CTCodelistRoot, "HAS_CODELIST")
    has_codelist_term = RelationshipTo(
        CTTermRoot, "HAS_CODELIST_TERM", model=OdmItemTermRelationship
    )
    item_ref = RelationshipFrom(OdmItemGroupRoot, "ITEM_REF", model=OdmItemRefRelation)
    has_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    has_xml_extension_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    has_xml_extension_tag_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_TAG_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )

    has_version = RelationshipTo(OdmItemValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmItemValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmItemValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmItemValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmItemValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmTemplateValue(ConceptValue):
    oid = StringProperty()
    effective_date = DateProperty()
    retired_date = DateProperty()
    description = StringProperty()


class OdmTemplateRoot(ConceptRoot):
    form_ref = RelationshipTo(OdmFormRoot, "FORM_REF", model=OdmFormRefRelation)
    has_version = RelationshipTo(
        OdmTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmTemplateValue, "LATEST")

    latest_draft = RelationshipTo(
        OdmTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmXmlExtensionValue(ConceptValue):
    prefix = StringProperty()
    namespace = StringProperty()


class OdmXmlExtensionRoot(ConceptRoot):
    has_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot",
        "HAS_XML_EXTENSION_TAG",
    )
    has_xml_extension_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot",
        "HAS_XML_EXTENSION_ATTRIBUTE",
    )

    has_version = RelationshipTo(
        OdmXmlExtensionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmXmlExtensionValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmXmlExtensionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmXmlExtensionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmXmlExtensionValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmXmlExtensionAttributeValue(ConceptValue):
    ...


class OdmXmlExtensionAttributeRoot(ConceptRoot):
    belongs_to_xml_extension = RelationshipFrom(
        "OdmXmlExtensionRoot", "HAS_XML_EXTENSION_ATTRIBUTE"
    )
    belongs_to_xml_extension_tag = RelationshipFrom(
        "OdmXmlExtensionTagRoot", "HAS_XML_EXTENSION_ATTRIBUTE"
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormRoot", "HAS_XML_EXTENSION_ATTRIBUTE", model=OdmXmlExtensionRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_XML_EXTENSION_ATTRIBUTE", model=OdmXmlExtensionRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemRoot", "HAS_XML_EXTENSION_ATTRIBUTE", model=OdmXmlExtensionRelation
    )
    belongs_to_tag_form = RelationshipFrom(
        "OdmFormRoot", "HAS_XML_EXTENSION_TAG_ATTRIBUTE", model=OdmXmlExtensionRelation
    )
    belongs_to_tag_item_group = RelationshipFrom(
        "OdmItemGroupRoot",
        "HAS_XML_EXTENSION_TAG_ATTRIBUTE",
        model=OdmXmlExtensionRelation,
    )
    belongs_to_tag_item = RelationshipFrom(
        "OdmItemRoot", "HAS_XML_EXTENSION_TAG_ATTRIBUTE", model=OdmXmlExtensionRelation
    )
    has_parent_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot", "HAS_PARENT_XML_EXTENSION_ATTRIBUTE"
    )

    has_version = RelationshipTo(
        OdmXmlExtensionAttributeValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmXmlExtensionAttributeValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmXmlExtensionAttributeValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmXmlExtensionAttributeValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmXmlExtensionAttributeValue, "LATEST_RETIRED", model=VersionRelationship
    )


class OdmXmlExtensionTagValue(ConceptValue):
    ...


class OdmXmlExtensionTagRoot(ConceptRoot):
    belongs_to_xml_extension = RelationshipFrom(
        "OdmXmlExtensionRoot", "HAS_XML_EXTENSION_TAG"
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemRoot", "HAS_XML_EXTENSION_TAG", model=OdmXmlExtensionRelation
    )
    has_parent_xml_extension_tag = RelationshipTo(
        "OdmXmlExtensionTagRoot", "HAS_PARENT_XML_EXTENSION_TAG"
    )
    has_child_xml_extension_tag = RelationshipFrom(
        "OdmXmlExtensionTagRoot", "HAS_PARENT_XML_EXTENSION_TAG"
    )
    has_xml_extension_attribute = RelationshipTo(
        "OdmXmlExtensionAttributeRoot", "HAS_XML_EXTENSION_ATTRIBUTE"
    )

    has_version = RelationshipTo(
        OdmXmlExtensionTagValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmXmlExtensionTagValue, "LATEST")
    latest_draft = RelationshipTo(
        OdmXmlExtensionTagValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        OdmXmlExtensionTagValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        OdmXmlExtensionTagValue, "LATEST_RETIRED", model=VersionRelationship
    )
