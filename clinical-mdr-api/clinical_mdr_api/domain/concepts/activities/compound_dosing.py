from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceVO,
)
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class CompoundDosingVO(ActivityInstanceVO):
    """
    The CompoundDosingVO acts as the single value object for CompoundDosingAR aggregate.
    """

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
        activity_type: Optional[str],
    ) -> "CompoundDosingVO":
        compound_dosing_vo = cls(
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
            specimen_uid=None,
            specimen_name=None,
        )

        return compound_dosing_vo

    def validate(
        self,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        activity_exists_by_name_callback: Callable[[str], bool] = None,
        previous_name: Optional[str] = None,
    ) -> None:

        super().validate(
            activity_exists_by_name_callback=activity_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            previous_name=previous_name,
        )


class CompoundDosingAR(ConceptARBase):
    _concept_vo: CompoundDosingVO

    @property
    def concept_vo(self) -> CompoundDosingVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: CompoundDosingVO,
        library: LibraryVO,
        compound_dosing_exists_by_name_callback: Callable[[str], bool],
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool],
        ct_term_exists_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "CompoundDosingAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            activity_exists_by_name_callback=compound_dosing_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
        )

        compound_dosing_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return compound_dosing_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: CompoundDosingVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        activity_hierarchy_exists_by_uid_callback: Callable[[str], bool] = None,
        ct_term_exists_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_exists_by_name_callback=concept_exists_by_name_callback,
            activity_hierarchy_exists_by_uid_callback=activity_hierarchy_exists_by_uid_callback,
            ct_term_exists_callback=ct_term_exists_callback,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo