from typing import Any, Callable, Iterable, Optional

from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.unit_definition import UnitDefinitionSimpleModel
from clinical_mdr_api.models.utils import (
    BaseModel,
    from_duration_object_to_value_and_unit,
)


class DurationJsonModel(BaseModel):
    class Config:
        title = "Duration"
        description = "Duration model to store ISO8601 duration."

    durationValue: Optional[int]
    durationUnitCode: Optional[UnitDefinitionSimpleModel]

    @classmethod
    def from_duration_object(
        cls,
        duration: Any,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> "DurationJsonModel":
        duration_value, duration_unit = from_duration_object_to_value_and_unit(
            duration, find_all_study_time_units
        )

        return cls(
            durationValue=duration_value,
            durationUnitCode=UnitDefinitionSimpleModel(
                uid=duration_unit.uid, name=duration_unit.name
            )
            if duration_unit
            else None,
        )
