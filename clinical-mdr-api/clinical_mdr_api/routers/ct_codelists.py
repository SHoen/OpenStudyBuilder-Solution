"""CTCodelist router."""
from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query
from fastapi_etag import Etag
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.ct_codelist import CTCodelistService

router = APIRouter()
CTCodelistUID = Path(None, description="The unique id of the CTCodelistRoot")


def get_etag(request: Request) -> str:
    ct_codelist_service = CTCodelistService()
    return ct_codelist_service.get_codelist_etag(request)


@router.post(
    "/codelists",
    summary="Creates new codelist.",
    description="""The following nodes are created
* CTCodelistRoot
  * CTCodelistAttributesRoot
  * CTCodelistAttributesValue
  * CTCodelistNameRoot
  * CTCodelistNameValue
""",
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {"description": "Created - The codelist was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue does not exist.\n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    codelist_input: models.CTCodelistCreateInput = Body(
        None,
        description="Properties to create CTCodelistAttributes and CTCodelistName.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_service = CTCodelistService(user=current_user_id)
    return ct_codelist_service.create(codelist_input)


@router.get(
    "/codelists",
    summary="Returns all codelists names and attributes.",
    response_model=CustomPage[models.CTCodelistNameAndAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
@decorators.allow_exports(
    {
        "defaults": [
            "libraryName",
            "conceptId=codelistUid",
            "sponsorPreferredName=name.name",
            "templateParameter=name.templateParameter",
            "cdStatus=name.status",
            "modifiedName=name.startDate",
            "cdName=attributes.name",
            "submissionValue=attributes.submissionValue",
            "nciPreferredName=attributes.nciPreferredName",
            "extensible=attributes.extensible",
            "attributesStatus=attributes.status",
            "modifiedAttributes=attributes.startDate",
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
def get_codelists(
    request: Request,  # request is actually required by the allow_exports decorator
    cataloguename: Optional[str] = Query(
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
    ct_codelist_service = CTCodelistService(user=current_user_id)
    results = ct_codelist_service.get_all_codelists(
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
    "/codelists/{codelistUid}/sub-codelists",
    summary="Returns all sub codelists names and attributes that only have the provided terms.",
    response_model=CustomPage[models.CTCodelistNameAndAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_sub_codelists_that_have_given_terms(
    codelistUid: str = CTCodelistUID,
    termUids: Sequence[str] = Query(
        ...,
        description="A list of term uids",
    ),
    library: Optional[str] = Query(
        None,
        description="If specified, only codelists from given library are returned.",
    ),
    sortBy: Json = Query(None, description=_generic_descriptions.SORT_BY),
    pageNumber: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    pageSize: Optional[int] = Query(0, description=_generic_descriptions.PAGE_SIZE),
    totalCount: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_service = CTCodelistService(user=current_user_id)
    results = ct_codelist_service.get_sub_codelists_that_have_given_terms(
        codelist_uid=codelistUid,
        term_uids=termUids,
        library=library,
        sort_by=sortBy,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
    )
    return CustomPage.create(
        items=results.items, total=results.total_count, page=pageNumber, size=pageSize
    )


@router.get(
    "/codelists/headers",
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
    cataloguename: Optional[str] = Query(
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
    ct_codelist_service = CTCodelistService(user=current_user_id)
    return ct_codelist_service.get_distinct_values_for_header(
        catalogue_name=cataloguename,
        library=library,
        package=package,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.post(
    "/codelists/{codelistuid}/add-term",
    dependencies=[Depends(Etag(get_etag))],
    summary="Adds new CTTerm to CTCodelist.",
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_VALUE relationship were successfully added "
            "if codelist identified by codelist_uid is a TemplateParameter."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist already has passed term.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_term(
    codelistuid: str = CTCodelistUID,
    term_input: models.CTCodelistTermInput = Body(
        None, description="UID of the CTTermRoot node."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_service = CTCodelistService(user=current_user_id)
    return ct_codelist_service.add_term(
        codelistuid=codelistuid, termUid=term_input.termUid, order=term_input.order
    )


@router.post(
    "/codelists/{codelistuid}/remove-term",
    summary="Removes given CTTerm from CTCodelist.",
    dependencies=[Depends(Etag(get_etag))],
    response_model=models.CTCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully deleted and "
            "HAD_TERM relationship was successfully created.\n"
            "The HAS_VALUE relationship was successfully deleted if codelist identified by "
            "codelist_uid is a TemplateParameter"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist is not extensible.\n"
            "- The codelist doesn't have passed term.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def remove_term(
    codelistuid: str = CTCodelistUID,
    term_input: models.CTCodelistTermInput = Body(
        None, description="UID of the CTTermRoot node."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_codelist_service = CTCodelistService(user=current_user_id)
    return ct_codelist_service.remove_term(
        codelistuid=codelistuid, termUid=term_input.termUid
    )
