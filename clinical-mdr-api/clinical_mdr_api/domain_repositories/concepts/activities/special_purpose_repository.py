from clinical_mdr_api.domain.concepts.activities.special_purpose import (
    SpecialPurposeAR,
    SpecialPurposeVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    SpecialPurposeRoot,
    SpecialPurposeValue,
)
from clinical_mdr_api.models.activities.special_purpose import SpecialPurpose


class SpecialPurposeRepository(ActivityInstanceRepository):
    root_class = SpecialPurposeRoot
    value_class = SpecialPurposeValue
    aggregate_class = SpecialPurposeAR
    value_object_class = SpecialPurposeVO
    return_model = SpecialPurpose
