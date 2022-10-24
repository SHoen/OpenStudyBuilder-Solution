"""Numeric findings router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic.types import Json

from clinical_mdr_api.models.activities.numeric_finding import (
    NumericFinding,
    NumericFindingCreateInput,
    NumericFindingEditInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.activities.numeric_finding_service import (
    NumericFindingService,
)

router = APIRouter()

NumericFindingUID = Path(None, description="The unique id of the numeric finding")


@router.get(
    "/numeric-findings",
    summary="List all numeric findings (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all numeric findings in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[NumericFinding],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_activities(
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
    numeric_finding_service = NumericFindingService(user=current_user_id)
    results = numeric_finding_service.get_all_concepts(
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
    "/numeric-findings/headers",
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
    numeric_finding_service = NumericFindingService(user=current_user_id)
    return numeric_finding_service.get_distinct_values_for_header(
        library=library,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/numeric-findings/{uid}",
    summary="Get details on a specific numeric finding (in a specific version)",
    description="""
State before:
 - a numeric finding with uid must exist.

Business logic:
 - If parameter atSpecifiedDateTime is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, atSpecifiedDateTime, status or version.
 """,
    response_model=NumericFinding,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_activity(
    uid: str = NumericFindingUID, current_user_id: str = Depends(get_current_user_id)
):
    numeric_finding_service = NumericFindingService(user=current_user_id)
    return numeric_finding_service.get_by_uid(uid=uid)


@router.get(
    "/numeric-findings/{uid}/versions",
    summary="List version history for numeric finding",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for numeric finding.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[NumericFinding],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The numeric finding with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    uid: str = NumericFindingUID, current_user_id: str = Depends(get_current_user_id)
):
    numeric_finding_service = NumericFindingService(user=current_user_id)
    return numeric_finding_service.get_version_history(uid=uid)


@router.post(
    "/numeric-findings",
    summary="Creates new numeric finding.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'isEditable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the numeric finding with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'changeDescription' property will be set automatically to 'Initial version'.

State after:
 - numeric-findings is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=NumericFinding,
    status_code=201,
    responses={
        201: {"description": "Created - The numeric finding was successfully created."},
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
    numeric_finding_create_input: NumericFindingCreateInput = Body(
        None, description=""
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    numeric_finding_service = NumericFindingService(user=current_user_id)
    return numeric_finding_service.create(concept_input=numeric_finding_create_input)


@router.patch(
    "/numeric-findings/{uid}",
    summary="Update numeric finding",
    description="""
State before:
 - uid must exist and numeric finding must exist in status draft.
 - The numeric finding must belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).

Business logic:
 - If numeric finding exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked numeric finding is updated, the relationships are updated to point to the numeric finding value node.

State after:
 - attributes are updated for the numeric finding.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=NumericFinding,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The numeric finding is not in draft status.\n"
            "- The numeric finding had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The numeric finding with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = NumericFindingUID,
    numeric_finding_edit_input: NumericFindingEditInput = Body(None, description=""),
    current_user_id: str = Depends(get_current_user_id),
):
    numeric_finding_service = NumericFindingService(user=current_user_id)
    return numeric_finding_service.edit_draft(
        uid=uid, concept_edit_input=numeric_finding_edit_input
    )
