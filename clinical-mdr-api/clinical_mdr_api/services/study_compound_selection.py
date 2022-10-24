from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_selection_compound import (
    StudySelectionCompoundsAR,
    StudySelectionCompoundVO,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_compound_repository import (
    StudyCompoundSelectionHistory,
)
from clinical_mdr_api.models import StudySelectionCompoundInput
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.study_compound_dosing_selection import (
    StudyCompoundDosingRelationMixin,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyCompoundSelectionService(
    StudyCompoundDosingRelationMixin, StudySelectionMixin
):
    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionCompoundsAR
    ) -> Sequence[models.StudySelectionCompound]:
        result = []
        for order, selection in enumerate(
            study_selection.study_compounds_selection, start=1
        ):
            if selection.compound_uid is None:
                compound_model = None
            else:
                compound_model = self._transform_compound_model(
                    compound_uid=selection.compound_uid
                )

            if selection.compound_alias_uid is None:
                compound_alias_model = None
            else:
                compound_alias_model = self._transform_compound_alias_model(
                    selection.compound_alias_uid
                )

            result.append(
                models.StudySelectionCompound.from_study_compound_ar(
                    study_uid=study_selection.study_uid,
                    selection=selection,
                    order=order,
                    compound_model=compound_model,
                    compound_alias_model=compound_alias_model,
                    find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )
            )
        return result

    def _transform_single_to_response_model(
        self, study_selection: StudySelectionCompoundVO, order: int, study_uid: str
    ) -> models.StudySelectionCompound:
        if study_selection.compound_uid is None:
            compound_model = None
        else:
            compound_model = self._transform_compound_model(
                compound_uid=study_selection.compound_uid
            )

        if study_selection.compound_alias_uid is None:
            compound_alias_model = None
        else:
            compound_alias_model = self._transform_compound_alias_model(
                study_selection.compound_alias_uid
            )

        result = models.StudySelectionCompound.from_study_compound_ar(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            compound_model=compound_model,
            compound_alias_model=compound_alias_model,
            find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
        )
        return result

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: models.StudySelectionCompoundInput
    ) -> models.StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_compound_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            new_selection = StudySelectionCompoundVO.from_input_values(
                compound_uid=repos.compound_alias_repository.get_compound_uid_by_alias_uid(
                    selection_create_input.compoundAliasUid
                ),
                study_uid=study_uid,
                compound_alias_uid=selection_create_input.compoundAliasUid,
                type_of_treatment_uid=selection_create_input.typeOfTreatmentUid,
                route_of_administration_uid=selection_create_input.routeOfAdministrationUid,
                strength_value_uid=selection_create_input.strengthValueUid,
                dosage_form_uid=selection_create_input.dosageFormUid,
                dispensed_in_uid=selection_create_input.dispensedInUid,
                device_uid=selection_create_input.deviceUid,
                formulation_uid=selection_create_input.formulationUid,
                other_info=selection_create_input.otherInfo,
                reason_for_missing_value_uid=selection_create_input.reasonForMissingNullValueUid,
                study_compound_dosing_count=0,
                generate_uid_callback=repos.study_selection_compound_repository.generate_uid,
                user_initials=self.author,
            )
            # add VO to aggregate
            try:
                selection_aggregate.add_compound_selection(
                    study_compound_selection=new_selection,
                    selection_uid_by_details_callback=repos.study_selection_compound_repository.get_selection_uid_by_details,
                    reason_for_missing_callback=repos.ct_term_name_repository.term_exists,
                    compound_exist_callback=repos.compound_repository.final_concept_exists,
                    compound_alias_exist_callback=repos.compound_alias_repository.final_concept_exists,
                    compound_callback=repos.compound_repository.find_by_uid_2,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_compound_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the AR object of the new selection, this time with name values for the control terminology
            selection_aggregate = (
                repos.study_selection_compound_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                new_selection.study_selection_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionCompound]:
        repos = self._repos
        compound_selection_ars = repos.study_selection_compound_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )
        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in compound_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar,
            )
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        filtered_items = service_level_generic_filtering(
            items=selections,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_items

    @db.transaction
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: Optional[str] = None,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):
        repos = self._repos

        if study_uid:
            compound_selection_ars = (
                repos.study_selection_compound_repository.find_by_study(study_uid)
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(compound_selection_ars),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        compound_selection_ars = repos.study_selection_compound_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in compound_selection_ars:
            parsed_selections = self._transform_all_to_response_model(ar)
            for selection in parsed_selections:
                selections.append(selection)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=selections,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionCompound]:
        repos = MetaRepository()
        try:
            compound_selection_ar = (
                repos.study_selection_compound_repository.find_by_study(study_uid)
            )
            selection = self._transform_all_to_response_model(compound_selection_ar)
            # Do filtering, sorting, pagination and count
            selection = service_level_generic_filtering(
                items=selection,
                filter_by=filter_by,
                filter_operator=filter_operator,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )
            return selection
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionCompound:
        selection_aggregate = (
            self._repos.study_selection_compound_repository.find_by_study(study_uid)
        )
        try:
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_compound_selection(study_selection_uid)
        except ValueError as value_error:
            raise exceptions.NotFoundException(value_error.args[0])
        return self._transform_single_to_response_model(new_selection, order, study_uid)

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_compound_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.remove_compound_selection(study_selection_uid)

            # cascade delete for compound dosings
            self._delete_compound_dosing_selections(
                study_uid, "study_compound_uid", study_selection_uid
            )

            # sync with DB and save the update
            repos.study_selection_compound_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_compound_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_compound_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_endpoint(
        self,
        request_study_compound: StudySelectionCompoundInput,
        current_study_compound: StudySelectionCompoundVO,
    ) -> StudySelectionCompoundVO:
        # transform current to input model
        transformed_current = StudySelectionCompoundInput(
            compoundUid=current_study_compound.compound_uid,
            typeOfTreatmentUid=current_study_compound.type_of_treatment_uid,
            routeOfAdministrationUid=current_study_compound.route_of_administration_uid,
            dosageFormUid=current_study_compound.dosage_form_uid,
            dispensedInUid=current_study_compound.dispensed_in_uid,
            deviceUid=current_study_compound.device_uid,
            formulationUid=current_study_compound.formulation_uid,
            otherInfo=current_study_compound.other_info,
            reasonForMissingNullValueUid=current_study_compound.reason_for_missing_value_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_compound,
            reference_base_model=transformed_current,
        )

        return StudySelectionCompoundVO.from_input_values(
            compound_uid=self._repos.compound_alias_repository.get_compound_uid_by_alias_uid(
                request_study_compound.compoundAliasUid
            ),
            compound_alias_uid=request_study_compound.compoundAliasUid,
            type_of_treatment_uid=request_study_compound.typeOfTreatmentUid,
            route_of_administration_uid=request_study_compound.routeOfAdministrationUid,
            strength_value_uid=request_study_compound.strengthValueUid,
            dosage_form_uid=request_study_compound.dosageFormUid,
            dispensed_in_uid=request_study_compound.dispensedInUid,
            device_uid=request_study_compound.deviceUid,
            formulation_uid=request_study_compound.formulationUid,
            other_info=request_study_compound.otherInfo,
            reason_for_missing_value_uid=request_study_compound.reasonForMissingNullValueUid,
            study_compound_dosing_count=current_study_compound.study_compound_dosing_count,
            study_selection_uid=current_study_compound.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionCompoundInput,
    ) -> models.StudySelectionCompound:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_compound_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # Load the current VO for updates
            try:
                current_vo, order = selection_aggregate.get_specific_compound_selection(
                    study_selection_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_endpoint(
                request_study_compound=selection_update_input,
                current_study_compound=current_vo,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_compound_selection=updated_selection,
                    selection_uid_by_details_callback=repos.study_selection_compound_repository.get_selection_uid_by_details,
                    reason_for_missing_callback=repos.ct_term_name_repository.term_exists,
                    compound_exist_callback=repos.compound_repository.final_concept_exists,
                    compound_alias_exist_callback=repos.compound_alias_repository.final_concept_exists,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_compound_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_compound_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _transform_history_to_response_model(
        self,
        study_selection_history: List[StudyCompoundSelectionHistory],
        study_uid: str,
    ) -> Sequence[models.StudySelectionCompound]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionCompound.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_compound_by_uid=self._transform_compound_model,
                    get_compound_alias_by_uid=self._transform_compound_alias_model,
                    find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionCompound]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_compound_repository.find_selection_history(
                    study_uid
                )
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionCompound]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_compound_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()
