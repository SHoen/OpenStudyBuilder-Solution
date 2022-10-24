from typing import Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.study_selection.study_selection_cohort import (
    StudySelectionCohortAR,
    StudySelectionCohortVO,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_cohort_repository import (
    SelectionHistoryCohort,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
)
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyCohortSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionCohortAR,
    ) -> Sequence[models.StudySelectionCohort]:
        result = []
        for order, selection in enumerate(
            study_selection.study_cohorts_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection, order=order, study_uid=study_selection.study_uid
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionCohortVO,
        order: int,
        study_uid: str,
    ) -> models.StudySelectionCohort:
        return models.StudySelectionCohort.from_study_selection_cohort_ar_and_order(
            study_uid=study_uid,
            selection=study_selection,
            order=order,
            find_arm_root_by_uid=self._get_specific_arm_selection,
            find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
        )

    @db.transaction
    def get_all_selection(
        self,
        study_uid: str,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
        arm_uid: Optional[str] = None,
    ) -> GenericFilteringReturn[models.StudySelectionCohort]:
        repos = self._repos
        try:
            cohort_selection_ar = repos.study_selection_cohort_repository.find_by_study(
                study_uid,
                arm_uid=arm_uid,
                project_name=project_name,
                project_number=project_number,
            )
            # In order for filtering to work, we need to unwind the aggregated AR object first
            # Unwind ARs
            selections = []
            parsed_selections = self._transform_all_to_response_model(
                cohort_selection_ar
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
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_selection_cohort_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.remove_cohort_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_cohort_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionCohort:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = repos.study_selection_cohort_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_cohort_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_cohort_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def _transform_each_history_to_response_model(
        self, study_selection_history: SelectionHistoryCohort, study_uid: str
    ) -> Sequence[models.StudySelectionCohortHistory]:
        return models.StudySelectionCohortHistory.from_study_selection_history(
            study_selection_history=study_selection_history,
            study_uid=study_uid,
        )

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionCohortVersion]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_cohort_repository.find_selection_history(
                        study_uid
                    )
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            unique_list_uids = list({x.study_selection_uid for x in selection_history})
            unique_list_uids.sort()
            # list of all study_cohorts
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
                    data = calculate_diffs(versions, models.StudySelectionCohortVersion)
                else:
                    data.extend(
                        calculate_diffs(versions, models.StudySelectionCohortVersion)
                    )
            return data
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection_audit_trail(
        self, study_uid: str, study_selection_uid: str
    ) -> Sequence[models.StudySelectionCohortVersion]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_cohort_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            versions = [
                self._transform_each_history_to_response_model(_, study_uid).dict()
                for _ in selection_history
            ]
            data = calculate_diffs(versions, models.StudySelectionCohortVersion)
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

    def _get_specific_branch_arm_selection(
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

    def make_selection(
        self,
        study_uid: str,
        selection_create_input: models.StudySelectionCohortCreateInput,
    ) -> models.StudySelectionCohort:
        repos = self._repos

        try:
            # Load aggregate
            with db.transaction:
                # create new VO to add
                new_selection = StudySelectionCohortVO.from_input_values(
                    study_uid=study_uid,
                    user_initials=self.author,
                    name=selection_create_input.name,
                    short_name=selection_create_input.shortName,
                    code=selection_create_input.code,
                    description=selection_create_input.description,
                    colour_code=selection_create_input.colourCode,
                    number_of_subjects=selection_create_input.numberOfSubjects,
                    branch_arm_root_uids=selection_create_input.branchArmUids,
                    arm_root_uids=selection_create_input.armUids,
                    generate_uid_callback=repos.study_selection_cohort_repository.generate_uid,
                )
                # add VO to aggregate
                selection_aggregate: StudySelectionCohortAR = (
                    repos.study_selection_cohort_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )
                assert selection_aggregate is not None
                try:
                    selection_aggregate.add_cohort_selection(
                        study_cohort_selection=new_selection,
                        study_arm_exists_callback=self._repos.study_selection_arm_repository.arm_specific_exists_by_uid,
                        study_branch_arm_exists_callback=self._repos.study_selection_branch_arm_repository.branch_arm_specific_exists_by_uid,
                        cohort_exists_callback_by=repos.study_selection_cohort_repository.cohort_exists_by,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_cohort_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_cohort_selection(
                    new_selection.study_selection_uid
                )

                # add the Cohort and return
                return models.StudySelectionCohort.from_study_selection_cohort_ar_and_order(
                    study_uid=study_uid,
                    selection=new_selection,
                    order=order,
                    find_arm_root_by_uid=self._get_specific_arm_selection,
                    find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
                )
        finally:
            repos.close()

    def _patch_prepare_new_study_cohort(
        self,
        request_study_cohort: models.StudySelectionCohortEditInput,
        current_study_cohort: StudySelectionCohortVO,
    ) -> StudySelectionCohortVO:
        # transform current to input model
        transformed_current = models.StudySelectionCohortEditInput(
            cohortUid=current_study_cohort.study_selection_uid,
            name=current_study_cohort.name,
            shortName=current_study_cohort.short_name,
            code=current_study_cohort.code,
            description=current_study_cohort.description,
            colourCode=current_study_cohort.colour_code,
            numberOfSubjects=current_study_cohort.number_of_subjects,
            branchArmUids=current_study_cohort.branch_arm_root_uids,
            armUids=current_study_cohort.arm_root_uids,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_cohort,
            reference_base_model=transformed_current,
        )

        return StudySelectionCohortVO.from_input_values(
            study_uid=current_study_cohort.study_uid,
            name=request_study_cohort.name,
            short_name=request_study_cohort.shortName,
            code=request_study_cohort.code,
            description=request_study_cohort.description,
            colour_code=request_study_cohort.colourCode,
            number_of_subjects=request_study_cohort.numberOfSubjects,
            branch_arm_root_uids=request_study_cohort.branchArmUids,
            arm_root_uids=request_study_cohort.armUids,
            study_selection_uid=current_study_cohort.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionCohortEditInput,
    ) -> models.StudySelectionCohort:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate: StudySelectionCohortAR = (
                repos.study_selection_cohort_repository.find_by_study(
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
            updated_selection = self._patch_prepare_new_study_cohort(
                request_study_cohort=selection_update_input,
                current_study_cohort=current_vo,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_cohort_selection=updated_selection,
                    study_arm_exists_callback=self._repos.study_selection_arm_repository.arm_specific_exists_by_uid,
                    study_branch_arm_exists_callback=self._repos.study_selection_branch_arm_repository.branch_arm_specific_exists_by_uid,
                    cohort_exists_callback_by=repos.study_selection_cohort_repository.cohort_exists_by,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])
            # sync with DB and save the update
            repos.study_selection_cohort_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_object_selection(
                study_selection_uid
            )

            # add the cohort and return
            return models.StudySelectionCohort.from_study_selection_cohort_ar_and_order(
                study_uid=study_uid,
                selection=new_selection,
                order=order,
                find_arm_root_by_uid=self._get_specific_arm_selection,
                find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
            )
        finally:
            repos.close()

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionCohort:
        (
            _,
            new_selection,
            order,
        ) = self._get_specific_cohort_selection_by_uids(study_uid, study_selection_uid)
        return models.StudySelectionCohort.from_study_selection_cohort_ar_and_order(
            study_uid=study_uid,
            selection=new_selection,
            order=order,
            find_arm_root_by_uid=self._get_specific_arm_selection,
            find_branch_arm_root_cohort_by_uid=self._get_specific_branch_arm_selection,
        )
