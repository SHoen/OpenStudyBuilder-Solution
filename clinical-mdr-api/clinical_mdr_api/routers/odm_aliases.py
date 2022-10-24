from typing import Any, Optional, Sequence

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmAlias,
    OdmAliasBatchInput,
    OdmAliasBatchOutput,
    OdmAliasPatchInput,
    OdmAliasPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_aliases import OdmAliasService

router = APIRouter()

# Argument definitions
OdmAliasUID = Path(None, description="The unique id of the ODM Alias.")


@router.get(
    "",
    summary="Return a listing of ODM Aliases",
    description="",
    response_model=CustomPage[OdmAlias],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_aliases(
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
    odm_alias_service = OdmAliasService()
    results = odm_alias_service.get_all_concepts(
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
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Alias' relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="Return a listing of versions of a specific ODM Alias",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Aliases.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmAlias],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_alias_versions(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.get_version_history(uid=uid)


@router.post(
    "",
    summary="Create a new ODM Alias",
    description="",
    response_model=OdmAlias,
    status_code=201,
    responses={
        201: {"description": "Created - The ODM Alias was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_alias(
    odm_alias_create_input: OdmAliasPostInput = Body(None, description="")
):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.create(concept_input=odm_alias_create_input)


@router.post(
    "/batch",
    summary="Batch operations (create, edit) for ODM Aliases",
    description="",
    response_model=Sequence[OdmAliasBatchOutput],
    status_code=201,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def odm_alias_batch_operations(
    operations: Sequence[OdmAliasBatchInput] = Body(
        None, description="List of operation to perform"
    ),
):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.handle_batch_operations(operations)


@router.patch(
    "/{uid}",
    summary="Update an ODM Alias",
    description="",
    response_model=OdmAlias,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The ODM Alias had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_alias(
    uid: str = OdmAliasUID,
    odm_alias_edit_input: OdmAliasPatchInput = Body(None, description=""),
):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.edit_draft(
        uid=uid, concept_edit_input=odm_alias_edit_input
    )


@router.post(
    "/{uid}/new-version",
    summary="Create a new version of an ODM Alias",
    description="""
State before:
 - uid must exist and the ODM Alias must be in status Final.

Business logic:
- The ODM Alias is changed to a draft state.

State after:
 - ODM Alias changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmAlias,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Aliases.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Alias is not in final status.\n"
            "- The ODM Alias with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_alias_version(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve an ODM Alias",
    description="",
    response_model=OdmAlias,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The library does not allow to approve ODM Alias.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_alias(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate an ODM Alias",
    description="",
    response_model=OdmAlias,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_alias(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate an ODM Alias",
    description="",
    response_model=OdmAlias,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Alias with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_alias(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    return odm_alias_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Alias",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Alias was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Alias is not in draft status.\n"
            "- The ODM Alias was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Alias.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Alias with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_alias(uid: str = OdmAliasUID):
    odm_alias_service = OdmAliasService()
    odm_alias_service.soft_delete(uid=uid)
