"""Objective templates router."""

from datetime import datetime
from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.template_parameter import ComplexTemplateParameter
from clinical_mdr_api.models.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateCreateInput,
    TimeframeTemplateEditInput,
    TimeframeTemplateNameInput,
    TimeframeTemplateVersion,
    TimeframeTemplateWithCount,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.timeframe_templates import TimeframeTemplateService

router = APIRouter()

Service = TimeframeTemplateService

# Argument definitions
TimeframeTemplateUID = Path(
    None, description="The unique id of the timeframe template."
)

PARAMETERS_NOTE = """**Parameters in the 'name' property**:

The 'name' of an timeframe template may contain parameters, that can - and usually will - be replaced with
concrete values once an timeframe is created out of the timeframe template.

Parameters are referenced by simple strings in square brackets [] that match existing parameters defined in the MDR repository.

See the *[GET] /parameter-templates/* endpoint for available values.

The timeframe template will be linked to those parameters defined in the 'name' property.

You may use an arbitrary number of parameters and you may use the same parameter multiple times within the same timeframe template 'name'.

*Example*:

name='MORE TESTING of the superiority in the efficacy of [Intervention] with [Activity] and [Activity] in [Timeframe].'

'Intervention', 'Activity' and 'Timeframe' are parameters."""


@router.get(
    "",
    summary="Returns all timeframe templates in their latest/newest version.",
    response_model=CustomPage[TimeframeTemplate],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library","uid","name","startDate","endDate","status","version","changeDescription","userInitials"
"Sponsor","826d80a7-0b6a-419d-8ef1-80aa241d7ac7","First  [ComparatorIntervention]","2020-10-22T10:19:29+00:00",,"Draft","0.1","Initial version","NdSJ"
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
            "library=library.name",
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
def get_timeframe_templates(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Optional[str] = Query(
        None,
        description="If specified, only those timeframe templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the timeframe template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
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
    current_user_id: str = Depends(get_current_user_id),
) -> CustomPage[TimeframeTemplate]:
    data = Service(current_user_id).get_all(
        status=status,
        return_study_count=True,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )
    return CustomPage.create(
        items=data.items, total=data.total_count, page=pageNumber, size=pageSize
    )


@router.get(
    "/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=List[Any],
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
    current_user_id: str = Depends(get_current_user_id),
    status: Optional[str] = Query(
        None,
        description="If specified, only those objective templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the objective template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
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
):
    return Service(current_user_id).get_distinct_values_for_header(
        status=status,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Returns the latest/newest version of a specific timeframe template identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=TimeframeTemplateWithCount,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
# pylint: disable=unused-argument
# TODO: Should `atSpecifiedDateTime` query param be supported?
def get_timeframe_template(
    uid: str = TimeframeTemplateUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified, the latest/newest representation of the timeframe template at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is ommitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the timeframe template in that status is returned (if existent). "
        "This may be particularly useful if the timeframe template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the timeframe template in that version is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    return_instantiation_counts: Optional[bool] = Query(
        None, description="if specified counts data will be returned along object"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    if status is not None or version is not None:
        # TODO: retrieval by status and/or version not implemented
        raise NotImplementedError(
            "TODO: retrieval by status and/or version not implemented"
        )
    return Service(current_user_id).get_by_uid(
        uid, return_instantiation_counts=bool(return_instantiation_counts)
    )


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific timeframe template identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=Sequence[TimeframeTemplateVersion],
    status_code=200,
    responses={
        200: {
            "content": {
                "text/csv": {
                    "example": """
"library";"uid";"name";"startDate";"endDate";"status";"version";"changeDescription";"userInitials"
"Sponsor";"826d80a7-0b6a-419d-8ef1-80aa241d7ac7";"First  [ComparatorIntervention]";"2020-10-22T10:19:29+00:00";;"Draft";"0.1";"Initial version";"NdSJ"
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
            "description": "Not Found - The timeframe template with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "library=library.name",
            "name",
            "changeDescription",
            "status",
            "version",
            "startDate",
            "endDate",
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
def get_timeframe_template_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = TimeframeTemplateUID,
    current_user_id: str = Depends(get_current_user_id),
) -> Sequence[TimeframeTemplateVersion]:
    return Service(current_user_id).get_version_history(uid)


@router.get(
    "/{uid}/versions/{version}",
    summary="Returns a specific version of a specific timeframe template identified by 'uid' and 'version'.",
    description="**Multiple versions**:\n\n"
    "Technically, there can be multiple versions of the timeframe template with the same version number. "
    "This is due to the fact, that the version number remains the same when inactivating or reactivating an timeframe template "
    "(switching between 'Final' and 'Retired' status). \n\n"
    "In that case the latest/newest representation is returned.",
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' and 'version' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_timeframe_template_version(
    uid: str = TimeframeTemplateUID,
    version: str = Path(
        None,
        description="A specific version number of the timeframe template. "
        "The version number is specified in the following format: \\<major\\>.\\<minor\\> where \\<major\\> and \\<minor\\> are digits.\n"
        "E.g. '0.1', '0.2', '1.0', ...",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    return Service(current_user_id).get_specific_version(uid, version)


@router.post(
    "",
    summary="Creates a new timeframe template in 'Draft' status.",
    description="""This request is only valid if the timeframe template
* belongs to a library that allows creating (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The timeframe template will be linked to a library.

"""
    + PARAMETERS_NOTE,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {
            "description": "Created - The timeframe template was successfully created."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template name is not valid.\n"
            "- The library does not allow to create timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'libraryName' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_timeframe_template(
    timeframe_template: TimeframeTemplateCreateInput = (
        Body(None, description="The timeframe template that shall be created.")
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    # TODO: do something to allow static type analysis
    return Service(current_user_id).create(timeframe_template)


@router.patch(
    "/{uid}",
    summary="Updates the timeframe template identified by 'uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

Parameters in the 'name' property can only be changed if the timeframe template has never been approved.
Once the timeframe template has been approved, only the surrounding text (excluding the parameters) can be changed.

"""
    + PARAMETERS_NOTE,
    response_model=TimeframeTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The timeframe template name is not valid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The change of parameters of previously approved timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = TimeframeTemplateUID,
    timeframe_template: TimeframeTemplateEditInput = Body(
        None,
        description="The new content of the timeframe template including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    return Service(current_user_id).edit_draft(uid, timeframe_template)


@router.post(
    "/{uid}/new-version",
    summary="Creates a new version of the timeframe template identified by 'uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in final or retired status or has a draft status.\n"
            "- The timeframe template name is not valid.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    uid: str = TimeframeTemplateUID,
    timeframe_template: TimeframeTemplateEditInput = Body(
        None,
        description="The content of the timeframe template for the new 'Draft' version including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    return Service(current_user_id).create_new_version(uid, timeframe_template)


@router.post(
    "/{uid}/approve",
    summary="Approves the timeframe template identified by 'uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).
If timeframe template has any related objects status will not be updated but item will be extended with 
related item counts.
If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - there are timeframes created from template and cascade is false",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = TimeframeTemplateUID,
    cascade: bool = False,
    current_user_id: str = Depends(get_current_user_id),
) -> TimeframeTemplate:
    """
    Approves timeframe template. Fails with 409 if there is some timeframes created
    from this template and cascade is false
    """
    if not cascade:
        return Service(current_user_id).approve(uid=uid)
    return Service(current_user_id).approve_cascade(uid=uid)


@router.post(
    "/{uid}/approve_cascading",
    summary="Approves the timeframe template identified by 'uid'. Updates all related items",
    description="""This request is only valid if the timeframe template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve_cascading(
    uid: str = TimeframeTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> TimeframeTemplate:
    # TODO: do sth not to mislead static analysis
    return Service(current_user_id).approve_cascade(uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the timeframe template identified by 'uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = TimeframeTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> TimeframeTemplate:
    # TODO: do sth to make static code analysis work fine for this code
    return Service(current_user_id).inactivate_final(uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the timeframe template identified by 'uid'.",
    description="""This request is only valid if the timeframe template
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=TimeframeTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The timeframe template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = TimeframeTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> TimeframeTemplate:
    # TODO: do sth to allow for static code analysis of this code
    return Service(current_user_id).reactivate_retired(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the timeframe template identified by 'uid'.",
    description="""This request is only valid if \n
* the timeframe template is in 'Draft' status and
* the timeframe template has never been in 'Final' status and
* the timeframe template has no references to any timeframes and
* the timeframe template belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The timeframe template was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The timeframe template is not in draft status.\n"
            "- The timeframe template was already in final state or is in use.\n"
            "- The library does not allow to delete timeframe templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An timeframe template with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_timeframe_template(
    uid: str = TimeframeTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> None:
    Service(current_user_id).soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


# TODO this endpoint potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{uid}/parameters",
    summary="Returns all parameters used in the timeframe template identified by 'uid'. Includes the available values per parameter.",
    description="""The returned parameters are ordered
0. as they occur in the timeframe template

Per parameter, the parameter.values are ordered by
0. value.name ascending

Note that parameters may be used multiple times in templates.
In that case, the same parameter (with the same values) is included multiple times in the response.
    """,
    response_model=Sequence[ComplexTemplateParameter],
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_parameters(
    uid: str = Path(None, description="The unique id of the timeframe template."),
    study_uid: Optional[str] = Query(
        None,
        description="if specified only valida parameters for a given study will be returned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).get_parameters(uid, study_uid=study_uid)


@router.post(
    "/pre-validate",
    summary="Validates the content of an timeframe template without actually processing it.",
    description="""Be aware that - even if this request is accepted - there is no guarantee that
a following request to e.g. *[POST] /timeframe-templates* or *[PATCH] /timeframe-templates/{uid}*
with the same content will succeed.

"""
    + PARAMETERS_NOTE,
    status_code=202,
    responses={
        202: {
            "description": "Accepted. The content is valid and may be submitted in another request."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden. The content is invalid - Reasons include e.g.: \n"
            "- The syntax of the 'name' is not valid.\n"
            "- One of the parameters wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def pre_validate(
    timeframe_template: TimeframeTemplateNameInput = Body(
        None,
        description="The content of the timeframe template that shall be validated.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    Service(current_user_id).validate_template_syntax(timeframe_template.name)
