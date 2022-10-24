from abc import abstractmethod
from dataclasses import dataclass
from typing import AbstractSet, Callable, Optional, TypeVar

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class ConceptVO:
    """
    The ConceptVO acts as the value object for a single ActivityInstance value object
    """

    name: str
    name_sentence_case: Optional[str]
    definition: Optional[str]
    abbreviation: Optional[str]
    is_template_parameter: bool

    def validate_uniqueness(
        self,
        lookup_callback: Callable[[str, str], str],
        uid: str,
        property_name: str,
        value: str,
        error_message: str,
    ):
        existing_node_uid = lookup_callback(property_name, value)
        if existing_node_uid and existing_node_uid != uid:
            raise ValueError(error_message)


_ConceptVOType = TypeVar("_ConceptVOType", bound=ConceptVO)
_AggregateRootType = TypeVar("_AggregateRootType")


@dataclass
class ConceptARBase(LibraryItemAggregateRootBase):
    """
    An abstract generic activity item aggregate for versioned activity items
    """

    _concept_vo: _ConceptVOType

    @property
    @abstractmethod
    def concept_vo(self) -> _ConceptVOType:
        raise NotImplementedError

    @concept_vo.setter
    def concept_vo(self, concept_vo: _ConceptVOType):
        self._concept_vo = concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: _ConceptVOType,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> _AggregateRootType:
        concept_ar = cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return concept_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        concept_vo: _ConceptVOType,
        library: LibraryVO,
        concept_exists_by_name_callback: Callable[[str], bool],
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> _AggregateRootType:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        if concept_exists_by_name_callback(concept_vo.name):
            raise ValueError(
                f"{cls.__name__} with name ({concept_vo.name}) already exists."
            )
        concept_ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )
        return concept_ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: _ConceptVOType,
        concept_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            concept_exists_by_name_callback(concept_vo.name)
            and self.name != concept_vo.name
        ):
            raise ValueError(
                f"{self.__class__.__name__} with name ({concept_vo.name}) already exists."
            )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self.concept_vo = concept_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()
