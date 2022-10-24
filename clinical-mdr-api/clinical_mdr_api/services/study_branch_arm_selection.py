from typing import Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_selection_branch_arm import (
    StudySelectionBranchArmAR,
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_branch_arm_repository import (
    SelectionHistoryBranchArm,
)
from clinical_mdr_api.models.study_selection import (
    StudyDesignCellBatchInput,
    StudyDesignCellEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyBranchArmSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionBranchArmAR,
    ) -> Sequence[models.StudySelectionBranchArm]:
        result = []
        for order, selection in enumerate(
            study_selection.study_branch_arms_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection, order=order, study_uid=study_selection.study_uid
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionBranchArmVO,
        order: int,
        study_uid: str,
    ) -> models.StudySelectionBranchArm:
        return (
            models.StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
                study_uid,
                study_selection,
                order,
                self._get_specific_arm_selection,
            )
        )

    @db.transaction
    def get_all_selection(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionBranchArm]:
        repos = MetaRepository()
        try:
            branch_arm_selection_ar = (
                repos.study_selection_branch_arm_repository.find_by_study(study_uid)
            )
            return self._transform_all_to_response_model(branch_arm_selection_ar)
        finally:
            repos.close()

    @db.transaction
    def get_all_selection_within_arm(
        self, study_uid: str, study_arm_uid: str
    ) -> Sequence[models.StudySelectionBranchArm]:
        repos = MetaRepository()
        try:
            branch_arm_selection_ar = (
                repos.study_selection_branch_arm_repository.find_by_arm(
                    study_uid=study_uid, study_arm_uid=study_arm_uid
                )
            )
            return self._transform_all_to_response_model(branch_arm_selection_ar)
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            branch_arm_aggregate = (
                repos.study_selection_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            for selection in branch_arm_aggregate.study_branch_arms_selection:
                if selection.study_selection_uid == study_selection_uid:
                    selection_to_delete = selection

            cascade_deletion_last_branch = False
            # if the branch_arm has connected design cells
            if repos.study_selection_branch_arm_repository.branch_arm_specific_has_connected_cell(
                study_uid=study_uid,
                branch_arm_uid=study_selection_uid,
            ):
                design_cells_on_branch_arm = self._repos.study_design_cell_repository.get_design_cells_connected_to_branch_arm(
                    study_uid=study_uid, study_branch_arm_uid=study_selection_uid
                )
                # if the studyBranchArm is the last StudyBranchArm of its StudyArm root
                if repos.study_selection_branch_arm_repository.branch_arm_specific_is_last_on_arm_root(
                    study_uid=study_uid,
                    arm_root_uid=selection_to_delete.arm_root_uid,
                    branch_arm_uid=study_selection_uid,
                ):
                    # switch all the study designcells to the study branch arm
                    cascade_deletion_last_branch = True

                # else the studyBranchArm is not last StudyBranchArm of its StudyArm root
                else:
                    for i_design_cell in design_cells_on_branch_arm:
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
                        for design_cell in all_design_cells[
                            study_design_cell.order - 1 :
                        ]:
                            design_cell.order -= 1
                            self._repos.study_design_cell_repository.save(
                                design_cell, author=self.author, create=False
                            )

            # remove the connection
            branch_arm_aggregate.remove_branch_arm_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_branch_arm_repository.save(
                branch_arm_aggregate, self.author
            )

            if cascade_deletion_last_branch:
                for i_design_cell in design_cells_on_branch_arm:
                    self._repos.study_design_cell_repository.patch_study_arm(
                        study_uid=study_uid,
                        design_cell_uid=i_design_cell.uid,
                        study_arm_uid=selection_to_delete.arm_root_uid,
                        author=self.author,
                    )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionBranchArm:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_branch_arm_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_branch_arm_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _transform_each_history_to_response_model(
        self, study_selection_history: SelectionHistoryBranchArm, study_uid: str
    ) -> Sequence[models.StudySelectionBranchArmHistory]:
        return models.StudySelectionBranchArmHistory.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
        )

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionBranchArmVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_branch_arm_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_branch_arms
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
                        versions, models.StudySelectionBranchArmVersion
                    )
                else:
                    data.extend(
                        calculate_diffs(versions, models.StudySelectionBranchArmVersion)
                    )
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionBranchArmVersion]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_branch_arm_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            versions = [
                self._transform_each_history_to_response_model(_, study_uid).dict()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, models.StudySelectionBranchArmVersion)
            return data
        finally:
            repos.close()

    def _get_specific_arm_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionArm:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_arm_selection_by_uids(study_uid, study_selection_uid)
        # Without Connected BranchArms due to only is necessary to have the StudyArm
        return models.StudySelectionArm.from_study_selection_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_arm_type_by_term_uid=self._find_by_uid_or_raise_not_found,
        )

    def _cascade_creation(
        self, study_uid: str, study_branch_arm_uid: str, study_arm_uid: str
    ) -> Sequence[models.StudyDesignCellBatchOutput]:
        repos = self._repos
        design_cells_on_arm = (
            repos.study_design_cell_repository.get_design_cells_connected_to_arm(
                study_uid=study_uid, study_arm_uid=study_arm_uid
            )
        )

        inputs = [
            StudyDesignCellBatchInput(
                method="PATCH",
                content=StudyDesignCellEditInput(
                    studyDesignCellUid=i_design_cell.uid,
                    studyBranchArmUid=study_branch_arm_uid,
                ),
            )
            for i_design_cell in design_cells_on_arm
        ]

        design_cell_service = StudyDesignCellService(author=self.author)
        design_cells_updated = design_cell_service.handle_batch_operations(
            study_uid=study_uid, operations=inputs
        )
        assert len(design_cells_updated) > 0
        return design_cells_updated

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionBranchArmCreateInput,
    ) -> models.StudySelectionBranchArm:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionBranchArmVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.shortName,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    colour_code=selection_create_input.colourCode,
                    randomization_group=selection_create_input.randomizationGroup,
                    number_of_subjects=selection_create_input.numberOfSubjects,
                    arm_root_uid=selection_create_input.armUid,
                    generate_uid_callback=repos.study_selection_branch_arm_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionBranchArmAR = (
                    repos.study_selection_branch_arm_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                try:
                    selection_aggregate.add_branch_arm_selection(
                        study_branch_arm_selection=new_selection,
                        study_branch_arm_study_arm_update_conflict_callback=(
                            repos.study_selection_branch_arm_repository.branch_arm_arm_update_conflict
                        ),
                        study_arm_exists_callback=self._repos.study_selection_arm_repository.arm_specific_exists_by_uid,
                        branch_arm_exists_callback_by=repos.study_selection_branch_arm_repository.branch_arm_exists_by,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_branch_arm_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_branch_arm_selection(
                    new_selection.study_selection_uid
                )

                # add the Brancharm and return
                return models.StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
                )
        finally:
            repos.close()
            # if the studyarm has studydesigncells connected?
            if repos.study_selection_arm_repository.arm_specific_has_connected_cell(
                study_uid=study_uid, arm_uid=new_selection.arm_root_uid
            ):
                # if it is the first study branch to be added
                # switch all the study designcells to the study branch arm
                self._cascade_creation(
                    study_uid=study_uid,
                    study_arm_uid=new_selection.arm_root_uid,
                    study_branch_arm_uid=new_selection.study_selection_uid,
                )

    def _patch_prepare_new_study_branch_arm(
        self,
        request_study_branch_arm: models.StudySelectionBranchArmEditInput,
        current_study_branch_arm: StudySelectionBranchArmVO,
    ) -> StudySelectionBranchArmVO:
        # transform current to input model
        transformed_current = models.StudySelectionBranchArmEditInput(
            branchArmUid=current_study_branch_arm.study_selection_uid,
            name=current_study_branch_arm.name,
            shortName=current_study_branch_arm.short_name,
            code=current_study_branch_arm.code,
            description=current_study_branch_arm.description,
            colourCode=current_study_branch_arm.colour_code,
            randomizationGroup=current_study_branch_arm.randomization_group,
            numberOfSubjects=current_study_branch_arm.number_of_subjects,
            armUid=current_study_branch_arm.arm_root_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_branch_arm,
            reference_base_model=transformed_current,
        )

        return StudySelectionBranchArmVO.from_input_values(
            study_uid=current_study_branch_arm.study_uid,
            name=request_study_branch_arm.name,
            short_name=request_study_branch_arm.shortName,
            code=request_study_branch_arm.code,
            description=request_study_branch_arm.description,
            colour_code=request_study_branch_arm.colourCode,
            randomization_group=request_study_branch_arm.randomizationGroup,
            number_of_subjects=request_study_branch_arm.numberOfSubjects,
            arm_root_uid=request_study_branch_arm.armUid,
            study_selection_uid=current_study_branch_arm.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        selection_update_input: models.StudySelectionBranchArmEditInput,
    ) -> models.StudySelectionBranchArm:
        repos = self._repos
        study_selection_uid = selection_update_input.branchArmUid  # to delete
        try:
            # Load aggregate
            selection_aggregate: StudySelectionBranchArmAR = (
                repos.study_selection_branch_arm_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            try:
                current_vo, order = selection_aggregate.get_specific_object_selection(
                    study_selection_uid=selection_update_input.branchArmUid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_branch_arm(
                request_study_branch_arm=selection_update_input,
                current_study_branch_arm=current_vo,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_branch_arm_selection=updated_selection,
                    study_branch_arm_study_arm_update_conflict_callback=repos.study_selection_branch_arm_repository.branch_arm_arm_update_conflict,
                    study_arm_exists_callback=self._repos.study_selection_arm_repository.arm_specific_exists_by_uid,
                    branch_arm_exists_callback_by=repos.study_selection_branch_arm_repository.branch_arm_exists_by,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])
            # sync with DB and save the update
            repos.study_selection_branch_arm_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the branch arm and return
            return models.StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionBranchArm:
        (_, new_selection, order,) = self._get_specific_branch_arm_selection_by_uids(
            study_uid, study_selection_uid
        )
        return models.StudySelectionBranchArm.from_study_selection_branch_arm_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_simple_term_branch_arm_root_by_term_uid=self._get_specific_arm_selection,
        )
