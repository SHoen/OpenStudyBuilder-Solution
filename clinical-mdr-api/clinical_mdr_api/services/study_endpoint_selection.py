from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.library.endpoints import EndpointAR
from clinical_mdr_api.domain.library.timeframes import TimeframeAR
from clinical_mdr_api.domain.study_selection.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.study_selection.study_selection_endpoint_repository import (
    SelectionHistoryObject,
)
from clinical_mdr_api.exceptions import ForbiddenException, NotFoundException
from clinical_mdr_api.models.study_selection import (
    EndpointUnits,
    StudySelectionEndpointCreateInput,
    StudySelectionEndpointInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    fill_missing_values_in_base_model_from_reference_base_model,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)
from clinical_mdr_api.services.endpoints import EndpointService
from clinical_mdr_api.services.study_selection_base import StudySelectionMixin


class StudyEndpointSelectionService(StudySelectionMixin):
    _repos: MetaRepository

    def __init__(self, author):
        self._repos = MetaRepository()
        self.author = author

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

    def _transform_all_to_response_model(
        self, study_selection: StudySelectionEndpointsAR, no_brackets: bool = False
    ) -> Sequence[models.StudySelectionEndpoint]:
        result = []
        for order, selection in enumerate(
            study_selection.study_endpoints_selection, start=1
        ):
            result.append(
                self._transform_single_to_response_model(
                    selection,
                    order=order,
                    study_uid=study_selection.study_uid,
                    no_brackets=no_brackets,
                )
            )
        return result

    def _transform_single_to_response_model(
        self,
        study_selection: StudySelectionEndpointVO,
        order: int,
        study_uid: str,
        no_brackets: bool = False,
        get_latest_endpoint_by_uid=None,
        get_endpoint_by_uid_and_version=None,
    ) -> models.StudySelectionEndpoint:
        return models.study_selection.StudySelectionEndpoint.from_study_selection_endpoint(
            study_selection=study_selection,
            study_uid=study_uid,
            get_endpoint_by_uid_and_version=self._transform_endpoint_model
            if get_endpoint_by_uid_and_version is None
            else get_endpoint_by_uid_and_version,
            get_latest_endpoint_by_uid=self._transform_latest_endpoint_model
            if get_latest_endpoint_by_uid is None
            else get_latest_endpoint_by_uid,
            get_timeframe_by_uid_and_version=self._transform_timeframe_model,
            get_latest_timeframe=self._transform_latest_timeframe_model,
            get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
            get_study_objective_by_uid=self._transform_single_study_objective_to_model,
            order=order,
            accepted_version=study_selection.accepted_version,
            no_brackets=no_brackets,
            find_project_by_study_uid=self._repos.project_repository.find_by_study_uid,
        )

    @db.transaction
    def make_selection(
        self, study_uid: str, selection_create_input: StudySelectionEndpointInput
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_endpoint_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            endpoint_repo = repos.endpoint_repository
            timeframe_repo = repos.timeframe_repository

            if selection_create_input.endpointUid:
                endpoint_ar: EndpointAR = endpoint_repo.find_by_uid_2(
                    selection_create_input.endpointUid, for_update=True
                )
                if endpoint_ar is None:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved endpoint identified by provided uid ({selection_create_input.endpointUid})"
                    )
                # if in draft status - approve
                if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    endpoint_ar.approve(self.author)
                    endpoint_repo.save(endpoint_ar)
                # if in retired then we return a error
                elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved endpoint identified by provided uid ({selection_create_input.endpointUid})"
                    )
            else:
                endpoint_ar = None
            if selection_create_input.timeframeUid:
                timeframe_ar: TimeframeAR = timeframe_repo.find_by_uid_2(
                    selection_create_input.timeframeUid, for_update=True
                )
                if timeframe_ar is None:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                    )
                # if in draft status - approve
                if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    timeframe_ar.approve(self.author)
                    timeframe_repo.save(timeframe_ar)
                # if in retired then we return a error
                elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                    )
            else:
                timeframe_ar = None
            if selection_create_input.endpointUnits is None:
                units = None
                separator = None
            else:
                units = selection_create_input.endpointUnits.units
                separator = selection_create_input.endpointUnits.separator
            # get order from the endpoint level CT term
            if selection_create_input.endpointLevelUid is not None:
                endpoint_level_order = (
                    self._repos.ct_term_name_repository.term_specific_order_by_uid(
                        uid=selection_create_input.endpointLevelUid
                    )
                )
            else:
                endpoint_level_order = None
            new_selection = StudySelectionEndpointVO.from_input_values(
                endpoint_uid=selection_create_input.endpointUid,
                endpoint_version=endpoint_ar.item_metadata.version
                if endpoint_ar
                else None,
                endpoint_level_uid=selection_create_input.endpointLevelUid,
                endpoint_sub_level_uid=selection_create_input.endpointSubLevelUid,
                endpoint_units=units,
                timeframe_uid=selection_create_input.timeframeUid,
                timeframe_version=timeframe_ar.item_metadata.version
                if timeframe_ar
                else None,
                unit_separator=separator,
                study_objective_uid=selection_create_input.studyObjectiveUid,
                generate_uid_callback=repos.study_selection_endpoint_repository.generate_uid,
                user_initials=self.author,
                endpoint_level_order=endpoint_level_order,
            )

            # add VO to aggregate
            try:

                selection_aggregate.add_endpoint_selection(
                    study_endpoint_selection=new_selection,
                    study_objective_exist_callback=repos.study_selection_objective_repository.study_objective_exists,
                    endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                    timeframe_exist_callback=timeframe_repo.check_exists_final_version,
                    ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
                )
                selection_aggregate.validate()
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_endpoint_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
                new_selection.study_selection_uid
            )
            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    def make_selection_create_endpoint(
        self, study_uid: str, selection_create_input: StudySelectionEndpointCreateInput
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                endpoint_service = EndpointService()
                endpoint_ar = endpoint_service.create_ar_from_input_values(
                    selection_create_input.endpointData
                )

                endpoint_uid = endpoint_ar.uid
                if not endpoint_service.repository.check_exists_by_name(
                    endpoint_ar.name
                ):
                    endpoint_service.repository.save(endpoint_ar)
                else:
                    endpoint_uid = endpoint_service.repository.find_uid_by_name(
                        name=endpoint_ar.name
                    )
                endpoint_ar = endpoint_service.repository.find_by_uid_2(
                    endpoint_uid, for_update=True
                )

                # getting selection aggregate
                selection_aggregate = (
                    repos.study_selection_endpoint_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )

                # if in draft status - approve
                if endpoint_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                    endpoint_ar.approve(self.author)
                    endpoint_service.repository.save(endpoint_ar)
                elif endpoint_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                    raise exceptions.BusinessLogicException(
                        f"There is no approved objective identified by provided uid ({endpoint_uid})"
                    )

                if selection_create_input.timeframeUid:
                    timeframe_ar: TimeframeAR = (
                        repos.timeframe_repository.find_by_uid_2(
                            selection_create_input.timeframeUid, for_update=True
                        )
                    )
                    if timeframe_ar is None:
                        raise exceptions.BusinessLogicException(
                            f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                        )
                    # if in draft status - approve
                    if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                        timeframe_ar.approve(self.author)
                        repos.timeframe_repository.save(timeframe_ar)
                    # if in retired then we return a error
                    elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                        raise exceptions.BusinessLogicException(
                            f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                        )
                else:
                    timeframe_ar = None
                if selection_create_input.endpointUnits is None:
                    units = None
                    separator = None
                else:
                    units = selection_create_input.endpointUnits.units
                    separator = selection_create_input.endpointUnits.separator

                # get order from the Objective level CT term
                if selection_create_input.endpointLevelUid is not None:
                    endpoint_level_order = (
                        self._repos.ct_term_name_repository.term_specific_order_by_uid(
                            uid=selection_create_input.endpointLevelUid
                        )
                    )
                else:
                    endpoint_level_order = None

                # create new VO to add
                new_selection = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=endpoint_uid,
                    endpoint_version=endpoint_ar.item_metadata.version,
                    endpoint_level_uid=selection_create_input.endpointLevelUid,
                    endpoint_sub_level_uid=selection_create_input.endpointSubLevelUid,
                    endpoint_units=units,
                    unit_separator=separator,
                    timeframe_uid=selection_create_input.timeframeUid,
                    timeframe_version=timeframe_ar.item_metadata.version
                    if timeframe_ar
                    else None,
                    study_objective_uid=selection_create_input.studyObjectiveUid,
                    generate_uid_callback=repos.study_selection_endpoint_repository.generate_uid,
                    user_initials=self.author,
                    endpoint_level_order=endpoint_level_order,
                )
                # add VO to aggregate
                try:
                    endpoint_repo = repos.endpoint_repository
                    assert selection_aggregate is not None
                    selection_aggregate.add_endpoint_selection(
                        study_endpoint_selection=new_selection,
                        endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                        study_objective_exist_callback=repos.study_selection_objective_repository.study_objective_exists,
                        timeframe_exist_callback=repos.timeframe_repository.check_exists_final_version,
                        ct_term_exists_callback=repos.ct_term_name_repository.term_specific_exists_by_uid,
                        unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
                    )
                except ValueError as value_error:
                    raise exceptions.ValidationException(value_error.args[0])

                # sync with DB and save the update
                repos.study_selection_endpoint_repository.save(
                    selection_aggregate, self.author
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_endpoint_selection(
                    new_selection.study_selection_uid
                )
                return self._transform_single_to_response_model(
                    new_selection, order, study_uid
                )
        finally:
            repos.close()

    def make_selection_preview_endpoint(
        self, study_uid: str, selection_create_input: StudySelectionEndpointCreateInput
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            with db.transaction:
                # check if name exists
                endpoint_service = EndpointService()
                endpoint_ar = endpoint_service.create_ar_from_input_values(
                    selection_create_input.endpointData,
                    generate_uid_callback=(lambda: "preview"),
                )

                endpoint_uid = endpoint_ar.uid
                endpoint_ar.approve(self.author)
                # getting selection aggregate
                selection_aggregate = (
                    repos.study_selection_endpoint_repository.find_by_study(
                        study_uid=study_uid, for_update=True
                    )
                )

                timeframe_repo = repos.timeframe_repository
                if selection_create_input.timeframeUid:
                    timeframe_ar: TimeframeAR = timeframe_repo.find_by_uid_2(
                        selection_create_input.timeframeUid, for_update=True
                    )
                    if timeframe_ar is None:
                        raise exceptions.BusinessLogicException(
                            f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                        )
                    # if in draft status - approve
                    if timeframe_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                        timeframe_ar.approve(self.author)
                        timeframe_repo.save(timeframe_ar)
                    # if in retired then we return a error
                    elif timeframe_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                        raise exceptions.BusinessLogicException(
                            f"There is no approved timeframe identified by provided uid ({selection_create_input.timeframeUid})"
                        )
                else:
                    timeframe_ar = None

                units = None
                separator = None

                # create new VO to add
                new_selection = StudySelectionEndpointVO.from_input_values(
                    endpoint_uid=endpoint_uid,
                    endpoint_version=endpoint_ar.item_metadata.version,
                    endpoint_level_uid=selection_create_input.endpointLevelUid,
                    endpoint_sub_level_uid=selection_create_input.endpointSubLevelUid,
                    endpoint_units=units,
                    unit_separator=separator,
                    timeframe_uid=selection_create_input.timeframeUid,
                    timeframe_version=timeframe_ar.item_metadata.version
                    if timeframe_ar
                    else None,
                    study_objective_uid=selection_create_input.studyObjectiveUid,
                    generate_uid_callback=(lambda: "preview"),
                    user_initials=self.author,
                    endpoint_level_order=None,
                )
                # add VO to aggregate
                selection_aggregate.add_endpoint_selection(
                    study_endpoint_selection=new_selection,
                    endpoint_exist_callback=(lambda _: True),
                    study_objective_exist_callback=repos.study_selection_objective_repository.study_objective_exists,
                    timeframe_exist_callback=repos.timeframe_repository.check_exists_final_version,
                    ct_term_exists_callback=repos.ct_term_name_repository.term_specific_exists_by_uid,
                    unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
                )

                # Fetch the new selection which was just added
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_endpoint_selection(
                    new_selection.study_selection_uid
                )
                return self._transform_single_to_response_model(
                    new_selection,
                    order,
                    study_uid,
                    get_latest_endpoint_by_uid=(
                        lambda _: models.Endpoint.from_endpoint_ar(endpoint_ar)
                    ),
                    get_endpoint_by_uid_and_version=(
                        lambda a, b: models.Endpoint.from_endpoint_ar(endpoint_ar)
                    ),
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
    ) -> GenericFilteringReturn[models.StudySelectionEndpoint]:
        repos = self._repos
        endpoint_selection_ars = repos.study_selection_endpoint_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in endpoint_selection_ars:
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
            endpoint_selection_ars = (
                repos.study_selection_endpoint_repository.find_by_study(study_uid)
            )

            header_values = service_level_generic_header_filtering(
                items=self._transform_all_to_response_model(
                    endpoint_selection_ars, no_brackets=False
                ),
                field_name=field_name,
                search_string=search_string,
                filter_by=filter_by,
                filter_operator=filter_operator,
                result_count=result_count,
            )

            return header_values

        endpoint_selection_ars = repos.study_selection_endpoint_repository.find_all(
            project_name=project_name,
            project_number=project_number,
        )

        # In order for filtering to work, we need to unwind the aggregated AR object first
        # Unwind ARs
        selections = []
        for ar in endpoint_selection_ars:
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
    ) -> GenericFilteringReturn:
        repos = MetaRepository()
        try:
            endpoint_selection_ar = (
                repos.study_selection_endpoint_repository.find_by_study(study_uid)
            )
            selection = self._transform_all_to_response_model(
                endpoint_selection_ar, no_brackets=no_brackets
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

    @db.transaction
    def get_specific_selection(
        self, study_uid: str, study_selection_uid: str, for_update: bool = False
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            selection_aggregate = (
                repos.study_selection_endpoint_repository.find_by_study(
                    study_uid, for_update
                )
            )
            try:
                (
                    new_selection,
                    order,
                ) = selection_aggregate.get_specific_endpoint_selection(
                    study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Verify that the study endpoint is not being used as a template parameter
            if repos.study_selection_endpoint_repository.is_used_as_parameter(
                study_selection_uid
            ):
                raise exceptions.BusinessLogicException(
                    "This study endpoint is currently used as a parameter by a study objective."
                )

            # Load aggregate
            selection_aggregate = (
                repos.study_selection_endpoint_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.remove_endpoint_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_selection_endpoint_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    @db.transaction
    def set_new_order(
        self, study_uid: str, study_selection_uid: str, new_order: int
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_endpoint_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            selection_aggregate.set_new_order_for_selection(
                study_selection_uid, new_order
            )

            # sync with DB and save the update
            repos.study_selection_endpoint_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just added
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
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
    def patch_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        selection_update_input: StudySelectionEndpointInput,
    ) -> models.StudySelectionEndpoint:
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_selection_endpoint_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # Load the current VO for updates
            try:
                current_vo, order = selection_aggregate.get_specific_endpoint_selection(
                    study_selection_uid=study_selection_uid
                )
            except ValueError as value_error:
                raise exceptions.NotFoundException(value_error.args[0])

            # merge current with updates
            updated_selection = self._patch_prepare_new_study_endpoint(
                request_study_endpoint=selection_update_input,
                current_study_endpoint=current_vo,
            )

            try:
                endpoint_repo = self._repos.endpoint_repository
                timeframe_repo = self._repos.timeframe_repository
                # let the aggregate update the value object
                selection_aggregate.update_selection(
                    updated_study_endpoint_selection=updated_selection,
                    study_objective_exist_callback=repos.study_selection_objective_repository.study_objective_exists,
                    endpoint_exist_callback=endpoint_repo.check_exists_final_version,
                    timeframe_exist_callback=timeframe_repo.check_exists_final_version,
                    ct_term_exists_callback=self._repos.ct_term_name_repository.term_specific_exists_by_uid,
                    unit_definition_exists_callback=repos.unit_definition_repository.check_exists_final_version,
                )
                selection_aggregate.validate()
            except ValueError as value_error:
                raise exceptions.BusinessLogicException(value_error.args[0])

            # sync with DB and save the update
            repos.study_selection_endpoint_repository.save(
                selection_aggregate, self.author
            )

            # Fetch the new selection which was just updated
            new_selection, order = selection_aggregate.get_specific_endpoint_selection(
                study_selection_uid
            )

            # add the objective and return
            return self._transform_single_to_response_model(
                new_selection, order, study_uid
            )
        finally:
            repos.close()

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

    def _transform_history_to_response_model(
        self, study_selection_history: List[SelectionHistoryObject], study_uid: str
    ) -> Sequence[models.StudySelectionEndpoint]:
        result = []

        for history in study_selection_history:
            result.append(
                models.StudySelectionEndpoint.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_endpoint_by_uid=self._transform_endpoint_model,
                    get_timeframe_by_uid=self._transform_timeframe_model,
                    get_study_objective_by_uid=self._transform_single_study_objective_to_model,
                    get_ct_term_objective_level=self._find_by_uid_or_raise_not_found,
                )
            )
        return result

    @db.transaction
    def get_all_selection_audit_trail(
        self, study_uid: str
    ) -> Sequence[models.StudySelectionEndpoint]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_endpoint_repository.find_selection_history(
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
    ) -> Sequence[models.StudySelectionEndpoint]:
        repos = self._repos
        try:
            selection_history = (
                repos.study_selection_endpoint_repository.find_selection_history(
                    study_uid, study_selection_uid
                )
            )
            return self._transform_history_to_response_model(
                selection_history, study_uid
            )
        finally:
            repos.close()
