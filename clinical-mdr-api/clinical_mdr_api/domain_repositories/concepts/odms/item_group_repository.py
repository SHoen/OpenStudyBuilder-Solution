from typing import Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.item_group import (
    OdmItemGroupAR,
    OdmItemGroupRefVO,
    OdmItemGroupVO,
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
    OdmItemGroupRoot,
    OdmItemGroupValue,
)
from clinical_mdr_api.models import OdmItemGroup


class ItemGroupRepository(OdmGenericRepository[OdmItemGroupAR]):
    root_class = OdmItemGroupRoot
    value_class = OdmItemGroupValue
    return_model = OdmItemGroup

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmItemGroupAR:
        return OdmItemGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmItemGroupVO.from_repository_values(
                oid=value.oid,
                name=value.name,
                repeating=value.repeating,
                is_reference_data=value.is_reference_data,
                sas_dataset_name=value.sas_dataset_name,
                origin=value.origin,
                purpose=value.purpose,
                comment=value.comment,
                description_uids=[
                    description.uid for description in root.has_description.all()
                ],
                alias_uids=[alias.uid for alias in root.has_alias.all()],
                sdtm_domain_uids=[
                    sdtm_domain.uid for sdtm_domain in root.has_sdtm_domain.all()
                ],
                activity_subgroup_uids=[
                    activity_subgroup.uid
                    for activity_subgroup in root.has_activity_subgroup.all()
                ],
                item_uids=[item.uid for item in root.item_ref.all()],
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
        odm_item_group_ar = OdmItemGroupAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmItemGroupVO.from_repository_values(
                oid=input_dict.get("oid"),
                name=input_dict.get("name"),
                repeating=input_dict.get("repeating"),
                is_reference_data=input_dict.get("is_reference_data"),
                sas_dataset_name=input_dict.get("sas_dataset_name"),
                origin=input_dict.get("origin"),
                purpose=input_dict.get("purpose"),
                comment=input_dict.get("comment"),
                description_uids=input_dict.get("description_uids"),
                alias_uids=input_dict.get("alias_uids"),
                sdtm_domain_uids=input_dict.get("sdtm_domain_uids"),
                activity_subgroup_uids=input_dict.get("activity_subgroup_uids"),
                item_uids=input_dict.get("item_uids"),
                xml_extension_tag_uids=input_dict.get("xml_extension_tag_uids"),
                xml_extension_attribute_uids=input_dict.get(
                    "xml_extension_attribute_uids"
                ),
                xml_extension_tag_attribute_uids=input_dict.get(
                    "xml_extension_tag_attribute_uids"
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("user_initials"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_item_group_ar

    def specific_alias_clause(
        self, only_specific_status: Optional[Sequence[str]] = None
    ) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,
        concept_value.oid AS oid,
        concept_value.repeating AS repeating,
        concept_value.is_reference_data AS is_reference_data,
        concept_value.sas_dataset_name AS sas_dataset_name,
        concept_value.origin AS origin,
        concept_value.purpose AS purpose,
        concept_value.comment AS comment,

        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[:HAS_DESCRIPTION]->(dr:OdmDescriptionRoot)-[:LATEST]->(dv:OdmDescriptionValue) | {{uid: dr.uid, name: dv.name, language: dv.language, description: dv.description, instruction: dv.instruction}}] AS descriptions,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[:HAS_ALIAS]->(ar:OdmAliasRoot)-[:LATEST]->(av:OdmAliasValue) | {{uid: ar.uid, name: av.name, context: av.context}}] AS aliases,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[:HAS_SDTM_DOMAIN]->(tr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST]->(tav:CTTermAttributesValue) | {{uid: tr.uid, code_submission_value: tav.code_submission_value, preferred_term: tav.preferred_term}}] AS sdtm_domains,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[:HAS_ACTIVITY_SUB_GROUP]->(agr:ActivitySubGroupRoot)-[:LATEST]->(agv:ActivitySubGroupValue) | {{uid: agr.uid, name: agv.name}}] AS activity_subgroups,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[iref:ITEM_REF]->(ir:OdmItemRoot)-[:LATEST]->(iv:OdmItemValue) | {{uid: ir.uid, name: iv.name, order: iref.order, mandatory: iref.mandatory}}] AS items,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[hxet:HAS_XML_EXTENSION_TAG]->(xetr:OdmXmlExtensionTagRoot)-[:LATEST]->(xetv:OdmXmlExtensionTagValue) | {{uid: xetr.uid, name: xetv.name, value: hxet.value}}] AS xml_extension_tags,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[hxea:HAS_XML_EXTENSION_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxea.value}}] AS xml_extension_attributes,
        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmItemGroupRoot)-[hxeta:HAS_XML_EXTENSION_TAG_ATTRIBUTE]->(xear:OdmXmlExtensionAttributeRoot)-[:LATEST]->(xeav:OdmXmlExtensionAttributeValue) | {{uid: xear.uid, name: xeav.name, value: hxeta.value}}] AS xml_extension_tag_attributes

        WITH *,
        [description in descriptions | description.uid] AS description_uids,
        [alias in aliases | alias.uid] AS alias_uids,
        [sdtm_domain in sdtm_domains | sdtm_domain.uid] AS sdtm_domain_uids,
        [activity_subgroup in activity_subgroups | activity_subgroup.uid] AS activity_subgroup_uids,
        [item in items | item.uid] AS item_uids,
        [xml_extension_tag in xml_extension_tags | xml_extension_tag.uid] AS xml_extension_tag_uids,
        [xml_extension_attribute in xml_extension_attributes | xml_extension_attribute.uid] AS xml_extension_attribute_uids,
        [xml_extension_tag_attribute in xml_extension_tag_attributes | xml_extension_tag_attribute.uid] AS xml_extension_tag_attribute_uids
        """

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        new_value = super()._get_or_create_value(root, ar)

        root.has_description.disconnect_all()
        root.has_alias.disconnect_all()
        root.has_sdtm_domain.disconnect_all()

        if ar.concept_vo.description_uids is not None:
            for description_uid in ar.concept_vo.description_uids:
                description = OdmDescriptionRoot.nodes.get_or_none(uid=description_uid)
                root.has_description.connect(description)

        if ar.concept_vo.alias_uids is not None:
            for alias_uid in ar.concept_vo.alias_uids:
                alias = OdmAliasRoot.nodes.get_or_none(uid=alias_uid)
                root.has_alias.connect(alias)

        if ar.concept_vo.sdtm_domain_uids is not None:
            for sdtm_domain_uid in ar.concept_vo.sdtm_domain_uids:
                sdtm_domain = CTTermRoot.nodes.get_or_none(uid=sdtm_domain_uid)
                root.has_sdtm_domain.connect(sdtm_domain)

        return new_value

    def _create_new_value_node(self, ar: OdmItemGroupAR) -> OdmItemGroupValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.repeating = ar.concept_vo.repeating
        value_node.is_reference_data = ar.concept_vo.is_reference_data
        value_node.sas_dataset_name = ar.concept_vo.sas_dataset_name
        value_node.origin = ar.concept_vo.origin
        value_node.purpose = ar.concept_vo.purpose
        value_node.comment = ar.concept_vo.comment

        return value_node

    def _has_data_changed(self, ar: OdmItemGroupAR, value: OdmItemGroupValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        root = OdmItemGroupRoot.nodes.get_or_none(uid=ar.uid)

        description_uids = {
            description.uid for description in root.has_description.all()
        }
        alias_uids = {alias.uid for alias in root.has_alias.all()}
        sdtm_domain_uids = {
            sdtm_domain.uid for sdtm_domain in root.has_sdtm_domain.all()
        }

        are_rels_changed = (
            set(ar.concept_vo.description_uids) != description_uids
            or set(ar.concept_vo.alias_uids) != alias_uids
            or set(ar.concept_vo.sdtm_domain_uids) != sdtm_domain_uids
        )

        return (
            are_concept_properties_changed
            or are_rels_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.repeating != value.repeating
            or ar.concept_vo.is_reference_data != value.is_reference_data
            or ar.concept_vo.sas_dataset_name != value.sas_dataset_name
            or ar.concept_vo.origin != value.origin
            or ar.concept_vo.purpose != value.purpose
            or ar.concept_vo.comment != value.comment
        )

    def find_by_uid_with_form_relation(self, uid: str, form_uid: str):
        item_group_root = self.root_class.nodes.get_or_none(uid=uid)
        item_group_value = item_group_root.has_latest_value.get_or_none()

        form_root = OdmFormRoot.nodes.get_or_none(uid=form_uid)

        rel = item_group_root.item_group_ref.relationship(form_root)

        return OdmItemGroupRefVO.from_repository_values(
            uid=uid,
            oid=item_group_value.oid,
            name=item_group_value.name,
            form_uid=form_uid,
            order_number=rel.order_number,
            mandatory=rel.mandatory,
            locked=rel.locked,
            collection_exception_condition_oid=rel.collection_exception_condition_oid,
        )
