from dataclasses import dataclass
from typing import Optional

from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueVO,
)


@dataclass(frozen=True)
class StudyDayVO(NumericValueVO):
    @classmethod
    def from_input_values(
        cls,
        value: float,
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
    ) -> "StudyDayVO":
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=f"Day {str(value)}",
            value=value,
            name_sentence_case=f"day {str(value)}",
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo


class StudyDayAR(NumericValueAR):
    _concept_vo: StudyDayVO

    @property
    def concept_vo(self) -> StudyDayVO:
        return self._concept_vo
