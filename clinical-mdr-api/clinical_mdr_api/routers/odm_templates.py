from typing import Any, Optional, Sequence

from fastapi import APIRouter, Body, Path, Query
from pydantic.types import Json, List

from clinical_mdr_api.models import (
    OdmTemplate,
    OdmTemplateFormPostInput,
    OdmTemplatePatchInput,
    OdmTemplatePostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.odm_templates import OdmTemplateService

router = APIRouter()

# Argument definitions
OdmTemplateUID = Path(None, description="The unique id of the ODM Template.")


@router.get(
    "",
    summary="Return every variable related to the selected status and version of the ODM Templates",
    description="",
    response_model=CustomPage[OdmTemplate],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_all_odm_templates(
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
    odm_template_service = OdmTemplateService()
    results = odm_template_service.get_all_concepts(
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
    odm_template_service = OdmTemplateService()
    return odm_template_service.get_distinct_values_for_header(
        library=libraryName,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Get details on a specific ODM Template (in a specific version)",
    description="",
    response_model=OdmTemplate,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_odm_template(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.get_by_uid(uid=uid)


@router.get(
    "/{uid}/relationships",
    summary="Get UIDs of a specific ODM Template's relationships",
    description="",
    response_model=dict,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_active_relationships(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.get_active_relationships(uid=uid)


@router.get(
    "/{uid}/versions",
    summary="List version history for ODM Templates",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Templates.
 - The returned versions are ordered by startDate descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    response_model=List[OdmTemplate],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Template with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_odm_template_versions(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.get_version_history(uid=uid)


@router.post(
    "",
    summary="Creates a new Template in 'Draft' status with version 0.1",
    description="",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {"description": "Created - The odm item was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not exist.\n"
            "- The library does not allow to add new items.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_template(
    odm_template_create_input: OdmTemplatePostInput = Body(None, description="")
):
    odm_template_service = OdmTemplateService()
    return odm_template_service.create(concept_input=odm_template_create_input)


@router.patch(
    "/{uid}",
    summary="Update odm item",
    description="",
    response_model=OdmTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Template is not in draft status.\n"
            "- The ODM Template had been in 'Final' status before.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Template with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit_odm_template(
    uid: str = OdmTemplateUID,
    odm_template_edit_input: OdmTemplatePatchInput = Body(None, description=""),
):
    odm_template_service = OdmTemplateService()
    return odm_template_service.edit_draft(
        uid=uid, concept_edit_input=odm_template_edit_input
    )


@router.post(
    "/{uid}/new-version",
    summary=" Create a new version of ODM Template",
    description="""
State before:
 - uid must exist and the ODM Template must be in status Final.

Business logic:
- The ODM Template is changed to a draft state.

State after:
 - ODM Template changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating a new draft version.

Possible errors:
 - Invalid uid or status not Final.
""",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create ODM Templates.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The ODM Template is not in final status.\n"
            "- The ODM Template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_odm_template_version(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.create_new_version(uid=uid)


@router.post(
    "/{uid}/approve",
    summary="Approve draft version of ODM Template",
    description="",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Template is not in draft status.\n"
            "- The library does not allow to approve ODM Template.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Template with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_odm_template(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.approve(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary=" Inactivate final version of ODM Template",
    description="",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Template is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate_odm_template(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivate retired version of a ODM Template",
    description="",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Template is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate_odm_template(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    return odm_template_service.reactivate_retired(uid=uid)


@router.post(
    "/{uid}/add-forms",
    summary="Adds forms to the ODM Template.",
    description="",
    response_model=OdmTemplate,
    status_code=201,
    responses={
        201: {
            "description": "Created - The forms were successfully added to the ODM Template."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The forms with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_forms_to_odm_template(
    uid: str = OdmTemplateUID,
    override: bool = Query(
        False,
        description="If true, all existing form relationships will be replaced with the provided form relationships.",
    ),
    odm_template_form_post_input: Sequence[OdmTemplateFormPostInput] = Body(
        None, description=""
    ),
):
    odm_template_service = OdmTemplateService()
    return odm_template_service.add_forms(
        uid=uid,
        odm_template_form_post_input=odm_template_form_post_input,
        override=override,
    )


@router.delete(
    "/{uid}",
    summary="Delete draft version of ODM Template",
    description="",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The ODM Template was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The ODM Template is not in draft status.\n"
            "- The ODM Template was already in final state or is in use.\n"
            "- The library does not allow to delete ODM Template.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An ODM Template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_odm_template(uid: str = OdmTemplateUID):
    odm_template_service = OdmTemplateService()
    odm_template_service.soft_delete(uid=uid)
