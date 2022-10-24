from typing import Any, Optional, Sequence

from fastapi import Body, Depends, Path, Query, Request, Response, status
from pydantic.types import Json

from clinical_mdr_api.models import study_epoch
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.services.study_epoch import StudyEpochService
from clinical_mdr_api.services.study_visit import StudyVisitService

studyUID = Path(None, description="The unique id of the study.")

studyEpochUidDescription = Path(None, description="The unique id of the study epoch.")

studyVisitUidDescription = Path(None, description="The unique id of the study visit.")

"""
    API endpoints to study epochs
"""


@router.get(
    "/{uid}/study-epochs",
    summary="List all study epochs currently selected for the study.",
    description="""
State before:
 - Study must exist.
 
Business logic:
 - By default (no study status is provided) list all study epochs for the study uid in status draft. If the study not exist in status draft then return the study epochs for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study epoch for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the study epochs for the specific locked study version is returned.
 - Indicate by an boolean variable if the study epoch can be updated (if the selected study is in status draft).  
 - Indicate by an boolean variable if all expected selections have been made for each study epochs, or some are missing.
   - e.g. duration time unit must is expected.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.""",
    response_model=CustomPage[study_epoch.StudyEpoch],
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
            "order",
            "epochName",
            "epochType",
            "epochSubType",
            "startRule",
            "endRule",
            "description",
            "studyVisitCount",
            "colorHash",
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
    request: Request,  # request is actually required by the allow_exports decorator
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
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[study_epoch.StudyEpoch]:
    service = StudyEpochService(current_user_id)

    all_items = service.get_all_epochs(
        study_uid=uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/{uid}/study-epochs/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
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
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyEpochService(author=current_user_id)
    return service.get_distinct_values_for_header(
        study_uid=uid,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}/study-epochs/{studyEpochUid}",
    summary="List all definitions for a specific study epoch",
    description="""
State before:
 - Study and study epoch must exist
 
Business logic:
 - By default (no study status is provided) list all details for specified study epoch for the study uid in status draft. If the study not exist in status draft then return the study epochs for the study in status released. If the study uid only exist as deleted then this is returned.
 - If a specific study status parameter is provided then return study epochs for this study status.
 - If the locked study status parameter is requested then a study version should also be provided, and then the specified study epoch  for the specific locked study version is returned.
 - Indicate by an boolean variable if the study epoch can be updated (if the selected study is in status draft).
 - Indicate by an boolean variable if all expected selections have been made for each study epoch , or some are missing.
 - e.g. epoch level, minimum one timeframe and one unit is expected.
 - Indicate by an boolean variable if the selected epoch is available in a newer version.
 
State after:
 - no change
 
Possible errors:
 - Invalid study-uid or studyEpoch Uid.
    """,
    response_model=study_epoch.StudyEpoch,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no epoch for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get_study_epoch(
    uid: str = studyUID,
    studyEpochUid: str = studyEpochUidDescription,
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyEpochService(current_user_id)
    return service.find_by_uid(studyEpochUid)


@router.get(
    "/{uid}/study-epochs/{studyEpochUid}/audit-trail/",
    summary="List audit trail related to definition of a specific study epoch",
    description="""
State before:
 - Study and study epochs must exist.

Business logic:
 - List a specific entry in the audit trail related to the specified study epoch for the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=Sequence[study_epoch.StudyEpochVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the visit for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_study_epoch_audit_trail(
    uid: str = studyUID,
    studyEpochUid: str = studyEpochUidDescription,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[study_epoch.StudyEpochVersion]:
    service = StudyEpochService(current_user_id)
    return service.audit_trail(uid, studyEpochUid, uid)


@router.get(
    "/{uid}/study-epoch/audit-trail/",
    summary="List audit trail related to all study epochs within the specified study-uid",
    description="""
State before:
 - Study and study epoch must exist.

Business logic:
 - List all study epoch audit trail within the specified study-uid.
 - If the released or a locked version of the study is selected then only entries up to the time of the study release or lock is included.

State after:
 - no change.
 
Possible errors:
 - Invalid study-uid.
     """,
    response_model=Sequence[study_epoch.StudyEpochVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the provided study.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_study_epochs_all_audit_trail(
    uid: str = studyUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[study_epoch.StudyEpochVersion]:
    service = StudyEpochService(current_user_id)
    return service.audit_trail_all_epochs(uid)


@router.post(
    "/{uid}/study-epochs",
    summary="Add a study epoch to a study",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Add a study epoch to a study based on selection of an Epoch CT Term.
- Update the order value of all other epochs for this study to be consecutive.

State after:
 - Epoch is added as study epoch to the study.
 - Added new entry in the audit trail for the creation of the study-epoch.
 
Possible errors:
 - Invalid study-uid or Epoch CT Term uid.
    """,
    response_model=study_epoch.StudyEpoch,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - There already exists a selection of the epoch",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_epoch_create(
    uid: str = studyUID,
    selection: study_epoch.StudyEpochCreateInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyEpochService(current_user_id)
    return service.create(study_uid=uid, study_epoch_input=selection)


@router.post(
    "/{uid}/study-epochs/preview",
    summary="Preview a study epoch",
    response_model=study_epoch.StudyEpoch,
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
def post_preview_epoch(
    uid: str = studyUID,
    selection: study_epoch.StudyEpochCreateInput = Body(
        None, description="Related parameters of the epoch that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyEpochService(current_user_id)
    return service.preview(study_uid=uid, study_epoch_input=selection)


@router.delete(
    "/{uid}/study-epochs/{studyEpochUid}",
    summary="Delete a study epoch.",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - study-epoch-uid must exist. 

Business logic:
 - Remove specified study-epoch from the study.
 - Reference to the study-epoch should still exist in the the audit trail.
- Update the order value of all other epochs for this study to be consecutive.

State after:
- Study epochis deleted from the study, but still exist as a node in the database with a reference from the audit trail.
- Added new entry in the audit trail for the deletion of the study-epoch.
 
Possible errors:
- Invalid study-uid or studyEpochUid.
    """,
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - the study or epoch does not exist.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_study_epoch(
    uid: str = studyUID,
    studyEpochUid: str = studyEpochUidDescription,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyEpochService(author=current_user_id)

    service.delete(study_uid=uid, study_epoch_uid=studyEpochUid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{uid}/study-epochs/{studyEpochUid}/order/{new_order}",
    summary="Change display order of study epoch",
    description="""
State before:
 - Study must exist and study status must be in draft.
 - studyEpochUid must exist. 
 - Old order number must match current order number in database for study epoch.

Business logic:
 - Old order number must match existing order number in the database for specified study epoch.
 - New order number must be increased or decreased with one.
 - If order number is decreased with 1, then the old order number must be > 1 and a preceding study epoch must exist (the specified study epoch cannot be the first on the list).
   - The specified study epoch get the order number set to be the new order number and the preceding study epoch get the order number to be the old order number.
 - If order number is increased with 1, then a following study epoch must exist (the specified study epoch cannot be the last on the list).
   - The specified study epoch get the order number set to be the new order number and the following study epoch  get the order number to be the old order number.

State after:
 - Order number for specified study epoch is updated to new order number.
 - Note this will change order on either the preceding or following study epoch as well.
 - Added new entry in the audit trail for the re-ordering of the study epoch.

Possible errors:
 - Invalid study-uid, studyEpochUid
 - Old order number do not match current order number in database.
 - New order number not an increase or decrease of 1
 - Decrease order number for the first study epoch on the list
 - Increase order number for the last study epoch on the list
    """,
    response_model=study_epoch.StudyEpoch,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no selection between the study and epoch to reorder.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def patch_reorder(
    uid: str = studyUID,
    studyEpochUid: str = studyEpochUidDescription,
    new_order: int = 0,
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyEpochService(current_user_id)
    return service.reorder(study_epoch_uid=studyEpochUid, new_order=new_order)


@router.patch(
    "/{uid}/study-epochs/{studyEpochUid}",
    summary="Edit a study epoch",
    description="""
State before:
 - Study must exist and study status must be in draft.

Business logic:
 - Same logic applies as for selecting or creating an study epoch (see two POST statements for /study-epochs)
 - Update the order value of all other epochs for this study to be consecutive.

State after:
 - Epoch is added as study epoch to the study.
 - This PATCH method can cover cover two parts:

 - Added new entry in the audit trail for the update of the study-epoch.

Possible errors:
 - Invalid study-uid or studyEpochUid .
    """,
    response_model=study_epoch.StudyEpoch,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - There exist no study or epoch .",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def patch_update_epoch(
    uid: str = studyUID,
    studyEpochUid: str = studyEpochUidDescription,
    selection: study_epoch.StudyEpochEditInput = Body(
        None, description="Related parameters of the selection that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> study_epoch.StudyEpoch:
    service = StudyEpochService(current_user_id)
    return service.edit(study_epoch_uid=studyEpochUid, study_epoch_input=selection)


@router.get(
    "/epochs/allowed-configs",
    summary="Returns all allowed config sets",
    response_model=Sequence[study_epoch.StudyEpochTypes],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_configs(
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[study_epoch.StudyEpoch]:
    service = StudyEpochService(current_user_id)
    return service.get_allowed_configs()


"""
    API endpoints to study visits
"""


@router.get(
    "/{uid}/allowed-consecutive-groups",
    summary="Returns all consecutive groups",
    response_model=Sequence[str],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_consecutive_groups(
    uid: str = studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[study_epoch.StudyEpoch]:
    service = StudyVisitService(current_user_id)
    return service.get_consecutive_groups(uid)
