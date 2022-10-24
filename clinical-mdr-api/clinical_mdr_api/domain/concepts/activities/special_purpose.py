from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceVO,
)


class SpecialPurposeVO(ActivityInstanceVO):
    pass


class SpecialPurposeAR(ActivityInstanceAR):
    _concept_vo: SpecialPurposeVO

    @property
    def concept_vo(self) -> SpecialPurposeVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name
