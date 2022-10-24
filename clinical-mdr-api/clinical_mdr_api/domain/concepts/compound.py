from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class CompoundVO(ConceptVO):
    """
    The CompoundVO acts as the single value object for CompoundAR aggregate.
    """

    analyte_number: Optional[str]
    nnc_short_number: Optional[str]
    nnc_long_number: Optional[str]
    substance_terms_uids: Sequence[str]
    dose_values_uids: Optional[Sequence[str]]
    strength_values_uids: Optional[Sequence[str]]
    lag_time_uids: Optional[Sequence[str]]
    delivery_devices_uids: Optional[Sequence[str]]
    dispensers_uids: Optional[Sequence[str]]
    dose_frequency_uids: Optional[Sequence[str]]
    dosage_form_uids: Optional[Sequence[str]]
    route_of_administration_uids: Optional[Sequence[str]]
    half_life_uid: Optional[str]
    projects_uids: Optional[Sequence[str]]
    brands_uids: Optional[Sequence[str]]
    is_sponsor_compound: bool = True
    is_name_inn: bool = True

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        dose_frequency_uids: Optional[Sequence[str]],
        dosage_form_uids: Optional[Sequence[str]],
        route_of_administration_uids: Optional[Sequence[str]],
        analyte_number: Optional[str],
        nnc_short_number: Optional[str],
        nnc_long_number: Optional[str],
        is_sponsor_compound: bool,
        is_name_inn: bool,
        substance_terms_uids: Sequence[str],
        dose_values_uids: Optional[Sequence[str]],
        strength_values_uids: Optional[Sequence[str]],
        lag_time_uids: Optional[Sequence[str]],
        delivery_devices_uids: Optional[Sequence[str]],
        dispensers_uids: Optional[Sequence[str]],
        half_life_uid: Optional[str],
        projects_uids: Optional[Sequence[str]],
        brands_uids: Optional[Sequence[str]],
    ) -> "CompoundVO":
        compound_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            dose_frequency_uids=dose_frequency_uids,
            dosage_form_uids=dosage_form_uids,
            route_of_administration_uids=route_of_administration_uids,
            analyte_number=analyte_number,
            nnc_short_number=nnc_short_number,
            nnc_long_number=nnc_long_number,
            is_sponsor_compound=is_sponsor_compound,
            is_name_inn=is_name_inn,
            substance_terms_uids=substance_terms_uids,
            dose_values_uids=dose_values_uids,
            strength_values_uids=strength_values_uids,
            lag_time_uids=lag_time_uids,
            delivery_devices_uids=delivery_devices_uids,
            dispensers_uids=dispensers_uids,
            half_life_uid=half_life_uid,
            projects_uids=projects_uids,
            brands_uids=brands_uids,
        )

        return compound_vo

    def validate(
        self,
        uid: Optional[str],
        compound_uid_by_property_value_callback: Callable[[str, str], str],
        ct_term_exists_callback: Callable[[str], bool],
        dictionary_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        project_exists_callback: Callable[[str], bool],
        brand_exists_callback: Callable[[str], bool],
    ):

        self.validate_uniqueness(
            lookup_callback=compound_uid_by_property_value_callback,
            uid=uid,
            property_name="name",
            value=self.name,
            error_message=f"Compound with name ({self.name}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_uid_by_property_value_callback,
            uid=uid,
            property_name="name_sentence_case",
            value=self.name_sentence_case,
            error_message=f"Compound with name sentence case ({self.name_sentence_case}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_uid_by_property_value_callback,
            uid=uid,
            property_name="analyte_number",
            value=self.analyte_number,
            error_message=f"Compound with analyte number ({self.analyte_number}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_uid_by_property_value_callback,
            uid=uid,
            property_name="nnc_long_number",
            value=self.nnc_long_number,
            error_message=f"Compound with long number ({self.nnc_long_number}) already exists",
        )

        self.validate_uniqueness(
            lookup_callback=compound_uid_by_property_value_callback,
            uid=uid,
            property_name="nnc_short_number",
            value=self.nnc_short_number,
            error_message=f"Compound with short number ({self.nnc_short_number}) already exists",
        )

        for term_uid in self.substance_terms_uids:
            if not dictionary_term_exists_callback(term_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing substance identified by uid ({term_uid})"
                )

        for dose_frequency_uid in self.dose_frequency_uids:
            if not ct_term_exists_callback(dose_frequency_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing dose frequency identified by uid ({dose_frequency_uid})"
                )

        for dosage_form_uid in self.dosage_form_uids:
            if not ct_term_exists_callback(dosage_form_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing dosage form identified by uid ({dosage_form_uid})"
                )

        for route_of_administration_uid in self.route_of_administration_uids:
            if not ct_term_exists_callback(route_of_administration_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing "
                    f"route of administration identified by uid ({route_of_administration_uid})"
                )

        for dose_values_uid in self.dose_values_uids:
            if not numeric_value_exists_callback(dose_values_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing dose value identified by uid ({dose_values_uid})"
                )

        for strength_values_uid in self.strength_values_uids:
            if not numeric_value_exists_callback(strength_values_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing strength value identified by uid ({strength_values_uid})"
                )

        for lag_time_uid in self.lag_time_uids:
            if not lag_time_exists_callback(lag_time_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing lag-time identified by uid ({lag_time_uid})"
                )

        for delivery_devices_uid in self.delivery_devices_uids:
            if not ct_term_exists_callback(delivery_devices_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing delivery device identified by uid ({delivery_devices_uid})"
                )

        for dispensers_uid in self.dispensers_uids:
            if not ct_term_exists_callback(dispensers_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing dispenser identified by uid ({dispensers_uid})"
                )

        for projects_uid in self.projects_uids:
            if not project_exists_callback(projects_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing project identified by uid ({projects_uid})"
                )

        for brands_uid in self.brands_uids:
            if not brand_exists_callback(brands_uid):
                raise ValueError(
                    f"{self.__class__.__name__} tried to connect to non existing brand identified by uid ({brands_uid})"
                )

        if self.half_life_uid is not None and not numeric_value_exists_callback(
            self.half_life_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing half life value identified by uid ({self.half_life_uid})"
            )


class CompoundAR(ConceptARBase):
    _concept_vo: CompoundVO

    @property
    def concept_vo(self) -> CompoundVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: CompoundVO,
        library: LibraryVO,
        compound_uid_by_property_value_callback: Callable[[str, str], str],
        ct_term_exists_callback: Callable[[str], bool],
        dictionary_term_exists_callback: Callable[[str], bool],
        numeric_value_exists_callback: Callable[[str], bool],
        lag_time_exists_callback: Callable[[str], bool],
        project_exists_callback: Callable[[str], bool],
        brand_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "CompoundAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        uid = generate_uid_callback()

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            uid=uid,
            compound_uid_by_property_value_callback=compound_uid_by_property_value_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            lag_time_exists_callback=lag_time_exists_callback,
            project_exists_callback=project_exists_callback,
            brand_exists_callback=brand_exists_callback,
        )

        compound_ar = cls(
            _uid=uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return compound_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: CompoundVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        compound_uid_by_property_value_callback: Callable[[str, str], str] = None,
        ct_term_exists_callback: Callable[[str], bool] = None,
        numeric_value_exists_callback: Callable[[str], bool] = None,
        dictionary_term_exists_callback: Callable[[str], bool] = None,
        lag_time_exists_callback: Callable[[str], bool] = None,
        project_exists_callback: Callable[[str], bool] = None,
        brand_exists_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            self.uid,
            compound_uid_by_property_value_callback=compound_uid_by_property_value_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            dictionary_term_exists_callback=dictionary_term_exists_callback,
            numeric_value_exists_callback=numeric_value_exists_callback,
            lag_time_exists_callback=lag_time_exists_callback,
            project_exists_callback=project_exists_callback,
            brand_exists_callback=brand_exists_callback,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
