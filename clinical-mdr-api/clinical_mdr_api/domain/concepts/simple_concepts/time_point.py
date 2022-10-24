from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domain.concepts.simple_concepts.simple_concept import (
    SimpleConceptAR,
    SimpleConceptVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR


@dataclass(frozen=True)
class TimePointVO(SimpleConceptVO):
    unit_definition_uid: str
    numeric_value_uid: str
    time_reference_uid: str

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
        unit_definition_uid: str,
        numeric_value_uid: str,
        time_reference_uid: str,
    ) -> "TimePointVO":
        simple_concept_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            numeric_value_uid=numeric_value_uid,
            time_reference_uid=time_reference_uid,
        )

        return simple_concept_vo

    @classmethod
    def from_input_values(
        cls,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
        unit_definition_uid: str,
        numeric_value_uid: str,
        time_reference_uid: str,
        find_numeric_value_by_uid: Callable[[str], NumericValueAR],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR],
        find_time_reference_by_uid: Callable[[str], CTTermNameAR],
    ) -> "TimePointVO":

        numeric_value = find_numeric_value_by_uid(numeric_value_uid)
        if numeric_value is None:
            raise ValueError(
                f"{cls.__name__} tried to connect to non existing numeric value identified by uid ({numeric_value_uid})"
            )

        unit_definition = find_unit_definition_by_uid(unit_definition_uid)
        if unit_definition is None:
            raise ValueError(
                f"{cls.__name__} tried to connect to non existing unit definition identified by uid ({unit_definition_uid})"
            )

        time_reference = find_time_reference_by_uid(time_reference_uid)
        if time_reference is None:
            raise ValueError(
                f"{cls.__name__} tried to connect to non existing CTTermRoot identified by uid ({time_reference_uid})"
            )

        simple_concept_vo = cls(
            name=f"{numeric_value.name} {unit_definition.name} after {time_reference.name}",
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
            unit_definition_uid=unit_definition_uid,
            numeric_value_uid=numeric_value_uid,
            time_reference_uid=time_reference_uid,
        )

        return simple_concept_vo


class TimePointAR(SimpleConceptAR):
    _concept_vo: TimePointVO
