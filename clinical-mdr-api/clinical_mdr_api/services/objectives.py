from typing import Optional

from clinical_mdr_api.domain.library.objectives import ObjectiveAR
from clinical_mdr_api.domain_repositories.library.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.models.objective import Objective, ObjectiveVersion
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_object_service import (
    GenericObjectService,  # type: ignore
)


class ObjectiveService(GenericObjectService[ObjectiveAR]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ObjectiveAR
    ) -> Objective:
        return Objective.from_objective_ar(item_ar)

    aggregate_class = ObjectiveAR
    repository_interface = ObjectiveRepository
    template_repository_interface = ObjectiveTemplateRepository
    version_class = ObjectiveVersion
    templateUidProperty = "objectiveTemplateUid"
    templateNameProperty = "objectiveTemplate"

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
    ) -> GenericFilteringReturn[Objective]:
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
