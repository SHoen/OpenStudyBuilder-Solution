from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO, _AggregateRootType
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class SimpleConceptVO(ConceptVO):
    """
    The SimpleConceptVO acts as the value object for a single SimpleConcept aggregate
    """

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        name_sentence_case: Optional[str],
        definition: Optional[str],
        abbreviation: Optional[str],
        is_template_parameter: bool,
    ) -> "SimpleConceptVO":
        simple_concept_vo = cls(
            name=name,
            name_sentence_case=name_sentence_case,
            definition=definition,
            abbreviation=abbreviation,
            is_template_parameter=is_template_parameter,
        )

        return simple_concept_vo


@dataclass
class SimpleConceptAR(LibraryItemAggregateRootBase):
    _concept_vo: SimpleConceptVO

    @property
    def concept_vo(self) -> SimpleConceptVO:
        return self._concept_vo

    @property
    def name(self) -> str:
        return self.concept_vo.name

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        simple_concept_vo: SimpleConceptVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> _AggregateRootType:
        activity_ar = cls(
            _uid=uid,
            _concept_vo=simple_concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return activity_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        simple_concept_vo: SimpleConceptVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        find_uid_by_name_callback: Callable[[str], Optional[str]] = (lambda _: None),
    ) -> _AggregateRootType:
        item_metadata = LibraryItemMetadataVO(
            _change_description="Initial version",
            _status=LibraryItemStatus.FINAL,
            _author=author,
            _start_date=datetime.now(),
            _end_date=None,
            _major_version=1,
            _minor_version=0,
        )

        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        # Check whether simple concept with the same name already exits. If yes, return its uid, otherwise None.
        simple_concept_uid = find_uid_by_name_callback(simple_concept_vo.name)

        simple_concept_ar = cls(
            _uid=generate_uid_callback()
            if simple_concept_uid is None
            else simple_concept_uid,
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=simple_concept_vo,
        )
        return simple_concept_ar

    def approve(self, **kwargs) -> None:
        raise AttributeError(
            "approve function is not defined for SimpleConcept objects"
        )

    def inactivate(self, **kwargs) -> None:
        raise AttributeError(
            "inactivate function is not defined for SimpleConcept objects"
        )

    def reactivate(self, **kwargs) -> None:
        raise AttributeError(
            "reactivate function is not defined for SimpleConcept objects"
        )

    def _create_new_version(self, **kwargs) -> None:
        raise AttributeError(
            "_create_new_version function is not defined for SimpleConcept objects"
        )

    def _edit_draft(self, **kwargs) -> None:
        raise AttributeError(
            "edit_draft function is not defined for SimpleConcept objects"
        )

    def soft_delete(self) -> None:
        raise AttributeError(
            "_soft_delete function is not defined for SimpleConcept objects"
        )

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise AttributeError(
            "get_possible_functions function is not defined for SimpleConcept objects"
        )
