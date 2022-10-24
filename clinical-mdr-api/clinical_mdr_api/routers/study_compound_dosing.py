from typing import Any, Optional, Sequence

from fastapi import Body, Depends, Query, Request, Response, status
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers import utils
from clinical_mdr_api.services.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)


@router.get(
    "/{uid}/study-compound-dosings",
    summary="List all study compound dosings currently defined for the study",
    response_model=GenericFilteringReturn[models.StudyCompoundDosing],
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
            "uid=studyCompoundDosingUid",
            "order",
            "element=studyElement.name",
            "compound=studyCompound.compound.name",
            "compoundAlias=studyCompound.compoundAlias.name",
            "doseValueValue=doseValue.value",
            "doseValueUnit=doseValue.unitLabel",
            "doseFrequency=doseFrequency.name",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
def get_all_selected_compound_dosings(
    _request: Request,  # request is actually required by the allow_exports decorator
    uid: str = utils.studyUID,
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
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_all_compound_dosings(
        study_uid=uid,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
    )


@router.get(
    "/{uid}/study-compound-dosings/headers",
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
def get_distinct_values_for_header(
    uid: str = utils.studyUID,
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
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/study-compound-dosings/headers",
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
def get_distinct_compound_dosings_values_for_header(
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
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-compound-dosings/{studycompounddosinguid}/audit-trail",
    summary="List audit trail related to definition of a specific study compound dosing.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-dosing-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compound dosing must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study compound dosing for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study compound dosing.
    """,
    response_model=Sequence[models.StudyCompoundDosing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_compound_dosing_audit_trail(
    uid: str = utils.studyUID,
    studycompounddosinguid: str = utils.studyCompoundDosingUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_compound_dosing_audit_trail(
        study_uid=uid, compound_dosing_uid=studycompounddosinguid
    )


@router.post(
    "/{uid}/study-compound-dosings/select",
    summary="Add a study compound dosing to a study",
    response_model=models.StudyCompoundDosing,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - A study compound dosing already exists for selected study compound and element",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study compound or study element is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_study_compound_dosing(
    uid: str = utils.studyUID,
    selection: models.StudyCompoundDosingInput = Body(
        None,
        description="Related parameters of the compound dosing that shall be created.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.delete(
    "/{uid}/study-compound-dosings/{studycompounddosinguid}",
    summary="Delete a study compound dosing",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_compound_dosing(
    uid: str = utils.studyUID,
    studycompounddosinguid: str = utils.studyCompoundDosingUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    service.delete_selection(study_uid=uid, study_selection_uid=studycompounddosinguid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-compound-dosings/{studycompounddosinguid}",
    summary="Edit or replace a study compound dosing",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:
 - Update specified study-compound-dosing with selection of existing study compound and study element items.
 - A single relationships can be defined for a study compound dosing to each of the following code list terms:
   - Dose frequency
 - Order number for the study compound cannot be changed by this API endpoint.

State after:
 - related parameters are updated for the study compound dosing.
 - Added new entry in the audit trail for the update of the study-compound-dosing.""",
    response_model=models.StudyCompoundDosing,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection with the given uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def update_compound_dosing(
    uid: str = utils.studyUID,
    studycompounddosinguid: str = utils.studyCompoundDosingUid,
    selection: models.StudyCompoundDosingInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=studycompounddosinguid,
        selection_update_input=selection,
    )
