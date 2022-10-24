from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.library.objectives import ObjectiveAR
from clinical_mdr_api.domain.study_selection.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.study_selection.study_selection_objective_repository import (
    SelectionHistory,
)
from clinical_mdr_api.exceptions import ForbiddenException, NotFoundException
from clinical_mdr_api.models.study_selection import (
    StudySelectionObjectiveCreateInput,
    StudySelectionObjectiveInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.objectives import ObjectiveService
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyObjectiveSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    #     # def _get_endpoint_count_for_objective(self, study_uid: str, study_objective_uid: str) -> int:
    #     study_endpoints = self._repos.study_selection_endpoint_repository.find_by_study(study_uid)
    #     assert study_endpoints is not None
    #     selection = study_endpoints.study_endpoints_selection
    #     return sum(map((lambda _: 1 if _.study_objective_uid == study_objective_uid else 0), selection))

    def _check_for_study_endpoints_and_update(
        self, study_uid: str, study_objective_uid: str
    ) -> None:
        """
        Function to check if there are any study endpoints using the study objective when the study objective is deleted
        if any study endpoint is using the study objective, then these study endpoints are set to have None as study
        objective

        :param study_uid:
        :param study_objective_uid:
        :return:
        """
        # load study endpoint aggregate
        endpoint_selection_aggregate = (
            self._repos.study_selection_endpoint_repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
        )

        # set any study endpoint using the study objective to have No study objective if they are using it
        assert endpoint_selection_aggregate is not None
        endpoint_selection_aggregate.deleting_study_objective(study_objective_uid)

        # save study endpoints
        self._repos.study_selection_endpoint_repository.save(
            study_selection=endpoint_selection_aggregate, author=self.author
        )

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionObjectivesAR, no_brackets: bool
    ) -> Sequence[models.StudySelectionObjective]:
        result = []
        for order, selection in enumerate(
            study_selection.study_objectives_selection, start=1
        ):
            result.append(
                models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                    study_selection_objectives_ar=study_selection,
                    order=order,
                    accepted_version=selection.accepted_version,
                    get_objective_by_uid_callback=self._transform_latest_objective_model,
                    get_objective_by_uid_version_callback=self._transform_objective_model,
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                    get_study_selection_endpoints_ar_by_study_uid_callback=(
                        self._repos.study_selection_endpoint_repository.find_by_study
                    ),
                    no_brackets=no_brackets,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
            )
        return result

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        selection_ar, selection, order = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        objective_uid = selection.objective_uid
        objective_ar = self._repos.objective_repository.find_by_uid_2(objective_uid)
        if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            objective_ar.approve(self.author)
            self._repos.objective_repository.save(objective_ar)
        elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.update_version(objective_ar.item_metadata.version)
        selection_ar.update_selection(
            new_selection, objective_exist_callback=lambda x: True
        )
        self._repos.study_selection_objective_repository.save(selection_ar, self.author)

        return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_ar,
            order=order,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
            get_study_selection_endpoints_ar_by_study_uid_callback=(
                self._repos.study_selection_endpoint_repository.find_by_study
            ),
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
        )

    @db.transaction
    def update_selection_accept_version(self, study_uid: str, study_selection_uid: str):
        selection: StudySelectionObjectiveVO
        selection_ar, selection, order = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid, for_update=True
        )
        objective_uid = selection.objective_uid
        objective_ar = self._repos.objective_repository.find_by_uid_2(objective_uid)
        if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            objective_ar.approve(self.author)
            self._repos.objective_repository.save(objective_ar)
        elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                "Cannot add retired objective as selection. Please reactivate."
            )
        new_selection = selection.accept_versions()
        selection_ar.update_selection(
            new_selection, objective_exist_callback=lambda x: True
        )
        self._repos.study_selection_objective_repository.save(selection_ar, self.author)

        return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_ar,
            order=order,
            accepted_version=new_selection.accepted_version,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
            get_study_selection_endpoints_ar_by_study_uid_callback=(
                self._repos.study_selection_endpoint_repository.find_by_study
            ),
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
        )

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_objective_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            objective_repo = repos.objective_repository
            selected_objective: ObjectiveAR = objective_repo.find_by_uid_2(
                selection_create_input.objectiveUid, status=LibraryItemStatus.FINAL
            )
            if selected_objective is None:
                raise exceptions.BusinessLogicException(
                    f"There is no approved objective identified by provided uid ({selection_create_input.objectiveUid})"
                )

            # load the order of the Objective level CT term
            if selection_create_input.objectiveLevelUid is not None:
                objective_level_order = (
                    self._repos.ct_term_name_repository.term_specific_order_by_uid(
                        uid=selection_create_input.objectiveLevelUid
                    )
                )
            else:
                objective_level_order = None
            # create new VO to add
            new_selection = StudySelectionObjectiveVO.from_input_values(
                objective_uid=selection_create_input.objectiveUid,
                objective_version=selected_objective.item_metadata.version,
                objective_level_uid=selection_create_input.objectiveLevelUid,
                objective_level_order=objective_level_order,
                generate_uid_callback=repos.study_selection_objective_repository.generate_uid,
                user_initials=self.author,
            )

            # Check the state of the objective, if latest version is in draft then we approve it, if retired then we throw a error
            objective_repo = self._repos.objective_repository
            if new_selection.objective_uid is not None:
                objective_ar = objective_repo.find_by_uid_2(
                    new_selection.objective_uid, for_update=True
                )
                if objective_ar is None:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({new_selection.objective_uid})"
                    )
                # if in draft status - approve
                if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    objective_ar.approve(self.author)
                    objective_repo.save(objective_ar)
                # if in retired then we return a error
                elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({new_selection.objective_uid})"
                    )

            # add VO to aggregate
            try:
                objective_repo = repos.objective_repository
                assert selection_aggregate is not None
                selection_aggregate.add_objective_selection(
                    new_selection,
                    objective_repo.check_exists_final_version,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                selection_aggregate.validate()
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_objective_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_objective_selection(
                new_selection.study_selection_uid
            )

            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                get_study_selection_endpoints_ar_by_study_uid_callback=(
                    self._repos.study_selection_endpoint_repository.find_by_study
                ),
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )

            # return self._transform_single_to_response_model(new_selection, order, study_uid)
        finally:
            repos.close()

    def make_selection_create_objective(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveCreateInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                objective_service = ObjectiveService()
                objective_ar = objective_service.create_ar_from_input_values(
                    selection_create_input.objectiveData,
                    study_uid=study_uid,
                    include_study_endpoints=True,
                )

                objective_uid = objective_ar.uid
                if not objective_service.repository.check_exists_by_name(
                    objective_ar.name
                ):
                    objective_service.repository.save(objective_ar)
                else:
                    objective_uid = objective_service.repository.find_uid_by_name(
                        name=objective_ar.name
                    )
                    if objective_uid is None:
                        raise NotFoundException(
                            f"Could not find node with label ObjectiveRoot and name {objective_ar.name}"
                        )
                objective_ar = objective_service.repository.find_by_uid_2(
                    objective_uid, for_update=True
                )
                # getting selection aggregate
                selection_aggregate = (
                    repos.study_selection_objective_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )

                # if in draft status - approve
                if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    objective_ar.approve(self.author)
                    objective_service.repository.save(objective_ar)
                elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({objective_uid})"
                    )

                # get order from the Objective level CT term
                if selection_create_input.objectiveLevelUid is not None:
                    objective_level_order = (
                        self._repos.ct_term_name_repository.term_specific_order_by_uid(
                            uid=selection_create_input.objectiveLevelUid
                        )
                    )
                else:
                    objective_level_order = None

                # create new VO to add
                new_selection = StudySelectionObjectiveVO.from_input_values(
                    user_initials=self.author,
                    objective_uid=objective_uid,
                    objective_version=objective_ar.item_metadata.version,
                    objective_level_uid=selection_create_input.objectiveLevelUid,
                    objective_level_order=objective_level_order,
                    generate_uid_callback=repos.study_selection_objective_repository.generate_uid,
                )

                # add VO to aggregate
                try:
                    objective_repo = repos.objective_repository
                    assert selection_aggregate is not None
                    selection_aggregate.add_objective_selection(
                        new_selection,
                        objective_repo.check_exists_final_version,
                        self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_objective_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_objective_selection(
                    new_selection.study_selection_uid
                )

                # add the objective and return
                return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                    study_selection_objectives_ar=selection_aggregate,
                    order=order,
                    get_objective_by_uid_callback=self._transform_latest_objective_model,
                    get_objective_by_uid_version_callback=self._transform_objective_model,
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                    get_study_selection_endpoints_ar_by_study_uid_callback=(
                        self._repos.study_selection_endpoint_repository.find_by_study
                    ),
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
        except ForbiddenException as e:
            raise e
        except NotFoundException as e:
            raise e
        finally:
            repos.close()

    def make_selection_preview_objective(
        self, study_uid: str, selection_create_input: StudySelectionObjectiveCreateInput
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                objective_service = ObjectiveService()
                objective_ar = objective_service.create_ar_from_input_values(
                    selection_create_input.objectiveData,
                    generate_uid_callback=(lambda: "preview"),
                    study_uid=study_uid,
                    include_study_endpoints=True,
                )
                objective_uid = objective_ar.uid
                objective_ar.approve(self.author)
                selection_aggregate = (
                    repos.study_selection_objective_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )

                # create new VO to add
                new_selection = StudySelectionObjectiveVO.from_input_values(
                    user_initials=self.author,
                    objective_uid=objective_uid,
                    objective_version=objective_ar.item_metadata.version,
                    objective_level_uid=selection_create_input.objectiveLevelUid,
                    objective_level_order=None,
                    generate_uid_callback=(lambda: "preview"),
                )

                selection_aggregate.add_objective_selection(
                    new_selection,
                    (lambda _: True),
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_objective_selection(
                    new_selection.study_selection_uid
                )

                # add the objective and return
                return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                    study_selection_objectives_ar=selection_aggregate,
                    order=order,
                    get_objective_by_uid_callback=(
                        lambda _: models.Objective.from_objective_ar(objective_ar)
                    ),
                    get_objective_by_uid_version_callback=(
                        lambda _: models.Objective.from_objective_ar(objective_ar)
                    ),
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                    get_study_selection_endpoints_ar_by_study_uid_callback=(
                        self._repos.study_selection_endpoint_repository.find_by_study
                    ),
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
        except ForbiddenException as e:
            raise e
        except NotFoundException as e:
            raise e
        finally:
            repos.close()

    @db.transaction
    def get_all_selections_for_all_studies(
        self,
        no_brackets: bool,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionObjective]:
        repos = self._repos
        objective_selection_ars = repos.study_selection_objective_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in objective_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=no_brackets
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
            objective_selection_ars = (
                repos.study_selection_objective_repository.find_by_study(study_uid)
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    objective_selection_ars, no_brackets=False
                ),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        objective_selection_ars = repos.study_selection_objective_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in objective_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=False
            )
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
        no_brackets: bool,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionObjective]:
        repos = self._repos
        try:
            objective_selection_ar = (
                repos.study_selection_objective_repository.find_by_study(study_uid)
            )
            assert objective_selection_ar is not None
            selection = self._transform_all_to_response_model(
                objective_selection_ar, no_brackets=no_brackets
            )
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

    def _transform_history_to_response_model(
        self, study_selection_history: List[SelectionHistory], study_uid: str
    ) -> Sequence[models.StudySelectionObjectiveCore]:
        result = []
        for history in study_selection_history:
            result.append(
                models.StudySelectionObjectiveCore.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_objective_by_uid_version_callback=self._transform_objective_model,
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionObjectiveCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_objective_repository.find_selection_history(
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
    ) -> Sequence[models.StudySelectionObjectiveCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_objective_repository.find_selection_history(
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
    ) -> models.StudySelectionObjective:
        (
            selection_aggregate,
            new_selection,
            order,
        ) = self._get_specific_objective_selection_by_uids(
            study_uid, study_selection_uid
        )
        return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
            study_selection_objectives_ar=selection_aggregate,
            order=order,
            accepted_version=new_selection.accepted_version,
            get_objective_by_uid_callback=self._transform_latest_objective_model,
            get_objective_by_uid_version_callback=self._transform_objective_model,
            get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
            get_study_selection_endpoints_ar_by_study_uid_callback=(
                self._repos.study_selection_endpoint_repository.find_by_study
            ),
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
        )

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_objective_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # update any study endpoints using the selection
            self._check_for_study_endpoints_and_update(
                study_uid=study_uid, study_objective_uid=study_selection_uid
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_objective_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_objective_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_objective_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            repos.study_selection_objective_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            _, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )

            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                get_study_selection_endpoints_ar_by_study_uid_callback=(
                    self._repos.study_selection_endpoint_repository.find_by_study
                ),
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )
            # return self._transform_single_to_response_model(new_selection, order, study_uid)
        finally:
            repos.close()

    def _patch_prepare_new_study_objective(
        self,
        request_study_objective: models.StudySelectionObjectiveInput,
        current_study_objective: StudySelectionObjectiveVO,
    ) -> StudySelectionObjectiveVO:
        # transform current to input model
        transformed_current = models.StudySelectionObjectiveInput(
            objectiveUid=current_study_objective.objective_uid,
            objectiveLevelUid=current_study_objective.objective_level_uid,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_study_objective,
            reference_base_model=transformed_current,
        )

        # get order from the Objective level CT term
        if request_study_objective.objectiveLevelUid is not None:
            objective_level_order = (
                self._repos.ct_term_name_repository.term_specific_order_by_uid(
                    uid=request_study_objective.objectiveLevelUid
                )
            )
        else:
            objective_level_order = None

        return StudySelectionObjectiveVO.from_input_values(
            objective_uid=request_study_objective.objectiveUid,
            objective_version=current_study_objective.objective_version,
            objective_level_order=objective_level_order,
            objective_level_uid=request_study_objective.objectiveLevelUid,
            study_selection_uid=current_study_objective.study_selection_uid,
            user_initials=self.author,
        )

    @db.transaction
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: models.StudySelectionObjectiveInput,
    ) -> models.StudySelectionObjective:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_objective_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            assert selection_aggregate is not None

            # Load the current VO for updates
            try:
                (
                    current_vo,
                    order,
                ) = selection_aggregate.get_specific_objective_selection(
                    study_selection_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_objective(
                request_study_objective=selection_update_input,
                current_study_objective=current_vo,
            )

            # if there is a new objective we have to check the state
            objective_repo = self._repos.objective_repository
            if (
                selection_update_input.objectiveUid
                and selection_update_input.objectiveUid != current_vo.objective_uid
            ):
                objective_ar = objective_repo.find_by_uid_2(
                    updated_selection.objective_uid, for_update=True
                )
                # if in draft status - approve
                if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    objective_ar.approve(self.author)
                    objective_repo.save(objective_ar)
                # if in retired then we return a error
                elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({updated_selection.objective_uid})"
                    )

            try:
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_objective_selection=updated_selection,
                    objective_exist_callback=objective_repo.check_exists_final_version,
                    ct_term_level_exist_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
                selection_aggregate.validate()
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_objective_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            _, order = selection_aggregate.get_specific_objective_selection(
                study_selection_uid
            )

            # add the objective and return
            return models.StudySelectionObjective.from_study_selection_objectives_ar_and_order(
                study_selection_objectives_ar=selection_aggregate,
                order=order,
                get_objective_by_uid_callback=self._transform_latest_objective_model,
                get_objective_by_uid_version_callback=self._transform_objective_model,
                get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                get_study_selection_endpoints_ar_by_study_uid_callback=(
                    self._repos.study_selection_endpoint_repository.find_by_study
                ),
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )
        finally:
            repos.close()
