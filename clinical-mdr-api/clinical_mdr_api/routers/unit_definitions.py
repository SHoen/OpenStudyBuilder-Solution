from datetime import datetime
from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query, Request, Response
from fastapi import status as fast_api_status
from pydantic.types import Json

from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.unit_definition import (
    UnitDefinitionModel,
    UnitDefinitionPatchInput,
    UnitDefinitionPostInput,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.unit_definition import UnitDefinitionService

router = APIRouter()

Service = UnitDefinitionService


# Argument definitions
UnitDefinitionUID = Path(None, description="The unique id of unit definition.")


@router.get(
    "",
    summary="Returns all unit definitions in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    response_model=CustomPage[UnitDefinitionModel],
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
            "uid",
            "libraryName",
            "name",
            "masterUnit",
            "displayUnit",
            "unitSubsets",
            "ucum=ucum.name",
            "ctUnits",
            "convertibleUnit",
            "siUnit",
            "usConventionalUnit",
            "unitDimension=unitDimension.name",
            "legacyCode",
            "molecularWeightConvExpon",
            "conversionFactorToMaster",
            "startDate",
            "status",
            "version",
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
    libraryName: Optional[str] = Query(None),
    dimension: Optional[str] = Query(
        None,
        description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'.",
    ),
    subset: Optional[str] = Query(
        None,
        description="The name of the unit subset to filter, for instance 'Age Unit'.",
    ),
    service: Service = Depends(),
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
) -> CustomPage[UnitDefinitionModel]:
    results = service.get_all(
        library_name=libraryName,
        dimension=dimension,
        subset=subset,
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
    libraryName: Optional[str] = Query(None),
    dimension: Optional[str] = Query(
        None,
        description="The code submission value of the unit dimension to filter, for instance 'Dose Unit'.",
    ),
    subset: Optional[str] = Query(
        None,
        description="The name of the unit subset to filter, for instance 'Age Unit'.",
    ),
    service: Service = Depends(),
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
    return service.get_distinct_values_for_header(
        library_name=libraryName,
        dimension=dimension,
        subset=subset,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/{uid}",
    summary="Returns the latest/newest version of a specific Unit definition identified by 'uid'.",
    description="""If multiple request query parameters are used, then they need to
    match all at the same time (they are combined with the AND operation).""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": """Not Found - The unit definition with the specified
            'uid' (and the specified date/time, version and/or status) wasn't found.""",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_by_uid(
    uid: str = UnitDefinitionUID,
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="If specified, the latest/newest representation of the unit definition at this point in time is returned.\n"
        "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
        "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
        "If the timezone is ommitted, UTC±0 is assumed.",
    ),
    status: Optional[str] = Query(
        None,
        description="If specified, the representation of the unit definition in that status is returned (if existent). "
        "This may be particularly useful if the unit definition has "
        "a) a 'Draft' and a 'Final' status or "
        "b) a 'Draft' and a 'Retired' status at the same time "
        "and you are interested in the 'Final' or 'Retired' status.\n"
        "Valid values are: 'Final', 'Draft' or 'Retired'.",
    ),
    version: Optional[str] = Query(
        None,
        description=r"If specified, the latest/newest representation of the concept is returned. "
        r"Only exact matches are considered. "
        r"The version is specified in the following format: \<major\>.\<minor\> where \<major\> and \<minor\> are digits. "
        r"E.g. '0.1', '0.2', '1.0', ...",
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.get_by_uid(
        uid, version=version, status=status, at_specified_datetime=atSpecifiedDateTime
    )


@router.get(
    "/{uid}/versions",
    summary="Returns the version history of a specific concept identified by 'uid'.",
    description="The returned versions are ordered by\n"
    "0. startDate descending (newest entries first)",
    response_model=Sequence[UnitDefinitionModel],
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
            "description": "Not Found - The concept with the specified 'uid' wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "libraryName",
            "uid",
            "name",
            "unitCt",
            "convertibleUnit",
            "displayUnit",
            "masterUnit",
            "siUnit",
            "usConventionalUnit",
            "legacyCode",
            "molecularWeightConvExpon",
            "conversionFactorToMaster",
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
def get_versions(
    request: Request,  # request is actually required by the allow_exports decorator
    uid: str = UnitDefinitionUID,
    service: Service = Depends(),
) -> Sequence[UnitDefinitionModel]:
    return service.get_versions(uid)


@router.post(
    "",
    response_model=UnitDefinitionModel,
    summary="Creates a new unit definition in 'Draft' status.",
    description="""This request is only valid if the unit definition
* belongs to a library that allows creating (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Draft'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be set to '0.1'.
* The unit definition template will be linked to a library.

""",
    status_code=201,
    responses={
        201: {"description": "Created - The concept was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept name is not valid.\n"
            "- The library does not allow to create concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The library with the specified 'libraryName' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def post(
    unit_definition_post_input: UnitDefinitionPostInput = Body(
        None, description="The concept that shall be created."
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.post(unit_definition_post_input)  # type: ignore


@router.patch(
    "/{uid}",
    summary="Updates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The 'version' property will be increased automatically by +0.1.
* The status will remain in 'Draft'.

""",
    response_model=UnitDefinitionModel,
    status_code=200,
    responses={
        200: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library does not allow to edit draft versions.\n",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch(
    uid: str = UnitDefinitionUID,
    patch_input: UnitDefinitionPatchInput = Body(
        None,
        description="The new content of the concept including the change description.",
    ),
    service: Service = Depends(),
) -> UnitDefinitionModel:
    return service.patch(uid, patch_input)


@router.post(
    "/{uid}/new-version",
    summary="Creates a new version of the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' or 'Retired' status only (so no latest 'Draft' status exists) and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The latest 'Final' or 'Retired' version will remain the same as before.
* The status of the new version will be automatically set to 'Draft'.
* The 'version' property of the new version will be automatically set to the version of the latest 'Final' or 'Retired' version increased by +0.1.

""",
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final or retired status or has a draft status.\n"
            "- The library does not allow to create a new version.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The  concept with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def new_version(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.new_version(uid)


@router.post(
    "/{uid}/approve",
    summary="Approves the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Draft' status and
* belongs to a library that allows editing (the 'isEditable' property of the library needs to be true).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will be increased automatically to the next major version.
    """,
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in draft status.\n"
            "- The library does not allow to approve drafts.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def approve(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.approve(uid)


@router.post(
    "/{uid}/inactivate",
    summary="Inactivates/deactivates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Final' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Retired'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in final status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The unit definition with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def inactivate(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.inactivate(uid)


@router.post(
    "/{uid}/reactivate",
    summary="Reactivates the unit definition identified by 'uid'.",
    description="""This request is only valid if the unit definition
* is in 'Retired' status only (so no latest 'Draft' status exists).

If the request succeeds:
* The status will be automatically set to 'Final'.
* The 'changeDescription' property will be set automatically.
* The 'version' property will remain the same as before.
    """,
    response_model=UnitDefinitionModel,
    status_code=201,
    responses={
        201: {"description": "OK."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The unit definition is not in retired status.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The concept with the specified 'uid' could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def reactivate(
    uid: str = UnitDefinitionUID, service: Service = Depends()
) -> UnitDefinitionModel:
    return service.reactivate(uid)


@router.delete(
    "/{uid}",
    summary="Deletes the unit definition identified by 'uid'.",
    description="""This request is only valid if \n
* the unit definition is in 'Draft' status and
* the unit definition has never been in 'Final' status and
* the unit definition belongs to a library that allows deleting (the 'isEditable' property of the library needs to be true).""",
    response_model=None,
    status_code=204,
    responses={
        204: {"description": "No Content - The concept was successfully deleted."},
        403: {
            "model": ErrorResponse,
            "description": "Forbidden - Reasons include e.g.: \n"
            "- The concept is not in draft status.\n"
            "- The concept was already in final state or is in use.\n"
            "- The library does not allow to delete concept.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - An concept with the specified uid could not be found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    dependencies=[Depends(get_current_user_id)],
)
def delete(uid: str = UnitDefinitionUID, service: Service = Depends()) -> None:
    service.delete(uid)
    return Response(status_code=fast_api_status.HTTP_204_NO_CONTENT)
