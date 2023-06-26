from typing import Optional, Union

from clinical_mdr_api.domain_repositories.syntax_instances.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.criteria import (
    CriteriaAR,
    CriteriaTemplateVO,
)
from clinical_mdr_api.models.syntax_instances.criteria import (
    Criteria,
    CriteriaVersion,
    CriteriaWithType,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class CriteriaService(
    GenericSyntaxInstanceService[Union[CriteriaAR, _AggregateRootType]]
):
    aggregate_class = CriteriaAR
    repository_interface = CriteriaRepository
    template_repository_interface = CriteriaTemplateRepository
    version_class = CriteriaVersion
    template_uid_property = "criteria_template_uid"
    template_name_property = "criteria_template"
    parametrized_template_vo_class = CriteriaTemplateVO

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaAR
    ) -> Criteria:
        return CriteriaWithType.from_criteria_ar(
            item_ar,
            get_criteria_type_name=self._repos.ct_term_name_repository.get_syntax_criteria_type,
            get_criteria_type_attributes=self._repos.ct_term_attributes_repository.get_syntax_criteria_type,
        )

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
    ) -> GenericFilteringReturn[Criteria]:
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
