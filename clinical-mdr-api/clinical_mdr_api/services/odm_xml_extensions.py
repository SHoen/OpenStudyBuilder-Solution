from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.xml_extension import (
    OdmXmlExtensionAR,
    OdmXmlExtensionVO,
)
from clinical_mdr_api.domain_repositories.concepts.odms.xml_extension_repository import (
    XmlExtensionRepository,
)
from clinical_mdr_api.models.odm_xml_extension import (
    OdmXmlExtension,
    OdmXmlExtensionPatchInput,
    OdmXmlExtensionPostInput,
    OdmXmlExtensionVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmXmlExtensionService(ConceptGenericService[OdmXmlExtensionAR]):
    aggregate_class = OdmXmlExtensionAR
    version_class = OdmXmlExtensionVersion
    repository_interface = XmlExtensionRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmXmlExtensionAR
    ) -> OdmXmlExtension:
        return OdmXmlExtension.from_odm_xml_extension_ar(
            odm_xml_extension_ar=item_ar,
            find_odm_xml_extension_tag_by_uid=self._repos.odm_xml_extension_tag_repository.find_by_uid_2,
            find_odm_xml_extension_attribute_by_uid=self._repos.odm_xml_extension_attribute_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmXmlExtensionPostInput, library
    ) -> _AggregateRootType:
        return OdmXmlExtensionAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmXmlExtensionVO.from_repository_values(
                name=concept_input.name,
                prefix=concept_input.prefix,
                namespace=concept_input.namespace,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_xml_extension_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmXmlExtensionAR, concept_edit_input: OdmXmlExtensionPatchInput
    ) -> OdmXmlExtensionAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmXmlExtensionVO.from_repository_values(
                name=concept_edit_input.name,
                prefix=concept_edit_input.prefix,
                namespace=concept_edit_input.namespace,
                xml_extension_tag_uids=item.concept_vo.xml_extension_tag_uids,
                xml_extension_attribute_uids=item.concept_vo.xml_extension_attribute_uids,
            ),
            concept_exists_by_callback=self._repos.odm_xml_extension_repository.exists_by,
        )
        return item

    def soft_delete(self, uid: str) -> None:
        if not self._repos.odm_xml_extension_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"ODM XML Extension with uid {uid} does not exist."
            )

        if self._repos.odm_xml_extension_repository.has_active_relationships(
            uid, ["has_xml_extension_tag", "has_xml_extension_attribute"]
        ):
            raise exceptions.BusinessLogicException("This ODM XML Extension is in use.")

        return super().soft_delete(uid)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_xml_extension_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Xml Extension with uid {uid} does not exist."
            )

        return self._repos.odm_xml_extension_repository.get_active_relationships(
            uid, []
        )
