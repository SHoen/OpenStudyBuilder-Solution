from datetime import datetime
from typing import Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status

from clinical_mdr_api.models.configuration import (
    CTConfigModel,
    CTConfigPatchInput,
    CTConfigPostInput,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.routers import decorators
from clinical_mdr_api.services.configuration import CTConfigService

router = APIRouter()

Service = CTConfigService


# Argument definitions
CodelistConfigUID = Path(None, description="The unique id of configuration.")


@router.get(
    "",
    summary="Returns all configurations in their latest/newest version.",
    response_model=Sequence[CTConfigModel],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"uid","name","startDate","endDate","status","version","changeDescription","userInitials"
"826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><uid type="str">e9117175-918f-489e-9a6e-65e0025233a6</uid><name type="str">Alamakota</name><startDate type="str">2020-11-19T11:51:43.000Z</startDate><status type="str">Draft</status><version type="str">0.2</version><changeDescription type="str">Test</changeDescription><userInitials type="str">TODO Initials</userInitials></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "startDate",
            "endDate",
            "status",
            "version",
            "changeDescription",
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
    request: Request,  # request is actually required by the allow_exports decorator
    service: Service = Depends(),
) -> Sequence[CTConfigModel]:
    return service.get_all()


@router.get(
    "/{uid}",
    summary="Returns the latest/newest version of a specific configuration identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=CTConfigModel,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": """Not Found - The configuration with the specified 'uid'
            (and the specified date/time, version and/or status) wasn't found.""",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_by_uid(
    uid: str = CodelistConfigUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified, the latest/newest representation of the configuration at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is ommitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the configuration in that status is returned (if existent). "
        "This may be particularly useful if the configuration has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the configuration is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    service: Service = Depends(),
) -> CTConfigModel:
    return service.get_by_uid(
        uid, version=version, status=status, at_specified_datetime=atSpecifiedDateTime
    )


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific configuration identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=Sequence[CTConfigModel],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"uid";"name";"startDate";"endDate";"status";"version";"changeDescription";"userInitials"
"826d80a7-0b6a-419d-8ef1-80aa241d7ac7";"First  [ComparatorIntervention]";"2020-10-22T10:19:29+00:00";;"Draft";"0.1";"Initial version";"NdSJ"
"""
                },
                "text/xml": {
                    "example": """
                    <?xml version="1.0" encoding="UTF-8" ?><root><data type="list"><item type="dict"><name type="str">Alamakota</name><startDate type="str">2020-11-19 11:51:43+00:00</startDate><endDate type="str">None</endDate><status type="str">Draft</status><version type="str">0.2</version><changeDescription type="str">Test</changeDescription><userInitials type="str">TODO Initials</userInitials></item><item type="dict"><name type="str">Alamakota</name><startDate type="str">2020-11-19 11:51:07+00:00</startDate><endDate type="str">2020-11-19 11:51:43+00:00</endDate><status type="str">Draft</status><version type="str">0.1</version><changeDescription type="str">Initial version</changeDescription><userInitials type="str">TODO user initials</userInitials></item></data></root>
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
            }
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The configuration with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "name",
            "startDate",
            "endDate",
            "status",
            "version",
            "changeDescription",
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
#  pylint: disable=unused-argument
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = CodelistConfigUID,
    service: Service = Depends(),
) -> Sequence[CTConfigModel]:
    return service.get_versions(uid)


@router.post(
    "",
    response_model=CTConfigModel,
    summary="Creates a new configuration in 'Draft' status.",
    description="""

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be set to '0.1'.

""",
    status_code=201,
    responses={
        201: {"description": "Created - The configuration was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration name is not valid.\n",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post(
    post_input: CTConfigPostInput = Body(
        None, description="The configuration that shall be created."
    ),
    service: Service = Depends(),
) -> CTConfigModel:
    return service.post(post_input)  # type: ignore


@router.patch(
    "/{uid}",
    summary="Updates the configuration identified by 'uid'.",
    description="""This request is only valid if the configuration
* is in 'Draft' status and

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

""",
    response_model=CTConfigModel,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in draft status.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The configuration with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch(
    uid: str = CodelistConfigUID,
    patch_input: CTConfigPatchInput = Body(
        None,
        description="The new content of the configuration including the change description.",
    ),
    service: Service = Depends(),
) -> CTConfigModel:
    return service.patch(uid, patch_input)


@router.post(
    "/{uid}/new-version",
    summary="Creates a new version of the configuration identified by 'uid'.",
    description="""This request is only valid if the configuration
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) 

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

""",
    response_model=CTConfigModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in final or retired status or has a draft status.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The  configuration with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def new_version(
    uid: str = CodelistConfigUID, service: Service = Depends()
) -> CTConfigModel:
    return service.new_version(uid)


@router.post(
    "/{uid}/approve",
    summary="Approves the configuration identified by 'uid'.",
    description="""This request is only valid if the configuration
* is in 'Draft' status

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=CTConfigModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in draft status.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The configuration with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = CodelistConfigUID, service: Service = Depends()
) -> CTConfigModel:
    return service.approve(uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the configuration identified by 'uid'.",
    description="""This request is only valid if the configuration
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=CTConfigModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The configuration with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = CodelistConfigUID, service: Service = Depends()
) -> CTConfigModel:
    return service.inactivate(uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the configuration identified by 'uid'.",
    description="""This request is only valid if the configuration
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=CTConfigModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The configuration with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    dependencies=[Depends(get_current_user_id)],
)
def reactivate(
    uid: str = CodelistConfigUID, service: Service = Depends()
) -> CTConfigModel:
    return service.reactivate(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the configuration identified by 'uid'.",
    description="""This request is only valid if \n
* the configuration is in 'Draft' status and
* the configuration has never been in 'Final' status.
""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The configuration was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The configuration is not in draft status.\n"
            "- The configuration was already in final state or is in use.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An configuration with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    dependencies=[Depends(get_current_user_id)],
)
def delete(uid: str = CodelistConfigUID, service: Service = Depends()) -> None:
    service.delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
