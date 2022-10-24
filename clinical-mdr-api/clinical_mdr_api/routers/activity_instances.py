"""New Activities router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.activities.activity_instance import ActivityInstance
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)

router = APIRouter()

ActivityInstanceUID = Path(None, description="The unique id of the ActivityInstance")


@router.get(
    "/activity-instances",
    summary="List all activity instances (for a given library)",
    description="""
State before:
 - The library must exist (if specified)
 
Business logic:
 - List all activity instances in their latest version, including properties derived from linked control terminology.
 
State after:
 - No change
 
Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[ActivityInstance],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "libraryName",
            "activity=activities.name",
            "name",
            "definition",
            "topicCode",
            "adamParamCode",
            "sdtmDomain=sdtmDomain.name",
            "startDate",
            "userInitials",
            "status",
            "version",
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
def get_activities(
    request: Request,  # request is actually required by the allow_exports decorator
    library: Optional[str] = Query(None, description=""),
    activityNames: Optional[List[str]] = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activityNames[]",
    ),
    specimenNames: Optional[List[str]] = Query(
        None,
        description="A list of specimen names to use as a specific filter",
        alias="specimenNames[]",
    ),
    sdtmVariableNames: Optional[List[str]] = Query(
        None,
        description="A list of sdtm variable names to use as a specific filter",
        alias="sdtmVariableNames[]",
    ),
    sdtmDomainNames: Optional[List[str]] = Query(
        None,
        description="A list of sdtm domain names to use as a specific filter",
        alias="sdtmDomainNames[]",
    ),
    sdtmCategoryNames: Optional[List[str]] = Query(
        None,
        description="A list of sdtm category names to use as a specific filter",
        alias="sdtmCategoryNames[]",
    ),
    sdtmSubCategoryNames: Optional[List[str]] = Query(
        None,
        description="A list of sdtm sub category names to use as a specific filter",
        alias="sdtmSubCategoryNames[]",
    ),
    sortBy: Json = Query({}, description=_generic_descriptions.SORT_BY),
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
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    results = activity_instance_service.get_all_concepts(
        library=library,
        activityNames=activityNames,
        specimenNames=specimenNames,
        sdtmCategoryNames=sdtmCategoryNames,
        sdtmSubCategoryNames=sdtmSubCategoryNames,
        sdtmDomainNames=sdtmDomainNames,
        sdtmVariableNames=sdtmVariableNames,
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
    "/activity-instances/headers",
    summary="Returns possibles values from the database for a given header",
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
    library: Optional[str] = Query(None, description=""),
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
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    return activity_instance_service.get_distinct_values_for_header(
        library=library,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.post(
    "/activity-instances/{uid}/new-version",
    summary=" Create a new version of an activity instance",
    description="""
State before:
 - uid must exist and the activity instance must be in status Final.
 
Business logic:
- The activity instance is changed to a draft state.

State after:
 - Activity instance changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.
 
Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create activity instances.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity instance is not in final status.\n"
            "- The activity instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    uid: str = ActivityInstanceUID,
    current_user_id: str = Depends(get_current_user_id),
):
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    return activity_instance_service.create_new_version(uid=uid)


@router.post(
    "/activity-instances/{uid}/approve",
    summary="Approve draft version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'changeDescription' property will be set automatically 'Approved version'.
 
State after:
 - Activity instance changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The library does not allow to approve activity instance.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = ActivityInstanceUID,
    current_user_id: str = Depends(get_current_user_id),
):
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    return activity_instance_service.approve(uid=uid)


@router.post(
    "/activity-instances/{uid}/inactivate",
    summary=" Inactivate final version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'changeDescription' property will be set automatically.
 - The 'version' property will remain the same as before.
 
State after:
 - Activity instance changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.
 
Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = ActivityInstanceUID,
    current_user_id: str = Depends(get_current_user_id),
):
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    return activity_instance_service.inactivate_final(uid=uid)


@router.post(
    "/activity-instances/{uid}/reactivate",
    summary="Reactivate retired version of an activity instance",
    description="""
State before:
 - uid must exist and activity instance must be in status Retired.
 
Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'changeDescription' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity instance changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.
 
Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=ActivityInstance,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = ActivityInstanceUID,
    current_user_id: str = Depends(get_current_user_id),
):
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    return activity_instance_service.reactivate_retired(uid=uid)


@router.delete(
    "/activity-instances/{uid}",
    summary="Delete draft version of an activity instance",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).
 
Business logic:
 - The draft concept is deleted.
 
State after:
 - Activity instance is successfully deleted.
 
Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The activity instance was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity instance is not in draft status.\n"
            "- The activity instance was already in final state or is in use.\n"
            "- The library does not allow to delete activity instance.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity instance with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_activity_instance(
    uid: str = ActivityInstanceUID,
    current_user_id: str = Depends(get_current_user_id),
):
    activity_instance_service = ActivityInstanceService(user=current_user_id)
    activity_instance_service.soft_delete(uid=uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
