from typing import Optional

from clinical_mdr_api.domain.templates.timeframe_templates import (  # noqa: E501
    TimeframeTemplateAR,
)
from clinical_mdr_api.domain_repositories.library.timeframe_repository import (
    TimeframeRepository,
)
from clinical_mdr_api.domain_repositories.templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.models.timeframe_template import (
    TimeframeTemplate,
    TimeframeTemplateVersion,
    TimeframeTemplateWithCount,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_template_service import (
    GenericTemplateService,  # type: ignore
)


class TimeframeTemplateService(GenericTemplateService[TimeframeTemplateAR]):
    aggregate_class = TimeframeTemplateAR
    version_class = TimeframeTemplateVersion
    repository_interface = TimeframeTemplateRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TimeframeTemplateAR
    ) -> TimeframeTemplate:
        cls = (
            TimeframeTemplateWithCount
            if item_ar.counts is not None
            else TimeframeTemplate
        )
        return cls.from_timeframe_template_ar(item_ar)

    object_repository_interface = TimeframeRepository

    def get_all(
        self,
        status: Optional[str] = None,
        return_study_count: bool = True,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[TimeframeTemplate]:
        all_items = super().get_all(status, return_study_count)

        # The get_all method is only using neomodel, without Cypher query
        # Therefore, the filtering will be done in this service layer
        filtered_items = service_level_generic_filtering(
            items=all_items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items
