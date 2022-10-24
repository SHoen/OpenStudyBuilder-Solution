from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.method import OdmMethodAR, OdmMethodVO
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories.concepts.odms.method_repository import (
    MethodRepository,
)
from clinical_mdr_api.models.odm_description import OdmDescriptionBatchPatchInput
from clinical_mdr_api.models.odm_formal_expression import (
    OdmFormalExpressionBatchPatchInput,
)
from clinical_mdr_api.models.odm_method import (
    OdmMethod,
    OdmMethodPatchInput,
    OdmMethodPostInput,
    OdmMethodVersion,
    OdmMethodWithRelationsPatchInput,
    OdmMethodWithRelationsPostInput,
)
from clinical_mdr_api.services._utils import get_input_or_new_value
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)
from clinical_mdr_api.services.odm_descriptions import OdmDescriptionService
from clinical_mdr_api.services.odm_formal_expressions import OdmFormalExpressionService


class OdmMethodService(ConceptGenericService[OdmMethodAR]):
    aggregate_class = OdmMethodAR
    version_class = OdmMethodVersion
    repository_interface = MethodRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmMethodAR
    ) -> OdmMethod:
        return OdmMethod.from_odm_method_ar(
            odm_method_ar=item_ar,
            find_odm_formal_expression_by_uid=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmMethodPostInput, library
    ) -> _AggregateRootType:
        return OdmMethodAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmMethodVO.from_repository_values(
                oid=get_input_or_new_value(concept_input.oid, "C.", concept_input.name),
                name=concept_input.name,
                method_type=concept_input.type,
                formal_expression_uids=concept_input.formalExpressionUids,
                description_uids=concept_input.descriptionUids,
                alias_uids=concept_input.aliasUids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_callback=self._repos.odm_method_repository.exists_by,
            find_odm_formal_expression_callback=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_callback=self._repos.odm_description_repository.find_by_uid_2,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmMethodAR, concept_edit_input: OdmMethodPatchInput
    ) -> OdmMethodAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmMethodVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                method_type=concept_edit_input.type,
                formal_expression_uids=concept_edit_input.formalExpressionUids,
                description_uids=concept_edit_input.descriptionUids,
                alias_uids=concept_edit_input.aliasUids,
            ),
            concept_exists_by_callback=self._repos.odm_method_repository.exists_by,
            find_odm_formal_expression_callback=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_callback=self._repos.odm_description_repository.find_by_uid_2,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )
        return item

    @db.transaction
    def create_with_relations(
        self, concept_input: OdmMethodWithRelationsPostInput
    ) -> _AggregateRootType:
        description_uids = [
            description
            if isinstance(description, str)
            else OdmDescriptionService()
            .non_transactional_create(concept_input=description)
            .uid
            for description in concept_input.descriptions
        ]

        formal_expression_uids = [
            formal_expression
            if isinstance(formal_expression, str)
            else OdmFormalExpressionService()
            .non_transactional_create(concept_input=formal_expression)
            .uid
            for formal_expression in concept_input.formalExpressions
        ]

        return self.non_transactional_create(
            concept_input=OdmMethodPostInput(
                library=concept_input.libraryName,
                oid=get_input_or_new_value(concept_input.oid, "C.", concept_input.name),
                name=concept_input.name,
                type=concept_input.type,
                formalExpressionUids=formal_expression_uids,
                descriptionUids=description_uids,
                aliasUids=concept_input.aliasUids,
            )
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmMethodWithRelationsPatchInput
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

        formal_expression_uids = [
            OdmFormalExpressionService()
            .non_transactional_edit(
                uid=formal_expression.uid, concept_edit_input=formal_expression
            )
            .uid
            if isinstance(formal_expression, OdmFormalExpressionBatchPatchInput)
            else OdmFormalExpressionService()
            .non_transactional_create(concept_input=formal_expression)
            .uid
            for formal_expression in concept_edit_input.formalExpressions
        ]

        return self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmMethodPatchInput(
                changeDescription=concept_edit_input.changeDescription,
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                type=concept_edit_input.type,
                formalExpressionUids=formal_expression_uids,
                descriptionUids=description_uids,
                aliasUids=concept_edit_input.aliasUids,
            ),
        )

    @db.transaction
    def soft_delete(self, uid: str):
        """
        Works exactly as the parent soft_delete method.
        However, after deleting the ODM Method, it also sets all method_oid that use this ODM Method to null.

        This method is temporary and should be removed when the database relationship between ODM Method and its reference nodes is ready.
        """
        try:
            method = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            method.soft_delete()
            self.repository.save(method)

            self._repos.odm_method_repository.set_all_method_oid_properties_to_null(
                method.concept_vo.oid
            )

        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_method_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Method with uid {uid} does not exist."
            )

        return self._repos.odm_method_repository.get_active_relationships(uid, [])
