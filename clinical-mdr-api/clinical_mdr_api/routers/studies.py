from typing import Any, List, Optional, Sequence

from fastapi import APIRouter, Body, Depends, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyComponentEnum,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.study import (
    Study,
    StudyCreateInput,
    StudyFieldAuditTrailEntry,
    StudyPatchRequestJsonModel,
    StudyProtocolTitle,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.study import StudyService

router = APIRouter()

StudyUID = Path(None, description="The unique id of the study.")


@router.get(
    "",
    summary="Returns all studies in their latest/newest version.",
    description="Allowed parameters include : filter on fields, sort by field name with sort direction, pagination",
    response_model=CustomPage[Study],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "currentMetadata.identificationMetadata.clinicalProgrammeName",
            "currentMetadata.identificationMetadata.projectNumber",
            "currentMetadata.identificationMetadata.projectName",
            "currentMetadata.identificationMetadata.studyNumber",
            "currentMetadata.identificationMetadata.studyId",
            "currentMetadata.identificationMetadata.studyAcronym",
            "currentMetadata.studyDescription.studyTitle",
            "currentMetadata.versionMetadata.studyStatus",
            "currentMetadata.versionMetadata.versionTimestamp",
            "currentMetadata.versionMetadata.lockedVersionAuthor",
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
    fields: Optional[str] = Query(
        default=None,
        description="Parameter specifies which parts of the whole Study Definition representation to retrieve."
        " This endpoint won't return underlying metadata parts like highLevelStudyDesign or studyIntervention"
        " even if they will be prefixed with a `+` because it was set to return only the most important part of the information"
        " like identification metadata."
        " In the form of comma separated name of the fields prefixed by (optional) `+` "
        " if the client wishes"
        " to retrieve the field or `-` if the client wants to skip the field."
        " If not specified identification metadata and version metadata are retrieved."
        " If value starts with `+` or `-` above default is extended or reduced by the specified fields"
        " otherwise (if not started with `+` or `-`) provided fields specification"
        " replaces the default. The `uid` and `studyStatus` fields will be always returned"
        " as they are mandatory fields for the Study API model. Currently supported fields are"
        " `currentMetadata.identificationMetadata`, `currentMetadata.highLevelStudyDesign`"
        " , `currentMetadata.studyPopulation` and `currentMetadata.studyIntervention`"
        " , `currentMetadata.studyDescription`.",
    ),
    hasStudyObjective: Optional[bool] = Query(
        default=None,
        description="Optionaly, filter studies based on the existence of related study objectives or not",
    ),
    hasStudyEndpoint: Optional[bool] = Query(
        default=None,
        description="Optionaly, filter studies based on the existence of related study endpoints or not",
    ),
    hasStudyCriteria: Optional[bool] = Query(
        default=None,
        description="Optionaly, filter studies based on the existence of related study criteria or not",
    ),
    hasStudyActivity: Optional[bool] = Query(
        default=None,
        description="Optionaly, filter studies based on the existence of related study activities or not",
    ),
    hasStudyActivityInstruction: Optional[bool] = Query(
        default=None,
        description="Optionaly, filter studies based on the existence of related study activity instruction or not",
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
) -> CustomPage[Study]:
    study_service = StudyService(user=current_user_id)
    results = study_service.get_all(
        fields=fields,
        has_study_objective=hasStudyObjective,
        has_study_endpoint=hasStudyEndpoint,
        has_study_criteria=hasStudyCriteria,
        has_study_activity=hasStudyActivity,
        has_study_activity_instruction=hasStudyActivityInstruction,
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
    summary="Returns possibles values from the database for a given header",
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
    study_service = StudyService(user=current_user_id)
    return study_service.get_distinct_values_for_header(
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.patch(
    "/{uid}",
    summary="Request to change some aspects (parts) of a specific study definition identified by 'uid'.",
    description="The request to change (some aspect) of the state of current aggregate. "
    "There are some special cases and considerations:\n"
    "* patching studyStatus in currentMetadata.versionMetadata is considered as the request for"
    "  locking/unlocking/releasing the study definition and should not be combined with any other"
    "  changes\n"
    "* there are many business rules that apply in different patching scenario or state of the"
    "  study definition. If request is not compliant it will fail with 403 and response body"
    "  will (hopefully) explain what is wrong.\n"
    "* the method may be invoked with dry=true query param. if that's the case it wokrs the same"
    "  except that any change made to the resource are not persisted (however all validations are"
    "  performed.\n",
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        403: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def patch(
    uid: str = StudyUID,
    dry: bool = Query(
        False,
        description="If specified the operation does full validation and returns either 200 or 403 but"
        "nothing is persisted.",
    ),
    study_patch_request: StudyPatchRequestJsonModel = Body(
        None,
        description="The request with the structure similar to the GET /{uid} response. Carrying only those"
        "fields requested to change.",
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Study:
    # study_service = StudyService(user="auth-not-implemented")
    study_service = StudyService(user=current_user_id)
    if study_patch_request is None:
        raise ValueError("No data to patch was provided.")
    response = study_service.patch(uid, dry, study_patch_request)
    return response


@router.get(
    "/{uid}",
    summary="Returns the current state of a specific study definition identified by 'uid'.",
    description="If multiple request query parameters are used, then they need to match all at the same time"
    " (they are combined with the AND operation).",
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " (and the specified date/time and/or status) wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get(
    uid: str = StudyUID,  # ,
    fields: Optional[str] = Query(
        default=None,
        description="Parameter specifies which parts of the whole Study Definition representation to retrieve. In"
        " the form of comma separated name of the fields prefixed by (optional) `+` "
        " if the client wishes"
        " to retrieve the field or `-` if the client wants to skip the field."
        " If not specified identification metadata and version metadata are retrieved."
        " If value starts with `+` or `-` above default is extended or reduced by the specified fields"
        " otherwise (if not started with `+` or `-`) provided fields specification"
        " replaces the default. The `uid` and `studyStatus` fields will be always returned"
        " as they are mandatory fields for the Study API model. Currently supported fields are"
        " `currentMetadata.identificationMetadata`, `currentMetadata.highLevelStudyDesign`"
        " ,`currentMetadata.studyPopulation` and `currentMetadata.studyIntervention`"
        " , `currentMetadata.studyDescription`.",
    ),
    current_user_id: str = Depends(get_current_user_id)
    # atSpecifiedDateTime: Optional[datetime] = Query(
    #     None,
    #     description="If specified, the latest/newest representation of the study at"
    #                                                               " this point in time is returned.\n"
    #                 "The point in time needs to be specified in ISO 8601 format including the timezone, e.g.: "
    #                 "'2020-10-31T16:00:00+02:00' for October 31, 2020 at 4pm in UTC+2 timezone. "
    #                 "If the timezone is omitted, UTC±0 is assumed."
    # ),
    #
    # status: Optional[str] = Query(
    #     None,
    #     description="If specified, the representation of the study in that status is returned (if existent). "
    #                 "Valid values are: 'Released', 'Draft' or 'Locked'."),
    # version: Optional[str] = Query(
    #     None,
    #     description=r"If specified, the latest/newest representation of the study in that version is returned. "
    #                 r"Only exact matches are considered. "
    #                 r"The version is specified as an integer number: "
    #                 r"E.g. 0, 1, 2, ..."
    # )
):
    study_service = StudyService(user=current_user_id)
    study_definition = study_service.get_by_uid(uid=uid, fields=fields)
    return study_definition


@router.get(
    "/{uid}/fields-audit-trail",
    summary="Returns the audit trail for the fields of a specific study definition identified by 'uid'.",
    description="Actions on the study are grouped by date of edit."
    "Optionally select which subset of fields should be reflected in the audit trail.",
    response_model=Sequence[StudyFieldAuditTrailEntry],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_fields_audit_trail(
    uid: str = StudyUID,  # ,
    sections: Optional[str] = Query(
        default=None,
        description="Optionally specify a list of sections to filter the audit trail by. "
        "Each section name must be preceded by a '+' or a '-', "
        "valid values are: 'IdentificationMetadata, RegistryIdentifiers, VersionMetadata, "
        "HighLevelStudyDesign, StudyPopulation, StudyIntervention, StudyDescription'. "
        "Example valid input: '-IdentificationMetadata,+StudyPopulation'."
        " If no filters are specified, the entire audit trail is returned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    study_service = StudyService(user=current_user_id)
    study_fields_audit_trail = study_service.get_fields_audit_trail_by_uid(
        uid=uid, sections=sections
    )
    return study_fields_audit_trail


@router.post(
    "",
    summary="Creates a new Study Definition.",
    description="""
If the request succeeds new DRAFT Study Definition will be with initial identification data as provided in 
request body with new unique uid generated and returned in response body.
        """,
    response_model=Study,
    response_model_exclude_unset=True,
    status_code=201,
    responses={
        201: {"description": "Created - The study was successfully created."},
        403: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def create(
    study_create_input: StudyCreateInput = Body(
        None, description="Related parameters of the objective that shall be created."
    ),
    current_user_id: str = Depends(get_current_user_id),
) -> Study:
    # study_service = StudyService(user="auth-not-implemented")
    study_service = StudyService(user=current_user_id)
    return study_service.create(study_create_input)


@router.get(
    "/{uid}/protocol-title",
    summary="Retrieve all information related to Protocol Title",
    description="""
State before:
 - Study-uid must exist

Business logic:
 - Retrieve Study title, Universal Trial Number, EudraCT number, IND number, Study phase fields
 - Retrieve all names of study compounds associated to {uid} and where type of treatment is equal to Investigational Product

State after:
 - No change
""",
    response_model=StudyProtocolTitle,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_protocol_title(
    uid: str = StudyUID, current_user_id: str = Depends(get_current_user_id)
):
    study_service = StudyService(user=current_user_id)
    return study_service.get_protocol_title(uid)


@router.patch(
    "/{uid}/copy-component",
    summary="Copy study form from another study",
    description="""
State before:
 - uid must exist
 - referenceStudyUid must exist

Business logic:
 - if overwrite is set to false, then the projection of the copy will be returned
 - if overwrite is set to true, then the component referenced as a componentToCopy will be copied
 from the study referenced by referenceStudyUid to the study referenced by uid.

State after:
 - The specific form is copied or projected into a study referenced by uid 'uid'.
""",
    response_model=Study,
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The study with the specified 'uid'"
            " wasn't found.",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def copy_simple_form_from_another_study(
    uid: str = StudyUID,
    referenceStudyUid: str = Query(
        ..., description="The uid of the study to copy component from"
    ),
    componentToCopy: StudyComponentEnum = Query(
        ..., description="The uid of the study to copy component from"
    ),
    overwrite: bool = Query(
        False,
        description="Indicates whether to overwrite the component of the study referenced by the uid"
        "or return a projection",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    study_service = StudyService(user=current_user_id)
    return study_service.copy_component_from_another_study(
        uid=uid,
        reference_study_uid=referenceStudyUid,
        component_to_copy=componentToCopy,
        overwrite=overwrite,
    )
