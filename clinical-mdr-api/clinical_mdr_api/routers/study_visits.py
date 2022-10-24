from typing import Any, List, Optional, Sequence

from fastapi import Body, Depends, Path, Query
from pydantic.types import Json
from starlette import status
from starlette.requests import Request
from starlette.responses import Response

import clinical_mdr_api.models
from clinical_mdr_api.models import study_epoch
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers.study_epochs import studyUID, studyVisitUidDescription
from clinical_mdr_api.services.study_visit import StudyVisitService


@router.get(
    "/{uid}/study-visits",
    summary="List all study visits currently defined for the study",
    description="""
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
    """,
    response_model=CustomPage[clinical_mdr_api.models.study_visit.StudyVisit],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "studyEpochUid",
            "studyEpochName",
            "visitTypeName",
            "visitContactModeName",
            "order",
            "uniqueVisitNumber",
            "visitName",
            "visitShortName",
            "studyDayLabel",
            "studyWeekLabel",
            "visitWindow",
            "timeReferenceName",
            "timeValue",
            "consecutiveVisitGroup",
            "showVisit",
            "description",
            "startRule",
            "endRule",
            "modifiedDate",
            "userInitials",
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
) -> CustomPage[clinical_mdr_api.models.study_visit.StudyVisit]:
    service = StudyVisitService(current_user_id)
    results = service.get_all_visits(
        study_uid=uid,
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
    "/{uid}/study-visits/headers",
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
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
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
    return StudyVisitService(current_user_id).get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-visits-references",
    summary="Returns all study visit references for study currently selected",
    response_model=Sequence[clinical_mdr_api.models.study_visit.StudyVisit],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_references(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[clinical_mdr_api.models.study_visit.StudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_all_references(study_uid=uid)


@router.post(
    "/{uid}/study-visits",
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
    response_model=clinical_mdr_api.models.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - The settings for visit are invalid",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study or visit is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_visit_create(
    uid: str = studyUID,
    selection: clinical_mdr_api.models.study_visit.StudyVisitCreateInput = Body(
        None, description="Related parameters of the visit that shalll be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> clinical_mdr_api.models.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.create(study_uid=uid, study_visit_input=selection)


@router.post(
    "/{uid}/study-visits/preview",
    summary="Preview a study visit",
    response_model=clinical_mdr_api.models.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_preview_visit(
    uid: str = studyUID,
    selection: clinical_mdr_api.models.study_visit.StudyVisitCreateInput = Body(
        None, description="Related parameters of the visit that shalll be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> clinical_mdr_api.models.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.preview(study_uid=uid, study_visit_input=selection)


@router.patch(
    "/{uid}/study-visits/{studyVisitUid}",
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
 - Invalid study-uid or studyVisitUidDescription .
    """,
    response_model=clinical_mdr_api.models.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no study or visit.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_update_visit(
    uid: str = studyUID,
    studyVisitUid: str = studyVisitUidDescription,
    selection: clinical_mdr_api.models.study_visit.StudyVisitEditInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyVisitService(current_user_id)
    return service.edit(
        study_uid=uid, study_visit_uid=studyVisitUid, study_visit_input=selection
    )


@router.delete(
    "/{uid}/study-visits/{studyVisitUid}",
    summary="Delete a study visit",
    description=""""
State before:
 - Study must exist and study status must be in draft.
 - studyVisitUid must exist. 

Business logic:
 - Remove specified study-visit from the study.
 - Reference to the study-visit should still exist in the the audit trail.
 - Simple concepts that are now unused should continue to be persisted in the database.

State after:
 - Study visit deleted from the study, but still exist as a node in the database with a reference from the audit trail.
 - Added new entry in the audit trail for the deletion of the study-visit .
 
Possible errors:
 - Invalid study-uid or studyVisitUid.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the visit and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_study_visit(
    uid: str = studyUID,
    studyVisitUid: str = studyVisitUidDescription,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyVisitService(current_user_id)
    service.delete(study_uid=uid, study_visit_uid=studyVisitUid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/study-visits/{studyVisitUid}/audit-trail/",
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
    response_model=Sequence[clinical_mdr_api.models.study_visit.StudyVisitVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the study visit for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get_study_visit_audit_trail(
    uid: str = studyUID,
    studyVisitUid: str = studyVisitUidDescription,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[clinical_mdr_api.models.study_visit.StudyVisitVersion]:
    service = StudyVisitService(current_user_id)
    return service.audit_trail(studyVisitUid, study_uid=uid)


@router.get(
    "/{uid}/study-visit/audit-trail/",
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
    response_model=Sequence[clinical_mdr_api.models.study_visit.StudyVisitVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the study visit for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_study_visits_all_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[clinical_mdr_api.models.study_visit.StudyVisitVersion]:
    service = StudyVisitService(current_user_id)
    return service.audit_trail_all_visits(study_uid=uid)


@router.get(
    "/{uid}/study-visits/{studyVisitUid}",
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
 - Invalid study-uid or studyVisitUid.
    """,
    response_model=clinical_mdr_api.models.study_visit.StudyVisit,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no visit for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get_study_visit(
    uid: str = studyUID,
    studyVisitUid: str = studyVisitUidDescription,
    current_user_id: str = Depends(get_current_user_id),
) -> clinical_mdr_api.models.study_visit.StudyVisit:
    service = StudyVisitService(current_user_id)
    return service.find_by_uid(studyVisitUid)


@router.get(
    "/study-visits/allowed-visit-types",
    summary="Returns all allowed Visit Types for specified epoch type",
    response_model=Sequence[
        clinical_mdr_api.models.study_visit.AllowedVisitTypesForEpochType
    ],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_allowed_visit_types_for_epoch_type(
    current_user_id: str = Depends(get_current_user_id),
    epoch_type_uid: str = Query(
        ...,
        description="The unique uid of the epoch type for which the "
        "allowed visit types should be returned",
    ),
    study_uid: str = Query(..., description="The unique uid of the study"),
) -> Sequence[clinical_mdr_api.models.study_visit.AllowedVisitTypesForEpochType]:
    service = StudyVisitService(current_user_id)
    return service.get_valid_visit_types_for_epoch_type(
        epoch_type_uid=epoch_type_uid, study_uid=study_uid
    )


@router.get(
    "/study-visits/allowed-time-references",
    summary="Returns all allowed time references for a study visit",
    response_model=Sequence[clinical_mdr_api.models.study_visit.AllowedTimeReferences],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_allowed_time_references_for_given_study(
    current_user_id: str = Depends(get_current_user_id),
    study_uid: str = Query(..., description="The unique uid of the study"),
) -> Sequence[clinical_mdr_api.models.study_visit.AllowedTimeReferences]:
    service = StudyVisitService(current_user_id)
    return service.get_allowed_time_references_for_study(study_uid=study_uid)


@router.get(
    "/{uid}/get-amount-of-visits-in-epoch/{studyEpochUid}",
    summary="Counts amount of visits in a specified study epoch",
    description="""
State before:
- Study must exist.

Business logic:
 - Counts amount of visits in a specified study epoch.

State after:
 - no change.

Possible errors:
 - Invalid studyUid.
 - Invalid studyEpochUid.
    """,
    response_model=int,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_amount_of_visits_in_given_epoch(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
    studyEpochUid: str = Path(..., description="The unique uid of the study epoch"),
) -> int:
    service = StudyVisitService(current_user_id)
    return service.get_amount_of_visits_in_given_epoch(
        study_uid=uid, study_epoch_uid=studyEpochUid
    )


@router.get(
    "/{uid}/global-anchor-visit",
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
    response_model=Optional[clinical_mdr_api.models.study_visit.SimpleStudyVisit],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_global_anchor_visit(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Optional[clinical_mdr_api.models.study_visit.SimpleStudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_global_anchor_visit(study_uid=uid)


@router.get(
    "/{uid}/anchor-visits-in-group-of-subvisits",
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
    response_model=Sequence[clinical_mdr_api.models.study_visit.SimpleStudyVisit],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_anchor_visits_in_group_of_subvisits(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[clinical_mdr_api.models.study_visit.SimpleStudyVisit]:
    service = StudyVisitService(current_user_id)
    return service.get_anchor_visits_in_a_group_of_subvisits(study_uid=uid)
