from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActivityGroupVO(ConceptVO):
    """
    The ActivityGroupVO acts as the value object for a single ActivityGroup aggregate
    """

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
    ) -> "ActivityGroupVO":
        activity_group_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
        )

        return activity_group_vo


@dataclass
class ActivityGroupAR(ConceptARBase):
    _concept_vo: ActivityGroupVO

    @property
    def concept_vo(self) -> ActivityGroupVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActivityGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        activity_group_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
    ) -> "ActivityGroupAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        if activity_group_exists_by_name_callback(concept_vo.name):
            raise ValueError(
                f"ActivityGroup with name ({concept_vo.name}) already exists."
            )

        activity_group_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_group_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: ActivityGroupVO,
        concept_exists_by_name_callback: Callable[[str], bool],
    ) -> False:
        """
        Creates a new draft version for the object.
        """
        if (
            concept_exists_by_name_callback(concept_vo.name)
            and self.concept_vo.name != concept_vo.name
        ):
            raise ValueError(
                f"ActivityGroup with name ({concept_vo.name}) already exists."
            )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
