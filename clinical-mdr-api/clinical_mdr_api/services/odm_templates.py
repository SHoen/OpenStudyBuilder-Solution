from distutils.util import strtobool
from typing import Sequence

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.odms.template import OdmTemplateAR, OdmTemplateVO
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.concepts.odms.template_repository import (
    TemplateRepository,
)
from clinical_mdr_api.models.odm_template import (
    OdmTemplate,
    OdmTemplateFormPostInput,
    OdmTemplatePatchInput,
    OdmTemplatePostInput,
    OdmTemplateVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value, normalize_string
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmTemplateService(ConceptGenericService[OdmTemplateAR]):
    aggregate_class = OdmTemplateAR
    version_class = OdmTemplateVersion
    repository_interface = TemplateRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmTemplateAR
    ) -> OdmTemplate:
        return OdmTemplate.from_odm_template_ar(
            odm_template_ar=item_ar,
            find_odm_form_by_uid_with_template_relation=self._repos.odm_form_repository.find_by_uid_with_template_relation,
        )

    def _create_aggregate_root(
        self, concept_input: OdmTemplatePostInput, library
    ) -> _AggregateRootType:
        return OdmTemplateAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmTemplateVO.from_repository_values(
                name=concept_input.name,
                oid=get_input_or_new_value(concept_input.oid, "T.", concept_input.name),
                effective_date=concept_input.effectiveDate,
                retired_date=concept_input.retiredDate,
                description=concept_input.description,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_name_callback=self._repos.odm_template_repository.concept_exists_by_name,
        )

    def _edit_aggregate(
        self, item: OdmTemplateAR, concept_edit_input: OdmTemplatePatchInput
    ) -> OdmTemplateAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmTemplateVO.from_repository_values(
                name=concept_edit_input.name,
                oid=concept_edit_input.oid,
                effective_date=concept_edit_input.effectiveDate,
                retired_date=concept_edit_input.retiredDate,
                description=concept_edit_input.description,
            ),
            concept_exists_by_name_callback=self._repos.odm_template_repository.concept_exists_by_name,
        )
        return item

    @db.transaction
    def add_forms(
        self,
        uid: str,
        odm_template_form_post_input: Sequence[OdmTemplateFormPostInput],
        override: bool,
    ) -> OdmTemplate:
        odm_template_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        if odm_template_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException("The object is inactive")

        if override:
            self._repos.odm_template_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.FORM,
                disconnect_all=True,
            )

        try:
            for form in odm_template_form_post_input:
                self._repos.odm_template_repository.add_relation(
                    uid=uid,
                    relation_uid=form.uid,
                    relationship_type=RelationType.FORM,
                    parameters={
                        "order_number": form.orderNumber,
                        "mandatory": strtobool(form.mandatory),
                        "locked": strtobool(form.locked),
                        "collection_exception_condition_oid": form.collectionExceptionConditionOid,
                    },
                )
        except ValueError as exception:
            raise exceptions.ValidationException(exception.args[0])

        odm_template_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_template_ar)

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_template_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Template with uid {uid} does not exist."
            )

        return self._repos.odm_template_repository.get_active_relationships(uid, [])
