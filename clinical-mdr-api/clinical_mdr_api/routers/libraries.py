"""Objective templates router."""

from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query

from clinical_mdr_api import models
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services import libraries as service

router = APIRouter()


@router.get(
    "",
    summary="Returns all libraries",
    response_model=List[models.Library],
)
# pylint: disable=unused-argument
def get_libraries(
    isEditable: Optional[bool] = Query(
        None,
        description="If specified, only those libraries are returned that are editable. \n"
        "Valid values are: 'true' or 'false'.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return service.get_libraries(isEditable)


@router.post(
    "",
    summary="Creates a new library.",
    response_model=models.Library,
    status_code=201,
    responses={
        201: {"description": "Created - The library was successfully created."},
    },
)
# pylint: disable=unused-argument
def create_library(
    library: models.Library = Body(None, description=""),
    current_user_id: str = Depends(get_current_user_id),
):
    return service.create(library.name, library.isEditable)
