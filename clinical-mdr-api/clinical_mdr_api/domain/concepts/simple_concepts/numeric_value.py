from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from clinical_mdr_api.domain.concepts.simple_concepts.simple_concept import (
    SimpleConceptAR,
    SimpleConceptVO,
)


class NumericValueType(Enum):
    NUMERIC_VALUE = "numeric_value"
    STUDY_DAY = "study_day"
    STUDY_WEEK = "study_week"
    STUDY_DURATION_DAYS = "study_duration_days"
    STUDY_DURATION_WEEKS = "study_duration_weeks"


@dataclass(frozen=True)
class NumericValueVO(SimpleConceptVO):
    name: str
    value: Union[float, int]

    @classmethod
    def derive_value_property(cls, value):
        return int(value) if value.is_integer() else value

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        value: float,
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
    ) -> "NumericValueVO":
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=name,
            value=value,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo

    @classmethod
    def from_input_values(
        cls,
        value: float,
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
    ) -> "NumericValueVO":
        value = cls.derive_value_property(value=value)
        simple_concept_vo = cls(
            name=str(value),
            value=value,
            name_sentence_case=str(value).lower(),
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo


class NumericValueAR(SimpleConceptAR):
    _concept_vo: NumericValueVO

    @property
    def concept_vo(self) -> NumericValueVO:
        return self._concept_vo
