from typing import Optional

from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.listings.query_service import QueryService
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import service_level_generic_filtering


class SDTMListingsService:
    _repos: MetaRepository

    def __init__(self):
        # self._repos = MetaRepository()
        self._query_service = QueryService()

    @db.transaction
    def list_tv(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.listings_sdtm.StudyVisitListing]:
        data = self._query_service.get_tv(study_uid=study_uid)
        result = list(map(models.listings_sdtm.StudyVisitListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ta(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudyArmListing]:
        data = self._query_service.get_ta(study_uid=study_uid)
        result = list(map(models.StudyArmListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ti(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.listings_sdtm.StudyCriterionListing]:
        data = self._query_service.get_ti(study_uid=study_uid)
        result = list(map(models.listings_sdtm.StudyCriterionListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_ts(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.listings_sdtm.StudySummaryListing]:
        data = self._query_service.get_ts(study_uid=study_uid)
        result = list(map(models.listings_sdtm.StudySummaryListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    @db.transaction
    def list_te(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[models.StudyElementListing]:
        data = self._query_service.get_te(study_uid=study_uid)
        result = list(map(models.StudyElementListing.from_query, data))

        filtered_items = service_level_generic_filtering(
            items=result,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items
