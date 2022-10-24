"""study duration weeks router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic.types import Json

from clinical_mdr_api.models.concept import NumericValue, NumericValueInput
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksService,
)

router = APIRouter()

StudyDurationWeeksUID = Path(
    None, description="The unique id of the study duration week"
)


@router.get(
    "",
    summary="List all study duration weeks (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all study duration weeks.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[NumericValue],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_study_duration_weeks(
    library: Optional[str] = Query(None, description="The library name"),
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
):
    study_duration_weeks_service = StudyDurationWeeksService(user=current_user_id)
    results = study_duration_weeks_service.get_all_concepts(
        library=library,
        sort_by=sortBy,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total_count, page=pageNumber, size=pageSize
    )


@router.get(
    "/headers",
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    current_user_id: str = Depends(get_current_user_id),
    library: Optional[str] = Query(None, description="The library name"),
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
):
    study_duration_weeks_service = StudyDurationWeeksService(user=current_user_id)
    return study_duration_weeks_service.get_distinct_values_for_header(
        library=library,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific study duration week",
    description="""
State before:
 - a study duration week with uid must exist.

State after:
 - No change

Possible errors:
 - Invalid uid
 """,
    response_model=NumericValue,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_study_duration_week(
    uid: str = StudyDurationWeeksUID,
    current_user_id: str = Depends(get_current_user_id),
):
    study_duration_weeks_service = StudyDurationWeeksService(user=current_user_id)
    return study_duration_weeks_service.get_by_uid(uid=uid)


@router.post(
    "",
    summary="Creates new study duration week or returns already existing study duration week.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'isEditable' property of the library needs to be true).

Business logic:
 - New node is created for the study duration week with the set properties.

Possible errors:
 - Invalid library.
""",
    response_model=NumericValue,
    status_code=201,
    responses={
        201: {
            "description": "Created - The study duration week was successfully created."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    numeric_value_create_input: NumericValueInput = Body(None, description=""),
    current_user_id: str = Depends(get_current_user_id),
):
    study_duration_weeks_service = StudyDurationWeeksService(user=current_user_id)
    return study_duration_weeks_service.create(concept_input=numeric_value_create_input)
