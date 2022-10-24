from datetime import datetime
from typing import Any, Optional, Sequence

from fastapi import APIRouter, Query
from pydantic.types import Json

from clinical_mdr_api import models
from clinical_mdr_api.models.error import ErrorResponse
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.listings import ListingsService

router = APIRouter()
### sdtm_router = APIRouter()
metadata_router = APIRouter()


@metadata_router.get(
    "/metadata",
    summary="Metadata for datasets",
    response_model=CustomPage[models.MetaData],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_metadata(
    dataset_name: Optional[str] = Query(
        None,
        description="Optional parameter to specify which legacy dataset(s) to get metadata for."
        " Multiple datasets are separated by commas",
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
    all_items = service.list_metadata(
        dataset_name=dataset_name,
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
    "/metadata/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_metadata,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/libraries/all/gcmd/topic-cd-def",  # might be different if we introduce a parameter
    summary="List library metadata for Activities in the legacy format for CDW-MMA General Clinical Metadata",
    response_model=CustomPage[models.TopicCdDef],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_all_activities_report(
    atSpecifiedDateTime: Optional[datetime] = Query(
        None,
        description="Optional parameter to specify the retrieve the status of the MDR at a specific timepoint, "
        "ISO Format with timezone, compatible with Neo4j e.g. 2021-01-01T09:00:00Z",
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
    all_items = service.list_topic_cd(
        at_specified_datetime=atSpecifiedDateTime,
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
    "/libraries/all/gcmd/topic-cd-def/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_topic_cd_def_values_for_header(
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_topic_cd,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/libraries/all/gcmd/cdisc_ct_ver",
    summary="CDW-MMA legacy dataset cdisc_ct_ver",
    response_model=CustomPage[models.CDISCCTVer],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_cdisc_ct_ver_data(
    cataloguename: Optional[str] = Query(
        None,
        description="If specified, only codelists from given catalogue are returned."
        " Multiple catalogues are separated by commas e.g. ADAM CT, SDTM CT",
    ),
    afterSpecifiedDate: Optional[str] = Query(
        None,
        description="If specified, only codelists from packages with effective date after this date are returned."
        "Date must be in ISO format e.g. 2021-01-01",
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
    all_items = service.list_cdisc_ct_ver(
        catalogue_name=cataloguename,
        after_date=afterSpecifiedDate,
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
    "/libraries/all/gcmd/cdisc_ct_ver/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_cdisc_ct_ver_values_for_header(
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_cdisc_ct_ver,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/libraries/all/gcmd/cdisc_ct_pkg",
    summary="CDW-MMA legacy dataset cdisc_ct_pkg",
    response_model=CustomPage[models.CDISCCTPkg],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_cdisc_ct_pkg_data(
    cataloguename: Optional[str] = Query(
        None,
        description="If specified, only codelists from given catalogue are returned."
        " Multiple catalogues are separated by commas e.g. ADAM CT, SDTM CT",
    ),
    afterSpecifiedDate: Optional[str] = Query(
        None,
        description="If specified, only codelists from packages with effective date after this date are returned."
        "Date must be in ISO format e.g. 2021-01-01",
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
    all_items = service.list_cdisc_ct_pkg(
        catalogue_name=cataloguename,
        after_date=afterSpecifiedDate,
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
    "/libraries/all/gcmd/cdisc_ct_pkg/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_cdisc_ct_pkg_values_for_header(
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_cdisc_ct_pkg,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/libraries/all/gcmd/cdisc_ct_list",
    summary="CDW-MMA legacy dataset cdisc_ct_list",
    response_model=CustomPage[models.CDISCCTList],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_cdisc_ct_list_data(
    cataloguename: Optional[str] = Query(
        None,
        description="If specified, only codelists from given catalogue are returned."
        " Multiple catalogues are separated by commas e.g. ADAM CT, SDTM CT",
    ),
    package: Optional[str] = Query(
        None,
        description="If specified, only codelists from given package are returned."
        "Multiple packages are separated by commas e.g. SDTM CT 2021-06-25, SDTM CT 2021-09-24",
    ),
    afterSpecifiedDate: Optional[str] = Query(
        None,
        description="If specified, only codelists from packages with effective date after this date are returned."
        "Date must be in ISO format e.g. 2021-01-01",
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
    all_items = service.list_cdisc_ct_list(
        catalogue_name=cataloguename,
        package=package,
        after_date=afterSpecifiedDate,
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
    "/libraries/all/gcmd/cdisc_ct_list/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_cdisc_ct_list_values_for_header(
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_cdisc_ct_list,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )


@router.get(
    "/libraries/all/gcmd/cdisc_ct_val",
    summary="CDW-MMA legacy dataset cdisc_ct_val",
    response_model=CustomPage[models.CDISCCTVal],
    response_model_exclude_unset=True,
    status_code=200,
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_cdisc_ct_val_data(
    cataloguename: Optional[str] = Query(
        None,
        description="If specified, only codelist values from given catalogue are returned."
        " Multiple catalogues are separated by commas e.g. ADAM CT, SDTM CT",
    ),
    package: Optional[str] = Query(
        None,
        description="If specified, only codelist values from given package are returned."
        "Multiple packages are separated by commas e.g. SDTM CT 2021-06-25, SDTM CT 2021-09-24",
    ),
    afterSpecifiedDate: Optional[str] = Query(
        None,
        description="If specified, only codelist values from packages with effective date after this date are returned."
        "Date must be in ISO format e.g. 2021-01-01",
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
    all_items = service.list_cdisc_ct_val(
        catalogue_name=cataloguename,
        package=package,
        after_date=afterSpecifiedDate,
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
    "/libraries/all/gcmd/cdisc_ct_val/headers",
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    response_model=Sequence[Any],
    status_code=200,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)
def get_distinct_cdisc_ct_val_values_for_header(
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
    service = ListingsService()
    return service.get_distinct_values_for_header(
        action=service.list_cdisc_ct_val,
        field_name=fieldName,
        search_string=searchString,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        result_count=resultCount,
    )
