"""CTCodelistAttributes router."""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi_etag import Etag
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.ct_codelist_attributes import CTCodelistAttributesService

router = APIRouter()

CTCodelistUID = Path(None, description="The unique id of the CTCodelistAttributes")


def get_etag(request: Request) -> str:
    ct_codelist_attribute_service = CTCodelistAttributesService()
    return ct_codelist_attribute_service.get_codelist_etag(request)


@router.get(
    "/codelists/attributes",
    summary="Returns all codelists attributes.",
    response_model=CustomPage[models.CTCodelistAttributes],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_codelists(
    cataloguename: str = Query(
        None,
        description="If specified, only codelists from given catalogue are returned.",
    ),
    library: Optional[str] = Query(
        None,
        description="If specified, only codelists from given library are returned.",
    ),
    package: Optional[str] = Query(
        None,
        description="If specified, only codelists from given package are returned.",
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
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    results = ct_codelist_attribute_service.get_all_ct_codelists(
        catalogue_name=cataloguename,
        library=library,
        package=package,
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
    "/codelists/attributes/headers",
    summary="Returns possibles values from the database for a given header",
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
    cataloguename: str = Query(
        None,
        description="If specified, only codelists from given catalogue are returned.",
    ),
    library: Optional[str] = Query(
        None, description="If specified, only terms from given library are returned."
    ),
    package: Optional[str] = Query(
        None, description="If specified, only terms from given package are returned."
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
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.get_distinct_values_for_header(
        catalogue_name=cataloguename,
        library=library,
        package=package,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/codelists/{codelistuid}/attributes",
    dependencies=[Depends(Etag(get_etag))],
    summary="Returns the latest/newest version of a specific codelist identified by 'uid'",
    response_model=models.CTCodelistAttributes,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_codelist_attributes(
    codelistuid: str = CTCodelistUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified then the latest/newest representation of the sponsor defined name "
        "for CTCodelistAttributesValue at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, "
        "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is omitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified then the representation of the sponsor defined name for "
        "CTCodelistAttributesValue in that status is returned (if existent).\nThis is useful if the"
        " CTCodelistAttributesValue has a status 'Draft' and a status 'Final'.",
    ),
    version: Optional[str] = Query(
        None,
        description="If specified then the latest/newest representation of the sponsor defined name "
        "for CTCodelistAttributesValue in that version is returned.\n"
        "Only exact matches are considered. The version is specified in the following format:"
        "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.get_by_uid(
        codelist_uid=codelistuid,
        at_specific_date=atSpecifiedDateTime,
        status=status,
        version=version,
    )


@router.get(
    "/codelists/{codelistuid}/attributes/versions",
    summary="Returns the version history of a specific CTCodelistAttributes identified by 'codelistuid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=List[models.CTCodelistAttributesVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelistuid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    codelistuid: str = CTCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.get_version_history(codelist_uid=codelistuid)


@router.patch(
    "/codelists/{codelistuid}/attributes",
    summary="Updates the codelist identified by 'codelistuid'.",
    description="""This request is only valid if the codelist
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.CTCodelistAttributes,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The codelist had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelistuid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    codelistuid: str = CTCodelistUID,
    codelist_input: models.CTCodelistAttributesEditInput = Body(
        None,
        description="The new parameter values for the codelist including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.edit_draft(
        codelist_uid=codelistuid, codelist_input=codelist_input
    )


@router.post(
    "/codelists/{codelistuid}/attributes/new-version",
    summary="Creates a new codelist in 'Draft' status.",
    description="""This request is only valid if
* the specified codelist is in 'Final' status and
* the specified library allows creating codelists (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically to 'new-version'.
* The 'version' property will be increased by '0.1'.
""",
    response_model=models.CTCodelistAttributes,
    status_code=201,
    responses={
        201: {"description": "Created - The codelist was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create codelists.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The codelist is not in final status.\n"
            "- The codelist with the specified 'codelistuid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    codelistuid: str = CTCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.create_new_version(codelist_uid=codelistuid)


@router.post(
    "/codelists/{codelistuid}/attributes/approve",
    summary="Approves the codelist identified by 'codelistuid'.",
    description="""This request is only valid if the codelist
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically to 'Approved version'.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.CTCodelistAttributes,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist is not in draft status.\n"
            "- The library does not allow to approve codelist.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The codelist with the specified 'codelistuid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    codelistuid: str = CTCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_attribute_service = CTCodelistAttributesService(user=current_user_id)
    return ct_codelist_attribute_service.approve(codelist_uid=codelistuid)
