from typing import Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.library.endpoints import EndpointAR
from clinical_mdr_api.domain.library.timeframes import TimeframeAR
from clinical_mdr_api.domain.study_selection.study_selection_arm import (
    StudySelectionArmAR,
    StudySelectionArmVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_endpoint import (
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.study_selection.study_selection_arm_repository import (
    SelectionHistoryArm,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.study_selection import (
    EndpointUnits,
    StudySelectionEndpointInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyArmSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionArmAR,
    ) -> Sequence[models.StudySelectionArmWithConnectedBranchArms]:
        result = []
        for order, selection in enumerate(
            study_selection.study_arms_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection, order=order, study_uid=study_selection.study_uid
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionArmVO,
        order: int,
        study_uid: str,
    ) -> models.StudySelectionArmWithConnectedBranchArms:
        return models.study_selection.StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
        )

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
    ) -> GenericFilteringReturn[models.StudySelectionArmWithConnectedBranchArms]:
        repos = self._repos
        arm_selection_ars = repos.study_selection_arm_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in arm_selection_ars:
            parsed_selections = self._transform_all_to_response_model(ar)
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
            arm_selection_ar = repos.study_selection_arm_repository.find_by_study(
                study_uid
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(arm_selection_ar),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        arm_selection_ars = repos.study_selection_arm_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in arm_selection_ars:
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
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionArmWithConnectedBranchArms]:
        repos = MetaRepository()
        try:
            arm_selection_ar = repos.study_selection_arm_repository.find_by_study(
                study_uid
            )

            filtered_items = service_level_generic_filtering(
                items=self._transform_all_to_response_model(arm_selection_ar),
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
            # delete study branch arms assigned to arm
            branch_arms_on_arm = None
            if repos.study_selection_arm_repository.arm_specific_has_connected_branch_arms(
                study_uid=study_uid, arm_uid=study_selection_uid
            ):
                branch_arms_on_arm = repos.study_selection_branch_arm_repository.get_branch_arms_connected_to_arm(
                    study_uid=study_uid, study_arm_uid=study_selection_uid
                )
            design_cells_on_branch_arm = []
            design_cells_to_delete_from_branch_arm = []
            if branch_arms_on_arm is not None:
                for i_branch_arm in branch_arms_on_arm:
                    cascade_deletion_last_branch = False
                    # if the branch_arm has connected design cells
                    if repos.study_selection_branch_arm_repository.branch_arm_specific_has_connected_cell(
                        study_uid=study_uid,
                        branch_arm_uid=i_branch_arm.uid,
                    ):
                        design_cells_on_branch_arm = self._repos.study_design_cell_repository.get_design_cells_connected_to_branch_arm(
                            study_uid=study_uid, study_branch_arm_uid=i_branch_arm.uid
                        )
                        # if the studyBranchArm is the last StudyBranchArm of its StudyArm root
                        if repos.study_selection_branch_arm_repository.branch_arm_specific_is_last_on_arm_root(
                            study_uid=study_uid,
                            arm_root_uid=study_selection_uid,
                            branch_arm_uid=i_branch_arm.uid,
                        ):
                            # switch all the study designcells to the study branch arm
                            cascade_deletion_last_branch = True

                        # else the studyBranchArm is not last StudyBranchArm of its StudyArm root
                        else:
                            design_cells_to_delete_from_branch_arm = (
                                design_cells_on_branch_arm
                            )
                    # Load aggregate
                    branch_arm_aggregate = (
                        repos.study_selection_branch_arm_repository.find_by_study(
                            study_uid=study_uid, for_update=True
                        )
                    )
                    # remove the connection
                    branch_arm_aggregate.remove_branch_arm_selection(i_branch_arm.uid)

                    # sync with DB and save the update
                    repos.study_selection_branch_arm_repository.save(
                        branch_arm_aggregate, self.author
                    )

                    if cascade_deletion_last_branch:
                        for i_design_cell in design_cells_on_branch_arm:
                            self._repos.study_design_cell_repository.patch_study_arm(
                                study_uid=study_uid,
                                design_cell_uid=i_design_cell.uid,
                                study_arm_uid=study_selection_uid,
                                author=self.author,
                            )

            # delete study design cells assigned assigned to arm
            design_cells_on_arm = []
            if repos.study_selection_arm_repository.arm_specific_has_connected_cell(
                study_uid=study_uid, arm_uid=study_selection_uid
            ):
                design_cells_on_arm = self._repos.study_design_cell_repository.get_design_cells_connected_to_arm(
                    study_uid=study_uid, study_arm_uid=study_selection_uid
                )
            if (
                design_cells_on_arm != []
                or design_cells_to_delete_from_branch_arm != []
            ):
                # service_design_cell = StudyDesignCellService(author=current_user_id)
                design_cells_to_delete_in_desc_order = (
                    design_cells_on_arm + design_cells_to_delete_from_branch_arm
                )
                design_cells_to_delete_in_desc_order = sorted(
                    design_cells_to_delete_in_desc_order,
                    key=lambda dc: dc.order,
                    reverse=True,
                )
                for i_design_cell in design_cells_to_delete_in_desc_order:
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

            # delete arm
            # Load aggregate
            selection_aggregate = repos.study_selection_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_arm_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_arm_repository.save(selection_aggregate, self.author)
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionArmWithConnectedBranchArms:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_selection_arm_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_arm_selection(
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
        request_study_endpoint: StudySelectionEndpointInput,
        current_study_endpoint: StudySelectionEndpointVO,
    ) -> StudySelectionEndpointVO:

        endpoint_repo = self._repos.endpoint_repository
        timeframe_repo = self._repos.timeframe_repository
        if request_study_endpoint.endpointUid:
            endpoint_ar: EndpointAR = endpoint_repo.find_by_uid_2(
                request_study_endpoint.endpointUid
            )
        elif current_study_endpoint.endpoint_uid:
            endpoint_ar: EndpointAR = endpoint_repo.find_by_uid_2(
                current_study_endpoint.endpoint_uid
            )
        else:
            endpoint_ar = None
        if request_study_endpoint.timeframeUid:
            timeframe_ar: TimeframeAR = timeframe_repo.find_by_uid_2(
                request_study_endpoint.timeframeUid
            )
        elif current_study_endpoint.timeframe_uid:
            timeframe_ar: TimeframeAR = timeframe_repo.find_by_uid_2(
                current_study_endpoint.timeframe_uid
            )
        else:
            timeframe_ar = None

        # transform current to input model
        transformed_current = StudySelectionEndpointInput(
            endpointUid=current_study_endpoint.endpoint_uid,
            endpointLevelUid=current_study_endpoint.endpoint_level_uid,
            endpointUnits=EndpointUnits(
                units=current_study_endpoint.endpoint_units,
                separator=current_study_endpoint.unit_separator,
            ),
            studyObjectiveUid=current_study_endpoint.study_objective_uid,
            timeframeUid=current_study_endpoint.timeframe_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_endpoint,
            reference_base_model=transformed_current,
        )

        # get order from the endpoint level CT term
        if request_study_endpoint.endpointLevelUid is not None:
            endpoint_level_order = (
                self._repos.ct_term_name_repository.term_specific_order_by_uid(
                    uid=request_study_endpoint.endpointLevelUid
                )
            )
        else:
            endpoint_level_order = None

        return StudySelectionEndpointVO.from_input_values(
            endpoint_uid=request_study_endpoint.endpointUid,
            endpoint_version=endpoint_ar.item_metadata.version if endpoint_ar else None,
            endpoint_level_uid=request_study_endpoint.endpointLevelUid,
            endpoint_sub_level_uid=request_study_endpoint.endpointSubLevelUid,
            endpoint_units=request_study_endpoint.endpointUnits.units,
            timeframe_uid=request_study_endpoint.timeframeUid,
            timeframe_version=timeframe_ar.item_metadata.version
            if timeframe_ar
            else None,
            unit_separator=request_study_endpoint.endpointUnits.separator,
            study_objective_uid=request_study_endpoint.studyObjectiveUid,
            study_selection_uid=current_study_endpoint.study_selection_uid,
            endpoint_level_order=endpoint_level_order,
            user_initials=self.author,
        )

    @db.transaction
    def update_selection_to_latest_version_of_endpoint(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        endpoint_uid = selection.endpoint_uid
        endpoint_ar = self._repos.endpoint_repository.find_by_uid_2(endpoint_uid)
        if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            endpoint_ar.approve(self.author)
            self._repos.endpoint_repository.save(endpoint_ar)
        elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.update_endpoint_version(
            endpoint_ar.item_metadata.version
        )
        selection_ar.update_selection(
            new_selection, endpoint_exist_callback=lambda x: True
        )
        self._repos.study_selection_endpoint_repository.save(selection_ar, self.author)

        return self._transform_single_to_response_model(new_selection, order, study_uid)

    @db.transaction
    def update_selection_to_latest_version_of_timeframe(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        timeframe_uid = selection.timeframe_uid
        timeframe_ar = self._repos.timeframe_repository.find_by_uid_2(timeframe_uid)
        if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            timeframe_ar.approve(self.author)
            self._repos.timeframe_repository.save(timeframe_ar)
        elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired timeframe as selection. Please reactivate."
            )
        new_selection = selection.update_timeframe_version(
            timeframe_ar.item_metadata.version
        )
        selection_ar.update_selection(
            new_selection, timeframe_exist_callback=lambda x: True
        )
        self._repos.study_selection_endpoint_repository.save(selection_ar, self.author)

        return self._transform_single_to_response_model(new_selection, order, study_uid)

    @db.transaction
    def update_selection_accept_versions(
        self, study_uid: str, study_selection_uid: str
    ):
        selection: StudySelectionEndpointVO
        selection_ar, selection, order = self._get_specific_endpoint_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        endpoint_uid = selection.endpoint_uid
        endpoint_ar = self._repos.endpoint_repository.find_by_uid_2(endpoint_uid)
        if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            endpoint_ar.approve(self.author)
            self._repos.endpoint_repository.save(endpoint_ar)
        elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.accept_versions()
        selection_ar.update_selection(
            new_selection, endpoint_exist_callback=lambda x: True
        )
        self._repos.study_selection_endpoint_repository.save(selection_ar, self.author)

        return self._transform_single_to_response_model(new_selection, order, study_uid)

    def _transform_single_study_objective_to_model(
        self, study_uid: str, study_selection_uid: str, no_brackets: bool = False
    ) -> models.StudySelectionObjective:
        repos = self._repos
        selection_aggregate = repos.study_selection_objective_repository.find_by_study(
            study_uid
        )
        try:
            assert selection_aggregate is not None
            _, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )
        except ValueError as value_error:
            raise exceptions.NotFoundException(value_error.args[0])
        result = models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_aggregate,
            order=order,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
            get_study_selection_endpoints_ar_by_study_uid_callback=(
                repos.study_selection_endpoint_repository.find_by_study
            ),
            no_brackets=no_brackets,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
        )
        return result

    def _transform_each_history_to_response_model(
        self, study_selection_history: SelectionHistoryArm, study_uid: str
    ) -> Sequence[models.StudySelectionArm]:
        return models.StudySelectionArm.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
            get_ct_term_arm_type=self._find_by_uid_or_raise_not_found,
        )

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionArmVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_arm_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_arms
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
                    data = calculate_diffs(versions, models.StudySelectionArmVersion)
                else:
                    data.extend(
                        calculate_diffs(versions, models.StudySelectionArmVersion)
                    )
            return data
            # return self._transform_history_to_response_model(
            #     selection_history, study_uid
            # )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionArmVersion]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_arm_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            versions = [
                self._transform_each_history_to_response_model(_, study_uid).dict()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, models.StudySelectionArmVersion)
            return data
        finally:
            repos.close()

    # Helper function to find CT term names
    def find_term_name_by_uid(self, uid):
        return SimpleTermModel.from_ct_code(
            uid, self._repos.ct_term_name_repository.find_by_uid
        )

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionArmCreateInput,
    ) -> models.StudySelectionArm:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionArmVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.shortName,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    arm_colour=selection_create_input.armColour,
                    randomization_group=selection_create_input.randomizationGroup,
                    number_of_subjects=selection_create_input.numberOfSubjects,
                    arm_type_uid=selection_create_input.armTypeUid,
                    generate_uid_callback=repos.study_selection_arm_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionArmAR = (
                    repos.study_selection_arm_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                try:
                    selection_aggregate.add_arm_selection(
                        new_selection,
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                        arm_exists_callback_by=repos.study_selection_arm_repository.arm_exists_by,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_arm_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                new_selection, order = selection_aggregate.get_specific_arm_selection(
                    new_selection.study_selection_uid
                )

                # add the arm and return
                # StudyArm without connected BranchArms not make sense that has BranchArms yet
                return models.StudySelectionArm.from_study_selection_arm_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
                )
        finally:
            repos.close()

    def _patch_prepare_new_study_arm(
        self,
        request_study_arm: models.StudySelectionArmInput,
        current_study_arm: StudySelectionArmVO,
    ) -> StudySelectionArmVO:
        # transform current to input model
        transformed_current = models.StudySelectionArmInput(
            armUid=current_study_arm.study_selection_uid,
            name=current_study_arm.name,
            shortName=current_study_arm.short_name,
            code=current_study_arm.code,
            description=current_study_arm.description,
            armColour=current_study_arm.arm_colour,
            randomizationGroup=current_study_arm.randomization_group,
            numberOfSubjects=current_study_arm.number_of_subjects,
            armTypeUid=current_study_arm.arm_type_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_arm,
            reference_base_model=transformed_current,
        )

        return StudySelectionArmVO.from_input_values(
            study_uid=current_study_arm.study_uid,
            name=request_study_arm.name,
            short_name=request_study_arm.shortName,
            code=request_study_arm.code,
            description=request_study_arm.description,
            arm_colour=request_study_arm.armColour,
            randomization_group=request_study_arm.randomizationGroup,
            number_of_subjects=request_study_arm.numberOfSubjects,
            arm_type_uid=request_study_arm.armTypeUid,
            study_selection_uid=current_study_arm.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionArmInput,
    ) -> models.StudySelectionArmWithConnectedBranchArms:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionArmAR = (
                repos.study_selection_arm_repository.find_by_study(
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
            updated_selection = self._patch_prepare_new_study_arm(
                request_study_arm=selection_update_input, current_study_arm=current_vo
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_arm_selection=updated_selection,
                    ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    arm_exists_callback_by=repos.study_selection_arm_repository.arm_exists_by,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])
            # sync with DB and save the update
            repos.study_selection_arm_repository.save(selection_aggregate, self.author)

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the arm and return
            # With Connected BranchArms because can carry out the connected BranchARms
            return models.study_selection.StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
                find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionArmWithConnectedBranchArms:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_arm_selection_by_uids(study_uid, study_selection_uid)
        # With Connected BranchArms due to it may has already connected BranchArms to it
        return models.study_selection.StudySelectionArmWithConnectedBranchArms.from_study_selection_arm_ar__order__connected_branch_arms(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
            find_multiple_connected_branch_arm=self._find_branch_arms_connected_to_arm_uid,
        )
