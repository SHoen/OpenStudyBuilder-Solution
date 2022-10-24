"""CT stats router."""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services.ct_codelist import CTCodelistService
from clinical_mdr_api.services.ct_stats import CTStatsService

router = APIRouter()


@router.get(
    "/stats",
    summary="Returns stats about Catalogues, Packages and Terms",
    response_model=models.CTStats,
    status_code=200,
    responses={500: {"model": ErrorResponse, "description": "Internal Server Error"}},
)
def get_stats(
    latestCount: Optional[int] = Query(
        3, description="Optional, number of latest codelists to return"
    ),
    current_user_id: str = Depends(get_current_user_id),
):
    ct_stats_service = CTStatsService()

    # Get latest codelists from codelist service
    # Use get_all method from codelist repo with order by startDate desc and pageSize = latestCount
    ct_codelist_service = CTCodelistService(user=current_user_id)
    latest_codelists = ct_codelist_service.get_all_codelists(
        sort_by={"name.startDate": True}, page_number=1, page_size=latestCount
    )

    return ct_stats_service.get_stats(latest_codelists=latest_codelists.items)
