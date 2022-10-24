from typing import Sequence

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.item import OdmItemAR, OdmItemVO
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.concepts.odms.item_repository import (
    ItemRepository,
)
from clinical_mdr_api.models.odm_common_models import OdmXmlExtensionRelationPostInput
from clinical_mdr_api.models.odm_description import OdmDescriptionBatchPatchInput
from clinical_mdr_api.models.odm_item import (
    OdmItem,
    OdmItemActivityPostInput,
    OdmItemPatchInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
    OdmItemVersion,
    OdmItemWithRelationsPatchInput,
    OdmItemWithRelationsPostInput,
)
from clinical_mdr_api.services._utils import get_input_or_new_value, normalize_string
from clinical_mdr_api.services.concepts.concept_generic_service import (
    _AggregateRootType,
)
from clinical_mdr_api.services.odm_descriptions import OdmDescriptionService
from clinical_mdr_api.services.odm_generic_service import OdmGenericService


class OdmItemService(OdmGenericService[OdmItemAR]):
    aggregate_class = OdmItemAR
    version_class = OdmItemVersion
    repository_interface = ItemRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmItemAR
    ) -> OdmItem:
        return OdmItem.from_odm_item_ar(
            odm_item_ar=item_ar,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
            find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_unit_definition_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_codelist_attribute_by_codelist_uid=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_term_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid,
            find_activity_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_odm_xml_extension_tag_by_uid_with_odm_element_relation=(
                self._repos.odm_xml_extension_tag_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_xml_extension_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_xml_extension_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(
        self, concept_input: OdmItemPostInput, library
    ) -> _AggregateRootType:
        return OdmItemAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmItemVO.from_repository_values(
                oid=get_input_or_new_value(concept_input.oid, "I.", concept_input.name),
                name=concept_input.name,
                prompt=concept_input.prompt,
                datatype=concept_input.datatype,
                length=concept_input.length,
                significant_digits=concept_input.significantDigits,
                sas_field_name=concept_input.sasFieldName,
                sds_var_name=concept_input.sdsVarName,
                origin=concept_input.origin,
                comment=concept_input.comment,
                description_uids=concept_input.descriptionUids,
                alias_uids=concept_input.aliasUids,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in concept_input.unitDefinitions
                ],
                codelist_uid=concept_input.codelistUid,
                term_uids=[term.uid for term in concept_input.terms],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_item_repository.exists_by,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
        )

    def _edit_aggregate(
        self, item: OdmItemAR, concept_edit_input: OdmItemPatchInput
    ) -> OdmItemAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmItemVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                prompt=concept_edit_input.prompt,
                datatype=concept_edit_input.datatype,
                length=concept_edit_input.length,
                significant_digits=concept_edit_input.significantDigits,
                sas_field_name=concept_edit_input.sasFieldName,
                sds_var_name=concept_edit_input.sdsVarName,
                origin=concept_edit_input.origin,
                comment=concept_edit_input.comment,
                description_uids=concept_edit_input.descriptionUids,
                alias_uids=concept_edit_input.aliasUids,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in concept_edit_input.unitDefinitions
                ],
                codelist_uid=concept_edit_input.codelistUid,
                term_uids=[term.uid for term in concept_edit_input.terms],
            ),
            concept_exists_by_callback=self._repos.odm_item_repository.exists_by,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
        )
        return item

    @db.transaction
    def create(self, concept_input: OdmItemPostInput):
        terms = concept_input.terms
        unit_definitions = concept_input.unitDefinitions
        setattr(concept_input, "terms", [])
        setattr(concept_input, "unitDefinitions", [])

        item = super().non_transactional_create(concept_input)

        self._manage_terms(item.uid, terms)
        self._manage_unit_definitions(item.uid, unit_definitions)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(item.uid)
        )

    @db.transaction
    def create_with_relations(
        self, concept_input: OdmItemWithRelationsPostInput
    ) -> _AggregateRootType:
        description_uids = [
            description
            if isinstance(description, str)
            else OdmDescriptionService()
            .non_transactional_create(concept_input=description)
            .uid
            for description in concept_input.descriptions
        ]

        item = self.non_transactional_create(
            concept_input=OdmItemPostInput(
                library=concept_input.libraryName,
                oid=concept_input.oid,
                name=concept_input.name,
                prompt=concept_input.prompt,
                datatype=concept_input.datatype,
                length=concept_input.length,
                significantDigits=concept_input.significantDigits,
                sasFieldName=concept_input.sasFieldName,
                sdsVarName=concept_input.sdsVarName,
                origin=concept_input.origin,
                comment=concept_input.comment,
                descriptionUids=description_uids,
                aliasUids=concept_input.aliasUids,
                unitDefinitions=[],
                codelistUid=concept_input.codelistUid,
                terms=[],
            ),
        )

        self._manage_terms(item.uid, concept_input.terms)
        self._manage_unit_definitions(item.uid, concept_input.unitDefinitions)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(item.uid)
        )

    @db.transaction
    def edit_draft(self, uid: str, concept_edit_input: OdmItemPatchInput):
        terms = concept_edit_input.terms
        unit_definitions = concept_edit_input.unitDefinitions

        setattr(concept_edit_input, "terms", [])
        setattr(concept_edit_input, "unitDefinitions", [])

        super().non_transactional_edit(uid, concept_edit_input)

        self._manage_terms(uid, terms, True)
        self._manage_unit_definitions(uid, unit_definitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmItemWithRelationsPatchInput
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

        self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmItemPatchInput(
                changeDescription=concept_edit_input.changeDescription,
                name=concept_edit_input.name,
                oid=concept_edit_input.oid,
                prompt=concept_edit_input.prompt,
                datatype=concept_edit_input.datatype,
                length=concept_edit_input.length,
                significantDigits=concept_edit_input.significantDigits,
                sasFieldName=concept_edit_input.sasFieldName,
                sdsVarName=concept_edit_input.sdsVarName,
                origin=concept_edit_input.origin,
                comment=concept_edit_input.comment,
                descriptionUids=description_uids,
                aliasUids=concept_edit_input.aliasUids,
                unitDefinitions=[],
                codelistUid=concept_edit_input.codelistUid,
                terms=[],
            ),
        )

        self._manage_terms(uid, concept_edit_input.terms, True)
        self._manage_unit_definitions(uid, concept_edit_input.unitDefinitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    def _manage_terms(
        self,
        item_uid: str,
        terms: Sequence[OdmItemTermRelationshipInput],
        for_update: bool = False,
    ):
        try:
            if for_update:
                self._repos.odm_item_repository.remove_relation(
                    uid=item_uid,
                    relation_uid=None,
                    relationship_type=RelationType.TERM,
                    disconnect_all=True,
                )

            for term in terms:
                self._repos.odm_item_repository.add_relation(
                    uid=item_uid,
                    relation_uid=term.uid,
                    relationship_type=RelationType.TERM,
                    parameters={"mandatory": term.mandatory, "order": term.order},
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

    def _manage_unit_definitions(
        self,
        item_uid: str,
        unit_definitions: Sequence[OdmItemUnitDefinitionRelationshipInput],
        for_update: bool = False,
    ):
        try:
            if for_update:
                self._repos.odm_item_repository.remove_relation(
                    uid=item_uid,
                    relation_uid=None,
                    relationship_type=RelationType.UNIT_DEFINITION,
                    disconnect_all=True,
                )

            for unit_definition in unit_definitions:
                self._repos.odm_item_repository.add_relation(
                    uid=item_uid,
                    relation_uid=unit_definition.uid,
                    relationship_type=RelationType.UNIT_DEFINITION,
                    parameters={
                        "mandatory": unit_definition.mandatory,
                        "order": unit_definition.order,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

    @db.transaction
    def add_activities(
        self,
        uid: str,
        odm_item_activity_post_input: Sequence[OdmItemActivityPostInput],
        override: bool,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ACTIVITY,
                disconnect_all=True,
            )

        try:
            for activity in odm_item_activity_post_input:
                self._repos.odm_item_repository.add_relation(
                    uid=uid,
                    relation_uid=activity.uid,
                    relationship_type=RelationType.ACTIVITY,
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_xml_extension_tags(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self.fail_if_non_present_tags_are_used_by_current_odm_element_attributes(
                odm_item_ar._concept_vo.xml_extension_tag_attribute_uids,
                odm_xml_extension_relation_post_input,
            )

            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_TAG,
                disconnect_all=True,
            )

        try:
            for xml_extension_tag in odm_xml_extension_relation_post_input:
                self._repos.odm_item_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_tag.uid,
                    relationship_type=RelationType.XML_EXTENSION_TAG,
                    parameters={
                        "value": xml_extension_tag.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_xml_extension_attributes(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        self.fail_if_these_attributes_cannot_be_added(
            odm_xml_extension_relation_post_input
        )

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_ATTRIBUTE,
                disconnect_all=True,
            )

        try:
            for xml_extension_attribute in odm_xml_extension_relation_post_input:
                self._repos.odm_item_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_attribute.uid,
                    relationship_type=RelationType.XML_EXTENSION_ATTRIBUTE,
                    parameters={
                        "value": xml_extension_attribute.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_xml_extension_tag_attributes(
        self,
        uid: str,
        odm_xml_extension_relation_post_input: Sequence[
            OdmXmlExtensionRelationPostInput
        ],
        override: bool,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        self.fail_if_these_attributes_cannot_be_added(
            odm_xml_extension_relation_post_input,
            odm_item_ar.concept_vo.xml_extension_tag_uids,
        )

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.XML_EXTENSION_TAG_ATTRIBUTE,
                disconnect_all=True,
            )

        try:
            for xml_extension_tag_attribute in odm_xml_extension_relation_post_input:
                self._repos.odm_item_repository.add_relation(
                    uid=uid,
                    relation_uid=xml_extension_tag_attribute.uid,
                    relationship_type=RelationType.XML_EXTENSION_TAG_ATTRIBUTE,
                    parameters={
                        "value": xml_extension_tag_attribute.value,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_item_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Item with uid {uid} does not exist."
            )

        return self._repos.odm_item_repository.get_active_relationships(
            uid, ["item_ref"]
        )
