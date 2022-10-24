from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceVO,
)


class ReminderVO(ActivityInstanceVO):
    pass


class ReminderAR(ActivityInstanceAR):
    _concept_vo: ReminderVO

    @property
    def concept_vo(self) -> ReminderVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name
