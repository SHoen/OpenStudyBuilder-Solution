from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from fastapi.param_functions import Body

from clinical_mdr_api import models
from clinical_mdr_api.domain_repositories.models.criteria import CriteriaValue
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study import Study
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.routers import decorators
from clinical_mdr_api.services.criteria import CriteriaService

router = APIRouter()

Service = CriteriaService

# Argument definitions
CriteriaUID = Path(None, description="The unique id of the criteria.")


@router.get(
    "",
    summary="Returns all final versions of criteria referenced by any study.",
    response_model=List[models.Criteria],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","objective","criteriaTemplate","criteria","startDate","endDate","status","version","changeDescription","userInitials"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","Objective","First [ComparatorIntervention]","First Intervention","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
"""
                },
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
                "text/xml": {
                    "example": """
<?xml version="1.0" encoding="UTF-8" ?>
<root>
    <data type="list">
        <item type="dict">
            <library type="str">Sponsor</library>
            <uid type="str">682d7003-8dcc-480d-b07b-878e659b8697</uid>
            <objective type="str">Test template new [glucose metabolism] [MACE+] totot</objective>
            <criteriaTemplate type="str">Criteria using [Activity] and [Indication]</criteriaTemplate>
            <criteria type="str">Criteria using [body weight] and [type 2 diabetes]</criteria>
            <startDate type="str">2020-11-26T13:43:23.000Z</startDate>
            <endDate type="str"></endDate>
            <status type="str">Draft</status>
            <version type="str">0.2</version>
            <changeDescription type="str">Changed indication</changeDescription>
            <userInitials type="str">TODO Initials</userInitials>
        </item>
    </data>
</root>
"""
                },
            }
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "uid",
            "objective=objective.name",
            "criteriaTemplate=criteriaTemplate.name",
            "criteria=name",
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
    current_user_id: str = Depends(get_current_user_id),
):
    return CriteriaService(current_user_id).get_releases_referenced_by_any_study()


@router.get(
    "/{uid}",
    summary="Returns the latest/newest version of a specific criteria identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=Optional[models.Criteria],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get(
    uid: str = CriteriaUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified, the latest/newest representation of the criteria at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is ommitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the criteria in that status is returned (if existent). "
        "This may be particularly useful if the criteria has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the criteria in that version is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    if atSpecifiedDateTime is not None or status is not None or version is not None:
        raise NotImplementedError(
            "TODO: support for at_specified_date, status and version parameters not implemented."
        )
    return CriteriaService(current_user_id).get_by_uid(uid=uid)  # type: ignore


@router.get(
    "/get-by-name/{name}",
    summary="Returns the latest/newest version of a specific criteria identified by 'name'.",
    description="Gets an object by name - uses LATEST_DRAFT and LATEST_FINAL relations",
    response_model=Optional[models.Criteria],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'name' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_by_name(name: str, current_user_id: str = Depends(get_current_user_id)):
    return CriteriaService(current_user_id).find_by(name=name)  # type: ignore


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific criteria identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=List[models.CriteriaVersion],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_versions(
    uid: str = CriteriaUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).get_version_history(uid=uid)


@router.patch(
    "/{uid}",
    summary="Updates the criteria identified by 'uid'.",
    description="""This request is only valid if the criteria
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.
""",
    response_model=models.Criteria,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The criteria had been in 'Final' status before.\n"
            "- The provided list of parameters is invalid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The criteria does already exist.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = CriteriaUID,
    criteria: models.CriteriaEditInput = Body(
        None,
        description="The new parameter values for the criteria including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).edit_draft(uid, criteria)


@router.post(
    "/{uid}/approve",
    summary="Approves the criteria identified by 'uid'.",
    description="""This request is only valid if the criteria
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.Criteria,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The library does not allow to approve criteria.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = CriteriaUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).approve(uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the criteria identified by 'uid'.",
    description="""This request is only valid if the criteria
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.Criteria,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = CriteriaUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the criteria identified by 'uid'.",
    description="""This request is only valid if the criteria
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.Criteria,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = CriteriaUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).reactivate_retired(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the criteria identified by 'uid'.",
    description="""This request is only valid if \n
* the criteria is in 'Draft' status and
* the criteria has never been in 'Final' status and
* the criteria belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The criteria was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The criteria is not in draft status.\n"
            "- The criteria was already in final state or is in use.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An criteria with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete(uid: str = CriteriaUID, current_user_id: str = Depends(get_current_user_id)):
    Service(current_user_id).soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


@router.get(
    "/{uid}/studies",
    summary="",
    description="",
    response_model=List[Study],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The criteria with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_studies(
    uid: str = CriteriaUID,
    current_user_id: str = Depends(get_current_user_id),
    fields: Optional[str] = Query(
        default=None,
        description="Parameter specifies which parts of the whole Study Definition representation to retrieve. In"
        " the form of comma separated name of the fields prefixed by (optional) `+` "
        " if the client wishes"
        " to retrieve the field or `-` if the client wants to skip the field."
        " If not specified identification metadata and version metadata are retrieved."
        " If value starts with `+` or `-` above default is extended or reduced by the specified fields"
        " otherwise (if not started with `+` or `-`) provided fields specification"
        " replaces the default. Currently supported fields are"
        " `currentMetadata.identificationMetadata`, `currentMetadata.highLevelStudyDesign`"
        " , `currentMetadata.studyPopulation` and `currentMetadata.studyIntervention`"
        " , `currentMetadata.studyDescription`.",
    ),
):
    return Service(current_user_id).get_referencing_studies(
        uid=uid, node_type=CriteriaValue, fields=fields
    )


# TODO this criteria potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{uid}/parameters",
    summary="Returns all template parameters available for the criteria identified by 'uid'. Includes the available values per parameter.",
    description="""Returns all template parameters used in the criteria template
that is the basis for the criteria identified by 'uid'. 
Includes the available values per parameter.

The returned parameters are ordered
0. as they occur in the criteria template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    response_model=List[models.TemplateParameter],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_parameters(
    uid: str = Path(None, description="The unique id of the criteria."),
    current_user_id: str = Depends(get_current_user_id),
):
    return CriteriaService(current_user_id).get_parameters(uid)
