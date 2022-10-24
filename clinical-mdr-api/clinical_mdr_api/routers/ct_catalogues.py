"""CTCatalogue router."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.ct_catalogue import CTCatalogueService

router = APIRouter()


@router.get(
    "/catalogues",
    summary="Returns all controlled terminology catalogues.",
    response_model=List[models.CTCatalogue],
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
# pylint: disable=unused-argument
def get_catalogues(
    library: Optional[str] = Query(
        None,
        description="If specified, only catalogues from given library are returned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_catalogue_service = CTCatalogueService()
    return ct_catalogue_service.get_all_ct_catalogues(library_name=library)


@router.get(
    "/catalogues/changes",
    summary="List changes between codelists and terms in CT Catalogues.",
    response_model=models.CTCatalogueChanges,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_catalogues_changes(
    library_name: Optional[str] = Query(
        None,
        description="If specified, only codelists and terms from given library_name are compared.",
    ),
    catalogue_name: Optional[str] = Query(
        None,
        description="If specified, only codelists and terms from given catalogue_name are compared.",
    ),
    comparison_type: str = Query(
        ...,
        description="The type of the comparison.\n"
        "Valid types are 'attributes' or 'sponsor'",
    ),
    start_datetime: datetime = Query(
        ...,
        description="The start datetime to perform comparison, for instance '2020-03-27T00:00:00'",
    ),
    end_datetime: Optional[datetime] = Query(
        None,
        description="The end datetime to perform comparison, for instance '2020-06-26T00:00:00'\n"
        "If it is not passed, then the current datetime is assigned.",
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    if end_datetime is None:
        end_datetime = datetime.now()
    ct_catalogue_service = CTCatalogueService(current_user_id)
    return ct_catalogue_service.get_ct_catalogues_changes(
        library_name=library_name,
        catalogue_name=catalogue_name,
        comparison_type=comparison_type,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
