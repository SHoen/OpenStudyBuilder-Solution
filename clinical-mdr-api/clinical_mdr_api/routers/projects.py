from typing import Sequence

from fastapi import APIRouter, Body, Depends

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.project import ProjectService

router = APIRouter()


# Argument definitions
# ProjectUID = Path(
#     None, description="The unique id of the project.")


@router.get(
    "",
    summary="Returns all projects.",
    response_model=Sequence[models.Project],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_projects() -> Sequence[models.Project]:
    service = ProjectService()
    return service.get_all_projects()


@router.post(
    "",
    summary="Creates a new project.",
    response_model=models.Project,
    status_code=201,
    responses={
        201: {"description": "Created - The project was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    project_create_input: models.ProjectCreateInput = Body(
        None, description="Related parameters of the project that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.Project:
    service = ProjectService(user=current_user_id)
    return service.create(project_create_input)
