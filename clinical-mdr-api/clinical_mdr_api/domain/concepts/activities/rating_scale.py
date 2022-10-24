from clinical_mdr_api.domain.concepts.activities.categoric_finding import (
    CategoricFindingAR,
    CategoricFindingVO,
)


class RatingScaleVO(CategoricFindingVO):
    pass


class RatingScaleAR(CategoricFindingAR):
    _concept_vo: RatingScaleVO

    @property
    def concept_vo(self) -> RatingScaleVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name
