"""CTTermAttributes router."""
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.ct_term_attributes import CTTermAttributesService

router = APIRouter()

CTTermUID = Path(None, description="The unique id of the CTTermAttributes")


@router.get(
    "/terms/attributes",
    summary="Returns all terms attributes.",
    response_model=CustomPage[models.CTTermAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_terms(
    codelist_uid: Optional[str] = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    codelist_name: Optional[str] = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    library: Optional[str] = Query(
        None, description="If specified, only terms from given library are returned."
    ),
    package: Optional[str] = Query(
        None, description="If specified, only terms from given package are returned."
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
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    results = ct_term_attribute_service.get_all_ct_terms(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
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
    "/terms/attributes/headers",
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
    codelist_uid: Optional[str] = Query(
        None, description="If specified, only terms from given codelist are returned."
    ),
    codelist_name: Optional[str] = Query(
        None, description="If specified, only terms from given codelist are returned."
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
    ct_term_service = CTTermAttributesService(user=current_user_id)
    return ct_term_service.get_distinct_values_for_header(
        codelist_uid=codelist_uid,
        codelist_name=codelist_name,
        library=library,
        package=package,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/terms/{termuid}/attributes",
    summary="Returns the latest/newest version of a specific ct term identified by 'termuid'",
    response_model=models.CTTermAttributes,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_term_attributes(
    termuid: str = CTTermUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified then the latest/newest representation of the "
        "CTTermAttributesValue at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, "
        "e.g.: '2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is omitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified then the representation of the CTTermAttributesValue "
        "in that status is returned (if existent).\nThis is useful if the"
        " CTTermAttributesValue has a status 'Draft' and a status 'Final'.",
    ),
    version: Optional[str] = Query(
        None,
        description="If specified then the latest/newest representation of the "
        "for CTTermAttributesValue in that version is returned.\n"
        "Only exact matches are considered. The version is specified in the following format:"
        "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.get_by_uid(
        term_uid=termuid,
        at_specific_date=atSpecifiedDateTime,
        status=status,
        version=version,
    )


@router.get(
    "/terms/{termuid}/attributes/versions",
    summary="Returns the version history of a specific CTTermAttributes identified by 'termuid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=List[models.CTTermAttributesVersion],
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
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.get_version_history(term_uid=termuid)


@router.patch(
    "/terms/{termuid}/attributes",
    summary="Updates the term identified by 'termuid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.CTTermAttributes,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'termuid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    termuid: str = CTTermUID,
    term_input: models.CTTermAttributesEditInput = Body(
        None,
        description="The new parameter values for the term including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.edit_draft(term_uid=termuid, term_input=term_input)


@router.post(
    "/terms/{termuid}/attributes/new-version",
    summary="Creates a new term in 'Draft' status.",
    description="""This request is only valid if
* the specified term is in 'Final' status and
* the specified library allows creating term (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically to 'new-version'.
* The 'version' property will be increased by '0.1'.
""",
    response_model=models.CTTermAttributes,
    status_code=201,
    responses={
        201: {"description": "Created - The term was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create tterm.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The term is not in final status.\n"
            "- The term with the specified 'codelistuid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.create_new_version(term_uid=termuid)


@router.post(
    "/terms/{termuid}/attributes/approve",
    summary="Approves the term identified by 'termuid'.",
    description="""This request is only valid if the term
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically to 'Approved version'.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.CTTermAttributes,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The library does not allow to approve term.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'termuid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.approve(term_uid=termuid)


@router.post(
    "/terms/{termuid}/attributes/inactivate",
    summary="Inactivates/deactivates the term identified by 'termuid'.",
    description="""This request is only valid if the term
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.CTTermAttributes,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'termuid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.inactivate_final(term_uid=termuid)


@router.post(
    "/terms/{termuid}/attributes/reactivate",
    summary="Reactivates the term identified by 'termuid'.",
    description="""This request is only valid if the term
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.CTTermAttributes,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'termuid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    return ct_term_attribute_service.reactivate_retired(term_uid=termuid)


@router.delete(
    "/terms/{termuid}/attributes",
    summary="Deletes the term identified by 'termuid'.",
    description="""This request is only valid if \n
* the term is in 'Draft' status and
* the term has never been in 'Final' status and
* the term belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The term was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term is not in draft status.\n"
            "- The term was already in final state or is in use.\n"
            "- The library does not allow to delete term.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An term with the specified 'termuid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_ct_term(
    termuid: str = CTTermUID, current_user_id: str = Depends(get_current_user_id)
):
    ct_term_attribute_service = CTTermAttributesService(user=current_user_id)
    ct_term_attribute_service.soft_delete(term_uid=termuid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
