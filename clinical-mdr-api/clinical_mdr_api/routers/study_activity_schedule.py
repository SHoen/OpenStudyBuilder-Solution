from typing import Sequence

from fastapi import Body, Depends, Response, status

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers import utils
from clinical_mdr_api.services.study_activity_schedule import (
    StudyActivityScheduleService,
)


@router.get(
    "/{uid}/study-activity-schedules",
    summary="List all study activity schedules currently defined for the study",
    response_model=Sequence[models.StudyActivitySchedule],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there is no study with the given uid.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_activities(
    uid: str = utils.studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyActivitySchedule]:
    service = StudyActivityScheduleService(author=current_user_id)
    return service.get_all_schedules(study_uid=uid)


@router.post(
    "/{uid}/study-activity-schedules",
    summary="Add a study activity schedule to a study",
    response_model=models.StudyActivitySchedule,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - A study activity schedule already exists for selected study activity and visit",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study activity or study visit is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_activity_schedule_create(
    uid: str = utils.studyUID,
    selection: models.StudyActivityScheduleCreateInput = Body(
        None, description="Related parameters of the schedule that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyActivitySchedule:
    service = StudyActivityScheduleService(author=current_user_id)
    return service.create(study_uid=uid, schedule_input=selection)


@router.delete(
    "/{uid}/study-activity-schedules/{studyactivitiescheduleuid}",
    summary="Delete a study activity schedule",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the activity schedule and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_activity_schedule(
    uid: str = utils.studyUID,
    studyactivitiescheduleuid: str = utils.studyActivityScheduleUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyActivityScheduleService(author=current_user_id)
    service.delete(study_uid=uid, schedule_uid=studyactivitiescheduleuid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/study-activity-schedules/audit-trail/",
    summary="List full audit trail related to definition of all study activity schedules.",
    description="""
The following values should be returned for all study activities:
- dateTime
- userInitials
- action
- activity
- order
    """,
    response_model=Sequence[models.StudyActivityScheduleHistory],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_schedules_audit_trail(
    uid: str = utils.studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyActivityScheduleHistory]:
    service = StudyActivityScheduleService(author=current_user_id)
    return service.get_all_schedules_audit_trail(study_uid=uid)


@router.post(
    "/{uid}/study-activity-schedules/batch",
    summary="Batch operations (create, delete) for study activity schedules",
    response_model=Sequence[models.StudyActivityScheduleBatchOutput],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def activity_schedule_batch_operations(
    uid: str = utils.studyUID,
    operations: Sequence[models.StudyActivityScheduleBatchInput] = Body(
        None, description="List of operation to perform"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudyActivityScheduleBatchOutput]:
    service = StudyActivityScheduleService(author=current_user_id)
    return service.handle_batch_operations(uid, operations)
