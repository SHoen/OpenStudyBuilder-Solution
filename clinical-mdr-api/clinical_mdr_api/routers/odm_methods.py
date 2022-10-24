from typing import Any, Optional

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmMethod,
    OdmMethodPatchInput,
    OdmMethodPostInput,
    OdmMethodWithRelationsPatchInput,
    OdmMethodWithRelationsPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_methods import OdmMethodService

router = APIRouter()

# Argument definitions
OdmMethodUID = Path(None, description="The unique id of the ODM Method.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM Methods",
    description="",
    response_model=CustomPage[OdmMethod],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_methods(
    library: Optional[str] = Query(None),
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
):
    odm_method_service = OdmMethodService()
    results = odm_method_service.get_all_concepts(
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
    libraryName: Optional[str] = Query(None),
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
    odm_method_service = OdmMethodService()
    return odm_method_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM Method (in a specific version)",
    description="",
    response_model=OdmMethod,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_method(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Method's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM Methods",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Methods.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmMethod],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_method_versions(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.get_version_history(uid=uid)


@router.post(
    "/select",
    summary="Creates a new Method in 'Draft' status with version 0.1",
    description="",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "Created - The odm method was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_method(
    odm_method_create_input: OdmMethodPostInput = Body(None, description="")
):
    odm_method_service = OdmMethodService()
    return odm_method_service.create(concept_input=odm_method_create_input)


@router.post(
    "/create",
    summary="Creates an ODM Method with relationships",
    description="",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "Created - The odm method was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_method_with_relations(
    odm_method_with_relations_post_input: OdmMethodWithRelationsPostInput = Body(
        None, description=""
    )
):
    odm_method_service = OdmMethodService()
    return odm_method_service.create_with_relations(
        concept_input=odm_method_with_relations_post_input
    )


@router.patch(
    "/{uid}/select",
    summary="Update odm method",
    description="",
    response_model=OdmMethod,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in draft status.\n"
            "- The ODM Method had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_method(
    uid: str = OdmMethodUID,
    odm_method_edit_input: OdmMethodPatchInput = Body(None, description=""),
):
    odm_method_service = OdmMethodService()
    return odm_method_service.edit_draft(
        uid=uid, concept_edit_input=odm_method_edit_input
    )


@router.patch(
    "/{uid}/update",
    summary="Updates an ODM Method with relationships",
    description="",
    response_model=OdmMethod,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in draft status.\n"
            "- The ODM Method had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_method_with_relations(
    uid: str = OdmMethodUID,
    odm_method_with_relations_patch_input: OdmMethodWithRelationsPatchInput = Body(
        None, description=""
    ),
):
    odm_method_service = OdmMethodService()
    return odm_method_service.update_with_relations(
        uid=uid, concept_edit_input=odm_method_with_relations_patch_input
    )


@router.post(
    "/{uid}/new-version",
    summary=" Create a new version of ODM Method",
    description="""
State before:
 - uid must exist and the ODM Method must be in status Final.

Business logic:
- The ODM Method is changed to a draft state.

State after:
 - ODM Method changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Methods.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Method is not in final status.\n"
            "- The ODM Method with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_method_version(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve draft version of ODM Method",
    description="",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in draft status.\n"
            "- The library does not allow to approve ODM Method.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_method(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate final version of ODM Method",
    description="",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_method(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate retired version of a ODM Method",
    description="",
    response_model=OdmMethod,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Method with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_method(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    return odm_method_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Method",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Method was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Method is not in draft status.\n"
            "- The ODM Method was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Method.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Method with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_method(uid: str = OdmMethodUID):
    odm_method_service = OdmMethodService()
    odm_method_service.soft_delete(uid=uid)
