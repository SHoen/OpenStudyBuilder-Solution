from clinical_mdr_api.domain.concepts.activities.laboratory_activity import (
    LaboratoryActivityAR,
    LaboratoryActivityVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.categoric_finding_repository import (
    CategoricFindingRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    LaboratoryActivityRoot,
    LaboratoryActivityValue,
)
from clinical_mdr_api.models.activities.laboratory_activity import LaboratoryActivity


class LaboratoryActivityRepository(CategoricFindingRepository):
    root_class = LaboratoryActivityRoot
    value_class = LaboratoryActivityValue
    aggregate_class = LaboratoryActivityAR
    value_object_class = LaboratoryActivityVO
    return_model = LaboratoryActivity
