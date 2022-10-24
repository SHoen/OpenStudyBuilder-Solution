from typing import Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.item import (
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
    OdmItemVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmAliasRoot,
    OdmDescriptionRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmItemValue,
)
from clinical_mdr_api.models import OdmItem


class ItemRepository(OdmGenericRepository[OdmItemAR]):
    root_class = OdmItemRoot
    value_class = OdmItemValue
    return_model = OdmItem

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmItemAR:
        return OdmItemAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmItemVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                prompt=value.prompt,
                datatype=value.datatype,
                length=value.length,
                significant_digits=value.significant_digits,
                sas_field_name=value.sas_field_name,
                sds_var_name=value.sds_var_name,
                origin=value.origin,
                comment=value.comment,
                description_uids=[
                    description.uid for description in root.has_description.all()
                ],
                alias_uids=[alias.uid for alias in root.has_alias.all()],
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in root.has_unit_definition.all()
                ],
                codelist_uid=root.has_codelist.get_or_none().uid
                if root.has_codelist.get_or_none()
                else None,
                term_uids=[term.uid for term in root.has_codelist_term.all()],
                activity_uids=[activity.uid for activity in root.has_activity.all()],
                xml_extension_tag_uids=[
                    xml_extension_tag.uid
                    for xml_extension_tag in root.has_xml_extension_tag.all()
                ],
                xml_extension_attribute_uids=[
                    xml_extension_attribute.uid
                    for xml_extension_attribute in root.has_xml_extension_attribute.all()
                ],
                xml_extension_tag_attribute_uids=[
                    xml_extension_tag_attribute.uid
                    for xml_extension_tag_attribute in root.has_xml_extension_tag_attribute.all()
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        major, minor = input_dict.get("version").split(".")
        odm_item_ar = OdmItemAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmItemVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict.get("name"),
                prompt=input_dict.get("prompt"),
                datatype=input_dict.get("datatype"),
                length=input_dict.get("length"),
                significant_digits=input_dict.get("significantDigits"),
                sas_field_name=input_dict.get("sasFieldName"),
                sds_var_name=input_dict.get("sdsVarName"),
                origin=input_dict.get("origin"),
                comment=input_dict.get("comment"),
                description_uids=input_dict.get("descriptionUids"),
                alias_uids=input_dict.get("aliasUids"),
                unit_definition_uids=input_dict.get("unitDefinitionUids"),
                codelist_uid=input_dict.get("codelistUid"),
                term_uids=input_dict.get("termUids"),
                activity_uids=input_dict.get("activityUids"),
                xml_extension_tag_uids=input_dict.get("xmlExtensionTagUids"),
                xml_extension_attribute_uids=input_dict.get(
                    "xmlExtensionAttributeUids"
                ),
                xml_extension_tag_attribute_uids=input_dict.get(
                    "xmlExtensionTagAttributeUids"
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("changeDescription"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("userInitials"),
                start_date=convert_to_datetime(value=input_dict.get("startDate")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_item_ar

    def specific_alias_clause(self, only_specific_status: list = None) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,
        concept_value.oid as oid,
        concept_value.prompt as prompt,
        concept_value.datatype as datatype,
        concept_value.length as length,
        concept_value.significant_digits as significantDigits,
        concept_value.sas_field_name as sasFieldName,
        concept_value.sds_var_name as sdsVarName,
        concept_value.origin as origin,
        concept_value.comment as comment,

        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[:HAS_DESCRIPTION]->(dr:OdmDescriptionRoot)-[:LATEST]->(dv:OdmDescriptionValue) | {{uid: dr.uid, name: dv.name, language: dv.language, description: dv.description, instruction: dv.instruction}}] AS descriptions,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[:HAS_ALIAS]->(ar:OdmAliasRoot)-[:LATEST]->(av:OdmAliasValue) | {{uid: ar.uid, name: av.name, context: av.context}}] AS aliases,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[hud:HAS_UNIT_DEFINITION]->(udr:UnitDefinitionRoot)-[:LATEST]->(udv:UnitDefinitionValue) | {{uid: udr.uid, name: udv.name, mandatory: hud.mandatory, order: hud.order}}] AS unitDefinitions,
        head([(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[:HAS_CODELIST]->(ctcr:CTCodelistRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTCodelistAttributesRoot)-[:LATEST]->(ctcav:CTCodelistAttributesValue) | ctcr.uid]) AS codelistUid,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[hct:HAS_CODELIST_TERM]->(cttr:CTTermRoot)-[:HAS_NAME_ROOT]->(cttnr:CTTermNameRoot)-[:LATEST]->(cttnv:CTTermNameValue) | {{uid: cttr.uid, name: cttnv.name, mandatory: hct.mandatory, order: hct.order}}] AS terms,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[:HAS_ACTIVITY]->(ar:ActivityRoot)-[:LATEST]->(av:ActivityValue) | {{uid: ar.uid, name: av.name}}] AS activities,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[hxet:HAS_XML_EXTENSION_TAG]->(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name, value: hxet.value}}] AS xmlExtensionTags,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[hxea:HAS_XML_EXTENSION_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxea.value}}] AS xmlExtensionAttributes,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemRoot)-[hxeta:HAS_XML_EXTENSION_TAG_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxeta.value}}] AS xmlExtensionTagAttributes

        WITH *,
        [description in descriptions | description.uid] AS descriptionUids,
        [alias in aliases | alias.uid] AS aliasUids,
        [unitDefinition in unitDefinitions | unitDefinition.uid] AS unitDefinitionUids,
        [term in terms | term.uid] AS termUids,
        [activity in activities | activity.uid] AS activityUids,
        [xmlExtensionTag in xmlExtensionTags | xmlExtensionTag.uid] AS xmlExtensionTagUids,
        [xmlExtensionAttribute in xmlExtensionAttributes | xmlExtensionAttribute.uid] AS xmlExtensionAttributeUids,
        [xmlExtensionTagAttribute in xmlExtensionTagAttributes | xmlExtensionTagAttribute.uid] AS xmlExtensionTagAttributeUids
        """

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.has_description.disconnect_all()
        root.has_alias.disconnect_all()
        root.has_unit_definition.disconnect_all()
        root.has_codelist.disconnect_all()

        if ar.concept_vo.description_uids is not None:
            for description_uid in ar.concept_vo.description_uids:
                description = OdmDescriptionRoot.nodes.get_or_none(uid=description_uid)
                root.has_description.connect(description)

        if ar.concept_vo.alias_uids is not None:
            for alias_uid in ar.concept_vo.alias_uids:
                alias = OdmAliasRoot.nodes.get_or_none(uid=alias_uid)
                root.has_alias.connect(alias)

        if ar.concept_vo.codelist_uid is not None:
            codelist = CTCodelistRoot.nodes.get_or_none(uid=ar.concept_vo.codelist_uid)
            root.has_codelist.connect(codelist)

        return new_value

    def _create_new_value_node(self, ar: OdmItemAR) -> OdmItemValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.prompt = ar.concept_vo.prompt
        value_node.datatype = ar.concept_vo.datatype
        value_node.length = ar.concept_vo.length
        value_node.significant_digits = ar.concept_vo.significant_digits
        value_node.sas_field_name = ar.concept_vo.sas_field_name
        value_node.sds_var_name = ar.concept_vo.sds_var_name
        value_node.origin = ar.concept_vo.origin
        value_node.comment = ar.concept_vo.comment

        return value_node

    def _has_data_changed(self, ar: OdmItemAR, value: OdmItemValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmItemRoot.nodes.get_or_none(uid=ar.uid)

        description_uids = {
            description.uid for description in root.has_description.all()
        }
        alias_uids = {alias.uid for alias in root.has_alias.all()}
        unit_definition_uids = {
            unit_definition.uid for unit_definition in root.has_unit_definition.all()
        }
        codelist_uid = (
            root.has_codelist.get_or_none().uid
            if root.has_codelist.get_or_none()
            else None
        )
        term_uids = {term.uid for term in root.has_codelist_term.all()}

        are_rels_changed = (
            set(ar.concept_vo.description_uids) != description_uids
            or set(ar.concept_vo.alias_uids) != alias_uids
            or set(ar.concept_vo.unit_definition_uids) != unit_definition_uids
            or ar.concept_vo.codelist_uid != codelist_uid
            or set(ar.concept_vo.term_uids) != term_uids
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.prompt != value.prompt
            or ar.concept_vo.datatype != value.datatype
            or ar.concept_vo.length != value.length
            or ar.concept_vo.significant_digits != value.significant_digits
            or ar.concept_vo.sas_field_name != value.sas_field_name
            or ar.concept_vo.sds_var_name != value.sds_var_name
            or ar.concept_vo.origin != value.origin
            or ar.concept_vo.comment != value.comment
        )

    def find_by_uid_with_item_group_relation(self, uid: str, item_group_uid: str):
        item_root = self.root_class.nodes.get_or_none(uid=uid)
        item_value = item_root.has_latest_value.get_or_none()

        item_group_root = OdmItemGroupRoot.nodes.get_or_none(uid=item_group_uid)

        rel = item_root.item_ref.relationship(item_group_root)

        return OdmItemRefVO.from_repository_values(
            uid=uid,
            oid=item_value.oid,
            name=item_value.name,
            item_group_uid=item_group_uid,
            order_number=rel.order_number,
            mandatory=rel.mandatory,
            data_entry_required=rel.data_entry_required,
            sdv=rel.sdv,
            locked=rel.locked,
            key_sequence=rel.key_sequence,
            method_oid=rel.method_oid,
            imputation_method_oid=rel.imputation_method_oid,
            role=rel.role,
            role_codelist_oid=rel.role_codelist_oid,
            collection_exception_condition_oid=rel.collection_exception_condition_oid,
        )

    def find_term_with_item_relation_by_item_uid(self, uid: str, term_uid: str):
        item_root = self.root_class.nodes.get_or_none(uid=uid)

        ct_term_root = CTTermRoot.nodes.get_or_none(uid=term_uid)
        ct_term_name_root = ct_term_root.has_name_root.get_or_none()
        ct_term_name_value = ct_term_name_root.has_latest_value.get_or_none()

        rel = item_root.has_codelist_term.relationship(ct_term_root)

        if rel:
            return OdmItemTermVO.from_repository_values(
                uid=uid,
                name=ct_term_name_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
            )
        return None

    def find_unit_definition_with_item_relation_by_item_uid(
        self, uid: str, unit_definition_uid: str
    ):
        item_root = self.root_class.nodes.get_or_none(uid=uid)

        unit_definition_root = UnitDefinitionRoot.nodes.get_or_none(
            uid=unit_definition_uid
        )
        unit_definition_value = unit_definition_root.has_latest_value.get_or_none()

        rel = item_root.has_unit_definition.relationship(unit_definition_root)

        if rel:
            return OdmItemUnitDefinitionVO.from_repository_values(
                uid=uid,
                name=unit_definition_value.name,
                mandatory=rel.mandatory,
                order=rel.order,
            )
        return None
