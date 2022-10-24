import os
from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response, status
from pydantic.types import Json
from starlette.responses import StreamingResponse

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.study_arm_selection import StudyArmSelectionService
from clinical_mdr_api.services.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.study_cohort_selection import StudyCohortSelectionService
from clinical_mdr_api.services.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.services.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.services.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.study_objectives import StudyObjectivesService

router = APIRouter()

studyUID = Path(None, description="The unique id of the study.")

studySelectionUid = Path(None, description="The unique id of the study selection.")

"""
    API endpoints to study objectives
"""


@router.get(
    "/study-objectives",
    summary="Returns all study objectives currently selected",
    response_model=CustomPage[models.StudySelectionObjective],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_objectives_for_all_studies(
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "should be returned",
    ),
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionObjective]:
    service = StudyObjectiveSelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=noBrackets,
        project_name=projectName,
        project_number=projectNumber,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/study-objectives/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=List[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_objective_values_for_header(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-objectives",
    summary="Returns all study objectives currently selected for study with provided uid",
    response_model=GenericFilteringReturn[models.StudySelectionObjective],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "order",
            "objectiveLevel=objectiveLevel.sponsorPreferredName",
            "name=objective.name",
            "endpointCount",
            "startDate",
            "userInitials",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_objectives(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "should be returned",
    ),
    current_user_id: str = Depends(get_current_user_id),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
):
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_all_selection(
        study_uid=uid,
        no_brackets=noBrackets,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
    )


@router.get(
    "/{uid}/study-objectives/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=List[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_values_for_header(
    uid: str = studyUID,
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-objectives/audit-trail",
    summary="List full audit trail related to definition of all study objectives.",
    description="""
The following values should be return for all study objectives.
- dateTime
- userInitials
- action
- objectiveTemplate
- objective
- objectiveLevel
- order
    """,
    response_model=Sequence[models.StudySelectionObjectiveCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_objectives_audit_trail(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionObjectiveCore]:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-objectives/{studyobjectiveuid}",
    summary="Returns specific study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_objective(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studyobjectiveuid
    )


@router.get(
    "/{uid}/study-objectives/{studyobjectiveuid}/audit-trail",
    summary="List audit trail related to definition of a specific study objective.",
    description="""
The following values should be return for selected study objective:
- dateTime
- userInitials
- action
- objectiveTemplate
- objective
- objectiveLevel
- order
    """,
    response_model=Sequence[models.StudySelectionObjectiveCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_objective_audit_trail(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjectiveCore:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studyobjectiveuid
    )


@router.post(
    "/{uid}/study-objectives/select",
    summary="Creating a study objective selection based on the input data",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_objective_selection(
    uid: str = studyUID,
    selection: models.StudySelectionObjectiveInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.post(
    "/{uid}/study-objectives/create",
    summary="Creating a study objective selection based on the input data including creating new objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_objective_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionObjectiveCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.make_selection_create_objective(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/{uid}/study-objectives/create/preview",
    summary="Preview creating a study objective selection based on the input data",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def preview_new_objective_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionObjectiveCreateInput = Body(
        None, description="Related parameters of the selection that shall be previewed."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.make_selection_preview_objective(
        study_uid=uid, selection_create_input=selection
    )


@router.delete(
    "/{uid}/study-objectives/{studyobjectiveuid}",
    summary="Deletes a study objective",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_objective(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyObjectiveSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studyobjectiveuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-objectives/{studyobjectiveuid}/order",
    summary="Change a order of a study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_objective_selection_order(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    new_order_input: models.StudySelectionObjectiveNewOrder = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studyobjectiveuid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/{uid}/study-objectives/{studyobjectiveuid}",
    summary="update the objective level of a study objective",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_objective_selection(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    selection: models.StudySelectionObjectiveInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studyobjectiveuid,
        selection_update_input=selection,
    )


@router.post(
    "/{uid}/study-objectives/{studyobjectiveuid}/sync-latest-version",
    summary="update to latest objective version study selection",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def sync_latest_version(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.update_selection_to_latest_version(
        study_uid=uid, study_selection_uid=studyobjectiveuid
    )


"""
    API endpoints to study endpoints
"""


@router.get(
    "/study-endpoints",
    summary="Returns all study endpoints currently selected",
    response_model=CustomPage[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_endpoints_for_all_studies(
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Endpoint"
        "should be returned",
    ),
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionEndpoint]:
    service = StudyEndpointSelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=noBrackets,
        project_name=projectName,
        project_number=projectNumber,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/study-endpoints/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_endpoint_values_for_header(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-endpoints",
    summary="""List all study endpoints currently selected for study with provided uid""",
    description="""
State before:
- Study must exist.

Business logic:
 - By default (no study status is provided) list all study endpoints for the study uid in status draft. If the study not exist in status draft then return the study endpoints for the study in status released. If the study uid only exist as deleted then this is returned.
- If a specific study status parameter is provided then return study endpoints for this study status.
- If the locked study status parameter is requested then a study version should also be provided, and then the study endpoints for the specific locked study version is returned.
- Indicate by an boolean variable if the study endpoint can be updated (if the selected study is in status draft).
- Indicate by an boolean variable if all expected selections have been made for each study endpoint, or some are missing.
   - e.g. endpoint level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected endpoint is available in a newer version.
 - Indicate by an boolean variable if a study endpoint can be re-ordered.

State after:
- no change.
""",
    response_model=GenericFilteringReturn[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "order",
            "name=endpoint.name",
            "units=endpointUnits.units",
            "timeframe=timeframe.name",
            "objective=studyObjective",
            "startDate",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_endpoints(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Objective"
        "and Endpoint should be returned",
    ),
    current_user_id: str = Depends(get_current_user_id),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
):
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_all_selection(
        study_uid=uid,
        no_brackets=noBrackets,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
    )


@router.get(
    "/{uid}/study-endpoints/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_study_endpoint_values_for_header(
    uid: str = studyUID,
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-endpoints/audit-trail",
    summary="List full audit trail related to definition of all study endpoints.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study endpoints for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study endpoints.
    """,
    response_model=Sequence[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_endpoints_audit_trail(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionEndpoint]:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-endpoints/{studyendpointuid}",
    summary="Returns specific study endpoint",
    description="""
State before:
 - Study and study endpoint must exist

Business logic:
 - By default (no study status is provided) list all details for specified study endpoint for the study uid in status draft. If the study not exist in status draft then return the study endpoints for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study endpoints for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study endpoint for the specific locked study version is returned.
 - Indicate by an boolean variable if the study endpoint can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study endpoint, or some are missing.
 - e.g. endpoint level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected endpoint is available in a newer version.
 - Indicate by an boolean variable if a study endpoint can be re-ordered.

State after:
 - no change
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_endpoint(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studyendpointuid
    )


@router.get(
    "/{uid}/study-endpoints/{studyendpointuid}/audit-trail",
    summary="List audit trail related to definition of a specific study coendpointsmpound.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compounds must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study endpoints for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study endpoints.
    """,
    response_model=Sequence[models.StudySelectionEndpoint],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_endpoint_audit_trail(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studyendpointuid
    )


@router.post(
    "/{uid}/study-endpoints/select",
    summary="Creating a study endpoint selection based on the input data",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Selected endpoint-uid, endpoint-level, timeframe-uid and unit-definition-uid must exist.

Business logic:
 - Add a study-endpoint to a study based on selection of an existing endpoint.
 - Reference to endpoint-uid must be included, this will implicitly include reference to the endpoint template.
 - If the selected endpoint is in draft then approve it and select the new approved version.
 - If the selected endpoint is retired then an error message must be provided.
 - Selection of endpoint level is optional.
 - Selection of Unit is optional.
 - Order must be assigned as the next incremental order number or as 1 if this is the initial study endpoint.

State after:
 - Endpoint is added as study endpoint to the study.
 - Added new entry in the audit trail for the creation of the study-endpoint.
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_endpoint_selection(
    uid: str = studyUID,
    selection: models.StudySelectionEndpointInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.post(
    "/{uid}/study-endpoints/create",
    summary="Creating a study endpoint selection based on the input data including creating new endpoint",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the endpoint",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or endpoint is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_endpoint_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionEndpointCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.make_selection_create_endpoint(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/{uid}/study-endpoints/create/preview",
    summary="Preview creating a study endpoint selection based on the input data",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the endpoint",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or endpoint is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_endpoint_selection_preview(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionEndpointCreateInput = Body(
        None, description="Related parameters of the selection that shall be previewed."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.make_selection_preview_endpoint(
        study_uid=uid, selection_create_input=selection
    )


@router.delete(
    "/{uid}/study-endpoints/{studyendpointuid}",
    summary="Deletes a objective selection",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study-endpoint-uid must exist.

Business logic:
 - Remove specified study-endpoint from the study.
 - Reference to the study-endpoint should still exist in the the audit trail.
 - If a subsequent study endpoint exist in the list of study endpoints then the order number for following study endpoint must be decreased with 1.

State after:
- Study endpoint is deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-endpoint.
""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_endpoint(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyEndpointSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studyendpointuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-endpoints/{studyendpointuid}/order",
    summary="Change a order of a selection",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - studyEndpointUid must exist.

Business logic:
 - moves the study selection to the order which is send in the new_order property

State after:
 - Order number for specified study-endpoint is updated to new order number.
 - Note this will change order on either the preceding or following study-endpoints as well.
 - Added new entry in the audit trail for the re-ordering of the study-endpoints.
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Order is larger than the number of selections",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_endpoint_selection_order(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    new_order_input: models.StudySelectionEndpointNewOrder = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studyendpointuid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/{uid}/study-endpoints/{studyendpointuid}",
    summary="update the study endpoint",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - Selected endpoint-uid, endpoint-template-uid, endpoint-level, timeframe-uid and unit-definition-uid must exist.

Business logic:
 - Same logic applies as for selecting or creating an study endpoint (see two POST statements for /study-endpoints)

State after:
- Endpoint is added as study endpoint to the study.
 - This PATCH method can cover cover two parts:
    - Change the endpoint level for the currently selected study endpoint
    - Replace the currently selected study endpoint based on the same functionality as /study-endpoints/create
 - Added new entry in the audit trail for the update of the study-endpoint.
""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - When there exist no study endpoint with the study endpoint uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_endpoint_selection(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    selection: models.StudySelectionEndpointInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionEndpoint:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studyendpointuid,
        selection_update_input=selection,
    )


@router.get(
    "/{uid}/study-objectives.docx",
    summary="""Returns Study Objectives and Endpoints table in standard layout DOCX document""",
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_objectives_and_endpoints_standard_docx(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> StreamingResponse:
    docx = StudyObjectivesService(user_id=current_user_id).get_standard_docx(
        study_uid=uid
    )
    stream = docx.get_document_stream()
    size = stream.seek(0, os.SEEK_END)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{uid} objectives.docx"',
            "Content-Length": f"{size:d}",
        },
    )


"""
    API endpoints to study compounds
"""


@router.get(
    "/study-compounds",
    summary="Returns all study compounds currently selected",
    response_model=CustomPage[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_compounds_for_all_studies(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionCompound]:
    service = StudyCompoundSelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        project_name=projectName,
        project_number=projectNumber,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/study-compounds/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_compound_values_for_header(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-compounds",
    summary="List all study compounds currently selected for study with provided uid",
    description="""
State before:
 - Study-uid must exist.

Business logic:
 - By default (no study status is provided) list all study compounds for the study uid in status draft. If the study not exist in status draft then return the study compounds for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study compounds for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study compounds for the specific locked study version is returned.
 - Indicate by an boolean variable if the study compound can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study compound, or some are missing.
   - e.g. Compound and TypeOfTreatment are expected.
 - Indicate by an boolean variable if the selected compound is available in a newer version.
 - Indicate by an boolean variable if a study compound can be re-ordered.
 
State after:
- no change.
""",
    response_model=GenericFilteringReturn[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "compound=compound.name",
            "pharmaClass=compound.pClassConcept",
            "substanceNames=compound.uniiSubstanceName",
            "uniiCodes=compound.uniiSubstanceCd",
            "typeOfTreatment=typeOfTreatment.name",
            "routeOfAdmin=routeOfAdministration.name",
            "dosageForm=dosageForm.name",
            "dispensedIn=dispensedIn",
            "device=device",
            "formulation=formulation",
            "other=otherInfo",
            "reasonForMissing=reasonForMissingNullValueCode",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_compounds(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
):
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_all_selection(
        study_uid=uid,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
    )


@router.get(
    "/{uid}/study-compounds/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_compounds_values_for_header(
    uid: str = studyUID,
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-compounds/audit-trail",
    summary="List full audit trail related to definition of all study compounds.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study compounds for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study compounds.
    """,
    response_model=Sequence[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_compounds_audit_trail(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionCompound]:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-compounds/{studycompounduid}/audit-trail",
    summary="List audit trail related to definition of a specific study compound.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compounds must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study compound for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study compound.
    """,
    response_model=Sequence[models.StudySelectionCompound],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_compound_audit_trail(
    uid: str = studyUID,
    studycompounduid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studycompounduid
    )


@router.get(
    "/{uid}/study-compounds/{studycompounduid}",
    summary="Returns specific study objective",
    description="""
State before:
 - Study-uid and study-compound-uid must exist

Business logic:
 - By default (no study status is provided) list all details for specified study compound for the study uid in status draft. If the study not exist in status draft then return the study compounds for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study compounds for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study compound for the specific locked study version is returned.  - Indicate by an boolean variable if the study compound can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study compound, or some are missing.
   - e.g. Compound and TypeOfTreatment are expected.
 - Indicate by an boolean variable if the selected compound is available in a newer version.
 - Indicate by an boolean variable if a study compound can be re-ordered.

State after:
 - no change
""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_compound(
    uid: str = studyUID,
    studycompounduid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studycompounduid
    )


@router.post(
    "/{uid}/study-compounds/select",
    summary="Add a study compound to a study based on selection of a compound concept in library, or a 'Reason for missing'.",
    description="""
State before:
 - Study must exist and be in status draft
 - Compound-uid must exist and be in status Final.
 
Business logic:
 - Add a study-compound to the study based on selection of an existing compound concept in the library.
 - If the selected compound-uid is retired then an error message must be provided.
 - A single relationships can be defined for a study compound to each of the following code list terms:
   - Type of treatment
   - Route of administration
   - Dosages form
   - Dispensed in
   - Device
   - Formulation
 - It is also possible to save a free test string describing other information for the study-compound.
 - Order for the study compound must be assigged as the next incremental order number or as 1 if this is the initial study objective for the study.
 - It should be possible to define a 'Reason for missing' value for a specific value of 'Type of treatment'. In this case the following rule apply:
   - Only the parameter for 'Type of treatment' can be defined - the parameter value for compound or any other related parameters must be null.
   - No other study compound must exist for the study with the same value for 'Type of Treatment'.
   - No other 'Reason for missing' value must exist for the study with the same value for 'Type of Treatment' (ReasonForMissing can only be defined once for a TypeOfTreatment).
   - Thereby either the parameter compound-uid or type-of-treatment-uid must be provided, but not both of them 8they are mytually exclusive).

State after:
 - compound is added as study compound to the study.
 - Added new entry in the audit trail for the creation of the study-compound.
 """,
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the objective",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or objective is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_compound_selection(
    uid: str = studyUID,
    selection: models.StudySelectionCompoundInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.delete(
    "/{uid}/study-compounds/{studycompounduid}",
    summary="Delete a study compound.",
    description="""
State before:
- Study and study-compound-uid must exist and study must be in status draft.

Business logic:
 - Remove specified study-compound from the study.
 - Reference to the study-compound should still exist in the the audit trail.
 - If a subsequent study compound exist in the list of study compounds then the order number for following study compound must be decreased with 1.

State after:
- Study compound is deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-compound.
""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the objective and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_compound(
    uid: str = studyUID,
    studycompounduid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studycompounduid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-compounds/{studycompounduid}/order",
    summary="Change display order of study compound",
    description="""
State before:
- Study and study-compound-uid must exist and study must be in status draft.
- Old order number must match current order number in database for study compound.

Business logic:
 - moves the study selection to the order which is send in the new_order property
 
State after:
 - Order number for specified study-compound is updated to new order number.
 - Note this will change order on either the preceding or following study-compounds as well.
 - Added new entry in the audit trail for the re-ordering of the study-compounds.
""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_compound_selection_order(
    uid: str = studyUID,
    studycompounduid: str = studySelectionUid,
    new_order_input: models.StudySelectionCompoundNewOrder = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studycompounduid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/{uid}/study-compounds/{studycompounduid}",
    summary="Edit or replace a study compound",
    description="""
State before:
 - Study must exist and be in status draft
 - Compound-uid must exist and be in status Final.

Business logic:
 - Update specified study-compound with selection of an existing compound concept in the library.
 - If the selected compound-uid is retired then an error message must be provided.
 - A single relationships can be defined for a study compound to each of the following code list terms:
   - Type of treatment
   - Route of administration
   - Dosages form
   - Dispensed in
   - Device
   - Formulation
 - It is also possible to save a free text string describing other information for the study-compound.
 - Order number for the study compound cannot be changed by this API endpoint.
 - It should be possible to define a 'Reason for missing' value for a specific value of 'Type of treatment'. In this case the following rule apply:
   - Only the parameter for 'Type of treatment' can be defined - the parameter value for compound or any other related parameters must be null.
   - No other study compound must exist for the study with the same value for 'Type of Treatment'.
   - No other 'Reason for missing' value must exist for the study with the same value for 'Type of Treatment' (ReasonForMissing can only be defined once for a TypeOfTreatment).
   - Thereby either the parameter compound-uid or type-of-treatment-uid must be provided, but not both of them 8they are mutually exclusive).

State after:
 - compound or related parameters is updated for the study compound.
 - Added new entry in the audit trail for the update of the study-compound.""",
    response_model=models.StudySelectionCompound,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and objective.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_compound_selection(
    uid: str = studyUID,
    studycompounduid: str = studySelectionUid,
    selection: models.StudySelectionCompoundInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCompound:
    service = StudyCompoundSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studycompounduid,
        selection_update_input=selection,
    )


@router.post(
    "/{uid}/study-endpoints/{studyendpointuid}/sync-latest-endpoint-version",
    summary="update to latest endpoint version study selection",
    description="""
State before:
 - Study must exist
 - Study endpoint selection must exist
 - Endpoint version selected for study endpoint selection is not the latest available final version of endpoint.

Business logic:
 - Update specified endpoint study-selection with the latest final version of previously selected endpoint.

State after:
 - Study exists
 - Study endpoint selection exists
 - Endpoint version selected for study endpoint selection is the latest available final version.
 - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and endpoint",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def sync_latest_endpoint_version(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.update_selection_to_latest_version_of_endpoint(
        study_uid=uid, study_selection_uid=studyendpointuid
    )


@router.post(
    "/{uid}/study-endpoints/{studyendpointuid}/sync-latest-timeframe-version",
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Timeframe version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection with the latest final version of previously selected timeframe.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Timeframe version selected for study endpoint selection is the latest available final version.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def sync_latest_timeframe_version(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.update_selection_to_latest_version_of_timeframe(
        study_uid=uid, study_selection_uid=studyendpointuid
    )


@router.post(
    "/{uid}/study-endpoints/{studyendpointuid}/accept-version",
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Timeframe and/or endpoint version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection, setting accepted version to show that update was refused by user.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Timeframe and endpoint version selected for study endpoint selection is not changed.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionEndpoint,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_endpoint_accept_version(
    uid: str = studyUID,
    studyendpointuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyEndpointSelectionService(author=current_user_id)
    return service.update_selection_accept_versions(
        study_uid=uid, study_selection_uid=studyendpointuid
    )


@router.post(
    "/{uid}/study-objectives/{studyobjectiveuid}/accept-version",
    summary="update to latest timeframe version study selection",
    description="""
    State before:
     - Study must exist
     - Study endpoint selection must exist
     - Objective version selected for study endpoint selection is not the latest available final version of the timeframe.

    Business logic:
     - Update specified endpoint study-selection, setting accepted version to show that update was refused by user.

    State after:
     - Study exists
     - Study endpoint selection exists
     - Objective version selected for study endpoint selection is not changed.
     - Added new entry in the audit trail for the update of the study-endpoint.""",
    response_model=models.StudySelectionObjective,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and timeframe",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_objective_accept_version(
    uid: str = studyUID,
    studyobjectiveuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionObjective:
    service = StudyObjectiveSelectionService(author=current_user_id)
    return service.update_selection_accept_version(
        study_uid=uid, study_selection_uid=studyobjectiveuid
    )


"""
    API endpoints to study criteria
"""


@router.get(
    "/study-criteria",
    summary="Returns all study criteria currently selected",
    response_model=CustomPage[models.StudySelectionCriteria],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_criteria_for_all_studies(
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Criteria"
        "should be returned",
    ),
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionCriteria]:
    service = StudyCriteriaSelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        no_brackets=noBrackets,
        project_name=projectName,
        project_number=projectNumber,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/study-criteria/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_criteria_values_for_header(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        project_name=projectName,
        project_number=projectNumber,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-criteria",
    summary="Returns all study criteria currently selected for study with provided uid",
    description="""
    State before:
    - Study must exist.
    
    Business logic:
    - By default (no study status is provided) list all study criteria for the study uid in status draft. If the study not exist in status draft then return the study criteria for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study criteria for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study criteria for the specific locked study version is returned.
    - Indicate by a boolean variable if the study criteria can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study criteria, or some are missing.
    - e.g. a criteria instance is expected.
    - Indicate by an boolean variable if a study criteria can be re-ordered.

    State after:
    - no change.
    
    Possible errors:
    - Invalid study-uid.
    
    Returned data:
    List selected study with the following information:
    - studyUid
    - studyCriteriaUid
    - order (Derived Integer, valid in the scope of a criteriaType)
    - criteriaUid (Selected CriteriaRoot  uid)
    - criteriaName (String, CriteriaValue name)
    - criteriaType (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=CustomPage[models.StudySelectionCriteria],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "guidanceText",
            "keyCriteria",
            "startDate",
            "userInitials",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_criteria(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = studyUID,
    noBrackets: bool = Query(
        False,
        description="Indicates whether brackets around Template Parameters in the Criteria"
        "should be returned",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionCriteria]:
    service = StudyCriteriaSelectionService(author=current_user_id)
    all_items = service.get_all_selection(
        study_uid=uid,
        no_brackets=noBrackets,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-criteria/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_study_criteria_values_for_header(
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-criteria/audit-trail",
    summary="List full audit trail related to definition of all study criteria.",
    description="""
    State before:
    - Study must exist.

    Business logic:
    - List all entries in the audit trail related to study criteria for specified study-uid.
    - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

    State after:
    - no change.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - studyUid
    - studyCriteriaUid
    - order (Derived Integer)
    - criteriaUid (Selected CriteriaRoot  uid)
    - criteriaName (String, CriteriaValue name)
    - criteriaType (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=Sequence[models.StudySelectionCriteriaCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_criteria_audit_trail(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionCriteriaCore]:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-criteria/{studycriteriauid}",
    summary="Returns specific study criteria",
    description="""
    State before:
    - Study and study criteria must exist
    
    Business logic:
    - By default (no study status is provided) list all details for specified study criteria for the study uid in status draft. If the study not exist in status draft then return the study criteria for the study in status released. If the study uid only exist as deleted then this is returned.
    - If a specific study status parameter is provided then return study criteria for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the specified study criteria for the specific locked study version is returned.
    - Indicate by an boolean variable if the study criteria can be updated (if the selected study is in status draft).
    - Indicate by an boolean variable if all expected selections have been made for each study criteria, or some are missing.
    - Indicate by an boolean variable if the selected criteria is available in a newer version.
    - Indicate by an boolean variable if a study criteria can be re-ordered.
    
    State after:
    - no change
    
    Possible errors:
    - Invalid study-uid or studyCriteriaUid.
    
    Returned data:
    List selected study with the following information:
    - studyUid
    - studyCriteriaUid
    - order (Derived Integer)
    - criteriaUid (Selected CriteriaRoot  uid)
    - criteriaName (String, CriteriaValue name)
    - criteriaType (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the criteria for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_criteria(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studycriteriauid
    )


@router.get(
    "/{uid}/study-criteria/{studycriteriauid}/audit-trail",
    summary="List audit trail related to definition of a specific study criteria.",
    description="""
    State before:
    - Study and study criteria must exist.

    Business logic:
    - List a specific entry in the audit trail related to the specified study criteria for the specified study-uid.
    - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

    State after:
    - no change.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - studyUid
    - studyCriteriaUid
    - order (Derived Integer)
    - criteriaUid (Selected CriteriaRoot  uid)
    - criteriaName (String, CriteriaValue name)
    - criteriaType (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible.
        - Boolean indication if all expected selections have been made.
        - Boolean indication if the study criteria can be re-ordered.
    """,
    response_model=Sequence[models.StudySelectionCriteriaCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the criteria for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_criteria_audit_trail(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteriaCore:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studycriteriauid
    )


@router.post(
    "/{uid}/study-criteria/create",
    summary="Creating a study criteria selection based on the input data including creating new criteria",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Create a study criteria and to a study based on valid selections and values.
    
    State after:
    - criteria instance is created
    - criteria is added as study criteria to the study.
    - Added new entry in the audit trail for the creation of the study-criteria.
    
    Possible errors:
    - Invalid study-uid.

    Returned data:
    List selected study with the following information:
    - studyUid
    - studyCriteriaUid
    - order (Derived Integer)
    - criteriaUid (Selected CriteriaRoot  uid)
    - criteriaName (String, CriteriaValue name)
    - criteriaType (String, derived from the selected criteria instance's template, which has a connection to a type node)
    - note (String)
    - Modified (as a date of last modification).
    - Possible Actions (based on study state, version of selected nodes, metadata consistency checks, etc. - see business rules).
        - Boolean indication if edit is possible. (study is in Draft status)
        - Boolean indication if all expected selections have been made. (expected !== required)
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_criteria_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionCriteriaCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.make_selection_create_criteria(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/{uid}/study-criteria/create/preview",
    summary="Previews creating a study criteria selection based on the input data including creating new criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def preview_new_criteria_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionCriteriaCreateInput = Body(
        None, description="Related parameters of the selection that shall be previewed."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.make_selection_preview_criteria(
        study_uid=uid, selection_create_input=selection
    )


@router.post(
    "/{uid}/study-criteria/batch-select",
    summary="Select multiple criteria templates as a batch. If the template has no parameters, will also create the instance.",
    description="""
    State before:
    - Study must exist and study status must be in draft.

    Business logic:
    - Select criteria template without instantiating them.
    - This must be done as a batch
    
    State after:
    - Study criteria is created.
    - Criteria templates are all selected by the study criteria.
    - If a given template has no parameters, the instance will be created and selected.
    - Added new entry in the audit trail for the creation of the study-criteria.
    
    Possible errors:
    - Invalid study-uid.
    - Invalid study-criteria-template-uid.

    Returned data:
    List selected criteria templates/instances with the following information:
    - studyUid
    - studyCriteriaTemplateUid / studyCriteriaUid
    - order (Derived Integer)
    - latest version of the selected criteria template/instance
    """,
    response_model=Sequence[models.StudySelectionCriteria],
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the criteria",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or criteria is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_batch_select_criteria_template(
    uid: str = studyUID,
    selection: Sequence[
        models.study_selection.StudySelectionCriteriaTemplateSelectInput
    ] = Body(
        None,
        description="List of objects with properties needed to identify the templates to select",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.batch_select_criteria_template(
        study_uid=uid, selection_create_input=selection
    )


@router.patch(
    "/{uid}/study-criteria/{studycriteriauid}/finalize",
    summary="Finalize the study criteria template selection by creating an instance of this template",
    description="""
    State before:
    - Study and study selection must exist and the selected object must be a template and not an instance.

    Business logic:
    - Create an instance of the selected template
    - Re-attach the study criteria object to the instance instead of the template
    
    State after:
    - Instance of the template is created
    - Study criteria is detached from the template
    - Study criteria is attached to the instance
    
    Possible errors:
    - Invalid study-uid.
    - Invalid study-criteria-uid.

    Returned data:
    Selected criteria instance with the following information:
    - studyUid
    - studyCriteriaUid
    - order
    - latest version of the selected criteria
    """,
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or study criteria is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_finalize_criteria_selection(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    criteria_data: models.CriteriaCreateInput = Body(
        None,
        description="Data necessary to create the criteria instance from the template",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.finalize_criteria_selection(
        study_uid=uid, study_criteria_uid=studycriteriauid, criteria_data=criteria_data
    )


@router.delete(
    "/{uid}/study-criteria/{studycriteriauid}",
    summary="Deletes a study criteria",
    description="""
    State before:
    - Study must exist and study status must be in draft.
    - studyCriteriaUid must exist. 

    Business logic:
    - Remove specified study-criteria from the study.
    - Reference to the study-criteria should still exist in the the audit trail.

    State after:
    - Study criteria deleted from the study, but still exist as a node in the database with a reference from the audit trail.
    - Added new entry in the audit trail for the deletion of the study-criteria .
    
    Possible errors:
    - Invalid study-uid or studyCriteriaUid.

    Returned data:
    - none
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the criteria and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_criteria(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCriteriaSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studycriteriauid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-criteria/{studycriteriauid}/order",
    summary="Change the order of a study criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and criteria to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_criteria_selection_order(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    new_order_input: models.StudySelectionCriteriaNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studycriteriauid,
        new_order=new_order_input.new_order,
    )


@router.patch(
    "/{uid}/study-criteria/{studycriteriauid}/key-criteria",
    summary="Change the key-criteria property of a study criteria",
    response_model=models.StudySelectionCriteria,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and criteria to change.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_criteria_selection_key_criteria_property(
    uid: str = studyUID,
    studycriteriauid: str = studySelectionUid,
    key_criteria_input: models.StudySelectionCriteriaKeyCriteria = Body(
        None,
        description="New value to set for the key-criteria property of the selection",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCriteria:
    service = StudyCriteriaSelectionService(author=current_user_id)
    return service.set_key_criteria(
        study_uid=uid,
        study_selection_uid=studycriteriauid,
        key_criteria=key_criteria_input.key_criteria,
    )


#
# API endpoints to study activity
#


@router.get(
    "/study-activities",
    summary="Returns all study activities currently selected",
    response_model=CustomPage[models.StudySelectionActivity],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_activities_for_all_studies(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    activityNames: Optional[List[str]] = Query(
        None, description="A list of activity names to use as a specific filter"
    ),
    activitySubGroupNames: Optional[List[str]] = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
    ),
    activityGroupNames: Optional[List[str]] = Query(
        None, description="A list of activity group names to use as a specific filter"
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionEndpoint]:
    service = StudyActivitySelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        project_name=projectName,
        project_number=projectNumber,
        activity_names=activityNames,
        activity_sub_group_names=activitySubGroupNames,
        activity_group_names=activityGroupNames,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-activities",
    summary="Returns all study activities currently selected",
    response_model=CustomPage[models.StudySelectionActivity],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "flowchartGroup=flowchartGroup.sponsorPreferredName",
            "activityGroup",
            "activitySubGroup",
            "name=activity.name",
            "note",
            "startDate",
            "userInitials",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_activities(
    request: Request,  # request is actually required by the allow_exports decorator
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[models.StudySelectionActivity]:
    service = StudyActivitySelectionService(author=current_user_id)
    all_items = service.get_all_selection(
        study_uid=uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-activities/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_activity_values_for_header(
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyActivitySelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-activities/{studyactivityuid}",
    summary="Returns specific study activity",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_activity(
    uid: str = studyUID,
    studyactivityuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studyactivityuid
    )


@router.get(
    "/{uid}/study-activities/audit-trail",
    summary="List full audit trail related to definition of all study activities.",
    description="""
The following values should be returned for all study activities:
- dateTime
- userInitials
- action
- activity
- order
    """,
    response_model=Sequence[models.StudySelectionActivityCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_activity_audit_trail(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionActivityCore]:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-activities/{studyactivityuid}/audit-trail",
    summary="List audit trail related to definition of a specific study activity.",
    response_model=Sequence[models.StudySelectionActivityCore],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_activity_audit_trail(
    uid: str = studyUID,
    studyactivityuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivityCore:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studyactivityuid
    )


@router.post(
    "/{uid}/study-activities/create",
    summary="Creating a study activity selection based on the input data",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the activity",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or activity is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_activity_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionActivityCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.patch(
    "/{uid}/study-activities/{studyactivityuid}",
    summary="Edit a study activity",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:
 

State after:
 - Added new entry in the audit trail for the update of the study-activity.""",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and activity.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_activity_selection(
    uid: str = studyUID,
    studyactivityuid: str = studySelectionUid,
    selection: models.StudySelectionActivityInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studyactivityuid,
        selection_update_input=selection,
    )


@router.delete(
    "/{uid}/study-activities/{studyactivityuid}",
    summary="Delete a study activity",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_activity(
    uid: str = studyUID,
    studyactivityuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyActivitySelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studyactivityuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{uid}/study-activities/batch",
    summary="Batch create and/or edit of study activities",
    response_model=Sequence[models.StudySelectionActivityBatchOutput],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def activity_selection_batch_operations(
    uid: str = studyUID,
    operations: Sequence[models.StudySelectionActivityBatchInput] = Body(
        None, description=""
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionActivityBatchOutput]:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.handle_batch_operations(uid, operations)


@router.patch(
    "/{uid}/study-activities/{studyactivityuid}/order",
    summary="Change the order of a study activity",
    response_model=models.StudySelectionActivity,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and activity to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_activity_selection_order(
    uid: str = studyUID,
    studyactivityuid: str = studySelectionUid,
    new_order_input: models.StudySelectionActivityNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivity:
    service = StudyActivitySelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studyactivityuid,
        new_order=new_order_input.new_order,
    )


"""
Study Selection Arm endpoints 
 """


@router.get(
    "/{uid}/study-arms",
    summary="""List all study arms currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study arms for the study uid in status draft. If the study not exist in status draft then return the study arms for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study arm for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study arms for the specific locked study version is returned.
    - Indicate by a boolean variable if the study arm can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study arms, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=CustomPage[models.StudySelectionArmWithConnectedBranchArms],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "type=armType.sponsorPreferredName",
            "name",
            "code",
            "randomizationGroup",
            "numberOfSubjects",
            "description",
            "startDate",
            "userInitials",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_all_selected_arms(
    request: Request,  # request is actually required by the allow_exports decorator
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[models.StudySelectionArmWithConnectedBranchArms]:
    service = StudyArmSelectionService(author=current_user_id)
    all_items = service.get_all_selection(
        study_uid=uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-arms/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_arm_values_for_header(
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyArmSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/study-arms",
    summary="Returns all study arms currently selected",
    response_model=CustomPage[models.StudySelectionArmWithConnectedBranchArms],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_arms_for_all_studies(
    projectName: Optional[str] = Query(
        None,
        description="Optionally, the name of the project for which to return study selections.",
    ),
    projectNumber: Optional[str] = Query(
        None,
        description="Optionally, the number of the project for which to return study selections.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionArmWithConnectedBranchArms]:
    service = StudyArmSelectionService(author=current_user_id)
    all_selections = service.get_all_selections_for_all_studies(
        project_name=projectName,
        project_number=projectNumber,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.post(
    "/{uid}/study-arms/create",
    summary="Creating a study arm selection based on the input data",
    response_model=models.StudySelectionArm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the arm",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or arm is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_arm_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionArmCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionArm:
    service = StudyArmSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.patch(
    "/{uid}/study-arms/{studyarmuid}",
    summary="Edit a study arm",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:


State after:
 - Added new entry in the audit trail for the update of the study-arm.""",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and arm.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_arm_selection(
    uid: str = studyUID,
    studyarmuid: str = studySelectionUid,
    selection: models.StudySelectionArmInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid, study_selection_uid=studyarmuid, selection_update_input=selection
    )


@router.get(
    "/{uid}/study-arms/{studyarmuid}/audit-trail",
    summary="List audit trail related to definition of a specific study arm.",
    response_model=Sequence[models.StudySelectionArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_arm_audit_trail(
    uid: str = studyUID,
    studyarmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionArmVersion]:
    service = StudyArmSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studyarmuid
    )


@router.get(
    "/{uid}/study-arms/audit-trail",
    summary="List audit trail related to definition of all study arms.",
    response_model=Sequence[models.StudySelectionArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_arm_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionArmVersion]:
    service = StudyArmSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-arms/{studyarmuid}",
    summary="Returns specific study arm",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the arm for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_arm(
    uid: str = studyUID,
    studyarmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studyarmuid
    )


@router.patch(
    "/{uid}/study-arms/{studyarmuid}/order",
    summary="Change the order of a study arm",
    response_model=models.StudySelectionArmWithConnectedBranchArms,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and arm to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_arm_selection_order(
    uid: str = studyUID,
    studyarmuid: str = studySelectionUid,
    new_order_input: models.StudySelectionArmNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionArmWithConnectedBranchArms:
    service = StudyArmSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studyarmuid,
        new_order=new_order_input.new_order,
    )


@router.delete(
    "/{uid}/study-arms/{studyarmuid}",
    summary="Delete a study arm",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the arm and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_arm(
    uid: str = studyUID,
    studyarmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyArmSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studyarmuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#
# API endpoints to study elements
#


@router.post(
    "/{uid}/study-elements/create",
    summary="Creating a study element selection based on the input data",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the element",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or element is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_element_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionElementCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/{uid}/study-elements",
    summary="""List all study elements currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.

    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=CustomPage[models.StudySelectionElement],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_elements(
    uid: str = studyUID,
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[models.StudySelectionElement]:
    service = StudyElementSelectionService(author=current_user_id)
    all_items = service.get_all_selection(
        study_uid=uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-elements/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_element_values_for_header(
    fieldName: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    searchString: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    resultCount: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyElementSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-elements/{studyelementuid}",
    summary="Returns specific study element",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the element for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_element(
    uid: str = studyUID,
    studyelementuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studyelementuid
    )


@router.patch(
    "/{uid}/study-elements/{studyelementuid}",
    summary="Edit a study element",
    description="""
        State before:
        - Study must exist and be in status draft

        Business logic:

        State after:
        - Added new entry in the audit trail for the update of the study-element.""",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and element.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_element_selection(
    uid: str = studyUID,
    studyelementuid: str = studySelectionUid,
    selection: models.StudySelectionElementInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studyelementuid,
        selection_update_input=selection,
    )


@router.get(
    "/{uid}/study-elements/{studyelementuid}/audit-trail",
    summary="List audit trail related to definition of a specific study element.",
    response_model=Sequence[models.StudySelectionElementVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_element_audit_trail(
    uid: str = studyUID,
    studyelementuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionElementVersion]:
    service = StudyElementSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studyelementuid
    )


@router.get(
    "/{uid}/study-element/audit-trail",
    summary="List audit trail related to definition of all study element.",
    response_model=Sequence[models.StudySelectionElementVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_element_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionElementVersion]:
    service = StudyElementSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/{uid}/study-elements/{studyelementuid}",
    summary="Delete a study element",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the element and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_element(
    uid: str = studyUID,
    studyelementuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyElementSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studyelementuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/study-elements/allowed-element-configs",
    summary="Returns all allowed config sets for element type and subtype",
    response_model=Sequence[models.StudyElementTypes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_configs(
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudyElementTypes]:
    service = StudyElementSelectionService(current_user_id)
    return service.get_allowed_configs()


@router.patch(
    "/{uid}/study-elements/{studyelementuid}/order",
    summary="Change the order of a study element",
    response_model=models.StudySelectionElement,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and element to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_element_selection_order(
    uid: str = studyUID,
    studyelementuid: str = studySelectionUid,
    new_order_input: models.StudySelectionElementNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionElement:
    service = StudyElementSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studyelementuid,
        new_order=new_order_input.new_order,
    )


"""
API Study-Branch-Arms endpoints 
"""


@router.post(
    "/{uid}/study-branch-arms/create",
    summary="Creating a study branch arm selection based on the input data",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the branch arm",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or branch arm is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_branch_arm_selection_create(
    uid: str = studyUID,
    selection: models.study_selection.StudySelectionBranchArmCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/{uid}/study-branch-arms",
    summary="""List all study branch arms currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study branch arms for the study uid in status draft. If the study not exist in status draft then return the study branch arms for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study branch arm for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study branch arms for the specific locked study version is returned.
    - Indicate by a boolean variable if the study branch arm can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study branch arms, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=Sequence[models.StudySelectionBranchArm],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_branch_arms(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionBranchArm]:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.get_all_selection(study_uid=uid)


@router.get(
    "/{uid}/study-branch-arms/{studybrancharmuid}",
    summary="Returns specific study branch arm",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the branch arm for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_branch_arm(
    uid: str = studyUID,
    studybrancharmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studybrancharmuid
    )


@router.patch(
    "/{uid}/study-branch-arms/{studybrancharmuid}",
    summary="Edit a study branch arm",
    description="""
            State before:
            - Study must exist and be in status draft
            Business logic:

            State after:
            - Added new entry in the audit trail for the update of the study-branch-arm.""",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and branch arm.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_branch_arm_selection(
    uid: str = studyUID,
    studybrancharmuid: str = studySelectionUid,
    selection: models.StudySelectionBranchArmEditInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService(author=current_user_id)
    selection.branchArmUid = studybrancharmuid
    return service.patch_selection(
        study_uid=uid,
        # study_selection_uid=studybrancharmuid,
        selection_update_input=selection,
    )


@router.get(
    "/{uid}/study-branch-arms/{studybrancharmuid}/audit-trail",
    summary="List audit trail related to definition of a specific study branch-arm.",
    response_model=Sequence[models.StudySelectionBranchArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_branch_arm_audit_trail(
    uid: str = studyUID,
    studybrancharmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionBranchArmVersion]:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studybrancharmuid
    )


@router.get(
    "/{uid}/study-branch-arm/audit-trail",
    summary="List audit trail related to definition of all study branch-arm.",
    response_model=Sequence[models.StudySelectionBranchArmVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_branch_arm_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionBranchArmVersion]:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/{uid}/study-branch-arms/{studybrancharmuid}",
    summary="Delete a study branch arm",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the branch arm and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_branch_arm(
    uid: str = studyUID,
    studybrancharmuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyBranchArmSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studybrancharmuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-branch-arms/{studybrancharmuid}/order",
    summary="Change the order of a study branch arm",
    response_model=models.StudySelectionBranchArm,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and branch arm to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_branch_arm_selection_order(
    uid: str = studyUID,
    studybrancharmuid: str = studySelectionUid,
    new_order_input: models.StudySelectionBranchArmNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionBranchArm:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studybrancharmuid,
        new_order=new_order_input.new_order,
    )


@router.get(
    "/{uid}/study-branch-arms/arm/{armUid}",
    summary="""List all study branch arms currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study branch arms for the study uid in status draft. If the study not exist in status draft then return the study branch arms for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study branch arm for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study branch arms for the specific locked study version is returned.
    - Indicate by a boolean variable if the study branch arm can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study branch arms, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=Sequence[models.StudySelectionBranchArm],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_branch_arms_within_arm(
    uid: str, armUid: str, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudySelectionBranchArm]:
    service = StudyBranchArmSelectionService(author=current_user_id)
    return service.get_all_selection_within_arm(study_uid=uid, study_arm_uid=armUid)


"""
API Study-Cohorts endpoints 
"""


@router.post(
    "/{uid}/study-cohorts/create",
    summary="Creating a study cohort selection based on the input data",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the cohort",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or cohort is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_cohort_selection_create(
    uid: str = studyUID,
    selection: models.StudySelectionCohortCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.get(
    "/{uid}/study-cohorts",
    summary="""List all study cohorts currently selected for study with provided uid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study cohorts for the study uid in status draft. If the study not exist in status draft then return the study cohorts for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study cohort for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study cohorts for the specific locked study version is returned.
    - Indicate by a boolean variable if the study cohort can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study cohorts, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=CustomPage[models.StudySelectionCohort],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_cohorts(
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
    armUid: Optional[str] = Query(
        False,
        description="The unique id of the study arm for which specified study cohorts should be returned",
    ),
    uid: str = studyUID,
) -> CustomPage[models.StudySelectionCohort]:
    service = StudyCohortSelectionService(author=current_user_id)

    all_selections = service.get_all_selection(
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
        study_uid=uid,
        arm_uid=armUid,
    )
    return CustomPage.create(
        items=all_selections.items,
        total=all_selections.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-cohorts/{studycohortuid}",
    summary="Returns specific study cohort",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exists no selection of the cohort for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_cohort(
    uid: str = studyUID,
    studycohortuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.get_specific_selection(
        study_uid=uid, study_selection_uid=studycohortuid
    )


@router.patch(
    "/{uid}/study-cohorts/{studycohortuid}",
    summary="Edit a study cohort",
    description="""
            State before:
            - Study must exist and be in status draft
            Business logic:

            State after:
            - Added new entry in the audit trail for the update of the study-cohort.""",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and cohort.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_cohort_selection(
    uid: str = studyUID,
    studycohortuid: str = studySelectionUid,
    selection: models.StudySelectionCohortEditInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studycohortuid,
        selection_update_input=selection,
    )


@router.get(
    "/{uid}/study-cohorts/{studycohortuid}/audit-trail",
    summary="List audit trail related to definition of a specific study study-cohorts.",
    response_model=Sequence[models.StudySelectionCohortVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_selected_cohort_audit_trail(
    uid: str = studyUID,
    studycohortuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionCohortVersion]:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, study_selection_uid=studycohortuid
    )


@router.get(
    "/{uid}/study-cohort/audit-trail",
    summary="List audit trail related to definition of all study study-cohort.",
    response_model=Sequence[models.StudySelectionCohortVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_cohort_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudySelectionCohortVersion]:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.delete(
    "/{uid}/study-cohorts/{studycohortuid}",
    summary="Delete a study cohort",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the cohort and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_selected_cohort(
    uid: str = studyUID,
    studycohortuid: str = studySelectionUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCohortSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studycohortuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-cohorts/{studycohortuid}/order",
    summary="Change the order of a study cohort",
    response_model=models.StudySelectionCohort,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exists no selection between the study and cohort to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_new_cohort_selection_order(
    uid: str = studyUID,
    studycohortuid: str = studySelectionUid,
    new_order_input: models.StudySelectionCohortNewOrder = Body(
        None, description="New value to set for the order property of the selection"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionCohort:
    service = StudyCohortSelectionService(author=current_user_id)
    return service.set_new_order(
        study_uid=uid,
        study_selection_uid=studycohortuid,
        new_order=new_order_input.new_order,
    )
