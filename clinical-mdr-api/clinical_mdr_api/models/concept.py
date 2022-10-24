from abc import ABC
from datetime import datetime
from typing import Callable, Optional

from pydantic import Field
from pydantic.main import BaseModel

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


class NoLibraryConceptModelNoName(BaseModel, ABC):
    startDate: datetime
    endDate: Optional[datetime]
    status: str
    version: str
    userInitials: str
    changeDescription: str
    uid: str


class NoLibraryConceptModel(NoLibraryConceptModelNoName):
    name: str


class NoLibraryConceptPostInput(BaseModel, ABC):
    name: str


class ConceptModel(NoLibraryConceptModel):
    libraryName: str


class ConceptPostInput(NoLibraryConceptPostInput):
    libraryName: str = "Sponsor"


class ConceptPatchInput(BaseModel, ABC):
    changeDescription: str
    name: Optional[str] = None


class Concept(BaseModel):
    uid: str
    name: str = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    nameSentenceCase: Optional[str] = Field(
        None,
        title="nameSentenceCase",
        description="",
    )
    definition: Optional[str] = Field(
        None,
        title="definition",
        description="",
    )
    abbreviation: Optional[str] = None
    libraryName: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None


class ConceptInput(BaseModel):
    name: str = Field(
        None,
        title="name",
        description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
    )
    nameSentenceCase: Optional[str] = Field(
        None,
        title="nameSentenceCase",
        description="",
    )
    definition: Optional[str] = Field(
        None,
        title="definition",
        description="",
    )
    abbreviation: Optional[str] = None
    libraryName: Optional[str] = None


class SimpleConcept(Concept):
    templateParameter: bool


class SimpleConceptInput(ConceptInput):
    templateParameter: Optional[bool] = False


class TextValue(SimpleConcept):
    @classmethod
    def from_concept_ar(cls, text_value: TextValueAR) -> "TextValue":
        return cls(
            uid=text_value.uid,
            libraryName=Library.from_library_vo(text_value.library).name,
            name=text_value.concept_vo.name,
            nameSentenceCase=text_value.concept_vo.name_sentence_case,
            definition=text_value.concept_vo.definition,
            abbreviation=text_value.concept_vo.abbreviation,
            templateParameter=text_value.concept_vo.is_template_parameter,
        )


class TextValueInput(SimpleConceptInput):
    name: str
    nameSentenceCase: Optional[str] = None


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
            libraryName=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            nameSentenceCase=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            templateParameter=numeric_value.concept_vo.is_template_parameter,
        )


class NumericValueInput(SimpleConceptInput):
    value: float


class NumericValueWithUnit(NumericValue):
    unitDefinitionUid: str

    @classmethod
    def from_concept_ar(
        cls, numeric_value: NumericValueWithUnitAR
    ) -> "NumericValueWithUnit":
        return cls(
            uid=numeric_value.uid,
            libraryName=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            nameSentenceCase=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            templateParameter=numeric_value.concept_vo.is_template_parameter,
            unitDefinitionUid=numeric_value.concept_vo.unit_definition_uid,
        )


class NumericValueWithUnitInput(NumericValueInput):
    unitDefinitionUid: str


class SimpleNumericValueWithUnit(BaseModel):
    uid: str
    value: float
    unitDefinitionUid: str
    unitLabel: str

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
                    unitDefinitionUid=val.concept_vo.unit_definition_uid,
                    value=val.concept_vo.value,
                    unitLabel=unit.concept_vo.name,
                )

        return concept


class LagTime(NumericValueWithUnit):
    sdtmDomainUid: str

    @classmethod
    def from_concept_ar(cls, numeric_value: LagTimeAR) -> "LagTime":
        return cls(
            uid=numeric_value.uid,
            libraryName=Library.from_library_vo(numeric_value.library).name,
            name=numeric_value.concept_vo.name,
            value=numeric_value.concept_vo.value,
            nameSentenceCase=numeric_value.concept_vo.name_sentence_case,
            definition=numeric_value.concept_vo.definition,
            abbreviation=numeric_value.concept_vo.abbreviation,
            templateParameter=numeric_value.concept_vo.is_template_parameter,
            unitDefinitionUid=numeric_value.concept_vo.unit_definition_uid,
            sdtmDomainUid=numeric_value.concept_vo.sdtm_domain_uid,
        )


class LagTimeInput(NumericValueWithUnitInput):
    sdtmDomainUid: str


class SimpleLagTime(BaseModel):
    value: float
    unitDefinitionUid: str
    unitLabel: str
    sdtmDomainUid: str
    sdtmDomainLabel: str

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
                    unitDefinitionUid=val.concept_vo.unit_definition_uid,
                    unitLabel=unit.concept_vo.name,
                    sdtmDomainUid=val.concept_vo.sdtm_domain_uid,
                    sdtmDomainLabel=sdtm_domain.ct_term_vo.name,
                )

        return concept


class TimePoint(SimpleConcept):
    numericValueUid: str
    unitDefinitionUid: str
    timeReferenceUid: str

    @classmethod
    def from_concept_ar(cls, time_point: TimePointAR) -> "TimePoint":
        return cls(
            uid=time_point.uid,
            libraryName=Library.from_library_vo(time_point.library).name,
            name=time_point.concept_vo.name,
            nameSentenceCase=time_point.concept_vo.name_sentence_case,
            definition=time_point.concept_vo.definition,
            abbreviation=time_point.concept_vo.abbreviation,
            templateParameter=time_point.concept_vo.is_template_parameter,
            numericValueUid=time_point.concept_vo.numeric_value_uid,
            unitDefinitionUid=time_point.concept_vo.unit_definition_uid,
            timeReferenceUid=time_point.concept_vo.time_reference_uid,
        )


class TimePointInput(SimpleConceptInput):
    nameSentenceCase: Optional[str] = Field(
        None,
        title="nameSentenceCase",
        description="",
    )
    numericValueUid: str
    unitDefinitionUid: str
    timeReferenceUid: str
