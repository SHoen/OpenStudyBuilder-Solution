from typing import Sequence

from fastapi import APIRouter, Body, Depends, Path, Response, status

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.brand import BrandService

router = APIRouter()

BrandUID = Path(None, description="The unique id of brand")
Service = BrandService


@router.get(
    "",
    summary="Returns all brands.",
    response_model=Sequence[models.Brand],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_brands(
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[models.Brand]:
    return Service(current_user_id).get_all_brands()


@router.get(
    "/{uid}",
    summary="Returns the brand identified by the specified 'uid'.",
    response_model=models.Brand,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_brand(
    uid: str = BrandUID,
    current_user_id: str = Depends(get_current_user_id),
) -> models.Brand:
    return Service(current_user_id).get_brand(uid)


@router.post(
    "",
    summary="Creates a new brand.",
    response_model=models.Brand,
    status_code=201,
    responses={
        201: {"description": "Created - The brand was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    brand_create_input: models.BrandCreateInput = Body(
        None, description="Related parameters of the brand that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.Brand:
    return Service(current_user_id).create(brand_create_input)


@router.delete(
    "/{uid}",
    summary="Deletes the brand identified by 'uid'.",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The item was successfully deleted."},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete(
    uid: str = BrandUID, current_user_id: str = Depends(get_current_user_id)
) -> None:
    Service(current_user_id).delete(uid)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
