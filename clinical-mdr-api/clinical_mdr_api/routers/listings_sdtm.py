from typing import Optional

from fastapi import APIRouter, Path, Query
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.listings_sdtm import (
    SDTMListingsService as ListingsService,
)

router = APIRouter()


@router.get(
    "/studies/all/SDTM/TV/{study_uid}",
    summary="SDTM TV domain listing",
    response_model=CustomPage[models.listings_sdtm.StudyVisitListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_tv(
    study_uid: str = Path(
        None,
        description="Return study visit data of a given study in SDTM TV domain format.",
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
):
    service = ListingsService()
    all_items = service.list_tv(
        study_uid=study_uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/studies/all/SDTM/TA/{study_uid}",
    summary="SDTM TA domain listing",
    response_model=CustomPage[models.StudyArmListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_ta(
    study_uid: str = Path(
        None,
        description="Return study arm data of a given study number in SDTM TA domain format.",
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
):
    service = ListingsService()
    all_items = service.list_ta(
        study_uid=study_uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/studies/all/SDTM/TI/{study_uid}",
    summary="SDTM TI domain listing",
    response_model=CustomPage[models.listings_sdtm.StudyCriterionListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_ti(
    study_uid: str = Path(
        None,
        description="Return study criterion data of a given study in SDTM TI domain format.",
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
):
    service = ListingsService()
    all_items = service.list_ti(
        study_uid=study_uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/studies/all/SDTM/TS/{study_uid}",
    summary="SDTM TS domain listing",
    response_model=CustomPage[models.listings_sdtm.StudySummaryListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_ts(
    study_uid: str = Path(
        None,
        description="Return study summary data of a given study in SDTM TS domain format.",
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
):
    service = ListingsService()
    all_items = service.list_ts(
        study_uid=study_uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )


@router.get(
    "/studies/all/SDTM/TE/{study_uid}",
    summary="SDTM TE domain listing",
    response_model=CustomPage[models.StudyElementListing],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_te(
    study_uid: str = Path(
        None,
        description="Return study element data of a given study number in SDTM TE domain format.",
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
):
    service = ListingsService()
    all_items = service.list_te(
        study_uid=study_uid,
        page_number=pageNumber,
        page_size=pageSize,
        total_count=totalCount,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        sort_by=sortBy,
    )

    return CustomPage.create(
        items=all_items.items,
        total=all_items.total_count,
        page=pageNumber,
        size=pageSize,
    )
