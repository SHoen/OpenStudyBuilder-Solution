from typing import Any, Optional

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmXmlExtension,
    OdmXmlExtensionPatchInput,
    OdmXmlExtensionPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_xml_extensions import OdmXmlExtensionService

router = APIRouter()

# Argument definitions
OdmXmlExtensionUID = Path(None, description="The unique id of the ODM XML Extension.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM XML Extensions",
    description="",
    response_model=CustomPage[OdmXmlExtension],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_xml_extensions(
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
    odm_xml_extension_service = OdmXmlExtensionService()
    results = odm_xml_extension_service.get_all_concepts(
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
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM XML Extension (in a specific version)",
    description="",
    response_model=OdmXmlExtension,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_xml_extension(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM XML Extension's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM XML Extensions",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM XML Extensions.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmXmlExtension],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM XML Extension with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_xml_extension_versions(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.get_version_history(uid=uid)


@router.post(
    "",
    summary="Creates a new XML Extension in 'Draft' status with version 0.1",
    description="",
    response_model=OdmXmlExtension,
    status_code=201,
    responses={
        201: {
            "description": "Created - The odm xml extension was successfully created."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_xml_extension(
    odm_xml_extension_create_input: OdmXmlExtensionPostInput = Body(
        None, description=""
    )
):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.create(
        concept_input=odm_xml_extension_create_input
    )


@router.patch(
    "/{uid}",
    summary="Update odm xml extension",
    description="",
    response_model=OdmXmlExtension,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in draft status.\n"
            "- The ODM XML Extension had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM XML Extension with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_xml_extension(
    uid: str = OdmXmlExtensionUID,
    odm_xml_extension_edit_input: OdmXmlExtensionPatchInput = Body(
        None, description=""
    ),
):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.edit_draft(
        uid=uid, concept_edit_input=odm_xml_extension_edit_input
    )


@router.post(
    "/{uid}/new-version",
    summary=" Create a new version of ODM XML Extension",
    description="""
State before:
 - uid must exist and the ODM XML Extension must be in status Final.

Business logic:
- The ODM XML Extension is changed to a draft state.

State after:
 - ODM XML Extension changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmXmlExtension,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM XML Extensions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in final status.\n"
            "- The ODM XML Extension with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_xml_extension_version(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve draft version of ODM XML Extension",
    description="",
    response_model=OdmXmlExtension,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in draft status.\n"
            "- The library does not allow to approve ODM XML Extension.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM XML Extension with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_xml_extension(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate final version of ODM XML Extension",
    description="",
    response_model=OdmXmlExtension,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM XML Extension with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_xml_extension(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate retired version of a ODM XML Extension",
    description="",
    response_model=OdmXmlExtension,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM XML Extension with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_xml_extension(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    return odm_xml_extension_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM XML Extension",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The ODM XML Extension was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM XML Extension is not in draft status.\n"
            "- The ODM XML Extension was already in final state or is in use.\n"
            "- The library does not allow to delete ODM XML Extension.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM XML Extension with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_xml_extension(uid: str = OdmXmlExtensionUID):
    odm_xml_extension_service = OdmXmlExtensionService()
    odm_xml_extension_service.soft_delete(uid=uid)
