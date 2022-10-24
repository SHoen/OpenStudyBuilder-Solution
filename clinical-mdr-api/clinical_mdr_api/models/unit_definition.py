from typing import Callable, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.utils import BaseModel


class UnitDefinitionModel(ConceptModel):
    convertibleUnit: bool
    displayUnit: bool
    masterUnit: bool
    siUnit: bool
    usConventionalUnit: bool
    ctUnits: Sequence[SimpleTermModel]
    unitSubsets: Sequence[SimpleTermModel]
    ucum: Optional[SimpleTermModel]
    unitDimension: Optional[SimpleTermModel]
    legacyCode: Optional[str]
    molecularWeightConvExpon: Optional[int]
    conversionFactorToMaster: Optional[float]
    comment: Optional[str]
    order: Optional[int]
    definition: Optional[str]
    templateParameter: bool

    @classmethod
    def from_unit_definition_ar(
        cls,
        unit_definition_ar: UnitDefinitionAR,
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> "UnitDefinitionModel":
        ctUnits = []
        for ct_unit in unit_definition_ar.concept_vo.ct_units:
            if ct_unit.name is None:
                controlled_terminology_unit = SimpleTermModel.from_ct_code(
                    c_code=ct_unit.uid, find_term_by_uid=find_term_by_uid
                )
            else:
                controlled_terminology_unit = SimpleTermModel(
                    termUid=ct_unit.uid, name=ct_unit.name
                )
            ctUnits.append(controlled_terminology_unit)
        if not any(ct_unit.name is None for ct_unit in ctUnits):
            ctUnits.sort(key=lambda item: item.name)

        unitSubsets = []
        for unit_subset in unit_definition_ar.concept_vo.unit_subsets:
            if unit_subset.name is None:
                controlled_terminology_subset = SimpleTermModel.from_ct_code(
                    c_code=unit_subset.uid, find_term_by_uid=find_term_by_uid
                )
            else:
                controlled_terminology_subset = SimpleTermModel(
                    termUid=unit_subset.uid, name=unit_subset.name
                )
            unitSubsets.append(controlled_terminology_subset)
        if not any(unit_subset.name is None for unit_subset in unitSubsets):
            unitSubsets.sort(key=lambda item: item.name)

        if unit_definition_ar.concept_vo.ucum_name is None:
            ucum = SimpleTermModel.from_ct_code(
                c_code=unit_definition_ar.concept_vo.ucum_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            )
        else:
            ucum = SimpleTermModel(
                termUid=unit_definition_ar.concept_vo.ucum_uid,
                name=unit_definition_ar.concept_vo.ucum_name,
            )

        if unit_definition_ar.concept_vo.unit_dimension_name is None:
            unitDimension = SimpleTermModel.from_ct_code(
                c_code=unit_definition_ar.concept_vo.unit_dimension_uid,
                find_term_by_uid=find_term_by_uid,
            )
        else:
            unitDimension = SimpleTermModel(
                termUid=unit_definition_ar.concept_vo.unit_dimension_uid,
                name=unit_definition_ar.concept_vo.unit_dimension_name,
            )

        return UnitDefinitionModel(
            uid=unit_definition_ar.uid,
            name=unit_definition_ar.name,
            definition=unit_definition_ar.concept_vo.definition,
            ctUnits=ctUnits,
            unitSubsets=unitSubsets,
            ucum=ucum,
            convertibleUnit=unit_definition_ar.concept_vo.convertible_unit,
            displayUnit=unit_definition_ar.concept_vo.display_unit,
            masterUnit=unit_definition_ar.concept_vo.master_unit,
            siUnit=unit_definition_ar.concept_vo.si_unit,
            usConventionalUnit=unit_definition_ar.concept_vo.us_conventional_unit,
            legacyCode=unit_definition_ar.concept_vo.legacy_code,
            molecularWeightConvExpon=unit_definition_ar.concept_vo.molecular_weight_conv_expon,
            conversionFactorToMaster=unit_definition_ar.concept_vo.conversion_factor_to_master,
            startDate=unit_definition_ar.item_metadata.start_date,
            endDate=unit_definition_ar.item_metadata.end_date,
            userInitials=unit_definition_ar.item_metadata.user_initials,
            status=unit_definition_ar.item_metadata.status.value,
            changeDescription=unit_definition_ar.item_metadata.change_description,
            libraryName=unit_definition_ar.library.name,
            version=unit_definition_ar.item_metadata.version,
            unitDimension=unitDimension,
            comment=unit_definition_ar.concept_vo.comment,
            order=unit_definition_ar.concept_vo.order,
            templateParameter=unit_definition_ar.concept_vo.is_template_parameter,
        )


class UnitDefinitionPostInput(ConceptPostInput):
    convertibleUnit: bool
    displayUnit: bool
    masterUnit: bool
    siUnit: bool
    usConventionalUnit: bool
    ctUnits: Sequence[str]
    unitSubsets: Optional[Sequence[str]] = []
    ucum: Optional[str]
    unitDimension: Optional[str]
    legacyCode: Optional[str]
    molecularWeightConvExpon: Optional[int]
    conversionFactorToMaster: Optional[float]
    comment: Optional[str]
    order: Optional[int]
    definition: Optional[str]
    templateParameter: bool = False


class UnitDefinitionPatchInput(ConceptPatchInput):
    convertibleUnit: Optional[bool] = None
    displayUnit: Optional[bool] = None
    masterUnit: Optional[bool] = None
    siUnit: Optional[bool] = None
    usConventionalUnit: Optional[bool] = None
    ctUnits: Optional[Sequence[str]] = []
    unitSubsets: Optional[Sequence[str]] = []
    ucum: Optional[str] = None
    unitDimension: Optional[str] = None
    legacyCode: Optional[str] = None
    molecularWeightConvExpon: Optional[int] = None
    conversionFactorToMaster: Optional[float] = None
    comment: Optional[str] = None
    order: Optional[int] = None
    definition: Optional[str] = None
    templateParameter: Optional[bool] = None


class UnitDefinitionSimpleModel(BaseModel):

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
