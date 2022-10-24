"""ActivityGroup router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.activities.activity_group import (
    ActivityGroup,
    ActivityGroupCreateInput,
    ActivityGroupEditInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)

router = APIRouter()

ActivityGroupUID = Path(None, description="The unique id of the ActivityGroup")


@router.get(
    "/activity-groups",
    summary="List all activity groups (for a given library)",
    description="""
State before:
 - The library must exist (if specified)

Business logic:
 - List all activities groups in their latest version, including properties derived from linked control terminology.

State after:
 - No change

Possible errors:
 - Invalid library name specified.""",
    response_model=CustomPage[ActivityGroup],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "startDate", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_activity_groups(
    request: Request,  # request is actually required by the allow_exports decorator
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
    activity_group_service = ActivityGroupService(user=current_user_id)
    results = activity_group_service.get_all_concepts(
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
    "/activity-groups/headers",
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
    activitySubGroupNames: Optional[List[str]] = Query(
        None,
        description="A list of activity sub group names to use as a specific filter",
        alias="activitySubGroupNames[]",
    ),
    activityNames: Optional[List[str]] = Query(
        None,
        description="A list of activity names to use as a specific filter",
        alias="activityNames[]",
    ),
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
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.get_distinct_values_for_header(
        library=library,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
        activityNames=activityNames,
        activitySubGroupNames=activitySubGroupNames,
    )


@router.get(
    "/activity-groups/{uid}",
    summary="Get details on a specific activity group (in a specific version)",
    description="""
State before:
 - an activity sub group with uid must exist.

Business logic:
 - If parameter atSpecifiedDateTime is specified then the latest/newest representation of the concept at this point in time is returned. The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. If the timezone is ommitted, UTC�0 is assumed.
 - If parameter status is specified then the representation of the concept in that status is returned (if existent). This is useful if the concept has a status 'Draft' and a status 'Final'.
 - If parameter version is specified then the latest/newest representation of the concept in that version is returned. Only exact matches are considered. The version is specified in the following format: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...

State after:
 - No change

Possible errors:
 - Invalid uid, atSpecifiedDateTime, status or version.
 """,
    response_model=ActivityGroup,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_activity(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.get_by_uid(uid=uid)


@router.get(
    "/activity-groups/{uid}/versions",
    summary="List version history for activity groups",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for activity groups.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[ActivityGroup],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.get_version_history(uid=uid)


@router.post(
    "/activity-groups",
    summary="Creates new activity group.",
    description="""
State before:
 - The specified library allows creation of concepts (the 'isEditable' property of the library needs to be true).
 - The specified CT term uids must exist, and the term names are in a final state.

Business logic:
 - New node is created for the activity group with the set properties.
 - relationships to specified control terminology are created (as in the model).
 - relationships to specified activity parent are created (as in the model)
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to 0.1.
 - The 'changeDescription' property will be set automatically to 'Initial version'.

State after:
 - ActivityGroup is created in status Draft and assigned an initial minor version number as 0.1.
 - Audit trail entry must be made with action of creating new Draft version.

Possible errors:
 - Invalid library or control terminology uid's specified.
""",
    response_model=ActivityGroup,
    status_code=201,
    responses={
        201: {"description": "Created - The activity group was successfully created."},
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
    activity_create_input: ActivityGroupCreateInput = Body(None, description=""),
    current_user_id: str = Depends(get_current_user_id),
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.create(concept_input=activity_create_input)


@router.patch(
    "/activity-groups/{uid}",
    summary="Update activity group",
    description="""
State before:
 - uid must exist and activity group must exist in status draft.
 - The activity group must belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).

Business logic:
 - If activity group exist in status draft then attributes are updated.
 - If links to CT are selected or updated then relationships are made to CTTermRoots.
- If the linked activity group is updated, the relationships are updated to point to the activity group value node.

State after:
 - attributes are updated for the activity group.
 - Audit trail entry must be made with update of attributes.

Possible errors:
 - Invalid uid.

""",
    response_model=ActivityGroup,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in draft status.\n"
            "- The activity group had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = ActivityGroupUID,
    activity_edit_input: ActivityGroupEditInput = Body(None, description=""),
    current_user_id: str = Depends(get_current_user_id),
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.edit_draft(
        uid=uid, concept_edit_input=activity_edit_input
    )


@router.post(
    "/activity-groups/{uid}/new-version",
    summary=" Create a new version of activity group",
    description="""
State before:
 - uid must exist and the activity group must be in status Final.

Business logic:
- The activity group is changed to a draft state.

State after:
 - ActivityGroup changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=ActivityGroup,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create activity sub groups.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The activity group is not in final status.\n"
            "- The activity group with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.create_new_version(uid=uid)


@router.post(
    "/activity-groups/{uid}/approve",
    summary="Approve draft version of activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Draft.

Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'changeDescription' property will be set automatically 'Approved version'.

State after:
 - Activity group changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.

Possible errors:
 - Invalid uid or status not Draft.
    """,
    response_model=ActivityGroup,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in draft status.\n"
            "- The library does not allow to approve activity group.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.approve(uid=uid)


@router.post(
    "/activity-groups/{uid}/inactivate",
    summary=" Inactivate final version of activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Final.

Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status will be automatically set to 'Retired'.
 - The 'changeDescription' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity group changed status to Retired.
 - Audit trail entry must be made with action of inactivating to retired version.

Possible errors:
 - Invalid uid or status not Final.
    """,
    response_model=ActivityGroup,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.inactivate_final(uid=uid)


@router.post(
    "/activity-groups/{uid}/reactivate",
    summary="Reactivate retired version of a activity group",
    description="""
State before:
 - uid must exist and activity group must be in status Retired.

Business logic:
 - The latest 'Retired' version will remain the same as before.
 - The status will be automatically set to 'Final'.
 - The 'changeDescription' property will be set automatically.
 - The 'version' property will remain the same as before.

State after:
 - Activity group changed status to Final.
 - An audit trail entry must be made with action of reactivating to final version.

Possible errors:
 - Invalid uid or status not Retired.
    """,
    response_model=ActivityGroup,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The activity group with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    return activity_group_service.reactivate_retired(uid=uid)


@router.delete(
    "/activity-groups/{uid}",
    summary="Delete draft version of activity group",
    description="""
State before:
 - uid must exist
 - The concept must be in status Draft in a version less then 1.0 (never been approved).
 - The concept must belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).

Business logic:
 - The draft concept is deleted.

State after:
 - Activity group is successfully deleted.

Possible errors:
 - Invalid uid or status not Draft or exist in version 1.0 or above (previously been approved) or not in an editable library.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The activity group was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The activity group is not in draft status.\n"
            "- The activity group was already in final state or is in use.\n"
            "- The library does not allow to delete activity sub group.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An activity group with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_activity_group(
    uid: str = ActivityGroupUID, current_user_id: str = Depends(get_current_user_id)
):
    activity_group_service = ActivityGroupService(user=current_user_id)
    activity_group_service.soft_delete(uid=uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
