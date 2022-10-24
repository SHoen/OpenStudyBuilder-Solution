from dataclasses import dataclass, field
from enum import Enum
from typing import AbstractSet, Any, Callable, List, Optional, Tuple

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


class DictionaryType(Enum):
    """
    Enum for Type of dictionary
    """

    SNOMED = "SNOMED"
    MED_RT = "MED-RT"
    UNII = "UNII"
    UCUM = "UCUM"


@dataclass(frozen=True)
class DictionaryCodelistVO:
    """
    The DictionaryCodelistVO acts as the value object for a single DictionaryCodelist item
    """

    name: str
    is_template_parameter: bool

    current_terms: List[Tuple[str, str]]
    previous_terms: List[Tuple[str, str]]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        is_template_parameter: bool,
        current_terms: List[Tuple[str, str]],
        previous_terms: List[Tuple[str, str]],
    ) -> "DictionaryCodelistVO":
        dictionary_codelist_vo = cls(
            name=name,
            is_template_parameter=is_template_parameter,
            current_terms=current_terms,
            previous_terms=previous_terms,
        )

        return dictionary_codelist_vo

    @classmethod
    def from_input_values(
        cls,
        name: str,
        is_template_parameter: bool,
        current_terms: List[Tuple[str, str]],
        previous_terms: List[Tuple[str, str]],
        codelist_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
    ) -> "DictionaryCodelistVO":
        if codelist_exists_by_name_callback(name):
            raise ValueError(f"DictionaryCodelist with name ({name}) already exists")

        dictionary_codelist_vo = cls(
            name=name,
            is_template_parameter=is_template_parameter,
            current_terms=current_terms,
            previous_terms=previous_terms,
        )

        return dictionary_codelist_vo


@dataclass
class DictionaryCodelistAR(LibraryItemAggregateRootBase):
    _dictionary_codelist_vo: DictionaryCodelistVO
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    @property
    def name(self) -> str:
        return self.dictionary_codelist_vo.name

    @property
    def dictionary_codelist_vo(self) -> DictionaryCodelistVO:
        return self._dictionary_codelist_vo

    @dictionary_codelist_vo.setter
    def dictionary_codelist_vo(self, dictionary_codelist_vo):
        self._dictionary_codelist_vo = dictionary_codelist_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        dictionary_codelist_vo: DictionaryCodelistVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "DictionaryCodelistAR":
        dictionary_codelist_ar = cls(
            _uid=uid,
            _dictionary_codelist_vo=dictionary_codelist_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return dictionary_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        dictionary_codelist_vo: DictionaryCodelistVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "DictionaryCodelistAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _dictionary_codelist_vo=dictionary_codelist_vo,
        )
        return ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        dictionary_codelist_vo: DictionaryCodelistVO,
        codelist_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            codelist_exists_by_name_callback(dictionary_codelist_vo.name)
            and self.name != dictionary_codelist_vo.name
        ):
            raise ValueError(
                f"DictionaryCodelist with name ({dictionary_codelist_vo.name}) already exists."
            )
        if self._dictionary_codelist_vo != dictionary_codelist_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self.dictionary_codelist_vo = dictionary_codelist_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION}
        return frozenset()

    def inactivate(self, author: str, change_description: str = None):
        """
        Inactivates latest version.
        """
        raise NotImplementedError()

    def reactivate(self, author: str, change_description: str = None):
        """
        Reactivates latest retired version and sets the version to draft.
        """
        raise NotImplementedError()

    def soft_delete(self):
        raise NotImplementedError()

    def add_term(self, codelist_uid: str, term_uid: str, author: str) -> None:
        if term_uid in [term[0] for term in self.dictionary_codelist_vo.current_terms]:
            raise ValueError(
                f"The codelist identified by {codelist_uid} "
                f"already has a term identified by {term_uid}"
            )
        current_terms = self.dictionary_codelist_vo.current_terms
        current_terms.append((term_uid, author))
        self.dictionary_codelist_vo = DictionaryCodelistVO.from_repository_values(
            name=self.dictionary_codelist_vo.name,
            is_template_parameter=self.dictionary_codelist_vo.is_template_parameter,
            current_terms=current_terms,
            previous_terms=self.dictionary_codelist_vo.previous_terms,
        )

    def remove_term(self, codelist_uid: str, term_uid: str, author: str) -> None:
        if term_uid not in [
            term[0] for term in self.dictionary_codelist_vo.current_terms
        ]:
            raise ValueError(
                f"The codelist identified by {codelist_uid} doesn't have a term identified by {term_uid}"
            )
        previous_terms = self.dictionary_codelist_vo.previous_terms
        previous_terms.append((term_uid, author))

        current_terms = self.dictionary_codelist_vo.current_terms
        # removing term_uid from list of current terms
        current_terms = [
            current_term
            for current_term in current_terms
            if current_term[0] != term_uid
        ]
        self.dictionary_codelist_vo = DictionaryCodelistVO.from_repository_values(
            name=self.dictionary_codelist_vo.name,
            is_template_parameter=self.dictionary_codelist_vo.is_template_parameter,
            current_terms=current_terms,
            previous_terms=previous_terms,
        )
