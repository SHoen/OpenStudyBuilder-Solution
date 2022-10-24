import datetime
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_compound_dosing import (
    StudyCompoundDosingVO,
    StudySelectionCompoundDosingsAR,
)
from clinical_mdr_api.domain_repositories.study_selection.study_compound_dosing_repository import (
    SelectionHistory,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyCompoundDosingRelationMixin:
    def _delete_compound_dosing_selections(self, study_uid: str, key: str, value: str):
        """Delete all selected compound dosings for given study and key/value attr."""
        compound_dosing_selection_ar = (
            self._repos.study_compound_dosing_repository.find_by_study(
                study_uid, for_update=True
            )
        )
        for (
            compound_dosing
        ) in compound_dosing_selection_ar.study_compound_dosings_selection:
            if getattr(compound_dosing, key) == value:
                compound_dosing_selection_ar.remove_compound_dosing_selection(
                    compound_dosing.study_selection_uid
                )
        self._repos.study_compound_dosing_repository.save(
            compound_dosing_selection_ar, self.author
        )


class StudyCompoundDosingSelectionService(StudySelectionMixin):

    _repos: MetaRepository

    def __init__(self, author: str):
        self._repos = MetaRepository()
        self.author = author

    def _transform_study_compound_model(
        self,
        study_uid: str,
        study_compound_uid: str,
        compound_uid: str,
        compound_alias_uid: str,
    ) -> models.StudySelectionCompound:
        (
            study_compound,
            order,
        ) = self._repos.study_selection_compound_repository.find_by_uid(
            study_uid, study_compound_uid
        )
        compound = self._transform_compound_model(compound_uid)
        compound_alias = self._transform_compound_alias_model(compound_alias_uid)

        return models.StudySelectionCompound.from_study_compound_ar(
            study_uid=study_uid,
            selection=study_compound,
            order=order,
            compound_model=compound,
            compound_alias_model=compound_alias,
            find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
        )

    def _transform_study_element_model(
        self, study_uid: str, study_element_uid: str
    ) -> models.StudySelectionElement:
        (
            study_element,
            order,
        ) = self._repos.study_selection_element_repository.find_by_uid(
            study_uid, study_element_uid
        )
        return models.study_selection.StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid,
            study_element,
            order,
            self._find_by_uid_or_raise_not_found,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

    def _transform_to_response_model(
        self, study_uid: str, compound_dosing_vo: StudyCompoundDosingVO, order: int
    ) -> models.StudyCompoundDosing:
        return models.StudyCompoundDosing.from_vo(
            compound_dosing_vo,
            order,
            self._transform_study_compound_model(
                study_uid,
                compound_dosing_vo.study_compound_uid,
                compound_dosing_vo.compound_uid,
                compound_dosing_vo.compound_alias_uid,
            ),
            self._transform_study_element_model(
                study_uid, compound_dosing_vo.study_element_uid
            ),
            find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
        )

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionCompoundDosingsAR
    ) -> Sequence[models.StudyCompoundDosing]:
        result = []
        for order, selection in enumerate(
            study_selection.study_compound_dosings_selection, start=1
        ):
            result.append(
                self._transform_to_response_model(
                    study_selection.study_uid, selection, order
                )
            )
        return result

    @db.transaction
    def get_all_compound_dosings(
        self,
        study_uid: str,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudyCompoundDosing]:
        repos = MetaRepository()
        try:
            selection_ar = repos.study_compound_dosing_repository.find_by_study(
                study_uid
            )
            selection = self._transform_all_to_response_model(selection_ar)
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
    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):
        repos = self._repos

        if study_uid:
            selection_ars = repos.study_compound_dosing_repository.find_by_study(
                study_uid
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(selection_ars),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        selection_ars = repos.study_compound_dosing_repository.find_all()
        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in selection_ars:
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

    def _transform_history_to_response_model(
        self,
        study_selection_history: List[SelectionHistory],
        study_uid: str,
    ) -> Sequence[models.StudyCompoundDosing]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudyCompoundDosing.from_study_selection_history(
                    history,
                    study_uid,
                    history.order,
                    self._transform_study_compound_model(
                        study_uid,
                        history.study_compound_uid,
                        history.compound_uid,
                        history.compound_alias_uid,
                    ),
                    self._transform_study_element_model(
                        study_uid, history.study_element_uid
                    ),
                    find_simple_term_model_name_by_term_uid=self.find_term_name_by_uid,
                    find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
                    find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                )
            )
        return result

    def get_compound_dosing_audit_trail(
        self, study_uid: str, compound_dosing_uid: str
    ) -> Sequence[models.StudyCompoundDosing]:
        try:
            selection_history = (
                self._repos.study_compound_dosing_repository.find_selection_history(
                    study_uid, compound_dosing_uid
                )
            )
        except ValueError as value_error:
            raise exceptions.NotFoundException(value_error.args[0])

        return self._transform_history_to_response_model(selection_history, study_uid)

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: models.StudyCompoundDosingInput
    ) -> models.StudyCompoundDosing:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            (
                study_compound_vo,
                _order,
            ) = repos.study_selection_compound_repository.find_by_uid(
                study_uid=study_uid,
                study_compound_uid=selection_create_input.studyCompoundUid,
            )
            new_selection = StudyCompoundDosingVO.from_input_values(
                study_uid=study_uid,
                study_element_uid=selection_create_input.studyElementUid,
                study_compound_uid=selection_create_input.studyCompoundUid,
                compound_uid=study_compound_vo.compound_uid,
                compound_alias_uid=study_compound_vo.compound_alias_uid,
                dose_frequency_uid=selection_create_input.doseFrequencyUid,
                dose_value_uid=selection_create_input.doseValueUid,
                user_initials=self.author,
                start_date=datetime.datetime.now(),
                generate_uid_callback=repos.study_compound_dosing_repository.generate_uid,
            )
            # add VO to aggregate
            try:
                selection_aggregate.add_compound_dosing_selection(
                    study_compound_dosing_selection=new_selection,
                    selection_uid_by_compound_dose_and_frequency_callback=(
                        repos.study_compound_dosing_repository.get_selection_uid_by_compound_dose_and_frequency
                    ),
                    compound_callback=repos.compound_repository.find_by_uid_2,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the AR object of the new selection, this time with name values for the control terminology
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_compound_dosing_selection(
                new_selection.study_selection_uid
            )
            # add the objective and return
            return self._transform_to_response_model(study_uid, new_selection, order)
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_compound_dosing_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_selection(
        self,
        request_study_compound_dosing: models.StudyCompoundDosingInput,
        current_study_compound_dosing: StudyCompoundDosingVO,
    ) -> StudyCompoundDosingVO:
        # transform current to input model
        transformed_current = models.StudyCompoundDosingInput(
            studyCompoundUid=current_study_compound_dosing.study_compound_uid,
            studyElementUid=current_study_compound_dosing.study_element_uid,
            doseValueUid=current_study_compound_dosing.dose_value_uid,
            doseFrequencyUid=current_study_compound_dosing.dose_frequency_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_compound_dosing,
            reference_base_model=transformed_current,
        )

        return StudyCompoundDosingVO(
            study_uid=current_study_compound_dosing.study_uid,
            study_selection_uid=current_study_compound_dosing.study_selection_uid,
            study_element_uid=request_study_compound_dosing.studyElementUid,
            study_compound_uid=request_study_compound_dosing.studyCompoundUid,
            dose_frequency_uid=request_study_compound_dosing.doseFrequencyUid,
            dose_value_uid=request_study_compound_dosing.doseValueUid,
            user_initials=self.author,
            start_date=datetime.datetime.now(),
            compound_uid=current_study_compound_dosing.compound_uid,
            compound_alias_uid=current_study_compound_dosing.compound_alias_uid,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudyCompoundDosingInput,
    ) -> models.StudyCompoundDosing:
        repos = MetaRepository()
        try:
            # Load aggregate
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # Load the current VO for updates
            try:
                (
                    current_vo,
                    order,
                ) = selection_aggregate.get_specific_compound_dosing_selection(
                    study_selection_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_selection(
                request_study_compound_dosing=selection_update_input,
                current_study_compound_dosing=current_vo,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_compound_dosing_selection=updated_selection,
                    selection_uid_by_compound_dose_and_frequency_callback=(
                        repos.study_compound_dosing_repository.get_selection_uid_by_compound_dose_and_frequency
                    ),
                    compound_callback=repos.compound_repository.find_by_uid_2,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_compound_dosing_repository.save(
                selection_aggregate, self.author
            )

            # Reload aggregate (to fetch compound and alias uids)
            selection_aggregate = repos.study_compound_dosing_repository.find_by_study(
                study_uid=study_uid
            )

            # Fetch the new selection which was just updated
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_compound_dosing_selection(
                study_selection_uid
            )

            # add the compound dosing and return
            return self._transform_to_response_model(study_uid, new_selection, order)
        finally:
            repos.close()
