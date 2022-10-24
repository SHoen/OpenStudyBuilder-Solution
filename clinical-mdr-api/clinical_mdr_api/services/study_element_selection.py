from typing import Callable, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.study_selection.study_selection_element import (
    StudySelectionElementAR,
    StudySelectionElementVO,
)
from clinical_mdr_api.domain_repositories.study_selection.study_design_cell_repository import (
    StudyDesignCellRepository,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_element_repository import (
    SelectionHistoryElement,
)
from clinical_mdr_api.models.study_selection import StudyElementTypes
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    create_duration_object_from_api_input,
    fill_missing_values_in_base_model_from_reference_base_model,
    get_unit_def_uid_or_none,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.study_compound_dosing_selection import (
    StudyCompoundDosingRelationMixin,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyElementSelectionService(
    StudyCompoundDosingRelationMixin, StudySelectionMixin
):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionElementAR
    ) -> Sequence[models.StudySelectionElement]:
        result = []
        # go over each VO study element selection object
        for order, selection in enumerate(
            study_selection.study_elements_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection,
                    order=order,
                    study_uid=study_selection.study_uid,
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionElementVO,
        order: int,
        study_uid: str,
    ) -> models.StudySelectionElement:
        return models.study_selection.StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid,
            study_selection,
            order,
            self._find_by_uid_or_raise_not_found,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

    def _transform_each_history_to_response_model(
        self, study_selection_history: SelectionHistoryElement, study_uid: str
    ) -> Sequence[models.StudySelectionElement]:
        return models.StudySelectionElement.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
            get_ct_term_element_subtype=self._find_by_uid_or_raise_not_found,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionElementVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_element_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])
            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_elements
            data = []
            for i_unique in unique_list_uids:
                ith_selection_history = []
                # gather the selection history of the i_unique Uid
                for x in selection_history:
                    if x.study_selection_uid == i_unique:
                        ith_selection_history.append(x)
                # get the versions and compare
                versions = [
                    self._transform_each_history_to_response_model(_, study_uid).dict()
                    for _ in ith_selection_history
                ]
                if not data:
                    data = calculate_diffs(
                        versions, models.StudySelectionElementVersion
                    )
                else:
                    data.extend(
                        calculate_diffs(versions, models.StudySelectionElementVersion)
                    )
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionElementVersion]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_element_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            versions = [
                self._transform_each_history_to_response_model(_, study_uid).dict()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, models.StudySelectionElementVersion)
            return data
        finally:
            repos.close()

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionElementCreateInput,
    ) -> models.StudySelectionElement:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionElementVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.shortName,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    planned_duration=(
                        create_duration_object_from_api_input(
                            value=selection_create_input.plannedDuration.durationValue,
                            unit=get_unit_def_uid_or_none(
                                selection_create_input.plannedDuration.durationUnitCode
                            ),
                            find_duration_name_by_code=self._repos.unit_definition_repository.find_by_uid_2,
                        )
                        if selection_create_input.plannedDuration is not None
                        else None
                    ),
                    start_rule=selection_create_input.startRule,
                    end_rule=selection_create_input.endRule,
                    element_colour=selection_create_input.elementColour,
                    element_subtype_uid=selection_create_input.elementSubTypeUid,
                    study_compound_dosing_count=0,
                    generate_uid_callback=repos.study_selection_element_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionElementAR = (
                    repos.study_selection_element_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                try:

                    selection_aggregate.add_element_selection(
                        new_selection,
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                ## sync with DB and save the update
                repos.study_selection_element_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_element_selection(
                    new_selection.study_selection_uid
                )

                # add the element and return
                return models.StudySelectionElement.from_study_selection_element_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    find_simple_term_element_subtype_by_term_uid=self._find_by_uid_or_raise_not_found,
                    find_all_study_time_units=self._repos.unit_definition_repository.find_all,
                )
        finally:
            repos.close()

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionElement]:
        repos = MetaRepository()
        try:
            element_selection_ar = (
                repos.study_selection_element_repository.find_by_study(study_uid)
            )
            filtered_items = service_level_generic_filtering(
                items=self._transform_all_to_response_model(element_selection_ar),
                filter_by=filter_by,
                filter_operator=filter_operator,
                sort_by=sort_by,
                total_count=total_count,
                page_number=page_number,
                page_size=page_size,
            )

            return filtered_items
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # cascade delete
            # if the element has connected design cells
            design_cells_on_element = None
            if repos.study_selection_element_repository.element_specific_has_connected_cell(
                study_uid=study_uid, element_uid=study_selection_uid
            ):
                design_cells_on_element = (
                    StudyDesignCellRepository.get_design_cells_connected_to_element(
                        self, study_uid=study_uid, study_element_uid=study_selection_uid
                    )
                )

            if design_cells_on_element is not None:
                for i_design_cell in design_cells_on_element:
                    study_design_cell = (
                        self._repos.study_design_cell_repository.find_by_uid(
                            study_uid=study_uid, uid=i_design_cell.uid
                        )
                    )
                    self._repos.study_design_cell_repository.delete(
                        study_uid, i_design_cell.uid, self.author
                    )
                    all_design_cells = self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                        study_uid
                    )
                    # shift one order more to fit the modified
                    for design_cell in all_design_cells[study_design_cell.order - 1 :]:
                        design_cell.order -= 1
                        self._repos.study_design_cell_repository.save(
                            design_cell, author=self.author, create=False
                        )

            # Load aggregate
            selection_aggregate = (
                repos.study_selection_element_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.remove_element_selection(study_selection_uid)

            # cascade delete for compound dosings
            self._delete_compound_dosing_selections(
                study_uid, "study_element_uid", study_selection_uid
            )

            # sync with DB and save the update
            repos.study_selection_element_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionElement:
        (
            _selection_aggregate,
            new_selection,
            order,
        ) = self._get_specific_element_selection_by_uids(study_uid, study_selection_uid)
        return models.StudySelectionElement.from_study_selection_element_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_element_subtype_by_term_uid=self._find_by_uid_or_raise_not_found,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

    def _patch_prepare_new_study_element(
        self,
        request_study_element: models.StudySelectionElementInput,
        current_study_element: StudySelectionElementVO,
        find_duration_name_by_code: Callable[[str], Optional[CTTermNameAR]],
    ) -> StudySelectionElementVO:

        # transform current to input model
        transformed_current = models.StudySelectionElementInput.from_study_selection_element(
            selection=current_study_element,
            find_all_study_time_units=self._repos.unit_definition_repository.find_all,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_element,
            reference_base_model=transformed_current,
        )

        return StudySelectionElementVO.from_input_values(
            study_uid=current_study_element.study_uid,
            name=request_study_element.name,
            short_name=request_study_element.shortName,
            code=request_study_element.code,
            description=request_study_element.description,
            planned_duration=(
                create_duration_object_from_api_input(
                    value=request_study_element.plannedDuration.durationValue,
                    unit=get_unit_def_uid_or_none(
                        request_study_element.plannedDuration.durationUnitCode
                    ),
                    find_duration_name_by_code=find_duration_name_by_code,
                )
                if request_study_element.plannedDuration is not None
                else None
            ),
            start_rule=request_study_element.startRule,
            end_rule=request_study_element.endRule,
            element_colour=request_study_element.elementColour,
            element_subtype_uid=request_study_element.elementSubTypeUid,
            study_compound_dosing_count=current_study_element.study_compound_dosing_count,
            study_selection_uid=current_study_element.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionElementInput,
    ) -> models.StudySelectionElement:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionElementAR = (
                repos.study_selection_element_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            try:
                current_vo, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_element(
                request_study_element=selection_update_input,
                current_study_element=current_vo,
                find_duration_name_by_code=self._repos.unit_definition_repository.find_by_uid_2,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_element_selection=updated_selection,
                    ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])
            # sync with DB and save the update
            repos.study_selection_element_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the element and return
            return models.StudySelectionElement.from_study_selection_element_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_simple_term_element_subtype_by_term_uid=self._find_by_uid_or_raise_not_found,
                find_all_study_time_units=self._repos.unit_definition_repository.find_all,
            )
        finally:
            repos.close()

    def get_allowed_configs(self):
        resp = []
        for (
            item
        ) in self._repos.study_selection_element_repository.get_allowed_configs():
            resp.append(
                StudyElementTypes(
                    subtype=item[0],
                    subtype_name=item[1],
                    type=item[2],
                    type_name=item[3],
                )
            )
        return resp

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionElement:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_element_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_element_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_element_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def get_distinct_values_for_header(
        self,
        field_name: str,
        study_uid: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):
        all_items = self.get_all_selection(study_uid=study_uid)

        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )

        return header_values
