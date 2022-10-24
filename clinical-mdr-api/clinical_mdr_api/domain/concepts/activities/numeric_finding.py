from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.activities.categoric_finding import FindingVO
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class NumericFindingVO(FindingVO):
    """
    The CategoricFindingVO acts as the value object for a single CategoricFindingAR aggregate
    """

    molecular_weight: Optional[int]
    convert_to_si_unit: Optional[bool]
    convert_to_us_conventional_unit: Optional[bool]
    unit_dimension_uid: Optional[str]
    unit_definition_uid: Optional[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        topic_code: str,
        adam_param_code: str,
        legacy_description: Optional[str],
        sdtm_variable_uid: Optional[str],
        sdtm_variable_name: Optional[str],
        sdtm_subcat_uid: Optional[str],
        sdtm_subcat_name: Optional[str],
        sdtm_cat_uid: Optional[str],
        sdtm_cat_name: Optional[str],
        sdtm_domain_uid: Optional[str],
        sdtm_domain_name: Optional[str],
        activity_uids: Sequence[str],
        value_sas_display_format: Optional[str],
        specimen_uid: Optional[str],
        specimen_name: Optional[str],
        test_code_uid: Optional[str],
        molecular_weight: Optional[int],
        convert_to_si_unit: Optional[bool],
        convert_to_us_conventional_unit: Optional[bool],
        unit_dimension_uid: Optional[str],
        unit_definition_uid: Optional[str],
        activity_type: Optional[str],
    ) -> "NumericFindingVO":
        numeric_finding_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_type=activity_type,
            topic_code=topic_code,
            adam_param_code=adam_param_code,
            legacy_description=legacy_description,
            sdtm_variable_uid=sdtm_variable_uid,
            sdtm_variable_name=sdtm_variable_name,
            sdtm_subcat_uid=sdtm_subcat_uid,
            sdtm_subcat_name=sdtm_subcat_name,
            sdtm_cat_uid=sdtm_cat_uid,
            sdtm_cat_name=sdtm_cat_name,
            sdtm_domain_uid=sdtm_domain_uid,
            sdtm_domain_name=sdtm_domain_name,
            activity_uids=activity_uids,
            value_sas_display_format=value_sas_display_format,
            specimen_uid=specimen_uid,
            specimen_name=specimen_name,
            test_code_uid=test_code_uid,
            molecular_weight=molecular_weight,
            convert_to_si_unit=convert_to_si_unit,
            convert_to_us_conventional_unit=convert_to_us_conventional_unit,
            unit_dimension_uid=unit_dimension_uid,
            unit_definition_uid=unit_definition_uid,
        )

        return numeric_finding_vo

    def validate(
        self,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        activity_exists_by_name_callback: Callable[[str], bool] = None,
        previous_name: Optional[str] = None,
        unit_definition_exists_callback: Callable[[str], bool] = None,
    ):

        super().validate(
            activity_exists_by_name_callback=activity_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            previous_name=previous_name,
        )

        if self.unit_dimension_uid is not None and not ct_term_exists_callback(
            self.unit_dimension_uid
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing unit dimension identified by uid ({self.unit_dimension_uid})"
            )
        if (
            self.unit_definition_uid is not None
            and not unit_definition_exists_callback(self.unit_definition_uid)
        ):
            raise ValueError(
                f"{self.__class__.__name__} tried to connect to non existing unit definition identified by uid ({self.unit_definition_uid})"
            )


class NumericFindingAR(ConceptARBase):
    _concept_vo: NumericFindingVO

    @property
    def concept_vo(self) -> NumericFindingVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: NumericFindingVO,
        library: LibraryVO,
        numeric_finding_exists_by_name_callback: Callable[[str], bool],
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        unit_definition_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "NumericFindingAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            activity_exists_by_name_callback=numeric_finding_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            unit_definition_exists_callback=unit_definition_exists_callback,
        )

        numeric_finding_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return numeric_finding_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: NumericFindingVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool] = None,
        ct_term_exists_callback: Callable[[str], bool] = None,
        unit_definition_exists_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            unit_definition_exists_callback=unit_definition_exists_callback,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
