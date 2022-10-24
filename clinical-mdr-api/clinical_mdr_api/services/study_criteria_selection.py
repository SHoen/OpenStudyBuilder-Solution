from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.library.criteria import CriteriaAR
from clinical_mdr_api.domain.study_selection.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.study_selection.study_selection_criteria_repository import (
    SelectionHistory,
)
from clinical_mdr_api.models.criteria import CriteriaCreateInput
from clinical_mdr_api.models.study_selection import (
    StudySelectionCriteria,
    StudySelectionCriteriaCreateInput,
    StudySelectionCriteriaTemplateSelectInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.criteria import CriteriaService
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyCriteriaSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionCriteriaAR, no_brackets: bool
    ) -> Sequence[models.StudySelectionCriteria]:
        result = []
        for selection in study_selection.study_criteria_selection:
            if selection.is_instance:
                result.append(
                    models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                        study_selection_criteria_ar=study_selection,
                        criteria_type_uid=selection.criteria_type_uid,
                        criteria_type_order=selection.criteria_type_order,
                        accepted_version=selection.accepted_version,
                        get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                        get_criteria_by_uid_version_callback=self._transform_criteria_model,
                        get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                        no_brackets=no_brackets,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    )
                )
            else:
                result.append(
                    models.StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                        study_selection_criteria_ar=study_selection,
                        criteria_type_uid=selection.criteria_type_uid,
                        criteria_type_order=selection.criteria_type_order,
                        accepted_version=selection.accepted_version,
                        get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                        get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                        get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                        find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                    )
                )
        return result

    def batch_select_criteria_template(
        self,
        study_uid: str,
        selection_create_input: Sequence[StudySelectionCriteriaTemplateSelectInput],
    ) -> Sequence[StudySelectionCriteria]:
        """Select multiple criteria templates as a batch.
        This will only select the templates and not create instances, except for templates that have no parameters.

        Args:
            study_uid (str)
            selection_create_input (StudySelectionCriteriaBatchSelectInput): [description]

        Returns:
            Sequence[StudySelectionCriteria]
        """
        repos = self._repos
        try:
            with db.transaction:
                criteria_template_repo = repos.criteria_template_repository
                selections = []
                for template_input in selection_create_input:
                    # Get criteria template
                    criteria_template = criteria_template_repo.find_by_uid_2(
                        uid=template_input.criteriaTemplateUid
                    )
                    if criteria_template is None:
                        raise exceptions.NotFoundException(
                            f"Criteria template with uid {template_input.criteriaTemplateUid} does not exist"
                        )

                    if (
                        criteria_template.template_value.parameter_names is not None
                        and len(criteria_template.template_value.parameter_names) > 0
                    ):
                        criteria_type_uid = (
                            criteria_template_repo.get_criteria_type_uid(
                                template_uid=criteria_template.uid
                            )
                        )

                        # Get selection aggregate
                        selection_aggregate = (
                            repos.study_selection_criteria_repository.find_by_study(
                                study_uid=study_uid, for_update=True
                            )
                        )

                        # Create new VO to add
                        new_selection = StudySelectionCriteriaVO.from_input_values(
                            user_initials=self.author,
                            syntax_object_uid=criteria_template.uid,
                            syntax_object_version=criteria_template.item_metadata.version,
                            is_instance=False,
                            criteria_type_uid=criteria_type_uid,
                            generate_uid_callback=repos.study_selection_criteria_repository.generate_uid,
                        )

                        # Add template to selection
                        try:
                            assert selection_aggregate is not None
                            selection_aggregate.add_criteria_selection(
                                new_selection,
                                criteria_template_repo.check_exists_final_version,
                                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                            )
                        except ValueError as value_error:
                            raise exceptions.ValidationException(value_error.args[0])

                        # Sync with DB and save the update
                        repos.study_selection_criteria_repository.save(
                            selection_aggregate, self.author
                        )

                        # Fetch the new selection which was just added
                        (
                            new_selection,
                            order,
                        ) = selection_aggregate.get_specific_criteria_selection(
                            study_criteria_uid=new_selection.study_selection_uid,
                            criteria_type_uid=criteria_type_uid,
                        )

                        # add the criteria and return
                        selections.append(
                            models.StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                                study_selection_criteria_ar=selection_aggregate,
                                criteria_type_order=order,
                                criteria_type_uid=criteria_type_uid,
                                get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                                get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                                get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                            )
                        )
                    else:
                        new_selection = self.make_selection_create_criteria(
                            study_uid=study_uid,
                            selection_create_input=StudySelectionCriteriaCreateInput(
                                criteriaData=CriteriaCreateInput(
                                    criteriaTemplateUid=template_input.criteriaTemplateUid,
                                    parameterValues=[],
                                    libraryName=template_input.libraryName,
                                )
                            ),
                        )
                        selections.append(new_selection)
                return selections
        finally:
            repos.close()

    def _create_criteria_instance(
        self, criteria_data: CriteriaCreateInput
    ) -> CriteriaAR:
        # check if name exists
        criteria_service = CriteriaService()
        criteria_ar = criteria_service.create_ar_from_input_values(criteria_data)

        # create criteria
        criteria_uid = criteria_ar.uid
        if not criteria_service.repository.check_exists_by_name(criteria_ar.name):
            criteria_service.repository.save(criteria_ar)
        else:
            criteria_uid = criteria_service.repository.find_uid_by_name(
                name=criteria_ar.name
            )
        criteria_ar = criteria_service.repository.find_by_uid_2(
            criteria_uid, for_update=True
        )

        # if in draft status - approve
        if criteria_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            criteria_ar.approve(self.author)
            criteria_service.repository.save(criteria_ar)
        elif criteria_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                f"There is no approved criteria identified by provided uid ({criteria_uid})"
            )

        return criteria_ar

    def finalize_criteria_selection(
        self,
        study_uid: str,
        study_criteria_uid: str,
        criteria_data: CriteriaCreateInput,
    ) -> models.StudySelectionCriteria:
        """Finalizes criteria selection by instantiation the criteria from the selected template.
        It then update the study criteria relationship by selecting the instance instead of the template.

        Args:
            study_uid (str)
            study_criteria_uid (str)
            criteria_data (CriteriaCreateInput): Data necessary to create the criteria instance from the template

        Returns:
            StudySelectionCriteria : Newly created and selected criteria instance
        """
        repos = self._repos
        try:
            with db.transaction:
                # Create instance from the template
                criteria_ar = self._create_criteria_instance(
                    criteria_data=criteria_data
                )

                # Go to repository to reroute the study criteria relationship from template to instance
                repos.study_selection_criteria_repository.update_selection_to_instance(
                    study_uid=study_uid,
                    study_criteria_uid=study_criteria_uid,
                    criteria_uid=criteria_ar.uid,
                    criteria_version=criteria_ar.item_metadata.version,
                )

                # Fetch the latest state of the selection
                selection_aggregate = (
                    repos.study_selection_criteria_repository.find_by_study(
                        study_uid=study_uid, for_update=False
                    )
                )
                criteria_type_uid = (
                    repos.criteria_template_repository.get_criteria_type_uid(
                        criteria_data.criteriaTemplateUid
                    )
                )

                _, order = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=study_criteria_uid,
                    criteria_type_uid=criteria_type_uid,
                )

                # add the criteria and return
                return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=order,
                    criteria_type_uid=criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
        finally:
            repos.close()

    def make_selection_create_criteria(
        self,
        study_uid: str,
        selection_create_input: StudySelectionCriteriaCreateInput,
    ) -> models.StudySelectionCriteria:
        repos = self._repos
        try:
            # get criteria type uid from the criteria template
            criteria_type_uid = (
                repos.criteria_template_repository.get_criteria_type_uid(
                    template_uid=selection_create_input.criteriaData.criteriaTemplateUid
                )
            )

            # create criteria instance
            criteria_ar = self._create_criteria_instance(
                criteria_data=selection_create_input.criteriaData
            )

            # get pre-existing selection aggregate
            selection_aggregate = (
                repos.study_selection_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # create new selection VO to add
            new_selection = StudySelectionCriteriaVO.from_input_values(
                user_initials=self.author,
                syntax_object_uid=criteria_ar.uid,
                syntax_object_version=criteria_ar.item_metadata.version,
                criteria_type_uid=criteria_type_uid,
                generate_uid_callback=repos.study_selection_criteria_repository.generate_uid,
            )

            # add VO to aggregate
            try:
                criteria_repo = repos.criteria_repository
                assert selection_aggregate is not None
                selection_aggregate.add_criteria_selection(
                    new_selection,
                    criteria_repo.check_exists_final_version,
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_criteria_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            (
                new_selection,
                order,
            ) = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=new_selection.study_selection_uid,
                criteria_type_uid=criteria_type_uid,
            )

            # add the criteria and return
            return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=order,
                criteria_type_uid=criteria_type_uid,
                get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                get_criteria_by_uid_version_callback=self._transform_criteria_model,
                get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )
        finally:
            repos.close()

    def make_selection_preview_criteria(
        self, study_uid: str, selection_create_input: StudySelectionCriteriaCreateInput
    ) -> models.StudySelectionCriteria:
        repos = self._repos
        try:
            with db.transaction:
                criteria_service = CriteriaService()

                # get criteria type uid from the criteria template
                criteria_type_uid = repos.criteria_template_repository.get_criteria_type_uid(
                    template_uid=selection_create_input.criteriaData.criteriaTemplateUid
                )

                # create criteria instance
                criteria_ar = criteria_service.create_ar_from_input_values(
                    selection_create_input.criteriaData,
                    generate_uid_callback=(lambda: "preview"),
                )

                criteria_ar.approve(self.author)
                # get pre-existing selection aggregate
                selection_aggregate = (
                    repos.study_selection_criteria_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )

                # create new selection VO to add
                new_selection = StudySelectionCriteriaVO.from_input_values(
                    user_initials=self.author,
                    syntax_object_uid=criteria_ar.uid,
                    syntax_object_version=criteria_ar.item_metadata.version,
                    criteria_type_uid=criteria_type_uid,
                    generate_uid_callback=(lambda: "preview"),
                )

                # add VO to aggregate
                selection_aggregate.add_criteria_selection(
                    new_selection,
                    (lambda _: True),
                    self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=new_selection.study_selection_uid,
                    criteria_type_uid=criteria_type_uid,
                )

                # add the criteria and return
                return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=order,
                    criteria_type_uid=criteria_type_uid,
                    get_criteria_by_uid_callback=(
                        lambda _: models.Criteria.from_criteria_ar(criteria_ar)
                    ),
                    get_criteria_by_uid_version_callback=(
                        lambda _: models.Criteria.from_criteria_ar(criteria_ar)
                    ),
                    get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
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
    ) -> GenericFilteringReturn[models.StudySelectionCriteria]:
        repos = self._repos

        criteria_selection_ars = repos.study_selection_criteria_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in criteria_selection_ars:
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
            criteria_selection_ar = (
                repos.study_selection_criteria_repository.find_by_study(study_uid)
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    criteria_selection_ar, no_brackets=False
                ),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        criteria_selection_ars = repos.study_selection_criteria_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in criteria_selection_ars:
            parsed_selections = self._transform_all_to_response_model(
                ar, no_brackets=True
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
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudySelectionCriteria]:
        repos = self._repos
        try:
            criteria_selection_ar = (
                repos.study_selection_criteria_repository.find_by_study(study_uid)
            )
            assert criteria_selection_ar is not None

            # In order for filtering to work, we need to unwind the aggregated AR object first
            # Unwind ARs
            selections = []
            parsed_selections = self._transform_all_to_response_model(
                criteria_selection_ar, no_brackets=no_brackets
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
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str
    ) -> models.StudySelectionCriteria:
        repos = self._repos
        (
            selection_aggregate,
            new_selection,
        ) = self._get_specific_criteria_selection_by_uids(
            study_uid, study_selection_uid
        )
        if new_selection.is_instance:
            return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_selection.criteria_type_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                accepted_version=new_selection.accepted_version,
                get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                get_criteria_by_uid_version_callback=self._transform_criteria_model,
                get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                find_project_by_study_uid=repos.project_repository.find_by_study_uid,
            )
        return models.StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
            study_selection_criteria_ar=selection_aggregate,
            criteria_type_order=new_selection.criteria_type_order,
            criteria_type_uid=new_selection.criteria_type_uid,
            accepted_version=new_selection.accepted_version,
            get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
            get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
            get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
            find_project_by_study_uid=repos.project_repository.find_by_study_uid,
        )

    def _transform_history_to_response_model(
        self, study_selection_history: List[SelectionHistory], study_uid: str
    ) -> Sequence[models.StudySelectionCriteriaCore]:
        result = []
        for history in study_selection_history:
            if history.is_instance:
                result.append(
                    models.StudySelectionCriteriaCore.from_study_selection_history(
                        study_selection_history=history,
                        study_uid=study_uid,
                        get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    )
                )
            else:
                result.append(
                    models.StudySelectionCriteriaCore.from_study_selection_template_history(
                        study_selection_history=history,
                        study_uid=study_uid,
                        get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                    )
                )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionCriteriaCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_criteria_repository.find_selection_history(
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
    ) -> Sequence[models.StudySelectionCriteriaCore]:
        repos = self._repos
        try:
            try:
                selection_history = (
                    repos.study_selection_criteria_repository.find_selection_history(
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
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_criteria_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_criteria_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionCriteria:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # Set new order
            assert selection_aggregate is not None
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order, self.author
            )

            # sync with DB and save the update
            repos.study_selection_criteria_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, _ = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=study_selection_uid
            )

            # add the criteria and return
            if new_selection.is_instance:
                return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=new_order,
                    criteria_type_uid=new_selection.criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
            return models.StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )
        finally:
            repos.close()

    @db.transaction
    def set_key_criteria(
        self, study_uid: str, study_selection_uid: str, key_criteria: bool
    ) -> models.StudySelectionCriteria:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_criteria_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )
            # Load the current VO for updates
            try:
                current_vo, _ = selection_aggregate.get_specific_criteria_selection(
                    study_criteria_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = StudySelectionCriteriaVO.from_input_values(
                user_initials=self.author,
                syntax_object_uid=current_vo.syntax_object_uid,
                syntax_object_version=current_vo.syntax_object_version,
                criteria_type_uid=current_vo.criteria_type_uid,
                criteria_type_order=current_vo.criteria_type_order,
                is_instance=current_vo.is_instance,
                key_criteria=key_criteria,
                study_uid=current_vo.study_uid,
                study_selection_uid=current_vo.study_selection_uid,
                start_date=current_vo.start_date,
                accepted_version=current_vo.accepted_version,
            )

            try:
                # let the aggregate update the value object
                selection_aggregate.set_key_criteria_property(
                    updated_study_criteria_selection=updated_selection,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])
            # sync with DB and save the update
            repos.study_selection_criteria_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, _ = selection_aggregate.get_specific_criteria_selection(
                study_criteria_uid=study_selection_uid
            )

            # add the criteria and return
            if new_selection.is_instance:
                return models.StudySelectionCriteria.from_study_selection_criteria_ar_and_order(
                    study_selection_criteria_ar=selection_aggregate,
                    criteria_type_order=new_selection.criteria_type_order,
                    criteria_type_uid=new_selection.criteria_type_uid,
                    get_criteria_by_uid_callback=self._transform_latest_criteria_model,
                    get_criteria_by_uid_version_callback=self._transform_criteria_model,
                    get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                    find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
                )
            return models.StudySelectionCriteria.from_study_selection_criteria_template_ar_and_order(
                study_selection_criteria_ar=selection_aggregate,
                criteria_type_order=new_selection.criteria_type_order,
                criteria_type_uid=new_selection.criteria_type_uid,
                get_criteria_template_by_uid_callback=self._transform_latest_criteria_template_model,
                get_criteria_template_by_uid_version_callback=self._transform_criteria_template_model,
                get_ct_term_criteria_type=self._find_by_uid_or_raise_not_found,
                find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
            )
        finally:
            repos.close()
