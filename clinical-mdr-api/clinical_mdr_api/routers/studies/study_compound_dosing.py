from typing import Any

from fastapi import Body, Depends, Query, Request, Response, status
from pydantic.types import Json

from clinical_mdr_api import config, models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id, rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies import utils
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)


@router.get(
    "/studies/{uid}/study-compound-dosings",
    dependencies=[rbac.STUDY_READ],
    summary="List all study compound dosings currently defined for the study",
    description=_generic_descriptions.DATA_EXPORTS_HEADER,
    response_model=CustomPage[models.StudyCompoundDosing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid=study_compound_dosing_uid",
            "order",
            "element=study_element.name",
            "compound=study_compound.compound.name",
            "compound_alias=study_compound.compound_alias.name",
            "dose_value_value=dose_value.value",
            "dose_value_unit=dose_value.unit_label",
            "dose_frequency=dose_frequency.name",
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
def get_all_selected_compound_dosings(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = utils.studyUID,
    study_value_version: str | None = None,
    current_user_id: str = Depends(get_current_user_id),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
):
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    all_items = service.get_all_compound_dosings(
        study_uid=uid,
        study_value_version=study_value_version,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total,
        page=page_number,
        size=page_size,
    )


@router.get(
    "/studies/{uid}/study-compound-dosings/headers",
    dependencies=[rbac.STUDY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_distinct_values_for_header(
    uid: str = utils.studyUID,
    field_name: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    search_string: str
    | None = Query("", description=_generic_descriptions.HEADER_SEARCH_STRING),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    result_count: int
    | None = Query(10, description=_generic_descriptions.HEADER_RESULT_COUNT),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/study-compound-dosings/headers",
    dependencies=[rbac.STUDY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=list[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_distinct_compound_dosings_values_for_header(
    field_name: str = Query(..., description=_generic_descriptions.HEADER_FIELD_NAME),
    search_string: str
    | None = Query("", description=_generic_descriptions.HEADER_SEARCH_STRING),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    result_count: int
    | None = Query(10, description=_generic_descriptions.HEADER_RESULT_COUNT),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
    )


@router.get(
    "/studies/{uid}/study-compound-dosings/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List full audit trail related to definition of all study compound dosings.",
    description="""
Parameters:
 - uid as study-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study must exist.

Business logic:
 - List all entries in the audit trail related to study compound dosings for specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to study compounds.
    """,
    response_model=list[models.StudyCompoundDosing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_compound_dosings_audit_trail(
    uid: str = utils.studyUID, current_user_id: str = Depends(get_current_user_id)
) -> list[models.StudyCompoundDosing]:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_all_selection_audit_trail(study_uid=uid)


@router.get(
    "/studies/{uid}/study-compound-dosings/{study_compound_dosing_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study compound dosing.",
    description="""
Parameters:
 - uid as study-uid (required)
 - study-compound-dosing-uid (required)
 - [NOT YET IMPLEMENTED] study status (optional)
 - [NOT YET IMPLEMENTED] study version (required when study status is locked)

State before:
 - Study and study compound dosing must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study compound dosing for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.

Returned data:
 - List of actions and changes related to the specified study compound dosing.
    """,
    response_model=list[models.StudyCompoundDosing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_compound_dosing_audit_trail(
    uid: str = utils.studyUID,
    study_compound_dosing_uid: str = utils.study_compound_dosing_uid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.get_compound_dosing_audit_trail(
        study_uid=uid, compound_dosing_uid=study_compound_dosing_uid
    )


@router.post(
    "/studies/{uid}/study-compound-dosings",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study compound dosing to a study",
    response_model=models.StudyCompoundDosing,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - A study compound dosing already exists for selected study compound and element",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study compound or study element is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def create_study_compound_dosing(
    uid: str = utils.studyUID,
    selection: models.StudyCompoundDosingInput = Body(
        description="Related parameters of the compound dosing that shall be created.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.make_selection(study_uid=uid, selection_create_input=selection)


@router.delete(
    "/studies/{uid}/study-compound-dosings/{study_compound_dosing_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study compound dosing",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the compound dosing and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_compound_dosing(
    uid: str = utils.studyUID,
    study_compound_dosing_uid: str = utils.study_compound_dosing_uid,
    current_user_id: str = Depends(get_current_user_id),
):
    StudyService().check_if_study_exists(uid)
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    service.delete_selection(
        study_uid=uid, study_selection_uid=study_compound_dosing_uid
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/studies/{uid}/study-compound-dosings/{study_compound_dosing_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit or replace a study compound dosing",
    description="""
State before:
 - Study must exist and be in status draft

Business logic:
 - Update specified study-compound-dosing with selection of existing study compound and study element items.
 - A single relationships can be defined for a study compound dosing to each of the following code list terms:
   - Dose frequency
 - Order number for the study compound cannot be changed by this API endpoint.

State after:
 - related parameters are updated for the study compound dosing.
 - Added new entry in the audit trail for the update of the study-compound-dosing.""",
    response_model=models.StudyCompoundDosing,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection with the given uid.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def update_compound_dosing(
    uid: str = utils.studyUID,
    study_compound_dosing_uid: str = utils.study_compound_dosing_uid,
    selection: models.StudyCompoundDosingInput = Body(
        description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyCompoundDosing:
    service = StudyCompoundDosingSelectionService(author=current_user_id)
    return service.patch_selection(
        study_uid=uid,
        study_selection_uid=study_compound_dosing_uid,
        selection_update_input=selection,
    )