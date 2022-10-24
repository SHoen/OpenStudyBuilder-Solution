from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import (
    OdmXmlExtensionTagAR,
    OdmXmlExtensionTagVO,
)
from clinical_mdr_api.domain_repositories.concepts.odms.xml_extension_tag_repository import (
    XmlExtensionTagRepository,
)
from clinical_mdr_api.models.odm_xml_extension_tag import (
    OdmXmlExtensionTag,
    OdmXmlExtensionTagPatchInput,
    OdmXmlExtensionTagPostInput,
    OdmXmlExtensionTagVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmXmlExtensionTagService(ConceptGenericService[OdmXmlExtensionTagAR]):
    aggregate_class = OdmXmlExtensionTagAR
    version_class = OdmXmlExtensionTagVersion
    repository_interface = XmlExtensionTagRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmXmlExtensionTagAR
    ) -> OdmXmlExtensionTag:
        return OdmXmlExtensionTag.from_odm_xml_extension_tag_ar(
            odm_xml_extension_tag_ar=item_ar,
            find_odm_xml_extension_by_uid=self._repos.odm_xml_extension_repository.find_by_uid_2,
            find_odm_xml_extension_tag_by_uid=self._repos.odm_xml_extension_tag_repository.find_by_uid_2,
            find_odm_xml_extension_attribute_by_uid=self._repos.odm_xml_extension_attribute_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmXmlExtensionTagPostInput, library
    ) -> _AggregateRootType:
        return OdmXmlExtensionTagAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmXmlExtensionTagVO.from_repository_values(
                name=concept_input.name,
                xml_extension_uid=concept_input.xmlExtensionUid,
                parent_xml_extension_tag_uid=concept_input.parentXmlExtensionTagUid,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_xml_extension_tag_repository.exists_by,
            odm_xml_extension_exists_by_callback=self._repos.odm_xml_extension_repository.exists_by,
        )

    def _edit_aggregate(
        self,
        item: OdmXmlExtensionTagAR,
        concept_edit_input: OdmXmlExtensionTagPatchInput,
    ) -> OdmXmlExtensionTagAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmXmlExtensionTagVO.from_repository_values(
                name=concept_edit_input.name,
                xml_extension_uid=item.concept_vo.xml_extension_uid,
                parent_xml_extension_tag_uid=item.concept_vo.parent_xml_extension_tag_uid,
                child_xml_extension_tag_uids=item.concept_vo.child_xml_extension_tag_uids,
                xml_extension_attribute_uids=item.concept_vo.xml_extension_attribute_uids,
            ),
        )
        return item

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_xml_extension_tag_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Xml Extension Tag with uid {uid} does not exist."
            )

        return self._repos.odm_xml_extension_tag_repository.get_active_relationships(
            uid, ["belongs_to_xml_extension", "has_parent_xml_extension_tag"]
        )

    def soft_delete(self, uid: str) -> None:
        if not self._repos.odm_xml_extension_tag_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Xml Extension Tag with uid {uid} does not exist."
            )

        if self._repos.odm_xml_extension_tag_repository.has_active_relationships(
            uid, ["belongs_to_form", "belongs_to_item_group", "belongs_to_item"]
        ):
            raise exceptions.BusinessLogicException(
                "This ODM Xml Extension Tag is in use."
            )

        return super().soft_delete(uid)
