from clinical_mdr_api.domain.concepts.activities.rating_scale import (
    RatingScaleAR,
    RatingScaleVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.categoric_finding_repository import (
    CategoricFindingRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    RatingScaleRoot,
    RatingScaleValue,
)
from clinical_mdr_api.models.activities.rating_scale import RatingScale


class RatingScaleRepository(CategoricFindingRepository):
    root_class = RatingScaleRoot
    value_class = RatingScaleValue
    aggregate_class = RatingScaleAR
    value_object_class = RatingScaleVO
    return_model = RatingScale
