import math
from dataclasses import dataclass
from typing import AbstractSet, Callable, Optional, Sequence

from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    ObjectAction,
)

CONCENTRATION_UNIT_DIMENSION_VALUE = "Concentration"


@dataclass
class CTTerm:
    uid: str
    name: Optional[str]


@dataclass(frozen=True)
class UnitDefinitionValueVO(ConceptVO):
    ct_units: Sequence[CTTerm]
    unit_subsets: Sequence[CTTerm]
    ucum_uid: Optional[str]
    unit_dimension_uid: Optional[str]
    # TODO temporary solution to not break performance
    # Fix when matching optional relationships in the extended neomodel will be ready
    ucum_name: Optional[str]
    unit_dimension_name: Optional[str]
    convertible_unit: bool
    display_unit: bool
    master_unit: bool
    si_unit: bool
    us_conventional_unit: bool
    legacy_code: Optional[str]
    molecular_weight_conv_expon: Optional[int]
    conversion_factor_to_master: Optional[float]
    order: Optional[int]
    comment: Optional[str]

    @classmethod
    def from_input_values(
        cls,
        *,
        name: str,
        definition: Optional[str],
        convertible_unit: bool,
        display_unit: bool,
        master_unit: bool,
        si_unit: bool,
        us_conventional_unit: bool,
        ct_units: Sequence[str],
        unit_subsets: Sequence[str],
        ucum_uid: Optional[str],
        unit_dimension_uid: Optional[str],
        legacy_code: Optional[str],
        molecular_weight_conv_expon: Optional[int],
        conversion_factor_to_master: Optional[float],
        comment: Optional[str],
        order: Optional[int],
        unit_ct_uid_exists_callback: Callable[[str], bool],
        ucum_uid_exists_callback: Callable[[str], bool],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        is_template_parameter: bool,
    ) -> "UnitDefinitionValueVO":
        ucum_uid = normalize_string(ucum_uid)
        unit_dimension_uid = normalize_string(unit_dimension_uid)

        if conversion_factor_to_master is not None and math.isnan(
            conversion_factor_to_master
        ):
            raise ValueError(
                "conversion factor to master if specified cannot be NaN value."
            )

        if master_unit and conversion_factor_to_master != 1.0:
            raise ValueError(
                f"conversion factor to master must be 1.0 for master unit (provided value: {conversion_factor_to_master})"
            )

        if (
            molecular_weight_conv_expon is not None
            and molecular_weight_conv_expon != 0
            and molecular_weight_conv_expon != 1
        ):
            raise ValueError(
                f"molecular weight conv expon (if specified) can be 0 or 1 (provided value: {molecular_weight_conv_expon})"
            )

        if unit_dimension_uid is not None and not find_term_by_uid(unit_dimension_uid):
            raise ValueError(f"Unknown CT dimension uid: {unit_dimension_uid}")

        if (
            unit_dimension_uid is not None
            and find_term_by_uid(unit_dimension_uid).name
            == CONCENTRATION_UNIT_DIMENSION_VALUE
            and molecular_weight_conv_expon is None
        ):
            raise ValueError(
                "molecular weight conv expon must be provided with a value when unit dimension is set to 'Concentration'."
            )

        for unit_ct_uid in ct_units:
            if unit_ct_uid is not None and not unit_ct_uid_exists_callback(unit_ct_uid):
                raise ValueError(f"Unknown CT unit uid: {unit_ct_uid}")

        for unit_subset in unit_subsets:
            if unit_subset is not None and not unit_ct_uid_exists_callback(unit_subset):
                raise ValueError(f"Unknown Unit Subset uid: {unit_subset}")

        if ucum_uid is not None and not ucum_uid_exists_callback(ucum_uid):
            raise ValueError(f"Unknown ucum uid: {ucum_uid}")

        return cls.from_repository_values(
            name=normalize_string(name),
            definition=definition,
            ct_units=[CTTerm(uid=ct_unit, name=None) for ct_unit in ct_units],
            unit_subsets=[
                CTTerm(uid=unit_subset, name=None) for unit_subset in unit_subsets
            ],
            ucum_uid=ucum_uid,
            unit_dimension_uid=unit_dimension_uid,
            ucum_name=None,
            unit_dimension_name=None,
            convertible_unit=convertible_unit,
            display_unit=display_unit,
            master_unit=master_unit,
            si_unit=si_unit,
            us_conventional_unit=us_conventional_unit,
            legacy_code=normalize_string(legacy_code),
            molecular_weight_conv_expon=molecular_weight_conv_expon,
            conversion_factor_to_master=conversion_factor_to_master,
            order=order,
            comment=comment,
            is_template_parameter=is_template_parameter,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        name: str,
        definition: Optional[str],
        convertible_unit: bool,
        display_unit: bool,
        master_unit: bool,
        si_unit: bool,
        us_conventional_unit: bool,
        ct_units: Sequence[CTTerm],
        unit_subsets: Sequence[CTTerm],
        ucum_uid: Optional[str],
        unit_dimension_uid: Optional[str],
        ucum_name: Optional[str],
        unit_dimension_name: Optional[str],
        legacy_code: Optional[str],
        molecular_weight_conv_expon: Optional[int],
        conversion_factor_to_master: Optional[float],
        order: Optional[int],
        comment: Optional[str],
        is_template_parameter: bool,
    ) -> "UnitDefinitionValueVO":
        return cls(
            name=name,
            name_sentence_case=name.lower(),
            abbreviation=None,
            definition=definition,
            is_template_parameter=is_template_parameter,
            ct_units=ct_units,
            unit_subsets=unit_subsets,
            ucum_uid=ucum_uid,
            unit_dimension_uid=unit_dimension_uid,
            ucum_name=ucum_name,
            unit_dimension_name=unit_dimension_name,
            convertible_unit=convertible_unit,
            display_unit=display_unit,
            master_unit=master_unit,
            si_unit=si_unit,
            us_conventional_unit=us_conventional_unit,
            legacy_code=legacy_code,
            molecular_weight_conv_expon=molecular_weight_conv_expon,
            conversion_factor_to_master=conversion_factor_to_master,
            order=order,
            comment=comment,
        )


@dataclass
class UnitDefinitionAR(ConceptARBase):

    _concept_vo: UnitDefinitionValueVO

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise NotImplementedError("Possible actions retrieval not implemented.")

    @property
    def concept_vo(self) -> UnitDefinitionValueVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    def create_new_version(self, author: str):
        super()._create_new_version(author)

    def edit_draft(
        self,
        *,
        author: str,
        change_description: str,
        new_unit_definition_value: UnitDefinitionValueVO = None,
        unit_definition_by_name_exists_predicate: Callable[[str], bool] = None,
        master_unit_exists_for_dimension_predicate: Callable[[str], bool] = None,
        unit_definition_exists_by_legacy_code: Callable[[str], bool] = None,
    ) -> None:
        """
        Edits a draft version of the object, creating a new draft version.
        """

        if (
            self.name != new_unit_definition_value.name
            and unit_definition_by_name_exists_predicate(new_unit_definition_value.name)
        ):
            raise ValueError(
                f"Attempt to change name of Unit Definition into non-unique value: {new_unit_definition_value.name}"
            )

        if (
            new_unit_definition_value.legacy_code is not None
            and new_unit_definition_value.legacy_code != self.concept_vo.legacy_code
            and unit_definition_exists_by_legacy_code(
                new_unit_definition_value.legacy_code
            )
        ):
            raise ValueError(
                f"Attempt to change Unit Definition legacy code into non-unique value: {new_unit_definition_value.legacy_code}"
            )

        if (
            new_unit_definition_value.unit_dimension_uid is not None
            and new_unit_definition_value.master_unit
            and (
                not self.concept_vo.master_unit
                or new_unit_definition_value.unit_dimension_uid
                != self.concept_vo.unit_dimension_uid
            )
            and master_unit_exists_for_dimension_predicate(
                new_unit_definition_value.unit_dimension_uid
            )
        ):
            raise ValueError(
                f"Attempt to make '{self.uid}' another master unit in dimension '{new_unit_definition_value.unit_dimension_uid}'."
            )

        if self._concept_vo != new_unit_definition_value:
            super()._edit_draft(
                author=author, change_description=normalize_string(change_description)
            )
            self._concept_vo = new_unit_definition_value

    @classmethod
    def from_input_values(
        cls,
        *,
        unit_definition_value: UnitDefinitionValueVO,
        author: str,
        library: LibraryVO,
        unit_definition_exists_by_name_predicate: Callable[[str], bool],
        master_unit_exists_for_dimension_predicate: Callable[[str], bool],
        unit_definition_exists_by_legacy_code: Callable[[str], bool],
        uid_supplier: Callable[[], str] = lambda: None,  # type: ignore
    ) -> "UnitDefinitionAR":

        if unit_definition_exists_by_name_predicate(unit_definition_value.name):
            raise ValueError(
                f"Attempt to create an unit definition with non-unique name: {unit_definition_value.name}"
            )

        if (
            unit_definition_value.legacy_code is not None
            and unit_definition_exists_by_legacy_code(unit_definition_value.legacy_code)
        ):
            raise ValueError(
                f"Attempt to create an unit definition with non-unique legacy code: {unit_definition_value.legacy_code}"
            )

        if (
            unit_definition_value.unit_dimension_uid is not None
            and unit_definition_value.master_unit
            and master_unit_exists_for_dimension_predicate(
                unit_definition_value.unit_dimension_uid
            )
        ):
            raise ValueError(
                f"Attempt to create another master unit in dimension '{unit_definition_value.unit_dimension_uid}'."
            )

        result: UnitDefinitionAR = cls._from_input_values(
            author=author,
            library=library,
            uid_supplier=uid_supplier,
            _concept_vo=unit_definition_value,
        )
        return result

    @classmethod
    def from_repository_values(
        cls,
        *,
        library: LibraryVO,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        unit_definition_value: UnitDefinitionValueVO,
    ) -> "UnitDefinitionAR":
        result: UnitDefinitionAR = cls._from_repository_values(
            library=library,
            uid=uid,
            item_metadata=item_metadata,
            _concept_vo=unit_definition_value,
        )
        return result
