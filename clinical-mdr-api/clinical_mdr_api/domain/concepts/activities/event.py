from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceVO,
)


class EventVO(ActivityInstanceVO):
    pass


class EventAR(ActivityInstanceAR):
    _concept_vo: EventVO

    @property
    def concept_vo(self) -> EventVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name
