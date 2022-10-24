from datetime import datetime
from typing import Any, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.template_parameter import ComplexTemplateParameter
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.timeframes import TimeframeService

router = APIRouter()

Service = TimeframeService

# Argument definitions
TimeframeUID = Path(None, description="The unique id of the timeframe.")


@router.get(
    "",
    summary="Returns all timeframes in their latest/newest version.",
    response_model=CustomPage[models.Timeframe],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","timeframeTemplate","uid","timeframe","startDate","endDate","status","version","changeDescription","userInitials"
"Sponsor","First  [ComparatorIntervention]","826d80a7-0b6a-419d-8ef1-80aa241d7ac7",First Intervention,"2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "timeframeTemplate=timeframeTemplate.name",
            "uid",
            "timeframe=name",
            "startDate",
            "endDate",
            "status",
            "version",
            "changeDescription",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Optional[str] = Query(
        None,
        description="If specified, only those timeframes will be returned that are currently in the specified status. "
        "This may be particularly useful if the timeframe has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
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
):
    data = Service(current_user_id).get_all(
        status=status,
        return_study_count=True,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=data.items, total=data.total_count, page=pageNumber, size=pageSize
    )


@router.get(
    "/headers",
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
    current_user_id: str = Depends(get_current_user_id),
    status: Optional[str] = Query(
        None,
        description="If specified, only those objective templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the objective template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
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
):
    return Service(current_user_id).get_distinct_values_for_header(
        status=status,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Returns the latest/newest version of a specific timeframe identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=Optional[models.Timeframe],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get(
    uid: str = TimeframeUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified, the latest/newest representation of the timeframe at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is ommitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the timeframe in that status is returned (if existent). "
        "This may be particularly useful if the timeframe has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the timeframe in that version is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).get_by_uid(
        uid=uid
    )  # TODO:, at_specific_date=atSpecifiedDateTime, status=status, version=version)


@router.get(
    "/get-by-name/{name}",
    summary="Returns the latest/newest version of a specific timeframe identified by 'name'.",
    description="Gets an object by name - uses LATEST_DRAFT and LATEST_FINAL relations",
    response_model=Optional[models.Timeframe],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'name' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_by_name(name: str, current_user_id: str = Depends(get_current_user_id)):
    return Service(current_user_id).find_by(name=unquote(name))  # type: ignore


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific timeframe identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=List[models.TimeframeVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    uid: str = TimeframeUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).get_version_history(uid)


@router.post(
    "",
    summary="Creates a new timeframe in 'Draft' status.",
    description="""This request is only valid if
* the specified timeframe template is in 'Final' status and
* the specified library allows creating timeframes (the 'isEditable' property of the library needs to be true) and
* the timeframe does not yet exist (no timeframe with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be set to '0.1'.
""",
    response_model=models.Timeframe,
    status_code=201,
    responses={
        201: {"description": "Created - The timeframe was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to create timeframes.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'libraryName' could not be found.\n"
            "- The timeframe template with the specified 'timeframeTemplateUid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    timeframe: models.TimeframeCreateInput = Body(
        None, description="Related parameters of the timeframe that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).create(timeframe)


@router.post(
    "/preview",
    summary="Previews the creation of a new timeframe.",
    description="""This request is only valid if
* the specified timeframe template is in 'Final' status and
* the specified library allows creating timeframe (the 'isEditable' property of the library needs to be true) and
* the timeframe does not yet exist (no timeframe with the same content in 'Final' or 'Draft' status).

If the request succeeds:
* No timeframe will be created, but the result of the request will show what the timeframe will look like.
""",
    response_model=models.Timeframe,
    status_code=200,
    responses={
        200: {"description": "Success - The timeframe is able to be created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to create timeframes.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The library with the specified 'libraryName' could not be found.\n"
            "- The timeframe template with the specified 'timeframeTemplateUid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def preview(
    timeframe: models.TimeframeCreateInput = Body(
        None, description="Related parameters of the timeframe that shall be previewed."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).create(timeframe, preview=True)


@router.patch(
    "/{uid}",
    summary="Updates the timeframe identified by 'uid'.",
    description="""This request is only valid if the timeframe
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.Timeframe,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The timeframe had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The timeframe does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = TimeframeUID,
    timeframe: models.TimeframeEditInput = Body(
        None,
        description="The new parameter values for the timeframe including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).edit_draft(uid, timeframe)


@router.post(
    "/{uid}/approve",
    summary="Approves the timeframe identified by 'uid'.",
    description="""This request is only valid if the timeframe
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.Timeframe,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The library does not allow to approve timeframe.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = TimeframeUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).approve(uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the timeframe identified by 'uid'.",
    description="""This request is only valid if the timeframe
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.Timeframe,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = TimeframeUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).inactivate_final(uid)


# TODO check if * there is no other timeframe with the same name (it may be that one had been created after inactivating this one here)
@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the timeframe identified by 'uid'.",
    description="""This request is only valid if the timeframe
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.Timeframe,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = TimeframeUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).reactivate_retired(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the timeframe identified by 'uid'.",
    description="""This request is only valid if \n
* the timeframe is in 'Draft' status and
* the timeframe has never been in 'Final' status and
* the timeframe belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The timeframe was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe is not in draft status.\n"
            "- The timeframe was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An timeframe with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete(
    uid: str = TimeframeUID, current_user_id: str = Depends(get_current_user_id)
):
    Service(current_user_id).soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/parameters",
    summary="Returns all template parameters available for the timeframe identified by 'uid'. Includes the available values per parameter.",
    description="Returns all template parameters used in the timeframe template "
    "that is the basis for the timeframe identified by 'uid'. "
    "Includes the available values per parameter.",
    response_model=List[ComplexTemplateParameter],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_parameters(
    uid: str = Path(None, description="The unique id of the timeframe."),
    study_uid: Optional[str] = Query(
        None,
        description="if specified only valid parameters for a given study will be returned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).get_parameters(uid, study_uid=study_uid)
