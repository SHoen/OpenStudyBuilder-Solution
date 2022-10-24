from typing import List, Optional, Sequence

from fastapi import status
from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.study_selection.study_selection_activity_repository import (
    SelectionHistory,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyActivitySelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityAR,
    ) -> Sequence[models.StudySelectionActivity]:
        result = []
        for order, selection in enumerate(
            study_selection.study_objects_selection, start=1
        ):
            result.append(
                models.StudySelectionActivity.from_study_selection_activity_ar_and_order(
                    study_selection_activity_ar=study_selection,
                    activity_order=order,
                    accepted_version=selection.accepted_version,
                    get_activity_by_uid_callback=self._transform_latest_activity_model,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionActivityCreateInput,
    ) -> models.StudySelectionActivity:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                activity_service = ActivityService()
                activity_uid = selection_create_input.activityUid
                activity_ar = activity_service.repository.find_by_uid_2(
                    activity_uid, for_update=True
                )
                if not activity_ar:
                    raise exceptions.NotFoundException(
                        f"There is no activity identified by provided uid ({activity_uid})"
                    )

                # if in draft status - approve
                # FIXME: we should not approve ?!
                if activity_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    activity_ar.approve(self.author)
                    activity_service.repository.save(activity_ar)
                elif activity_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved activity identified by provided uid ({activity_uid})"
                    )

                # create new VO to add
                new_selection = StudySelectionActivityVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    activity_uid=activity_uid,
                    activity_version=activity_ar.item_metadata.version,
                    flowchart_group_uid=selection_create_input.flowchartGroupUid,
                    activity_order=None,
                    generate_uid_callback=repos.study_selection_activity_repository.generate_uid,
                )

                # add VO to aggregate
                selection_aggregate = (
                    repos.study_selection_activity_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                try:
                    activity_repo = repos.activity_repository
                    selection_aggregate.add_object_selection(
                        new_selection,
                        activity_repo.check_exists_final_version,
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )
                    selection_aggregate.validate()
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_activity_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_object_selection(
                    new_selection.study_selection_uid
                )

                # add the activity and return
                return models.StudySelectionActivity.from_study_selection_activity_ar_and_order(
                    study_selection_activity_ar=selection_aggregate,
                    activity_order=order,
                    get_activity_by_uid_callback=self._transform_latest_activity_model,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
                )
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        activity_names: Optional[List[str]] = None,
        activity_sub_group_names: Optional[List[str]] = None,
        activity_group_names: Optional[List[str]] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionObjective]:
        repos = self._repos
        selection_ars = repos.study_selection_activity_repository.find_all(
            project_name=project_name,
            project_number=project_number,
            activity_names=activity_names,
            activity_sub_group_names=activity_sub_group_names,
            activity_group_names=activity_group_names,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in selection_ars:
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
    def get_all_selection(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionActivity]:
        repos = self._repos
        try:
            activity_selection_ar = (
                repos.study_selection_activity_repository.find_by_study(study_uid)
            )
            assert activity_selection_ar is not None

            filtered_items = service_level_generic_filtering(
                items=self._transform_all_to_response_model(activity_selection_ar),
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

    def _transform_history_to_response_model(
        self, study_selection_history: List[SelectionHistory], study_uid: str
    ) -> Sequence[models.StudySelectionActivityCore]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionActivityCore.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionActivityCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_activity_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionActivityCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_activity_repository.find_selection_history(
                        study_uid, study_selection_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionActivity:
        (
            selection_aggregate,
            new_selection,
            order,
        ) = self._get_specific_activity_selection_by_uids(
            study_uid, study_selection_uid
        )
        return models.StudySelectionActivity.from_study_selection_activity_ar_and_order(
            study_selection_activity_ar=selection_aggregate,
            activity_order=order,
            accepted_version=new_selection.accepted_version,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
        )

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_activity_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_activity_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionActivity:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_activity_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            repos.study_selection_activity_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            _, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the activity and return
            return models.StudySelectionActivity.from_study_selection_activity_ar_and_order(
                study_selection_activity_ar=selection_aggregate,
                activity_order=order,
                get_activity_by_uid_callback=self._transform_latest_activity_model,
                get_activity_by_uid_version_callback=self._transform_activity_model,
                get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
            )
        finally:
            repos.close()

    def _patch_prepare_new_study_activity(
        self,
        request_study_activity: models.StudySelectionActivityInput,
        current_study_activity: StudySelectionActivityVO,
    ) -> StudySelectionActivityVO:
        # transform current to input model
        transformed_current = models.StudySelectionActivityInput(
            showActivityGroupInProtocolFlowchart=current_study_activity.show_activity_group_in_protocol_flowchart,
            showActivitySubGroupInProtocolFlowchart=current_study_activity.show_activity_subgroup_in_protocol_flowchart,
            showActivityInProtocolFlowchart=current_study_activity.show_activity_in_protocol_flowchart,
            flowchartGroupUid=current_study_activity.flowchart_group_uid,
            note=current_study_activity.note,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_activity,
            reference_base_model=transformed_current,
        )

        return StudySelectionActivityVO.from_input_values(
            study_uid=current_study_activity.study_uid,
            activity_uid=current_study_activity.activity_uid,
            activity_version=current_study_activity.activity_version,
            activity_order=current_study_activity.activity_order,
            flowchart_group_uid=request_study_activity.flowchartGroupUid,
            study_selection_uid=current_study_activity.study_selection_uid,
            show_activity_group_in_protocol_flowchart=request_study_activity.showActivityGroupInProtocolFlowchart,
            show_activity_subgroup_in_protocol_flowchart=request_study_activity.showActivitySubGroupInProtocolFlowchart,
            show_activity_in_protocol_flowchart=request_study_activity.showActivityInProtocolFlowchart,
            note=request_study_activity.note,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionActivityInput,
    ) -> models.StudySelectionActivity:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_activity_repository.find_by_study(
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
            updated_selection = self._patch_prepare_new_study_activity(
                request_study_activity=selection_update_input,
                current_study_activity=current_vo,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_object_selection=updated_selection,
                    object_exist_callback=self._repos.activity_repository.check_exists_final_version,
                    ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                selection_aggregate.validate()
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_activity_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            _, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the activity and return
            return models.StudySelectionActivity.from_study_selection_activity_ar_and_order(
                study_selection_activity_ar=selection_aggregate,
                activity_order=order,
                get_activity_by_uid_callback=self._transform_latest_activity_model,
                get_activity_by_uid_version_callback=self._transform_activity_model,
                get_ct_term_flowchart_group=self._find_by_uid_or_raise_not_found,
            )
        finally:
            repos.close()

    def handle_batch_operations(
        self,
        study_uid: str,
        operations: Sequence[models.StudySelectionActivityBatchInput],
    ) -> Sequence[models.StudySelectionActivityBatchOutput]:
        results = []
        for operation in operations:
            result = {}
            item = None
            try:
                if operation.method == "PATCH":
                    item = self.patch_selection(
                        study_uid,
                        operation.content.studyActivityUid,
                        operation.content.content,
                    )
                    response_code = status.HTTP_200_OK
                elif operation.method == "DELETE":
                    self.delete_selection(study_uid, operation.content.studyActivityUid)
                    response_code = status.HTTP_204_NO_CONTENT
                else:
                    item = self.make_selection(study_uid, operation.content)
                    response_code = status.HTTP_201_CREATED
            except exceptions.MDRApiBaseException as error:
                result["responseCode"] = error.status_code
                result["content"] = BatchErrorResponse(message=str(error))
            else:
                result["responseCode"] = response_code
                result["content"] = item
            finally:
                results.append(models.StudySelectionActivityBatchOutput(**result))
        return results

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
