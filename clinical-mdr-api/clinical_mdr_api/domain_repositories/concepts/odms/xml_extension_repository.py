from typing import Optional

from clinical_mdr_api.domain.concepts.odms.xml_extension import (
    OdmXmlExtensionAR,
    OdmXmlExtensionVO,
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
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmXmlExtensionRoot,
    OdmXmlExtensionValue,
)
from clinical_mdr_api.models import OdmXmlExtension


class XmlExtensionRepository(OdmGenericRepository[OdmXmlExtensionAR]):
    root_class = OdmXmlExtensionRoot
    value_class = OdmXmlExtensionValue
    return_model = OdmXmlExtension

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmXmlExtensionAR:
        return OdmXmlExtensionAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmXmlExtensionVO.from_repository_values(
                name=value.name,
                prefix=value.prefix,
                namespace=value.namespace,
                xml_extension_tag_uids=[
                    xml_extension_tag.uid
                    for xml_extension_tag in root.has_xml_extension_tag.all()
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
        odm_xml_extension_ar = OdmXmlExtensionAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmXmlExtensionVO.from_repository_values(
                name=input_dict.get("name"),
                prefix=input_dict.get("prefix"),
                namespace=input_dict.get("namespace"),
                xml_extension_tag_uids=input_dict.get("xmlExtensionTagUids"),
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

        return odm_xml_extension_ar

    def specific_alias_clause(self, only_specific_status: list = None) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,
        concept_value.prefix AS prefix,
        concept_value.namespace AS namespace,

        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionRoot)-[hxet:HAS_XML_EXTENSION_TAG]->(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name, prefix: xetv.prefix, namespace: xetv.namespace, value: hxet.value}}] AS xmlExtensionTags,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmXmlExtensionRoot)-[hxea:HAS_XML_EXTENSION_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, prefix: xeav.prefix, namespace: xeav.namespace, value: hxea.value}}] AS xmlExtensionAttributes

        WITH *,
        [xmlExtensionTag in xmlExtensionTags | xmlExtensionTag.uid] AS xmlExtensionTagUids,
        [xmlExtensionAttribute in xmlExtensionAttributes | xmlExtensionAttribute.uid] AS xmlExtensionAttributeUids
        """

    def _create_new_value_node(self, ar: OdmXmlExtensionAR) -> OdmXmlExtensionValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.prefix = ar.concept_vo.prefix
        value_node.namespace = ar.concept_vo.namespace

        return value_node

    def _has_data_changed(
        self, ar: OdmXmlExtensionAR, value: OdmXmlExtensionValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.prefix != value.prefix
            or ar.concept_vo.namespace != value.namespace
        )
