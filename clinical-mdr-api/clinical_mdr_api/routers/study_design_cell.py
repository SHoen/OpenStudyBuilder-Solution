from typing import Sequence

from fastapi import Body, Depends, Response, status

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.routers import study_router as router
from clinical_mdr_api.routers import utils
from clinical_mdr_api.services.study_design_cell import StudyDesignCellService


@router.get(
    "/{uid}/study-design-cells",
    summary="List all study design cells currently defined for the study",
    response_model=Sequence[models.StudyDesignCell],
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
def get_all_design_cells(
    uid: str = utils.studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyDesignCell]:
    service = StudyDesignCellService(author=current_user_id)
    cells = service.get_all_design_cells(study_uid=uid)
    return cells


@router.post(
    "/{uid}/study-design-cells",
    summary="Add a study design cell to a study",
    response_model=models.StudyDesignCell,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - A study design cell already exists for selected study arm and epoch",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Study, study arm or study epoch is not found with the passed 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post_new_design_cell_create(
    uid: str = utils.studyUID,
    selection: models.StudyDesignCellCreateInput = Body(
        None, description="Related parameters of the design cell that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyDesignCell:
    service = StudyDesignCellService(author=current_user_id)
    return service.create(study_uid=uid, design_cell_input=selection)


@router.patch(
    "/{uid}/study-design-cells/{studydesigncelluid}",
    summary="Update a study design cell",
    description="""
    The StudyDesignCell has the following properties:
        -StudyArm 
        -StudyBranchArm 
        -StudyEpoch 
        -StudyElement
        -Transition_rule
    Patching properties has different dependencies, to patch:
        -StudyArm
            -StudyArm has to exists
            -if the StudyDesignCell already has a StudyBranchArm then the StudyBranchArm has to be set as null on the payload.
        -StudyBranchArm
            -StudyBranchArm has to exists
            -if the StudyDesignCell already has a StudyArm then it will be disconnected from PREVIOUS StudyArm and switched to the NEW StudyBranchArm
        -StudyElement
            -StudyElement has to exists
        -StudyEpoch
            -StudyEpoch has to exists
        -Transition_rule
            -no dependencies, is just a string field
     """,
    response_model=None,
    response_model_exclude_unset=True,
    status_code=204,
    responses={
        200: {
            "description": "No content - The study design cell was successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study design cell with the specified 'studydesigncelluid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
#  pylint: disable=unused-argument
def edit_design_cell(
    uid: str = utils.studyUID,
    studydesigncelluid: str = utils.studyDesignCellUid,
    selection: models.StudyDesignCellEditInput = Body(
        None, description="Related parameters of the selection that shall be updated."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudySelectionActivity:
    service = StudyDesignCellService(author=current_user_id)
    service.patch(
        study_uid=uid,
        design_cell_update_input=selection,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{uid}/study-design-cells/{studydesigncelluid}",
    summary="Delete a study design cell",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The selection was successfully deleted."},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the design cell and the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_design_cell(
    uid: str = utils.studyUID,
    studydesigncelluid: str = utils.studyDesignCellUid,
    current_user_id: str = Depends(get_current_user_id),
):
    service = StudyDesignCellService(author=current_user_id)
    service.delete(study_uid=uid, design_cell_uid=studydesigncelluid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/study-design-cells/audit-trail/",
    summary="List full audit trail related to definition of all study design cells.",
    description="""
The following values should be returned for all study design cells:
- dateTime
- userInitials
- action
- activity
- order
    """,
    response_model=Sequence[models.StudyDesignCellVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_design_cells_audit_trail(
    uid: str = utils.studyUID, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyDesignCellVersion]:
    service = StudyDesignCellService(author=current_user_id)
    return service.get_all_design_cells_audit_trail(study_uid=uid)


@router.get(
    "/{uid}/study-design-cells/{studydesigncelluid}/audit-trail/",
    summary="List audit trail related to definition of a specific study design cell.",
    response_model=Sequence[models.StudyDesignCellVersion],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - there exist no selection of the design cell for the study provided.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_specific_schedule_audit_trail(
    uid: str = utils.studyUID,
    studydesigncelluid: str = utils.studyDesignCellUid,
    current_user_id: str = Depends(get_current_user_id),
) -> models.StudyDesignCellVersion:
    service = StudyDesignCellService(author=current_user_id)
    return service.get_specific_selection_audit_trail(
        study_uid=uid, design_cell_uid=studydesigncelluid
    )


@router.post(
    "/{uid}/study-design-cells/batch",
    summary="Batch operations (create, delete) for study design cells",
    response_model=Sequence[models.StudyDesignCellBatchOutput],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def design_cell_batch_operations(
    uid: str = utils.studyUID,
    operations: Sequence[models.StudyDesignCellBatchInput] = Body(
        None, description="List of operations to perform"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.StudyDesignCellBatchOutput]:
    service = StudyDesignCellService(author=current_user_id)
    return service.handle_batch_operations(uid, operations)


@router.get(
    "/{uid}/study-design-cells/arm/{armUid}",
    summary="""List all study desing-cells currently selected for study with provided uid that are connected to an StudyArm with armUid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study desing-cells for the study uid in status draft. If the study not exist in status draft then return the study desing-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study desing-cell for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study desing-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study desing-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study desing-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=Sequence[models.StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_desing_cells_connected_arm(
    uid: str, armUid: str, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyDesignCell]:
    service = StudyDesignCellService(author=current_user_id)
    return service.get_all_selection_within_arm(study_uid=uid, study_arm_uid=armUid)


@router.get(
    "/{uid}/study-design-cells/branch-arm/{branchArmUid}",
    summary="""List all study desing-cells currently selected for study with provided
    uid that are connected to an StudyBranchArm with branchArmUid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study desing-cells for the
     study uid in status draft. If the study not exist in status draft then return
     the study desing-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study desing-cell for this study status.
    - If the locked study status parameter is requested then a study version should
    also be provided, and then the study desing-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study desing-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study desing-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=Sequence[models.StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_desing_cells_connected_branch_arm(
    uid: str, branchArmUid: str, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyDesignCell]:
    service = StudyDesignCellService(author=current_user_id)
    return service.get_all_selection_within_branch_arm(
        study_uid=uid, study_branch_arm_uid=branchArmUid
    )


@router.get(
    "/{uid}/study-design-cells/study-epochs/{epochUid}",
    summary="""List all study desing-cells currently selected for study with provided uid that are connected to an StudyEpoch with epochUid""",
    description="""
    State before:
    - Study must exist.
     
    Business logic:
     - By default (no study status is provided) list all study desing-cells for the study uid in status draft. If the study not exist in status draft then return the study desing-cells for the study in status released. If the study uid only exist as deleted then this is returned.
     - If a specific study status parameter is provided then return study desing-cell for this study status.
    - If the locked study status parameter is requested then a study version should also be provided, and then the study desing-cells for the specific locked study version is returned.
    - Indicate by a boolean variable if the study desing-cell can be updated (if the selected study is in status draft).  
    - Indicate by a boolean variable if all expected selections have been made for each study desing-cells, or some are missing.


    State after:
    - no change.
     
    Possible errors:
    - Invalid study-uid.
""",
    response_model=Sequence[models.StudyDesignCell],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_selected_desing_cells_connected_epoch(
    uid: str, epochUid: str, current_user_id: str = Depends(get_current_user_id)
) -> Sequence[models.StudyDesignCell]:
    service = StudyDesignCellService(author=current_user_id)
    return service.get_all_selection_within_epoch(
        study_uid=uid, study_epoch_uid=epochUid
    )
