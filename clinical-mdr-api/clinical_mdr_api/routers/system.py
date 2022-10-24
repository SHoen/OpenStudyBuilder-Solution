"""System router."""

from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from clinical_mdr_api import models
from clinical_mdr_api.services import system as service

router = APIRouter()


@router.get(
    "/information",
    summary="Returns various information about this API (running version, etc.)",
    response_model=models.SystemInformation,
    status_code=200,
)
def get_system_information():
    return service.get_system_information()


@router.get(
    "/information/build-id",
    summary="Returns build id as plain text",
    response_class=PlainTextResponse,
    status_code=200,
)
def version_plain() -> str:
    return service.get_build_id()


@router.get(
    "/healthcheck",
    summary="Returns 200 OK status if the system is ready to serve requests",
    response_class=PlainTextResponse,
    status_code=200,
)
def healthcheck():
    return "OK"
