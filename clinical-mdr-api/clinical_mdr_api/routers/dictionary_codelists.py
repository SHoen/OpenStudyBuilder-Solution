"""DictionaryCodelist router."""
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.dictionary_codelist_generic_service import (
    DictionaryCodelistGenericService,
)

router = APIRouter()

DictionaryCodelistUID = Path(
    None, description="The unique id of the DictionaryCodelist"
)
DictionaryCodelistLibrary = Path(
    None,
    description="The Library from which the dictionaries codelists should be retrieved",
)


@router.get(
    "/codelists/{library}",
    summary="List all dictionary codelists.",
    description="""
State before:
 - The library must exist.
 
Business logic:
 - List all dictionary codelists (in their latest versions).
 
State after:
 - No change

Possible errors:
 - Invalid library name.""",
    response_model=CustomPage[models.DictionaryCodelist],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
@decorators.allow_exports(
    {
        "defaults": [
            "dictionaryId",
            "name",
            "nameSentenceCase",
            "abbreviation",
            "definition",
            "startDate",
            "status",
            "version",
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
    library: str = DictionaryCodelistLibrary,
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
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    results = dictionary_codelist_service.get_all_dictionary_codelists(
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
    "/codelists/{library}/headers",
    summary="Returns possibles values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
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
    library: str = DictionaryCodelistLibrary,
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
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.get_distinct_values_for_header(
        library=library,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.post(
    "/codelists",
    summary="Creates new dictionary codelist.",
    description="""The following nodes are created
  * DictionaryCodelistRoot
  * DictionaryCodelistValue
""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "Created - The dictionary codelist was successfully created."
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
def create(
    dictionary_codelist_input: models.DictionaryCodelistCreateInput = Body(
        None, description="Properties to create DictionaryCodelistValue node."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.create(dictionary_codelist_input)


@router.get(
    "/codelists/{uid}",
    summary="List details on the dictionary codelist with {uid}",
    description="""
State before:
 - The selected codelist must exist.
 
Business logic:
 - List details of the selected codelist (in a given version, if specified)

State after:
 - No change""",
    response_model=models.DictionaryCodelist,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_codelist(
    uid: str = DictionaryCodelistUID,
    version: Optional[str] = Query(
        None,
        description="If specified then the latest/newest representation of the dictionary codelist "
        "for DictionaryCodelistValue in that version is returned.\n"
        "Only exact matches are considered. The version is specified in the following format:"
        "<major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0',",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.get_by_uid(codelist_uid=uid, version=version)


@router.get(
    "/codelists/{uid}/versions",
    summary="List version history for a dictionary codelist",
    description="""
State before:
 - codelistuid must exist.
 
Business logic:
 - List version history for the representation of the dictionary codelist, including the use as template parameter.
 - The returned versions are ordered by startDate descending (newest entries first).
 
State after:
 - No change
 
Possible errors:
 - Invalid codelistuid.
    """,
    response_model=List[models.DictionaryCodelistVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The dictionary codelist with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    uid: str = DictionaryCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.get_version_history(codelist_uid=uid)


@router.patch(
    "/codelists/{uid}",
    summary=" Update name or template parameter flag for dictionary codelist",
    description="""
State before:
 - codelistuid must exist and the dictionary codelist must exist in status draft.
 
Business logic:
 - If the dictionary codelist related to codelistuid exist in status draft then name attribute and Template Parameter node label are updated.
 - If Template Parameter have been set to 'Y' then it cannot be set back to 'N' (i.e. when the Template Parameter node label have been added it cannot be removed).
 
State after:
 - name attribute and Template Parameter node label are updated for the dictionary codelist.
 - Audit trail entry must be made with update of name attribute or Template Parameter flag.
 
Possible errors:
 - Invalid codelistuid.
""",
    response_model=models.DictionaryCodelist,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist is not in draft status.\n"
            "- The dictionary codelist had been in 'Final' status before.\n"
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
    uid: str = DictionaryCodelistUID,
    dictionary_codelist_input: models.DictionaryCodelistEditInput = Body(
        None,
        description="The new parameter values for the dictionary codelist including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.edit_draft(
        codelist_uid=uid, codelist_input=dictionary_codelist_input
    )


@router.post(
    "/codelists/{uid}/new-version",
    summary=" Create a new version of the dictionary codelist",
    description="""
State before:
 - codelistuid must exist and the dictionary codelist must be in status Final.
 
Business logic:
 - The latest 'Final' version will remain the same as before.
 - The status of the new created version will be automatically set to 'Draft'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.
 - The 'changeDescription' property will be set automatically to 'New version'.
 
State after:
 - Dictionary codelist changed status to Draft and assigned a new minor version number.
 - Audit trail entry must be made with action of creating new Draft version.
 
Possible errors:
 - Invalid codelistuid or status not Final.
 
""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "Created - The dictionary codelist was successfully created."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The library does not allow to create codelists.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Reasons include e.g.: \n"
            "- The dictionary codelist is not in final status.\n"
            "- The dictionary codelist with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    uid: str = DictionaryCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.create_new_version(codelist_uid=uid)


@router.post(
    "/codelists/{uid}/approve",
    summary="Approve draft version of the dictionary codelist",
    description="""
State before:
 - codelistuid must exist and the dictionary codelist must be in status Draft.
 
Business logic:
 - The latest 'Draft' version will remain the same as before.
 - The status of the new approved version will be automatically set to 'Final'.
 - The 'version' property of the new version will be automatically set to the version of the latest 'Final' version increased by +1.0.
 - The 'changeDescription' property will be set automatically 'Approved version'.
 
State after:
 - Dictionary codelist changed status to Final and assigned a new major version number.
 - Audit trail entry must be made with action of approving to new Final version.
 
Possible errors:
 - Invalid codelistuid or status not Draft.
    """,
    response_model=models.DictionaryCodelist,
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
    uid: str = DictionaryCodelistUID,
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.approve(codelist_uid=uid)


@router.post(
    "/codelists/{uid}/add-term",
    summary=" Attaches a dictionary term to a dictionary codelist",
    description="""
State before:
 - codelistuid must exist.
 - termUid must exist.

Business logic:
 - Create a HAS_TERM relationship between the selected codelist root and the selected term root, with the current date and current user.

Possible errors:
 - Invalid codelistuid.
-  Invalid termuid.
-  Codelist with {uid} is not extensible.
- Term is already part of the specified codelist.""",
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully created.\n"
            "The TemplateParameter labels and HAS_VALUE relationship were successfully added "
            "if dictionary codelist identified by 'uid' is a TemplateParameter."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The dictionary codelist does not exist.\n"
            "- The dictionary term does not exist.\n"
            "- The dictionary codelist already has passed term.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def add_term(
    uid: str = DictionaryCodelistUID,
    term_input: models.DictionaryCodelistTermInput = Body(
        None, description="UID of the DictionaryTermRoot node."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.add_term(
        codelist_uid=uid, term_uid=term_input.termUid
    )


@router.post(
    "/codelists/{uid}/remove-term",
    summary="Removes a dictionary term from a dictionary codelist",
    description="""
State before:
 - codelistuid must exist.
 - termUid must exist.
 - the codelist contains the term that is removed.


Business logic:
 - Create a HAD_TERM relationship between the selected codelist root and the selected term root, with the current date as the end date, and current user.
 - Remove the old HAS_TERM relationship between the codelist and the term.

Possible errors:
 - Invalid codelistuid.
 - Invalid termuid.
- Term is not part of the specified codelist. """,
    response_model=models.DictionaryCodelist,
    status_code=201,
    responses={
        201: {
            "description": "The HAS_TERM relationship was successfully deleted and "
            "HAD_TERM relationship was successfully created.\n"
            "The HAS_VALUE relationship was successfully deleted if codelist identified by "
            "uid is a TemplateParameter"
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The codelist does not exist.\n"
            "- The term does not exist.\n"
            "- The codelist doesn't have passed term.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def remove_term(
    uid: str = DictionaryCodelistUID,
    term_input: models.DictionaryCodelistTermInput = Body(
        None, description="UID of the DictionaryTermRoot node."
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    dictionary_codelist_service = DictionaryCodelistGenericService(user=current_user_id)
    return dictionary_codelist_service.remove_term(
        codelist_uid=uid, term_uid=term_input.termUid
    )
