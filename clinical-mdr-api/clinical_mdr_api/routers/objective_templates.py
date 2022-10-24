"""Objective templates router."""

from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models import ObjectiveTemplateNameInput
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.objective_template import ObjectiveTemplateWithCount
from clinical_mdr_api.models.template_parameter_value import MultiTemplateParameterValue
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService

router = APIRouter()

Service = ObjectiveTemplateService

# Argument definitions
ObjectiveTemplateUID = Path(
    None, description="The unique id of the objective template."
)

PARAMETERS_NOTE = """**Parameters in the 'name' property**:

The 'name' of an objective template may contain parameters, that can - and usually will - be replaced with
concrete values once an objective is created out of the objective template.

Parameters are referenced by simple strings in square brackets [] that match existing parameters defined in the MDR repository.

See the *[GET] /parameter-templates/* endpoint for available values.

The objective template will be linked to those parameters defined in the 'name' property.

You may use an arbitrary number of parameters and you may use the same parameter multiple times within the same objective template 'name'.

*Example*:

name='MORE TESTING of the superiority in the efficacy of [Intervention] with [Activity] and [Activity] in [Timeframe].'

'Intervention', 'Activity' and 'Timeframe' are parameters."""


@router.get(
    "",
    summary="Returns all objective templates in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    response_model=CustomPage[models.ObjectiveTemplate],
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
            "indications=indications.name",
            "category=categories.name.sponsorPreferredName",
            "confirmatoryTesting",
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
def get_objective_templates(
    request: Request,  # request is actually required by the allow_exports decorator
    status: Optional[str] = Query(
        None,
        description="If specified, only those objective templates will be returned that are currently in the specified status. "
        "This may be particularly useful if the objective template has "
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
) -> CustomPage[models.ObjectiveTemplate]:
    results = Service(current_user_id).get_all(
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
        items=results.items, total=results.total_count, page=pageNumber, size=pageSize
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
    summary="Returns the latest/newest version of a specific objective template identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=ObjectiveTemplateWithCount,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' (and the specified date/time and/or status) wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_objective_template(
    uid: str = ObjectiveTemplateUID,
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the objective template in that status is returned (if existent). "
        "This may be particularly useful if the objective template has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the objective template in that version is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    return_instantiation_counts: bool = Query(
        False, description="if specified counts data will be returned along object"
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    if status is not None or version is not None:
        # TODO: retrieval by status and/or version not implemented
        raise NotImplementedError(
            "TODO: retrieval by status and/or version not implemented"
        )
    return Service(current_user_id).get_by_uid(
        uid=uid, return_instantiation_counts=bool(return_instantiation_counts)
    )


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific objective template identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=List[models.ObjectiveTemplateVersion],
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
            "description": "Not Found - The objective template with the specified 'uid' wasn't found.",
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
def get_objective_template_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = ObjectiveTemplateUID,
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).get_version_history(uid=uid)


@router.get(
    "/{uid}/versions/{version}",
    summary="Returns a specific version of a specific objective template identified by 'uid' and 'version'.",
    description="**Multiple versions**:\n\n"
    "Technically, there can be multiple versions of the objective template with the same version number. "
    "This is due to the fact, that the version number remains the same when inactivating or reactivating an objective template "
    "(switching between 'Final' and 'Retired' status). \n\n"
    "In that case the latest/newest representation is returned.",
    response_model=models.ObjectiveTemplate,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' and 'version' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_objective_template_version(
    uid: str = ObjectiveTemplateUID,
    version: str = Path(
        None,
        description="A specific version number of the objective template. "
        "The version number is specified in the following format: \\<major\\>.\\<minor\\> where \\<major\\> and \\<minor\\> are digits.\n"
        "E.g. '0.1', '0.2', '1.0', ...",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    # return service.get_specific_version(uid, version)
    return Service(current_user_id).get_specific_version(uid=uid, version=version)


@router.get(
    "/{uid}/releases",
    summary="List all final versions of a template identified by 'uid', including number of studies using a specific version",
    description="",
    response_model=List[models.ObjectiveTemplate],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_objective_template_releases(
    uid: str = ObjectiveTemplateUID, current_user_id: str = Depends(get_current_user_id)
):
    return Service(current_user_id).get_releases(uid=uid, return_study_count=False)


@router.post(
    "",
    summary="Creates a new objective template in 'Draft' status.",
    description="""This request is only valid if the objective template
* belongs to a library that allows creating (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The objective template will be linked to a library.

"""
    + PARAMETERS_NOTE,
    response_model=models.ObjectiveTemplate,
    status_code=201,
    responses={
        201: {
            "description": "Created - The objective template was successfully created."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template name is not valid.\n"
            "- The library does not allow to create objective templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'libraryName' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_objective_template(
    objective_template: models.ObjectiveTemplateCreateInput = Body(
        None, description="The objective template that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    # TODO: do sth to allow static analysis
    return Service(current_user_id).create(objective_template)  # type: ignore


@router.patch(
    "/{uid}",
    summary="Updates the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

Parameters in the 'name' property can only be changed if the objective template has never been approved.
Once the objective template has been approved, only the surrounding text (excluding the parameters) can be changed.

"""
    + PARAMETERS_NOTE,
    response_model=models.ObjectiveTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in draft status.\n"
            "- The objective template name is not valid.\n"
            "- The library does not allow to edit draft versions.\n"
            "- The change of parameters of previously approved objective templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def edit(
    uid: str = ObjectiveTemplateUID,
    objective_template: models.ObjectiveTemplateEditInput = Body(
        None,
        description="The new content of the objective template including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    return Service(current_user_id).edit_draft(uid=uid, template=objective_template)


@router.patch(
    "/{uid}/groupings",
    summary="Updates the groupings of the objective template identified by 'uid'.",
    description="""This request is only valid if the template
    * belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).
    
    This is version independent : it won't trigger a status or a version change.
    """,
    response_model=models.ObjectiveTemplate,
    status_code=200,
    responses={
        200: {
            "description": "No content - The groupings for this template were successfully updated."
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_groupings(
    uid: str = ObjectiveTemplateUID,
    groupings: models.ObjectiveTemplateEditGroupingsInput = Body(
        None,
        description="The lists of UIDs for the new groupings to be set, grouped by groupings to be updated.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    return Service(current_user_id).patch_groupings(uid=uid, groupings=groupings)


@router.patch(
    "/{uid}/default-parameter-values",
    summary="Edit the default parameter values of the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true). 

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

This endpoint can be used to either :
* Create a new set of default parameter values
* Edit an existing set of default parameter values

""",
    response_model=models.ObjectiveTemplate,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in draft status.\n"
            "- The objective template name is not valid.\n"
            "- The library does not allow to edit draft versions.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch_default_parameter_values(
    uid: str = ObjectiveTemplateUID,
    setNumber: Optional[int] = Body(
        None,
        description="Optionally, the set number of the default parameter values to be patched. If not set, a new set will be created.",
    ),
    defaultParameterValues: Sequence[MultiTemplateParameterValue] = Body(
        None,
        description="The set of default parameter values.\n"
        "If empty and an existing set_number is passed, the set will be deleted.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    return Service(current_user_id).patch_default_parameter_values(
        uid=uid, set_number=setNumber, default_parameter_values=defaultParameterValues
    )


@router.post(
    "/{uid}/new-version",
    summary="Creates a new version of the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

Parameters in the 'name' property cannot be changed with this request.
Only the surrounding text (excluding the parameters) can be changed.
""",
    response_model=models.ObjectiveTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in final or retired status or has a draft status.\n"
            "- The objective template name is not valid.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create_new_version(
    uid: str = ObjectiveTemplateUID,
    objective_template: models.ObjectiveTemplateEditInput = Body(
        None,
        description="The content of the objective template for the new 'Draft' version including the change description.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> models.ObjectiveTemplate:
    # return service.create_new_version_of_final_or_retired(uid, objective_template)
    # TODO: do sth not to mislead static code analysis
    return Service(current_user_id).create_new_version(
        uid=uid, template=objective_template
    )


@router.post(
    "/{uid}/approve",
    summary="Approves the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=models.ObjectiveTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        409: {
            "model": ErrorResponse,
            "description": "Conflict - there are objectives created from template and cascade is false",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = ObjectiveTemplateUID,
    cascade: bool = False,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Approves objective template. Fails with 409 if there is some objectives created
    from this template and cascade is false
    """
    if not cascade:
        return Service(current_user_id).approve(uid=uid)
    return Service(current_user_id).approve_cascade(uid=uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.ObjectiveTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = ObjectiveTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> models.ObjectiveTemplate:
    # return service.inactivate_final(uid)
    # TODO: do sth to make static code analysis work for this code
    return Service(current_user_id).inactivate_final(uid=uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the objective template identified by 'uid'.",
    description="""This request is only valid if the objective template
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically. 
* The 'version' property will remain the same as before.
    """,
    response_model=models.ObjectiveTemplate,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The objective template with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = ObjectiveTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> models.ObjectiveTemplate:
    # return service.reactivate_retired(uid)
    # TODO: do sth to allow for static code analysis of this code
    return Service(current_user_id).reactivate_retired(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the objective template identified by 'uid'.",
    description="""This request is only valid if \n
* the objective template is in 'Draft' status and
* the objective template has never been in 'Final' status and
* the objective template has no references to any objectives and
* the objective template belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {
            "description": "No Content - The objective template was successfully deleted."
        },
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The objective template is not in draft status.\n"
            "- The objective template was already in final state or is in use.\n"
            "- The library does not allow to delete objective templates.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An objective template with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def delete_objective_template(
    uid: str = ObjectiveTemplateUID, current_user_id: str = Depends(get_current_user_id)
) -> None:
    # service.soft_delete(uid)
    Service(current_user_id).soft_delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)


# TODO this endpoint potentially returns duplicated entries (by intention, currently).
#       however: check if that is ok with regard to the data volume we expect in the future. is paging needed?
@router.get(
    "/{uid}/parameters",
    summary="Returns all parameters used in the objective template identified by 'uid'. Includes the available values per parameter.",
    description="""The returned parameters are ordered
0. as they occur in the objective template

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
    uid: str = Path(None, description="The unique id of the objective template."),
    study_uid: Optional[str] = Query(
        None,
        description="Optionally, the uid of the study to subset the parameters to (e.g. for StudyEndpoints parameters)",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    return Service(current_user_id).get_parameters(
        uid=uid, study_uid=study_uid, include_study_endpoints=True
    )


@router.post(
    "/pre-validate",
    summary="Validates the content of an objective template without actually processing it.",
    description="""Be aware that - even if this request is accepted - there is no guarantee that
a following request to e.g. *[POST] /objective-templates* or *[PATCH] /objective-templates/{uid}*
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
    objective_template: ObjectiveTemplateNameInput = Body(
        None,
        description="The content of the objective template that shall be validated.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    # service.validate(objective_template)
    Service(current_user_id).validate_template_syntax(objective_template.name)
