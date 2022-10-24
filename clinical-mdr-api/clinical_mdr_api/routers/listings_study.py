from fastapi import APIRouter, Path

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.listings_study import (
    RegistryIdentifiersListingModel,
    StudyPopulationListingModel,
    StudyTypeListingModel,
)
from clinical_mdr_api.models.study import StudyDescriptionJsonModel
from clinical_mdr_api.services.listings_study import StudyListingService
from clinical_mdr_api.services.study import StudyService

router = APIRouter()


@router.get(
    "/studies/listing/{study_number}/study-title",
    summary="Retrieve study title from a given study number",
    response_model=StudyDescriptionJsonModel,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified 'study_number'.",
        },
    },
)
def get_study_title(
    study_number: int = Path(
        None, description="Return study title for specific study number"
    )
):
    study_service = StudyService()
    uid = StudyDefinitionRepository.find_uid_by_study_number(study_number)
    if uid is None:
        raise exceptions.NotFoundException(f"study '{study_number}' not found.")
    return study_service.get_by_uid(
        uid=uid, fields="currentMetadata.studyDescription"
    ).currentMetadata.studyDescription


@router.get(
    "/studies/listing/{study_number}/registry-identifiers",
    summary="Retrieve study registry identifiers from a given study number",
    response_model=RegistryIdentifiersListingModel,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified 'study_number'.",
        },
    },
)
def get_study_registry_identifiers(
    study_number: int = Path(
        None, description="Return study registry identifiers for specific study number"
    )
):
    study_listing_service = StudyListingService()
    return study_listing_service.get_registry_identifiers(study_number)


@router.get(
    "/studies/listing/{study_number}/study-type",
    summary="Retrieve study type from a given study number",
    response_model=StudyTypeListingModel,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified 'study_number'.",
        },
    },
)
def get_study_type(
    study_number: int = Path(
        None, description="Return study type for specific study number"
    )
):
    study_listing_service = StudyListingService()
    return study_listing_service.get_study_type(study_number)


@router.get(
    "/studies/listing/{study_number}/study-population",
    summary="Retrieve study population from a given study number",
    response_model=StudyPopulationListingModel,
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        404: {
            "model": ErrorResponse,
            "description": "Not Found - No study with the specified 'study_number'.",
        },
    },
)
def get_study_population(
    study_number: int = Path(
        None, description="Return study population for specific study number"
    )
):
    study_listing_service = StudyListingService()
    return study_listing_service.get_study_population(study_number)
