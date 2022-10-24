from clinical_mdr_api.domain.library.criteria import CriteriaAR, CriteriaTemplateVO
from clinical_mdr_api.domain_repositories.library.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.models import Criteria
from clinical_mdr_api.models.criteria import CriteriaVersion
from clinical_mdr_api.services.generic_object_service import (
    GenericObjectService,  # type: ignore
)


class CriteriaService(GenericObjectService[CriteriaAR]):

    aggregate_class = CriteriaAR
    repository_interface = CriteriaRepository
    template_repository_interface = CriteriaTemplateRepository
    version_class = CriteriaVersion
    templateUidProperty = "criteriaTemplateUid"
    templateNameProperty = "criteriaTemplate"
    parametrized_template_vo_class = CriteriaTemplateVO

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaAR
    ) -> Criteria:
        return Criteria.from_criteria_ar(item_ar)
