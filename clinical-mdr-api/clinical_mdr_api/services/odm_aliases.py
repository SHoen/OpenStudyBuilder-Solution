from typing import Sequence

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR, OdmAliasVO
from clinical_mdr_api.domain_repositories.concepts.odms.alias_repository import (
    AliasRepository,
)
from clinical_mdr_api.exceptions import BusinessLogicException, NotFoundException
from clinical_mdr_api.models.odm_alias import (
    OdmAlias,
    OdmAliasBatchInput,
    OdmAliasBatchOutput,
    OdmAliasPatchInput,
    OdmAliasPostInput,
    OdmAliasVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmAliasService(ConceptGenericService[OdmAliasAR]):
    aggregate_class = OdmAliasAR
    version_class = OdmAliasVersion
    repository_interface = AliasRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmAliasAR
    ) -> OdmAlias:
        return OdmAlias.from_odm_alias_ar(odm_alias_ar=item_ar)

    def _create_aggregate_root(
        self, concept_input: OdmAliasPostInput, library
    ) -> _AggregateRootType:
        return OdmAliasAR.from_input_values(
            author=self.user_initials,
            concept_vo=OdmAliasVO.from_repository_values(
                name=concept_input.name,
                context=concept_input.context,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_name_callback=self._repos.odm_alias_repository.concept_exists_by_name,
        )

    def _edit_aggregate(
        self, item: OdmAliasAR, concept_edit_input: OdmAliasPatchInput
    ) -> OdmAliasAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=OdmAliasVO.from_repository_values(
                name=concept_edit_input.name,
                context=concept_edit_input.context,
            ),
            concept_exists_by_name_callback=self._repos.odm_alias_repository.concept_exists_by_name,
        )
        return item

    def soft_delete(self, uid: str) -> None:
        if not self._repos.odm_alias_repository.exists_by("uid", uid, True):
            raise NotFoundException(f"Odm Alias with uid {uid} does not exist.")

        if self._repos.odm_alias_repository.has_active_relationships(
            uid,
            ["has_form", "has_item_group", "has_item", "has_condition", "has_method"],
        ):
            raise BusinessLogicException("This ODM Alias is in use.")

        return super().soft_delete(uid)

    def handle_batch_operations(
        self, operations: Sequence[OdmAliasBatchInput]
    ) -> Sequence[OdmAliasBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None

            try:
                if operation.method == "POST":
                    item = self.create(operation.content)
                    response_code = status.HTTP_201_CREATED
                else:
                    item = self.edit_draft(operation.content.uid, operation.content)
                    response_code = status.HTTP_200_OK
            except exceptions.MDRApiBaseException as error:
                result["responseCode"] = error.status_code
                result["content"] = models.error.BatchErrorResponse(message=str(error))
            else:
                result["responseCode"] = response_code
                if item:
                    result["content"] = item.dict()
            finally:
                results.append(OdmAliasBatchOutput(**result))
        return results

    @db.transaction
    def get_active_relationships(self, uid: str):
        if not self._repos.odm_alias_repository.exists_by("uid", uid, True):
            raise exceptions.NotFoundException(
                f"Odm Alias with uid {uid} does not exist."
            )

        return self._repos.odm_alias_repository.get_active_relationships(
            uid,
            ["has_form", "has_item_group", "has_item", "has_condition", "has_method"],
        )
