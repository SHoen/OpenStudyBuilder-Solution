from typing import Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import (
    OdmXmlExtensionTagAR,
    OdmXmlExtensionTagRelationVO,
    OdmXmlExtensionTagVO,
)
from clinical_mdr_api.domain.concepts.utils import RelationType
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
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmXmlExtensionRoot,
    OdmXmlExtensionTagRoot,
    OdmXmlExtensionTagValue,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models import OdmXmlExtensionTag


class XmlExtensionTagRepository(OdmGenericRepository[OdmXmlExtensionTagAR]):
    root_class = OdmXmlExtensionTagRoot
    value_class = OdmXmlExtensionTagValue
    return_model = OdmXmlExtensionTag

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmXmlExtensionTagAR:
        return OdmXmlExtensionTagAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmXmlExtensionTagVO.from_repository_values(
                name=value.name,
                xml_extension_uid=root.belongs_to_xml_extension.get_or_none().uid
                if root.belongs_to_xml_extension.get_or_none()
                else None,
                parent_xml_extension_tag_uid=root.has_parent_xml_extension_tag.get_or_none().uid
                if root.has_parent_xml_extension_tag.get_or_none()
                else None,
                child_xml_extension_tag_uids=[
                    child_xml_extension_tag.uid
                    for child_xml_extension_tag in root.has_child_xml_extension_tag.all()
                ],
                xml_extension_attribute_uids=[
                    xml_extension_attribute.uid
                    for xml_extension_attribute in root.has_xml_extension_attribute.all()
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
        odm_xml_extension_tag_ar = OdmXmlExtensionTagAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmXmlExtensionTagVO.from_repository_values(
                name=input_dict.get("name"),
                xml_extension_uid=input_dict.get("xmlExtensionUid"),
                parent_xml_extension_tag_uid=input_dict.get("parentXmlExtensionTagUid"),
                child_xml_extension_tag_uids=input_dict.get("childXmlExtensionTagUids"),
                xml_extension_attribute_uids=input_dict.get(
                    "xmlExtensionAttributeUids"
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

        return odm_xml_extension_tag_ar

    def specific_alias_clause(self, only_specific_status: list = None) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,

        head([(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionTagRoot)<-[:HAS_XML_EXTENSION_TAG]-(xer:OdmXmlExtensionRoot)-[:LATEST]->(xev:OdmXmlExtensionValue) | {{uid: xer.uid, name: xev.name, prefix: xev.prefix, namespace: xev.namespace}}]) AS xmlExtension,
        head([(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionTagRoot)-[:HAS_PARENT_XML_EXTENSION_TAG]->(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name}}]) AS parentXmlExtensionTag,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionTagRoot)<-[:HAS_PARENT_XML_EXTENSION_TAG]-(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name}}] AS childXmlExtensionTags,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionTagRoot)-[:HAS_XML_EXTENSION_ATTRIBUTE]->(xer:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xev:OdmXmlExtensionAttributeValue) | {{uid: xer.uid, name: xev.name}}] AS xmlExtensionAttributes

        WITH *,
        xmlExtension.uid AS xmlExtensionUid,
        parentXmlExtensionTag.uid AS parentXmlExtensionTagUid,
        [childXmlExtensionTag in childXmlExtensionTags | childXmlExtensionTag.uid] AS childXmlExtensionTagUids,
        [xmlExtensionAttribute in xmlExtensionAttributes | xmlExtensionAttribute.uid] AS xmlExtensionAttributeUids
        """

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.belongs_to_xml_extension.disconnect_all()
        root.has_parent_xml_extension_tag.disconnect_all()

        if ar.concept_vo.xml_extension_uid is not None:
            xml_extension = OdmXmlExtensionRoot.nodes.get_or_none(
                uid=ar.concept_vo.xml_extension_uid
            )
            root.belongs_to_xml_extension.connect(xml_extension)

        if ar.concept_vo.parent_xml_extension_tag_uid is not None:
            parent_xml_extension_tag = OdmXmlExtensionTagRoot.nodes.get_or_none(
                uid=ar.concept_vo.parent_xml_extension_tag_uid
            )
            root.has_parent_xml_extension_tag.connect(parent_xml_extension_tag)

        return new_value

    def _has_data_changed(
        self, ar: OdmXmlExtensionTagAR, value: OdmXmlExtensionTagValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmXmlExtensionTagRoot.nodes.get_or_none(uid=ar.uid)

        xml_extension_uid = (
            root.belongs_to_xml_extension.get_or_none().uid
            if root.belongs_to_xml_extension.get_or_none()
            else None
        )

        parent_xml_extension_tag_uid = (
            root.has_parent_xml_extension_tag.get_or_none().uid
            if root.has_parent_xml_extension_tag.get_or_none()
            else None
        )

        are_rels_changed = (
            ar.concept_vo.xml_extension_uid != xml_extension_uid
            or ar.concept_vo.parent_xml_extension_tag_uid
            != parent_xml_extension_tag_uid
        )

        return are_concept_properties_changed or are_rels_changed

    def find_by_uid_with_odm_element_relation(
        self, uid: str, odm_element_uid: str, odm_element_type: RelationType
    ):
        xml_extension_tag_root = self.root_class.nodes.get_or_none(uid=uid)
        xml_extension_tag_value = xml_extension_tag_root.has_latest_value.get_or_none()

        if odm_element_type == RelationType.FORM:
            odm_element_root = OdmFormRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = xml_extension_tag_root.belongs_to_form.relationship(odm_element_root)
        elif odm_element_type == RelationType.ITEM_GROUP:
            odm_element_root = OdmItemGroupRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = xml_extension_tag_root.belongs_to_item_group.relationship(
                odm_element_root
            )
        elif odm_element_type == RelationType.ITEM:
            odm_element_root = OdmItemRoot.nodes.get_or_none(uid=odm_element_uid)
            rel = xml_extension_tag_root.belongs_to_item.relationship(odm_element_root)
        else:
            raise BusinessLogicException("Invalid odm element type.")

        return OdmXmlExtensionTagRelationVO.from_repository_values(
            uid=uid,
            name=xml_extension_tag_value.name,
            value=rel.value,
        )
