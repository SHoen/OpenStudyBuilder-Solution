from typing import Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.form import (
    OdmFormAR,
    OdmFormRefVO,
    OdmFormVO,
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
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
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
    OdmFormRoot,
    OdmFormValue,
    OdmTemplateRoot,
)
from clinical_mdr_api.models import OdmForm


class FormRepository(OdmGenericRepository[OdmFormAR]):
    root_class = OdmFormRoot
    value_class = OdmFormValue
    return_model = OdmForm

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmFormAR:
        return OdmFormAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmFormVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                sdtm_version=value.sdtm_version,
                repeating=value.repeating,
                scope_uid=root.has_scope.get_or_none().uid
                if root.has_scope.get_or_none()
                else None,
                description_uids=[
                    description.uid for description in root.has_description.all()
                ],
                alias_uids=[alias.uid for alias in root.has_alias.all()],
                activity_group_uids=[
                    activity_group.uid
                    for activity_group in root.has_activity_group.all()
                ],
                item_group_uids=[
                    item_group.uid for item_group in root.item_group_ref.all()
                ],
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
        odm_form_ar = OdmFormAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmFormVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict.get("name"),
                sdtm_version=input_dict.get("sdtmVersion"),
                repeating=input_dict.get("repeating"),
                scope_uid=input_dict.get("scopeUid"),
                description_uids=input_dict.get("descriptionUids"),
                alias_uids=input_dict.get("aliasUids"),
                activity_group_uids=input_dict.get("activityGroupUids"),
                item_group_uids=input_dict.get("itemGroupUids"),
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

        return odm_form_ar

    def specific_alias_clause(self, only_specific_status: list = None) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,
        concept_value.oid AS oid,
        concept_value.repeating AS repeating,
        concept_value.sdtm_version AS sdtmVersion,

        head([(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[:HAS_SCOPE]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue) | tr.uid]) AS scopeUid,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[:HAS_DESCRIPTION]->(dr:OdmDescriptionRoot)-[:LATEST]->(dv:OdmDescriptionValue) | {{uid: dr.uid, name: dv.name, language: dv.language, description: dv.description, instruction: dv.instruction}}] AS descriptions,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[:HAS_ALIAS]->(ar:OdmAliasRoot)-[:LATEST]->(av:OdmAliasValue) | {{uid: ar.uid, name: av.name, context: av.context}}] AS aliases,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[:HAS_ACTIVITY_GROUP]->(agr:ActivityGroupRoot)-[:LATEST]->(agv:ActivityGroupValue) | {{uid: agr.uid, name: agv.name}}] AS activityGroups,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[igref:ITEM_GROUP_REF]->(igr:OdmItemGroupRoot)-[:LATEST]->(igv:OdmItemGroupValue) | {{uid: igr.uid, name: igv.name, order: igref.order, mandatory: igref.mandatory}}] AS itemGroups,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[hxet:HAS_XML_EXTENSION_TAG]->(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name, value: hxet.value}}] AS xmlExtensionTags,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[hxea:HAS_XML_EXTENSION_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxea.value}}] AS xmlExtensionAttributes,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmFormRoot)-[hxeta:HAS_XML_EXTENSION_TAG_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxeta.value}}] AS xmlExtensionTagAttributes

        WITH *,
        [description in descriptions | description.uid] AS descriptionUids,
        [alias in aliases | alias.uid] AS aliasUids,
        [activityGroup in activityGroups | activityGroup.uid] AS activityGroupUids,
        [itemGroup in itemGroups | itemGroup.uid] AS itemGroupUids,
        [xmlExtensionTag in xmlExtensionTags | xmlExtensionTag.uid] AS xmlExtensionTagUids,
        [xmlExtensionAttribute in xmlExtensionAttributes | xmlExtensionAttribute.uid] AS xmlExtensionAttributeUids,
        [xmlExtensionTagAttribute in xmlExtensionTagAttributes | xmlExtensionTagAttribute.uid] AS xmlExtensionTagAttributeUids
        """

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.has_scope.disconnect_all()
        root.has_description.disconnect_all()
        root.has_alias.disconnect_all()

        if ar.concept_vo.scope_uid is not None:
            scope = CTTermRoot.nodes.get_or_none(uid=ar.concept_vo.scope_uid)
            root.has_scope.connect(scope)

        if ar.concept_vo.description_uids is not None:
            for description_uid in ar.concept_vo.description_uids:
                description = OdmDescriptionRoot.nodes.get_or_none(uid=description_uid)
                root.has_description.connect(description)

        if ar.concept_vo.alias_uids is not None:
            for alias_uid in ar.concept_vo.alias_uids:
                alias = OdmAliasRoot.nodes.get_or_none(uid=alias_uid)
                root.has_alias.connect(alias)

        return new_value

    def _create_new_value_node(self, ar: OdmFormAR) -> OdmFormValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.sdtm_version = ar.concept_vo.sdtm_version
        value_node.repeating = ar.concept_vo.repeating

        return value_node

    def _has_data_changed(self, ar: OdmFormAR, value: OdmFormValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmFormRoot.nodes.get_or_none(uid=ar.uid)

        scope_uid = (
            root.has_scope.get_or_none().uid if root.has_scope.get_or_none() else None
        )
        description_uids = {
            description.uid for description in root.has_description.all()
        }
        alias_uids = {alias.uid for alias in root.has_alias.all()}

        are_rels_changed = (
            ar.concept_vo.scope_uid != scope_uid
            or set(ar.concept_vo.description_uids) != description_uids
            or set(ar.concept_vo.alias_uids) != alias_uids
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.repeating != value.repeating
        )

    def find_by_uid_with_template_relation(self, uid: str, template_uid: str):
        form_root = self.root_class.nodes.get_or_none(uid=uid)
        form_value = form_root.has_latest_value.get_or_none()

        template_root = OdmTemplateRoot.nodes.get_or_none(uid=template_uid)

        rel = form_root.form_ref.relationship(template_root)

        return OdmFormRefVO.from_repository_values(
            uid=uid,
            name=form_value.name,
            template_uid=template_uid,
            order_number=rel.order_number,
            mandatory=rel.mandatory,
            locked=rel.locked,
            collection_exception_condition_oid=rel.collection_exception_condition_oid,
        )
