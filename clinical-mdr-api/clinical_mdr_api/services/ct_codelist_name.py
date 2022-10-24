from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)
from clinical_mdr_api.models import CTCodelistName, CTCodelistNameVersion
from clinical_mdr_api.services.ct_codelist_generic_service import (
    CTCodelistGenericService,
)


class CTCodelistNameService(CTCodelistGenericService[CTCodelistNameAR]):
    aggregate_class = CTCodelistNameAR
    repository_interface = CTCodelistNameRepository
    version_class = CTCodelistNameVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CTCodelistNameAR
    ) -> CTCodelistName:
        return CTCodelistName.from_ct_codelist_ar(item_ar)

    @db.transaction
    def edit_draft(self, codelist_uid: str, codelist_input: BaseModel) -> BaseModel:
        try:
            item = self._find_by_uid_or_raise_not_found(codelist_uid, for_update=True)
            item.edit_draft(
                author=self.user_initials,
                change_description=codelist_input.changeDescription,
                ct_codelist_vo=CTCodelistNameVO.from_input_values(
                    name=self.get_input_or_previous_property(
                        codelist_input.name, item.name
                    ),
                    catalogue_name=item.ct_codelist_vo.catalogue_name,
                    is_template_parameter=self.get_input_or_previous_property(
                        codelist_input.templateParameter,
                        item.ct_codelist_vo.is_template_parameter,
                    ),
                    # passing always True callbacks, as we can't change catalogue
                    # in scope of CodelistName or CodelistAttributes, it can be only changed via CTCodelistRoot
                    catalogue_exists_callback=lambda _: True,
                ),
                codelist_exists_by_name_callback=self.repository.codelist_specific_exists_by_name,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
        except ValueError as e:
            raise exceptions.ValidationException(e)
