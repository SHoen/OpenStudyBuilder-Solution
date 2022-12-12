from abc import ABC
from datetime import datetime
from typing import Callable, Optional

from pydantic import Field

from clinical_mdr_api.domain.concepts.simple_concepts.lag_time import LagTimeAR
from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
)
from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domain.concepts.simple_concepts.text_value import TextValueAR
from clinical_mdr_api.domain.concepts.simple_concepts.time_point import TimePointAR
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class NoLibraryConceptModelNoName(BaseModel, ABC):
    start_date: datetime
    end_date: Optional[datetime]
    status: str
    version: str
    user_initials: str
    change_description: str
    uid: str


class NoLibraryConceptModel(NoLibraryConceptModelNoName):
    name: str


class NoLibraryConceptPostInput(BaseModel, ABC):
    name: str


class ConceptModel(NoLibraryConceptModel):
    library_name: str


class ConceptPostInput(NoLibraryConceptPostInput):
    library_name: str = "Sponsor"


class ConceptPatchInput(BaseModel, ABC):
    change_description: str
    name: Optional[str] = None


class VersionProperties(BaseModel):
    start_date: Optional[datetime] = Field(
        None,
        title="startDate",
        description="The most recent point in time when the study epoch was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="latest_version|start_date",
    )
    end_date: Optional[datetime] = Field(
        None,
        title="endDate",
        description="The most recent point in time when the study epoch was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="latest_version|end_date",
    )
    status: Optional[str] = Field(
        None,
        title="status",
        description="",
        source="latest_version|status",
    )
    version: Optional[str] = Field(
        None,
        title="version",
        description="",
        source="latest_version|version",
    )
    change_description: Optional[str] = Field(
        None,
        title="changeDescription",
        description="",
        source="latest_version|change_description",
    )
    user_initials: Optional[str] = Field(
        None,
        title="userInitials",
        description="",
        source="latest_version|user_initials",
    )


class Concept(VersionProperties):
    class Config:
        orm_mode = True

    uid: str
    name: str = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
        source="has_latest_value.name",
    )
    name_sentence_case: Optional[str] = Field(
        None,
        title="name_sentence_case",
        description="",
        source="has_latest_value.name_sentence_case",
    )
    definition: Optional[str] = Field(
        None, title="definition", description="", source="has_latest_value.definition"
    )
    abbreviation: Optional[str] = Field(
        None,
        title="abbreviation",
        description="",
        source="has_latest_value.abbreviation",
    )
    library_name: str = Field(
        None,
        title="libraryName",
        description="",
        source="has_library.name",
    )


class ConceptInput(BaseModel):
    name: str = Field(
        None,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    name_sentence_case: Optional[str] = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    definition: Optional[str] = Field(
        None,
        title="definition",
        description="",
    )
    abbreviation: Optional[str] = None
    library_name: Optional[str] = None


class SimpleConcept(Concept):
    template_parameter: bool


class SimpleConceptInput(ConceptInput):
    template_parameter: Optional[bool] = False


class TextValue(SimpleConcept):
    @classmethod
    def from_concept_ar(cls, text_value: TextValueAR) -> "TextValue":
        return cls(
            uid=text_value.uid,
            library_name=Library.from_library_vo(text_value.library).name,
            name=text_value.concept_vo.name,
            name_sentence_case=text_value.concept_vo.name_sentence_case,
            definition=text_value.concept_vo.definition,
            abbreviation=text_value.concept_vo.abbreviation,
            template_parameter=text_value.concept_vo.is_template_parameter,
        )


class TextValueInput(SimpleConceptInput):
    name: str
    name_sentence_case: Optional[str] = None


class VisitName(TextValue):
    pass


class VisitNameInput(TextValueInput):
    pass


class NumericValue(SimpleConcept):
    name: str
    value: float

    @classmethod
    def from_concept_ar(cls, numeric_value: NumericValueAR) -> "NumericValue":
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
        )


class NumericValueInput(SimpleConceptInput):
    value: float


class NumericValueWithUnit(NumericValue):
    unit_definition_uid: str

    @classmethod
    def from_concept_ar(
        cls, numeric_value: NumericValueWithUnitAR
    ) -> "NumericValueWithUnit":
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
        )


class NumericValueWithUnitInput(NumericValueInput):
    unit_definition_uid: str


class SimpleNumericValueWithUnit(BaseModel):
    uid: str
    value: float
    unit_definition_uid: str
    unit_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_numeric_value_by_uid: Callable[[str], Optional[NumericValueWithUnitAR]],
    ) -> Optional["SimpleNumericValueWithUnit"]:
        concept = None
        if uid is not None:
            val: NumericValueWithUnitAR = find_numeric_value_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                concept = cls(
                    uid=val.uid,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    value=val.concept_vo.value,
                    unit_label=unit.concept_vo.name,
                )

        return concept


class LagTime(NumericValueWithUnit):
    sdtm_domain_uid: str

    @classmethod
    def from_concept_ar(cls, numeric_value: LagTimeAR) -> "LagTime":
        return cls(
            uid=numeric_value.uid,
            library_name=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            name_sentence_case=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            template_parameter=numeric_value.concept_vo.is_template_parameter,
            unit_definition_uid=numeric_value.concept_vo.unit_definition_uid,
            sdtm_domain_uid=numeric_value.concept_vo.sdtm_domain_uid,
        )


class LagTimeInput(NumericValueWithUnitInput):
    sdtm_domain_uid: str


class SimpleLagTime(BaseModel):
    value: float
    unit_definition_uid: str
    unit_label: str
    sdtm_domain_uid: str
    sdtm_domain_label: str

    @classmethod
    def from_concept_uid(
        cls,
        uid: str,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_lag_time_by_uid: Callable[[str], Optional[LagTimeAR]],
    ) -> Optional["SimpleLagTime"]:
        concept = None
        if uid is not None:
            val: LagTimeAR = find_lag_time_by_uid(uid)

            if val is not None:
                unit: UnitDefinitionAR = find_unit_by_uid(
                    val.concept_vo.unit_definition_uid
                )

                sdtm_domain: CTTermNameAR = find_term_by_uid(
                    val.concept_vo.sdtm_domain_uid
                )

                concept = cls(
                    value=val.concept_vo.value,
                    unit_definition_uid=val.concept_vo.unit_definition_uid,
                    unit_label=unit.concept_vo.name,
                    sdtm_domain_uid=val.concept_vo.sdtm_domain_uid,
                    sdtm_domain_label=sdtm_domain.ct_term_vo.name,
                )

        return concept


class TimePoint(SimpleConcept):
    numeric_value_uid: str
    unit_definition_uid: str
    time_reference_uid: str

    @classmethod
    def from_concept_ar(cls, time_point: TimePointAR) -> "TimePoint":
        return cls(
            uid=time_point.uid,
            library_name=Library.from_library_vo(time_point.library).name,
            name=time_point.concept_vo.name,
            name_sentence_case=time_point.concept_vo.name_sentence_case,
            definition=time_point.concept_vo.definition,
            abbreviation=time_point.concept_vo.abbreviation,
            template_parameter=time_point.concept_vo.is_template_parameter,
            numeric_value_uid=time_point.concept_vo.numeric_value_uid,
            unit_definition_uid=time_point.concept_vo.unit_definition_uid,
            time_reference_uid=time_point.concept_vo.time_reference_uid,
        )


class TimePointInput(SimpleConceptInput):
    name_sentence_case: Optional[str] = Field(
        None,
        title="name_sentence_case",
        description="",
    )
    numeric_value_uid: str
    unit_definition_uid: str
    time_reference_uid: str
