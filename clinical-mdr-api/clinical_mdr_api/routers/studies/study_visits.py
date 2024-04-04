from typing import Any

from fastapi import Body, Depends, Path, Query
from pydantic.types import Json
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

import clinical_mdr_api.models
from clinical_mdr_api import config
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study_selections import study_epoch
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id, rbac
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.studies.study_epochs import (
    study_visit_uid_description,
    studyUID,
)
from clinical_mdr_api.services.studies.study_visit import StudyVisitService


@router.get(
    "/studies/{uid}/study-visits",
    dependencies=[rbac.STUDY_READ],
    summary="List all study visits currently defined for the study",
    description=f"""
State before:
- Study must exist.
 
Business logic:
 - By default (no study status is provided) list all study visits for the study uid in status draft. If the study not exist in status draft then return the study visits for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study visit for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study visits for the specific locked study version is returned.
 - Indicate by an boolean variable if the study visit can be updated (if the selected study is in status draft).  
 - Indicate by an boolean variable if all expected selections have been made for each study visits , or some are missing.
   - e.g. time unit must is expected.
 - Indicate by an boolean variable if a study visit can be re-ordered.
 - Duration time is calculated in the duration time unit specified for the study epoch based on the following rule:

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    response_model=CustomPage[
        clinical_mdr_api.models.study_selections.study_visit.StudyVisit
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "study_epoch_uid",
            "study_epoch_name",
            "visit_type_name",
            "visit_contact_mode_name",
            "order",
            "unique_visit_number",
            "visit_name",
            "visit_short_name",
            "study_day_label",
            "study_week_label",
            "visit_window",
            "time_reference_name",
            "time_value",
            "consecutive_visit_group",
            "show_visit",
            "description",
            "start_rule",
            "end_rule",
            "modified_date",
            "user_initials",
            "study_uid",
            "study_version",
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
def get_all(
    request: Request,  # request is actually required by the allow_exports decorator,
    uid: str = studyUID,
    sort_by: Json = Query(None, description=_generic_descriptions.SORT_BY),
    page_number: int
    | None = Query(1, ge=1, description=_generic_descriptions.PAGE_NUMBER),
    page_size: int
    | None = Query(
        config.DEFAULT_PAGE_SIZE,
        ge=0,
        le=config.MAX_PAGE_SIZE,
        description=_generic_descriptions.PAGE_SIZE,
    ),
    filters: Json
    | None = Query(
        None,
        description=_generic_descriptions.FILTERS,
        example=_generic_descriptions.FILTERS_EXAMPLE,
    ),
    operator: str | None = Query("and", description=_generic_descriptions.OPERATOR),
    total_count: bool
    | None = Query(False, description=_generic_descriptions.TOTAL_COUNT),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[clinical_mdr_api.models.StudyVisit]:
    service = StudyVisitService(current_user_id)
    results = service.get_all_visits(
        study_uid=uid,
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        study_value_version=study_value_version,
    )
    return CustomPage.create(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/studies/{uid}/study-visits/headers",
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
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
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
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
):
    return StudyVisitService(current_user_id).get_distinct_values_for_header(
        study_uid=uid,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=result_count,
        study_value_version=study_value_version,
    )


@router.get(
    "/studies/{uid}/study-visits-references",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all study visit references for study currently selected",
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.StudyVisit
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_all_references(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> list[clinical_mdr_api.models.study_selections.study_visit.StudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_all_references(study_uid=uid)


@router.post(
    "/studies/{uid}/study-visits",
    dependencies=[rbac.STUDY_WRITE],
    summary="Add a study visit to a study",
    description="""

State before:
 - Study must exist and study status must be in draft.

Business logic:
 - A subset of the visit types are of the type being a time reference (the sponsor defined term exist both in the code list visit type as well as time reference) - only one visit in the study visits can refer to a visit type related to a specific time reference.
 
 - The initial study visit specified for a study must refer to a visit type being a time reference type, it must have this as the time reference as well, and the time value must be set to 0.
 
 - All other study visits, than the initial visit, must either refer to a time reference that exist as a visit type for one of the other study visits for the study; or refer to the time reference for 'previous visit'. [previous visit needs to be selected in up - this probably will not be implemented in 0.1]

 - The duration time must be calculated as the duration time at the visit for the reference time + the time value specified for the study visit. [absolute value of time difference from initial reference time visit (e.g. the Baseline visit)" - to be discussed in point 3]
 
 - The duration time must be returned in the duration time unit specified for the related study epoch. [changed calculated to returned]
 
 - The time value is only valid, if the derived duration time for the study visit is greater than or equal to the duration time for the last study visit in the previous study epoch (given the study visit not is in the first epoch). [depending on a epoch definition, not in v 0.1]
 
 - The time value is only valid, if the derived duration time for the study visit is less than or equal to the duration time for the first study visit in the following study epoch (given the study visit not is in the last epoch). [depending on epoch definition, not in c 0.1)
 ]
 - The study day number is derived as:
    - Equal to the derived study duration time in days if value is less than 0.
    - Equal to 1 + the derived study duration time in days if value is greater than or equal to 0.
    - If the derived study duration time is blank, then the study day number must also be blank.
    - The derived result for the study day number is rounded: If result is below zero, the result is rounded using ceil function. Otherwise the result is rounded using floor function.
   
 - The study day label is a text string derived by concatenation of: Day+<space>+[Study day number]
 - The study week number is derived as
    - Equal to the derived study duration time in weeks if value is less than 0.
    - Equal to 1 + the derived study duration time in weeks if value is greater than or equal to 0.
    - If the derived study duration time is blank, then the study week number must also be blank.
    - The derived result for the study week number is rounded: If result is below zero, the result is rounded using ceil function. Otherwise the result is rounded using floor function.
 - The study week label is a text string derived by concatenation of:  Week+space+[Study week number]


 - The visit number is derived as an running integer with 1 for the very first visit sorted by chronological order (i.e. 1, 2. 3, 4, etc.). [NOTE: we have to figure out a rule for how we avoid counting sub visits? 1.1, 1.2, 1.3 etc?]
 
 - The unique visit number is derived as an integer with 10 for the very first visit, increasing with +10 for each visit, sorted by chronological order  (i.e. 10, 20. 30, 40, etc.). [NOTE: we have to figure out a rule for how we create unique visit numbers for sub visits?]
 
 - The visit name is a text string derived by concatenation of: Visit+space+[Visit number]+[Visit sub-label] (if available)
 
 - The visit short name is a text string derived by concatenation of: V+[Visit number]+[Visit sub-label] (if available)


State after:
 - the visit is added as study visit to the study.
 - Added new entry in the audit trail for the creation of the study-visit .
 - new simple concepts are possibly created based on the result of the "get or create" operation.
 
Possible errors:
 - Invalid study-uid.
 - Invalid timepointuid, visitnameuid, ... etc.
    """,
    response_model=clinical_mdr_api.models.study_selections.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Forbidden - The settings for visit are invalid",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or visit is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_new_visit_create(
    uid: str = studyUID,
    selection: clinical_mdr_api.models.study_selections.study_visit.StudyVisitCreateInput = Body(
        description="Related parameters of the visit that shalll be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> clinical_mdr_api.models.study_selections.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.create(study_uid=uid, study_visit_input=selection)


@router.post(
    "/studies/{uid}/study-visits/preview",
    dependencies=[rbac.STUDY_WRITE],
    summary="Preview a study visit",
    response_model=clinical_mdr_api.models.study_selections.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study is not found with the passed 'uid'.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def post_preview_visit(
    uid: str = studyUID,
    selection: clinical_mdr_api.models.study_selections.study_visit.StudyVisitCreateInput = Body(
        description="Related parameters of the visit that shalll be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> clinical_mdr_api.models.study_selections.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.preview(study_uid=uid, study_visit_input=selection)


@router.get(
    "/studies/{uid}/study-visits/allowed-visit-types",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all allowed Visit Types for specified epoch type",
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.AllowedVisitTypesForEpochType
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_allowed_visit_types_for_epoch_type(
    current_user_id: str = Depends(get_current_user_id),
    epoch_type_uid: str = Query(
        ...,
        description="The unique uid of the epoch type for which the "
        "allowed visit types should be returned",
    ),
    uid: str = Path(description="The unique uid of the study"),
) -> list[
    clinical_mdr_api.models.study_selections.study_visit.AllowedVisitTypesForEpochType
]:
    service = StudyVisitService(current_user_id)
    return service.get_valid_visit_types_for_epoch_type(
        epoch_type_uid=epoch_type_uid, study_uid=uid
    )


@router.get(
    "/studies/{uid}/study-visits/allowed-time-references",
    dependencies=[rbac.STUDY_READ],
    summary="Returns all allowed time references for a study visit",
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.AllowedTimeReferences
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_allowed_time_references_for_given_study(
    current_user_id: str = Depends(get_current_user_id),
    uid: str = Path(description="The unique uid of the study"),
) -> list[clinical_mdr_api.models.study_selections.study_visit.AllowedTimeReferences]:
    service = StudyVisitService(current_user_id)
    return service.get_allowed_time_references_for_study(study_uid=uid)


@router.patch(
    "/studies/{uid}/study-visits/{study_visit_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Edit a study visit",
    description="""
State before:
 - Study and study visit must exist and study status must be in draft.

Business logic:
 - Same logic applies as for selecting or creating an study visit (see POST statements for /study-visits)

State after:
 - Visit is added as study visit to the study.
 - Add new entry in the audit trail for the update of the study-visit .

Possible errors:
 - Invalid study-uid or study_visit_uid_description .
    """,
    response_model=clinical_mdr_api.models.study_selections.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no study or visit.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def patch_update_visit(
    uid: str = studyUID,
    study_visit_uid: str = study_visit_uid_description,
    selection: clinical_mdr_api.models.study_selections.study_visit.StudyVisitEditInput = Body(
        description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyVisitService(current_user_id)
    return service.edit(
        study_uid=uid, study_visit_uid=study_visit_uid, study_visit_input=selection
    )


@router.delete(
    "/studies/{uid}/study-visits/{study_visit_uid}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Delete a study visit",
    description=""""
State before:
 - Study must exist and study status must be in draft.
 - study_visit_uid must exist. 

Business logic:
 - Remove specified study-visit from the study.
 - Reference to the study-visit should still exist in the audit trail.
 - Simple concepts that are now unused should continue to be persisted in the database.

State after:
 - Study visit deleted from the study, but still exist as a node in the database with a reference from the audit trail.
 - Added new entry in the audit trail for the deletion of the study-visit .
 
Possible errors:
 - Invalid study-uid or study_visit_uid.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the visit and the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def delete_study_visit(
    uid: str = studyUID,
    study_visit_uid: str = study_visit_uid_description,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyVisitService(current_user_id)
    service.delete(study_uid=uid, study_visit_uid=study_visit_uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/studies/{uid}/study-visits/{study_visit_uid}/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of a specific study visit.",
    description="""
State before:
 - Study and study visits must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study visit for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.StudyVisitVersion
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the study visit for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_study_visit_audit_trail(
    uid: str = studyUID,
    study_visit_uid: str = study_visit_uid_description,
    current_user_id: str = Depends(get_current_user_id),
) -> list[clinical_mdr_api.models.study_selections.study_visit.StudyVisitVersion]:
    service = StudyVisitService(current_user_id)
    return service.audit_trail(study_visit_uid, study_uid=uid)


@router.get(
    "/studies/{uid}/study-visit/audit-trail",
    dependencies=[rbac.STUDY_READ],
    summary="List audit trail related to definition of all study visits within the specified study-uid.",
    description="""
State before:
 - Study and study visits must exist.

Business logic:
 - List all study visit audit trail within the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.StudyVisitVersion
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the study visit for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
def get_study_visits_all_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> list[clinical_mdr_api.models.study_selections.study_visit.StudyVisitVersion]:
    service = StudyVisitService(current_user_id)
    return service.audit_trail_all_visits(study_uid=uid)


@router.get(
    "/studies/{uid}/study-visits/{study_visit_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="List all definitions for a specific study visit",
    description="""
State before:
 - Study and study visit must exist
 
Business logic:
 - By default (no study status is provided) list all details for specified study visit for the study uid in status draft. If the study not exist in status draft then return the study visits for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study visits for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study visit for the specific locked study version is returned.
 - Indicate by an boolean variable if the study visit can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study visit , or some are missing.
 - Indicate by an boolean variable if the selected visit is available in a newer version.
 
State after:
 - no change
 
Possible errors:
 - Invalid study-uid or study_visit_uid.
    """,
    response_model=clinical_mdr_api.models.study_selections.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no visit for the study provided.",
        },
        500: _generic_descriptions.ERROR_500,
    },
)
# pylint: disable=unused-argument
def get_study_visit(
    uid: str = studyUID,
    study_visit_uid: str = study_visit_uid_description,
    current_user_id: str = Depends(get_current_user_id),
    study_value_version: str | None = _generic_descriptions.STUDY_VALUE_VERSION_QUERY,
) -> clinical_mdr_api.models.study_selections.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.find_by_uid(
        study_uid=uid, uid=study_visit_uid, study_value_version=study_value_version
    )


@router.get(
    "/studies/{uid}/get-amount-of-visits-in-epoch/{study_epoch_uid}",
    dependencies=[rbac.STUDY_READ],
    summary="Counts amount of visits in a specified study epoch",
    description="""
State before:
- Study must exist.

Business logic:
 - Counts amount of visits in a specified study epoch.

State after:
 - no change.

Possible errors:
 - Invalid study_uid.
 - Invalid study_epoch_uid.
    """,
    response_model=int,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_amount_of_visits_in_given_epoch(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
    study_epoch_uid: str = Path(..., description="The unique uid of the study epoch"),
) -> int:
    service = StudyVisitService(current_user_id)
    return service.get_amount_of_visits_in_given_epoch(
        study_uid=uid, study_epoch_uid=study_epoch_uid
    )


@router.get(
    "/studies/{uid}/global-anchor-visit",
    dependencies=[rbac.STUDY_READ],
    summary="List global anchor visit study visits for selected study referenced by 'uid' ",
    description="""
State before:
- Study must exist.

Business logic:
 - Looks for a study visit that is a global anchor visit.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.
    """,
    response_model=clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit
    | None,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_global_anchor_visit(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit | None:
    service = StudyVisitService(current_user_id)
    return service.get_global_anchor_visit(study_uid=uid)


@router.get(
    "/studies/{uid}/anchor-visits-in-group-of-subvisits",
    dependencies=[rbac.STUDY_READ],
    summary="List all anchor visits for group of subvisits for selected study referenced by 'uid' ",
    description="""
State before:
- Study must exist.

Business logic:
 - Looks for a study visits that are anchor visits in a group of subvisits.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.
    """,
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_anchor_visits_in_group_of_subvisits(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> list[clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_anchor_visits_in_a_group_of_subvisits(study_uid=uid)


@router.get(
    "/studies/{uid}/anchor-visits-for-special-visit",
    dependencies=[rbac.STUDY_READ],
    summary="List all visits that can be anchor visits for special visit for a selected study referenced by 'uid' ",
    description="""
State before:
- Study must exist.

Business logic:
 - Looks for a study visits that can be anchor visits for a special visit.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.
    """,
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
def get_anchor_visits_for_special_visit(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> list[clinical_mdr_api.models.study_selections.study_visit.SimpleStudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_anchor_for_special_visit(study_uid=uid)


@router.post(
    "/studies/{uid}/consecutive-visit-groups",
    dependencies=[rbac.STUDY_WRITE],
    summary="Assign consecutive visit groups for specific study visits for a selected study referenced by 'uid' ",
    description="""
State before:
- Study must exist.

Business logic:
 - Assigns consecutive visit groups for specified study visits.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.
    """,
    response_model=list[
        clinical_mdr_api.models.study_selections.study_visit.StudyVisit
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def assign_consecutive_visit_group_for_selected_study_visit(
    uid: str = studyUID,
    consecutive_visit_group_input: clinical_mdr_api.models.study_selections.study_visit.VisitConsecutiveGroupInput = Body(
        description="The properties needed to assign visits into consecutive visit group",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> list[clinical_mdr_api.models.study_selections.study_visit.StudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.assign_visit_consecutive_group(
        study_uid=uid,
        visits_to_assign=consecutive_visit_group_input.visits_to_assign,
        overwrite_visit_from_template=consecutive_visit_group_input.overwrite_visit_from_template,
    )


@router.delete(
    "/studies/{uid}/consecutive-visit-groups/{consecutive_visit_group_name}",
    dependencies=[rbac.STUDY_WRITE],
    summary="Remove consecutive visit group specified by consecutive-visit-group-name for a selected study referenced by 'uid' ",
    description="""
State before:
- Study must exist.

Business logic:
 - Removes consecutive-visit-group.

State after:
 - no change.

Possible errors:
 - Invalid study-uid.
    """,
    response_model=None,
    status_code=204,
    responses={
        404: _generic_descriptions.ERROR_404,
        500: _generic_descriptions.ERROR_500,
    },
)
@decorators.validate_if_study_is_not_locked("uid")
def remove_consecutive_group(
    uid: str = studyUID,
    consecutive_visit_group_name: str = Path(
        ...,
        description="The name of the consecutive-visit-group that is removed",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyVisitService(current_user_id)
    service.remove_visit_consecutive_group(
        study_uid=uid, consecutive_visit_group=consecutive_visit_group_name
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
