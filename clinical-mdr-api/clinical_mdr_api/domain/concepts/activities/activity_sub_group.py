from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase, ConceptVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class ActivitySubGroupVO(ConceptVO):
    """
    The ActivitySubGroupVO acts as the value object for a single ActivitySubGroup aggregate
    """

    activity_group: str

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        activity_group: Optional[str],
    ) -> "ActivitySubGroupVO":
        activity_sub_group_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=True,
            activity_group=activity_group if activity_group is not None else None,
        )

        return activity_sub_group_vo

    def validate(
        self,
        activity_sub_group_exists_by_name_callback: Callable[[str], bool],
        activity_group_exists: Callable[[str], bool],
        previous_name: Optional[str] = None,
    ):
        if (
            activity_sub_group_exists_by_name_callback(self.name)
            and previous_name != self.name
        ):
            raise ValueError(
                f"ActivitySubGroup with name ({self.name}) already exists."
            )
        if not activity_group_exists(self.activity_group):
            raise ValueError(
                f"ActivitySubGroup tried to connect to non existing ActivityGroup identified by uid ({self.activity_group})."
            )


@dataclass
class ActivitySubGroupAR(ConceptARBase):
    _concept_vo: ActivitySubGroupVO

    @property
    def concept_vo(self) -> ActivitySubGroupVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: ActivitySubGroupVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        activity_sub_group_exists_by_name_callback: Callable[
            [str], bool
        ] = lambda _: True,
        activity_group_exists: Callable[[str], bool] = lambda _: False,
    ) -> "ActivitySubGroupAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        concept_vo.validate(
            activity_sub_group_exists_by_name_callback=activity_sub_group_exists_by_name_callback,
            activity_group_exists=activity_group_exists,
        )

        activity_sub_group_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return activity_sub_group_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: ActivitySubGroupVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        activity_group_exists: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            activity_sub_group_exists_by_name_callback=concept_exists_by_name_callback,
            activity_group_exists=activity_group_exists,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
