from typing import Any, List, Optional

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json

from clinical_mdr_api import config
from clinical_mdr_api.models import (
    OdmVendorElement,
    OdmVendorElementPatchInput,
    OdmVendorElementPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_vendor_elements import OdmVendorElementService

router = APIRouter()

# Argument definitions
OdmVendorElementUID = Path(None, description="The unique id of the ODM Vendor Element.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM Vendor Elements",
    description="",
    response_model=CustomPage[OdmVendorElement],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_vendor_elements(
    library: Optional[str] = Query(None),
    sort_by: Json = Query(None, description=_generic_descriptions.SORT_BY),
    page_number: Optional[int] = Query(
        1, ge=1, description=_generic_descriptions.PAGE_NUMBER
    ),
    page_size: Optional[int] = Query(
        config.DEFAULT_PAGE_SIZE, ge=0, description=_generic_descriptions.PAGE_SIZE
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: Optional[bool] = Query(
        False, description=_generic_descriptions.TOTAL_COUNT
    ),
):
    odm_vendor_element_service = OdmVendorElementService()
    results = odm_vendor_element_service.get_all_concepts(
        library=library,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage.create(
        items=results.items, total=results.total_count, page=page_number, size=page_size
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
    library_name: Optional[str] = Query(None),
    field_name: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    search_string: Optional[str] = Query(
        "", description=_generic_descriptions.HEADER_SEARCH_STRING
    ),
    filters: Optional[Json] = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: Optional[str] = Query("and", description=_generic_descriptions.OPERATOR),
    result_count: Optional[int] = Query(
        10, description=_generic_descriptions.HEADER_RESULT_COUNT
    ),
):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM Vendor Element (in a specific version)",
    description="",
    response_model=OdmVendorElement,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_vendor_element(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Vendor Element's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM Vendor Element",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Vendor Elements.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmVendorElement],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_vendor_element_versions(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.get_version_history(uid=uid)


@router.post(
    "",
    summary="Creates a new Vendor Element in 'Draft' status with version 0.1",
    description="",
    response_model=OdmVendorElement,
    status_code=201,
    responses={
        201: {
            "description": "Created - The ODM Vendor Element was successfully created."
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
def create_odm_vendor_element(
    odm_vendor_element_create_input: OdmVendorElementPostInput = Body(
        None, description=""
    )
):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.create(
        concept_input=odm_vendor_element_create_input
    )


@router.patch(
    "/{uid}",
    summary="Update ODM Vendor Element",
    description="",
    response_model=OdmVendorElement,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in draft status.\n"
            "- The ODM Vendor Element had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_vendor_element(
    uid: str = OdmVendorElementUID,
    odm_vendor_element_edit_input: OdmVendorElementPatchInput = Body(
        None, description=""
    ),
):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.edit_draft(
        uid=uid, concept_edit_input=odm_vendor_element_edit_input
    )


@router.post(
    "/{uid}/versions",
    summary=" Create a new version of ODM Vendor Element",
    description="""
State before:
 - uid must exist and the ODM Vendor Element must be in status Final.

Business logic:
- The ODM Vendor Element is changed to a draft state.

State after:
 - ODM Vendor Element changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmVendorElement,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Vendor Elements.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in final status.\n"
            "- The ODM Vendor Element with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_vendor_element_version(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approvals",
    summary="Approve draft version of ODM Vendor Element",
    description="",
    response_model=OdmVendorElement,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in draft status.\n"
            "- The library does not allow to approve ODM Vendor Element.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_vendor_element(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.approve(uid=uid)


@router.delete(
    "/{uid}/activations",
    summary=" Inactivate final version of ODM Vendor Element",
    description="",
    response_model=OdmVendorElement,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_vendor_element(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/activations",
    summary="Reactivate retired version of a ODM Vendor Element",
    description="",
    response_model=OdmVendorElement,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Vendor Element with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_vendor_element(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    return odm_vendor_element_service.reactivate_retired(uid=uid)


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Vendor Element",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The ODM Vendor Element was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Vendor Element is not in draft status.\n"
            "- The ODM Vendor Element was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Vendor Element.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Vendor Element with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_vendor_element(uid: str = OdmVendorElementUID):
    odm_vendor_element_service = OdmVendorElementService()
    odm_vendor_element_service.soft_delete(uid=uid)
