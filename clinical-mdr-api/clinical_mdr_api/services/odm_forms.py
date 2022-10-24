from distutils.util import strtobool
from typing import Sequence

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.form import OdmFormAR, OdmFormVO
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.concepts.odms.form_repository import (
    FormRepository,
)
from clinical_mdr_api.models.odm_common_models import OdmXmlExtensionRelationPostInput
from clinical_mdr_api.models.odm_description import OdmDescriptionBatchPatchInput
from clinical_mdr_api.models.odm_form import (
    OdmForm,
    OdmFormActivityGroupPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPatchInput,
    OdmFormPostInput,
    OdmFormVersion,
    OdmFormWithRelationsPatchInput,
    OdmFormWithRelationsPostInput,
)
from clinical_mdr_api.services._utils import get_input_or_new_value, normalize_string
from clinical_mdr_api.services.concepts.concept_generic_service import (
    _AggregateRootType,
)
from clinical_mdr_api.services.odm_descriptions import OdmDescriptionService
from clinical_mdr_api.services.odm_generic_service import OdmGenericService


class OdmFormService(OdmGenericService[OdmFormAR]):
    aggregate_class = OdmFormAR
    version_class = OdmFormVersion
    repository_interface = FormRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmFormAR
    ) -> OdmForm:
        return OdmForm.from_odm_form_ar(
            odm_form_ar=item_ar,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
            find_odm_item_group_by_uid_with_form_relation=self._repos.odm_item_group_repository.find_by_uid_with_form_relation,
            find_odm_xml_extension_tag_by_uid_with_odm_element_relation=(
                self._repos.odm_xml_extension_tag_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_xml_extension_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_xml_extension_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(
        self, concept_input: OdmFormPostInput, library
    ) -> _AggregateRootType:
        return OdmFormAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmFormVO.from_repository_values(
                oid=get_input_or_new_value(concept_input.oid, "F.", concept_input.name),
                name=concept_input.name,
                sdtm_version=concept_input.sdtmVersion,
                repeating=strtobool(concept_input.repeating),
                scope_uid=concept_input.scopeUid,
                description_uids=concept_input.descriptionUids,
                alias_uids=concept_input.aliasUids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_form_repository.exists_by,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmFormAR, concept_edit_input: OdmFormPatchInput
    ) -> OdmFormAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmFormVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                sdtm_version=concept_edit_input.sdtmVersion,
                repeating=strtobool(concept_edit_input.repeating),
                scope_uid=concept_edit_input.scopeUid,
                description_uids=concept_edit_input.descriptionUids,
                alias_uids=concept_edit_input.aliasUids,
            ),
            concept_exists_by_callback=self._repos.odm_form_repository.exists_by,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )
        return item

    @db.transaction
    def create_with_relations(
        self, concept_input: OdmFormWithRelationsPostInput
    ) -> _AggregateRootType:
        description_uids = [
            description
            if isinstance(description, str)
            else OdmDescriptionService()
            .non_transactional_create(concept_input=description)
            .uid
            for description in concept_input.descriptions
        ]

        return self.non_transactional_create(
            concept_input=OdmFormPostInput(
                library=concept_input.libraryName,
                name=concept_input.name,
                sdtmVersion=concept_input.sdtmVersion,
                oid=get_input_or_new_value(concept_input.oid, "F.", concept_input.name),
                repeating=concept_input.repeating,
                descriptionUids=description_uids,
                aliasUids=concept_input.aliasUids,
            )
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmFormWithRelationsPatchInput
    ) -> _AggregateRootType:
        description_uids = [
            OdmDescriptionService()
            .non_transactional_edit(uid=description.uid, concept_edit_input=description)
            .uid
            if isinstance(description, OdmDescriptionBatchPatchInput)
            else OdmDescriptionService()
            .non_transactional_create(concept_input=description)
            .uid
            for description in concept_edit_input.descriptions
        ]

        return self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmFormPatchInput(
                changeDescription=concept_edit_input.changeDescription,
                name=concept_edit_input.name,
                sdtmVersion=concept_edit_input.sdtmVersion,
                oid=concept_edit_input.oid,
                repeating=concept_edit_input.repeating,
                descriptionUids=description_uids,
                aliasUids=concept_edit_input.aliasUids,
            ),
        )

    @db.transaction
    def add_activity_groups(
        self,
        uid: str,
        odm_form_activity_group_post_input: Sequence[OdmFormActivityGroupPostInput],
        override: bool,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ACTIVITY_GROUP,
                disconnect_all=True,
            )

        try:
            for activity_group in odm_form_activity_group_post_input:
                self._repos.odm_form_repository.add_relation(
                    uid=uid,
                    relation_uid=activity_group.uid,
                    relationship_type=RelationType.ACTIVITY_GROUP,
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_item_groups(
        self,
        uid: str,
        odm_form_item_group_post_input: Sequence[OdmFormItemGroupPostInput],
        override: bool,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ITEM_GROUP,
                disconnect_all=True,
            )

        try:
            for item_group in odm_form_item_group_post_input:
                self._repos.odm_form_repository.add_relation(
                    uid=uid,
                    relation_uid=item_group.uid,
                    relationship_type=RelationType.ITEM_GROUP,
                    parameters={
                        "order_number": item_group.orderNumber,
                        "mandatory": strtobool(item_group.mandatory),
                        "locked": strtobool(item_group.locked),
                        "collection_exception_condition_oid": item_group.collectionExceptionConditionOid,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_xml_extension_tags(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self.fail_if_non_present_tags_are_used_by_current_odm_element_attributes(
                odm_form_ar._concept_vo.xml_extension_tag_attribute_uids,
                odm_xml_extension_relation_post_input,
            )

            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_TAG,
                disconnect_all=True,
            )

        try:
            for xml_extension_tag in odm_xml_extension_relation_post_input:
                self._repos.odm_form_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_tag.uid,
                    relationship_type=RelationType.XML_EXTENSION_TAG,
                    parameters={
                        "value": xml_extension_tag.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_xml_extension_attributes(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        self.fail_if_these_attributes_cannot_be_added(
            odm_xml_extension_relation_post_input
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_ATTRIBUTE,
                disconnect_all=True,
            )

        try:
            for xml_extension_attribute in odm_xml_extension_relation_post_input:
                self._repos.odm_form_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_attribute.uid,
                    relationship_type=RelationType.XML_EXTENSION_ATTRIBUTE,
                    parameters={
                        "value": xml_extension_attribute.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_xml_extension_tag_attributes(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        self.fail_if_these_attributes_cannot_be_added(
            odm_xml_extension_relation_post_input,
            odm_form_ar.concept_vo.xml_extension_tag_uids,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_TAG_ATTRIBUTE,
                disconnect_all=True,
            )

        try:
            for xml_extension_tag_attribute in odm_xml_extension_relation_post_input:
                self._repos.odm_form_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_tag_attribute.uid,
                    relationship_type=RelationType.XML_EXTENSION_TAG_ATTRIBUTE,
                    parameters={
                        "value": xml_extension_tag_attribute.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_form_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Form with uid {uid} does not exist."
            )

        return self._repos.odm_form_repository.get_active_relationships(
            uid, ["form_ref"]
        )
