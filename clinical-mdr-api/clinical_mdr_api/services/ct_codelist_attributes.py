from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.models import CTCodelistAttributes, CTCodelistAttributesVersion
from clinical_mdr_api.services.ct_codelist_generic_service import (
    CTCodelistGenericService,
)


class CTCodelistAttributesService(CTCodelistGenericService[CTCodelistAttributesAR]):
    aggregate_class = CTCodelistAttributesAR
    repository_interface = CTCodelistAttributesRepository
    version_class = CTCodelistAttributesVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTCodelistAttributesAR
    ) -> CTCodelistAttributes:
        return CTCodelistAttributes.from_ct_codelist_ar(item_ar)

    @db.transaction
    def edit_draft(self, codelist_uid: str, codelist_input: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
            item.edit_draft(
                author=self.user_initials,
                change_description=codelist_input.changeDescription,
                ct_codelist_vo=CTCodelistAttributesVO.from_input_values(
                    name=self.get_input_or_previous_property(
                        codelist_input.name, item.ct_codelist_vo.name
                    ),
                    catalogue_name=item.ct_codelist_vo.catalogue_name,
                    parent_codelist_uid=item.ct_codelist_vo.parent_codelist_uid,
                    child_codelist_uids=item.ct_codelist_vo.child_codelist_uids,
                    submission_value=self.get_input_or_previous_property(
                        codelist_input.submissionValue,
                        item.ct_codelist_vo.submission_value,
                    ),
                    preferred_term=self.get_input_or_previous_property(
                        codelist_input.nciPreferredName,
                        item.ct_codelist_vo.preferred_term,
                    ),
                    definition=self.get_input_or_previous_property(
                        codelist_input.definition, item.ct_codelist_vo.definition
                    ),
                    extensible=self.get_input_or_previous_property(
                        codelist_input.extensible, item.ct_codelist_vo.extensible
                    ),
                    # passing always True callbacks, as we can't change catalogue
                    # in scope of CodelistName or CodelistAttributes, it can be only changed via CTCodelistRoot
                    catalogue_exists_callback=lambda _: True,
                    # passing True, as parent codelist can't be changed once set.
                    codelist_exists_by_uid_callback=lambda _: True,
                ),
                codelist_exists_by_name_callback=self.repository.codelist_specific_exists_by_name,
                codelist_exists_by_submission_value_callback=self.repository.codelist_attributes_exists_by_submission_value,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
        except ValueError as e:
            raise exceptions.ValidationException(e)
