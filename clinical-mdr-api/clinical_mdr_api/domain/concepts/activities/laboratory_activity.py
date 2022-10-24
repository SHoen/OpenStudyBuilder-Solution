from clinical_mdr_api.domain.concepts.activities.categoric_finding import (
    CategoricFindingAR,
    CategoricFindingVO,
)


class LaboratoryActivityVO(CategoricFindingVO):
    pass


class LaboratoryActivityAR(CategoricFindingAR):
    _concept_vo: LaboratoryActivityVO

    @property
    def concept_vo(self) -> LaboratoryActivityVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name
