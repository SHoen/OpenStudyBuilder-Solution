"""CTTerms router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.ct_term import CTTermService

router = APIRouter()
CTTermUID = Path(None, description="The unique id of the ct term.")


@router.post(
    "/terms",
    summary="Creates new ct term.",
    description="""The following nodes are created
* CTTermRoot
  * CTTermAttributesRoot
  * CTTermAttributesValue
  * CTTermNameRoot
  * CTTermNameValue
""",
    response_model=models.CTTerm,
    status_code=201,
    responses={
        201: {"description": "Created - The term was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The catalogue does not exist.\n"
            "- The library does not exist..\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    term_input: models.CTTermCreateInput = Body(
        None, description="Properties to create CTTermAttributes and CTTermName."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_term_service = CTTermService(user=current_user_id)
    return ct_term_service.create(term_input)


@router.get(
    "/terms",
    summary="Returns all terms names and attributes.",
    response_model=CustomPage[models.CTTermNameAndAttributes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_terms(
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
    ct_term_service = CTTermService(user=current_user_id)
    results = ct_term_service.get_all_terms(
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
    "/terms/headers",
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
    ct_term_service = CTTermService(user=current_user_id)
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


@router.post(
    "/terms/{term_uid}/add-parent",
    summary="Adds a CT Term Root node as a parent to the selected term node.",
    description="",
    response_model=models.CTTerm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The term was successfully added as a parent to the term identified by term-uid."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term already has a defined parent of the same type.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term-uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_parent(
    term_uid: str = CTTermUID,
    parent_uid: str = Query(..., description="The unique id for the parent node."),
    relationship_type: str = Query(
        ...,
        description="The type of the parent relationship.\n"
        "Valid types are 'type' or 'subtype', 'valid_for_epoch'",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_term_service = CTTermService(user=current_user_id)
    return ct_term_service.add_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.post(
    "/terms/{term_uid}/remove-parent",
    summary="Removes a parent term from the selected term node",
    description="",
    response_model=models.CTTerm,
    status_code=201,
    responses={
        201: {
            "description": "Created - The term was successfully removed as a parent to the term identified by term-uid."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The term already has no defined parent with given parent-uid and relationship type.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The term with the specified 'term-uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def remove_parent(
    term_uid: str = CTTermUID,
    parent_uid: str = Query(..., description="The unique id for the parent node."),
    relationship_type: str = Query(
        ...,
        description="The type of the parent relationship.\n"
        "Valid types are 'type' or 'subtype'",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_term_service = CTTermService(user=current_user_id)
    return ct_term_service.remove_parent(
        term_uid=term_uid, parent_uid=parent_uid, relationship_type=relationship_type
    )


@router.patch(
    "/terms/{term_uid}/order",
    summary="Change an order of codelist-term relationship",
    description="""Reordering will create new HAS_TERM relationship.""",
    response_model=models.CTTerm,
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
def patch_new_term_order(
    term_uid: str = CTTermUID,
    new_order_input: models.CTTermNewOrder = Body(
        None, description="Parameters needed for the reorder action."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.CTTerm:
    ct_term_service = CTTermService(user=current_user_id)
    return ct_term_service.set_new_order(
        term_uid=term_uid,
        codelist_uid=new_order_input.codelistUid,
        new_order=new_order_input.newOrder,
    )
