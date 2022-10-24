from datetime import datetime
from typing import Sequence

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_design_cell import StudyDesignCellVO
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignCell as StudyDesignCellNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selection.study_design_cell_repository import (
    StudyDesignCellHistory,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.study_endpoint_selection import StudySelectionMixin


class StudyDesignCellService(StudySelectionMixin):

    _repos: MetaRepository

    def __init__(self, author: str):
        self._repos = MetaRepository()
        self.author = author

    @db.transaction
    def get_all_design_cells(self, study_uid: str) -> Sequence[models.StudyDesignCell]:
        return [
            models.StudyDesignCell.from_orm(sdc_node)
            for sdc_node in StudyDesignCellNeoModel.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "study_element",
                "has_after",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(study_value__study_root__uid=study_uid)
            .order_by("order")
            .to_relation_trees()
        ]

    @db.transaction
    def get_all_selection_within_arm(
        self, study_uid: str, study_arm_uid: str
    ) -> Sequence[models.StudyDesignCell]:

        sdc_nodes = (
            self._repos.study_design_cell_repository.get_design_cells_connected_to_arm(
                study_uid, study_arm_uid
            )
        )

        return [models.StudyDesignCell.from_orm(sdc_node) for sdc_node in sdc_nodes]

    @db.transaction
    def get_all_selection_within_branch_arm(
        self, study_uid: str, study_branch_arm_uid: str
    ) -> Sequence[models.StudyDesignCell]:

        sdc_nodes = self._repos.study_design_cell_repository.get_design_cells_connected_to_branch_arm(
            study_uid, study_branch_arm_uid
        )

        return [models.StudyDesignCell.from_orm(sdc_node) for sdc_node in sdc_nodes]

    @db.transaction
    def get_all_selection_within_epoch(
        self, study_uid: str, study_epoch_uid: str
    ) -> Sequence[models.StudyDesignCell]:

        sdc_nodes = self._repos.study_design_cell_repository.get_design_cells_connected_to_epoch(
            study_uid, study_epoch_uid
        )

        return [models.StudyDesignCell.from_orm(sdc_node) for sdc_node in sdc_nodes]

    def get_specific_design_cell(
        self, study_uid: str, design_cell_uid: str
    ) -> models.StudyDesignCell:
        sdc_node = (
            StudyDesignCellNeoModel.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "study_element",
                "has_after",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(study_value__study_root__uid=study_uid, uid=design_cell_uid)
            .to_relation_trees()
        )
        if sdc_node is None or len(sdc_node) == 0:
            raise exceptions.NotFoundException(
                f"Not Found - The study design cell with the specified 'uid' {design_cell_uid} could not be found.",
            )
        return models.StudyDesignCell.from_orm(sdc_node[0])

    def _from_input_values(
        self, study_uid: str, design_cell_input: models.StudyDesignCellCreateInput
    ) -> StudyDesignCellVO:
        return StudyDesignCellVO(
            study_uid=study_uid,
            study_arm_uid=design_cell_input.studyArmUid,
            study_arm_name=None,
            study_branch_arm_uid=design_cell_input.studyBranchArmUid,
            study_branch_arm_name=None,
            study_epoch_uid=design_cell_input.studyEpochUid,
            study_epoch_name=None,
            study_element_uid=design_cell_input.studyElementUid,
            study_element_name=None,
            order=design_cell_input.order,
            transition_rule=design_cell_input.transitionRule,
            user_initials=self.author,
            start_date=datetime.now(),
        )

    @db.transaction
    def create(
        self, study_uid: str, design_cell_input: models.StudyDesignCellCreateInput
    ) -> models.StudyDesignCell:

        # all_design_cells: Sequence[StudyDesignCellVO]
        all_design_cells = (
            self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid
            )
        )

        # created_design_cell: StudyDesignVO, from the input
        created_design_cell = self._from_input_values(study_uid, design_cell_input)

        # if the order want an specific order
        if design_cell_input.order:
            if len(all_design_cells) + 1 < created_design_cell.order:
                raise exceptions.BusinessLogicException("Order is too big.")
            # shift one order more to fit the modified
            for design_cell in all_design_cells[created_design_cell.order - 1 :]:
                design_cell.order += 1
                self._repos.study_design_cell_repository.save(
                    design_cell, self.author, create=False
                )
        # if not just add one to the order
        else:
            created_design_cell.order = len(all_design_cells) + 1

        # created_item: StudyDesignCellVO
        created_item = self._repos.study_design_cell_repository.save(
            created_design_cell, self.author, create=True
        )

        # return json response model
        return models.StudyDesignCell.from_vo(created_item)

    def _edit_study_design_cell_vo(
        self,
        study_design_cell_to_edit: StudyDesignCellVO,
        study_design_cell_edit_input: models.StudyDesignCellEditInput,
    ):
        study_design_cell_to_edit.edit_core_properties(
            study_epoch_uid=study_design_cell_to_edit.study_epoch_uid,
            study_element_uid=study_design_cell_edit_input.studyElementUid,
            study_arm_uid=study_design_cell_edit_input.studyArmUid,
            study_branch_arm_uid=study_design_cell_edit_input.studyBranchArmUid,
            transition_rule=study_design_cell_edit_input.transitionRule,
            order=study_design_cell_edit_input.order,
        )

    @db.transaction
    def patch(
        self, study_uid: str, design_cell_update_input: models.StudyDesignCellEditInput
    ) -> models.StudyDesignCell:

        # study_design_cell: StudyDesignCellVO
        study_design_cell = self._repos.study_design_cell_repository.find_by_uid(
            study_uid=study_uid, uid=design_cell_update_input.studyDesignCellUid
        )
        if design_cell_update_input.studyBranchArmUid is not None:
            design_cell_update_input.studyArmUid = None
        elif design_cell_update_input.studyArmUid is not None:
            design_cell_update_input.studyBranchArmUid = None

        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=design_cell_update_input,
            # return json response model
            reference_base_model=models.StudyDesignCell.from_vo(study_design_cell),
        )
        self._edit_study_design_cell_vo(
            study_design_cell_to_edit=study_design_cell,
            study_design_cell_edit_input=design_cell_update_input,
        )

        # updated_item: StudyDesignCellVO
        updated_item = self._repos.study_design_cell_repository.save(
            study_design_cell, self.author, create=False
        )

        # return json response model
        return models.StudyDesignCell.from_vo(updated_item)

    @db.transaction
    def delete(self, study_uid: str, design_cell_uid: str):
        study_design_cell = self._repos.study_design_cell_repository.find_by_uid(
            study_uid=study_uid, uid=design_cell_uid
        )
        self._repos.study_design_cell_repository.delete(
            study_uid, design_cell_uid, self.author
        )
        all_design_cells = (
            self._repos.study_design_cell_repository.find_all_design_cells_by_study(
                study_uid
            )
        )
        # shift one order more to fit the modified
        for design_cell in all_design_cells[study_design_cell.order - 1 :]:
            design_cell.order -= 1
            self._repos.study_design_cell_repository.save(
                design_cell, author=self.author, create=False
            )

    def _transform_each_history_to_response_model(
        self, study_selection_history: StudyDesignCellHistory, study_uid: str
    ) -> Sequence[models.StudyDesignCellHistory]:
        return models.StudyDesignCellHistory(
            studyUid=study_uid,
            studyDesignCellUid=study_selection_history.study_selection_uid,
            studyArmUid=study_selection_history.study_arm_uid,
            studyBranchArmUid=study_selection_history.study_branch_arm_uid,
            studyEpochUid=study_selection_history.study_epoch_uid,
            studyElementUid=study_selection_history.study_element_uid,
            transitionRule=study_selection_history.transition_rule,
            changeType=study_selection_history.change_type,
            modified=study_selection_history.start_date,
            order=study_selection_history.order,
        )

    @db.transaction
    def get_all_design_cells_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudyDesignCellVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_design_cell_repository.find_selection_history(study_uid)
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
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
                    data = calculate_diffs(versions, models.StudyDesignCellVersion)
                else:
                    data.extend(
                        calculate_diffs(versions, models.StudyDesignCellVersion)
                    )
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, design_cell_uid: str
    ) -> Sequence[models.StudyDesignCellVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_design_cell_repository.find_selection_history(
                        study_uid, design_cell_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            versions = [
                self._transform_each_history_to_response_model(_, study_uid).dict()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, models.StudyDesignCellVersion)
            return data
        finally:
            repos.close()

    def handle_batch_operations(
        self, study_uid: str, operations: Sequence[models.StudyDesignCellBatchInput]
    ) -> Sequence[models.StudyDesignCellBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "POST":
                    item = self.create(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
                elif operation.method == "PATCH":
                    item = self.patch(study_uid, operation.content)
                    response_code = status.HTTP_200_OK
                else:
                    self.delete(study_uid, operation.content.uid)
                    response_code = status.HTTP_204_NO_CONTENT
            except exceptions.MDRApiBaseException as error:
                result["responseCode"] = error.status_code
                result["content"] = models.error.BatchErrorResponse(error)
            else:
                result["responseCode"] = response_code
                if item:
                    result["content"] = item.dict()
            finally:
                results.append(models.StudyDesignCellBatchOutput(**result))
        return results
