from datetime import datetime
from typing import Callable, Optional, Sequence, cast

from fastapi import Depends
from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api.domain.unit_definition.unit_definition import (
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from clinical_mdr_api.models.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


def _get_current_user_id(current_user_id: str = Depends(get_current_user_id)) -> str:
    return current_user_id


def _get_meta_repository(
    user_id: str = Depends(_get_current_user_id),
) -> MetaRepository:
    return MetaRepository(user=user_id)


class UnitDefinitionService:
    _repos: MetaRepository
    _user_id: str

    def __init__(
        self,
        *,
        user_id: str = Depends(_get_current_user_id),
        meta_repository: MetaRepository = Depends(_get_meta_repository)
    ):
        self._repos = meta_repository
        self._user_id = user_id

    @db.transaction
    def get_all(
        self,
        library_name: Optional[str],
        dimension: Optional[str] = None,
        subset: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[UnitDefinitionModel]:
        items, total_items = self._repos.unit_definition_repository.find_all(
            library=library_name,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
            dimension=dimension,
            subset=subset,
        )
        units = GenericFilteringReturn.create(items, total_items)
        units.items = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in units.items
        ]

        return units

    def get_distinct_values_for_header(
        self,
        field_name: str,
        library_name: Optional[str],
        dimension: Optional[str] = None,
        subset: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):

        header_values = self._repos.unit_definition_repository.get_distinct_headers(
            library=library_name,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
            dimension=dimension,
            subset=subset,
        )

        return header_values

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        *,
        at_specified_datetime: Optional[datetime],
        status: Optional[str],
        version: Optional[str]
    ) -> UnitDefinitionModel:

        status_as_enum = LibraryItemStatus(status) if status is not None else None

        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid,
            status=status_as_enum,
            version=version,
            for_update=False,
            at_specific_date=at_specified_datetime,
        )
        if unit_definition_ar is None:
            raise NotFoundException("Resource not found.")
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def get_versions(self, uid: str) -> Sequence[UnitDefinitionModel]:
        versions = self._repos.unit_definition_repository.get_all_versions_2(uid)
        if not versions:
            raise NotFoundException("Resource not found.")
        return [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_def_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_def_ar in versions
        ]

    @db.transaction
    def post(self, post_input: UnitDefinitionPostInput) -> UnitDefinitionModel:
        try:
            unit_definition_ar = UnitDefinitionAR.from_input_values(
                author=self._user_id,
                unit_definition_value=self._post_input_to_unit_definition_value_vo(
                    post_input
                ),
                library=LibraryVO.from_input_values_2(
                    library_name=post_input.libraryName,
                    is_library_editable_callback=self._is_library_editable,
                ),
                uid_supplier=self._generate_unit_definition_uid,
                unit_definition_exists_by_name_predicate=self._repos.unit_definition_repository.check_exists_by_name,
                master_unit_exists_for_dimension_predicate=self._repos.unit_definition_repository.master_unit_exists_by_unit_dimension,
                unit_definition_exists_by_legacy_code=self._repos.unit_definition_repository.exists_by_legacy_code,
            )
        except ValueError as value_error:
            raise ValidationException(value_error.args[0]) from value_error
        self._repos.unit_definition_repository.save(unit_definition_ar)
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def patch(
        self, uid: str, patch_input: UnitDefinitionPatchInput
    ) -> UnitDefinitionModel:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )
        if unit_definition_ar is None:
            raise NotFoundException("Resource not found.")
        try:
            new_unit_dimension_value = (
                self._patch_input_to_new_unit_definition_value_vo(
                    patch_input=patch_input, current=unit_definition_ar
                )
            )
            unit_definition_ar.edit_draft(
                author=self._user_id,
                change_description=patch_input.changeDescription,
                new_unit_definition_value=new_unit_dimension_value,
                unit_definition_by_name_exists_predicate=(
                    self._repos.unit_definition_repository.check_exists_by_name
                ),
                master_unit_exists_for_dimension_predicate=(
                    self._repos.unit_definition_repository.master_unit_exists_by_unit_dimension
                ),
                unit_definition_exists_by_legacy_code=(
                    self._repos.unit_definition_repository.exists_by_legacy_code
                ),
            )
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.unit_definition_repository.save(unit_definition_ar)
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    @db.transaction
    def delete(self, uid: str) -> None:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )
        if unit_definition_ar is None:
            raise NotFoundException("Resource not found.")
        try:
            unit_definition_ar.soft_delete()
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.unit_definition_repository.save(unit_definition_ar)

    @db.transaction
    def approve(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).approve(self._user_id)
        )

    @db.transaction
    def inactivate(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).inactivate(self._user_id)
        )

    @db.transaction
    def reactivate(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).reactivate(self._user_id)
        )

    @db.transaction
    def new_version(self, uid: str) -> UnitDefinitionModel:
        return self._workflow_action(
            uid, lambda ar: cast(UnitDefinitionAR, ar).create_new_version(self._user_id)
        )

    def _workflow_action(
        self, uid: str, workflow_ar_method: Callable[[UnitDefinitionAR], None]
    ) -> UnitDefinitionModel:
        unit_definition_ar = self._repos.unit_definition_repository.find_by_uid_2(
            uid, for_update=True
        )
        if unit_definition_ar is None:
            raise NotFoundException("Resource not found.")
        try:
            workflow_ar_method(unit_definition_ar)
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.unit_definition_repository.save(unit_definition_ar)
        return UnitDefinitionModel.from_unit_definition_ar(
            unit_definition_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )

    def _is_library_editable(self, library_name: str) -> Optional[bool]:
        library_ar = self._repos.library_repository.find_by_name(library_name)
        return library_ar.is_editable if library_ar is not None else None

    def _post_input_to_unit_definition_value_vo(
        self, post_input: UnitDefinitionPostInput
    ) -> UnitDefinitionValueVO:
        return UnitDefinitionValueVO.from_input_values(
            si_unit=post_input.siUnit,
            name=post_input.name,
            definition=post_input.definition,
            ct_units=post_input.ctUnits,
            unit_subsets=post_input.unitSubsets,
            ucum_uid=post_input.ucum,
            display_unit=post_input.displayUnit,
            convertible_unit=post_input.convertibleUnit,
            us_conventional_unit=post_input.usConventionalUnit,
            legacy_code=post_input.legacyCode,
            molecular_weight_conv_expon=post_input.molecularWeightConvExpon,
            conversion_factor_to_master=post_input.conversionFactorToMaster,
            unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
            master_unit=post_input.masterUnit,
            unit_dimension_uid=post_input.unitDimension,
            comment=post_input.comment,
            order=post_input.order,
            ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            is_template_parameter=post_input.templateParameter,
        )

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:

        for field_name in base_model_with_missing_values.__fields_set__:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                UnitDefinitionService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.__fields_set__
            - base_model_with_missing_values.__fields_set__
        ).intersection(base_model_with_missing_values.__fields__):
            setattr(
                base_model_with_missing_values,
                field_name,
                getattr(reference_base_model, field_name),
            )

    def _patch_input_to_new_unit_definition_value_vo(
        self, *, patch_input: UnitDefinitionPatchInput, current: UnitDefinitionAR
    ) -> UnitDefinitionValueVO:
        unit_definition_model = UnitDefinitionModel.from_unit_definition_ar(
            current,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
        )
        ConceptGenericService._fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=patch_input,
            reference_base_model=unit_definition_model,
        )
        return UnitDefinitionValueVO.from_input_values(
            name=patch_input.name,
            definition=patch_input.definition,
            ct_units=patch_input.ctUnits,
            unit_subsets=patch_input.unitSubsets,
            ucum_uid=patch_input.ucum,
            convertible_unit=patch_input.convertibleUnit,
            display_unit=patch_input.displayUnit,
            master_unit=patch_input.masterUnit,
            si_unit=patch_input.siUnit,
            us_conventional_unit=patch_input.usConventionalUnit,
            unit_dimension_uid=patch_input.unitDimension,
            legacy_code=patch_input.legacyCode,
            molecular_weight_conv_expon=patch_input.molecularWeightConvExpon,
            conversion_factor_to_master=patch_input.conversionFactorToMaster,
            comment=patch_input.comment,
            order=patch_input.order,
            unit_ct_uid_exists_callback=self._repos.ct_term_name_repository.term_exists,
            ucum_uid_exists_callback=self._repos.dictionary_term_generic_repository.term_exists,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            is_template_parameter=patch_input.templateParameter,
        )

    # noinspection PyMethodMayBeStatic
    def _generate_unit_definition_uid(self) -> str:
        return UnitDefinitionRoot.get_next_free_uid_and_increment_counter()
