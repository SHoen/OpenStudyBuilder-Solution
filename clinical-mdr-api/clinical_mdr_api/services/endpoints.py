from typing import Optional

from clinical_mdr_api.domain.library.endpoints import EndpointAR
from clinical_mdr_api.domain_repositories.library.endpoint_repository import (
    EndpointRepository,
)
from clinical_mdr_api.domain_repositories.templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.models import Endpoint, EndpointVersion
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_object_service import (
    GenericObjectService,  # type: ignore
)


class EndpointService(GenericObjectService[EndpointAR]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: EndpointAR
    ) -> Endpoint:
        return Endpoint.from_endpoint_ar(item_ar)

    aggregate_class = EndpointAR
    repository_interface = EndpointRepository
    template_repository_interface = EndpointTemplateRepository
    version_class = EndpointVersion
    templateUidProperty = "endpointTemplateUid"
    templateNameProperty = "endpointTemplate"

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
    ) -> GenericFilteringReturn[Endpoint]:
        all_items = super().get_releases_referenced_by_any_study()

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
