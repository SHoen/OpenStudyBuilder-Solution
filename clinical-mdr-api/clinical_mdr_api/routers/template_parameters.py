from typing import List

from fastapi import APIRouter, Depends, Query

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services import template_parameters as service

router = APIRouter()


@router.get(
    "",
    summary="Returns all template parameter available with samples of the available values.",
    description="The returned template parameter are ordered by\n" "0. name ascending",
    response_model=List[models.TemplateParameter],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get_all_template_parameters(current_user_id: str = Depends(get_current_user_id)):
    return service.get_all()


@router.get(
    "/{name}/values",
    summary="Return all values available for the given template parameter.",
    response_model=List[models.TemplateParameterValue],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
def get_template_parameter_values(
    name: str = Query(..., description="Name of the template parameter"),
    current_user_id: str = Depends(get_current_user_id),
):
    return service.get_template_parameter_values(name)
