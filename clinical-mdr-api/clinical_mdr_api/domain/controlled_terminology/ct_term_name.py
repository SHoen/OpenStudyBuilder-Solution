from dataclasses import dataclass
from typing import AbstractSet, Callable, Optional

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class CTTermNameVO:
    """
    The CTTermNameVO acts as the value object for a single CTTerm name
    """

    codelist_uid: str
    name: Optional[str]
    name_sentence_case: Optional[str]
    catalogue_name: str
    order: Optional[int]

    @classmethod
    def from_repository_values(
        cls,
        codelist_uid: str,
        name: Optional[str],
        name_sentence_case: Optional[str],
        order: Optional[int],
        catalogue_name: str,
    ) -> "CTTermNameVO":
        ct_term_name_vo = cls(
            codelist_uid=codelist_uid,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
            order=order,
        )

        return ct_term_name_vo

    @classmethod
    def from_input_values(
        cls,
        codelist_uid: str,
        name: Optional[str],
        name_sentence_case: Optional[str],
        order: Optional[int],
        catalogue_name: str,
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
    ) -> "CTTermNameVO":

        if not codelist_exists_callback(codelist_uid):
            raise ValueError(
                f"There is no codelist identified by provided codelist uid ({codelist_uid})"
            )
        if not catalogue_exists_callback(catalogue_name):
            raise ValueError(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )

        ct_term_name_vo = cls(
            codelist_uid=codelist_uid,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
            order=order,
        )

        return ct_term_name_vo


@dataclass
class CTTermNameAR(LibraryItemAggregateRootBase):
    _ct_term_name_vo: CTTermNameVO

    @property
    def name(self) -> str:
        return self._ct_term_name_vo.name

    @property
    def ct_term_vo(self) -> CTTermNameVO:
        return self._ct_term_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_name_vo: CTTermNameVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "CTTermNameAR":
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_name_vo=ct_term_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_term_name_vo: CTTermNameVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "CTTermNameAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_term_name_vo=ct_term_name_vo,
        )
        return ar

    def edit_draft(
        self, author: str, change_description: Optional[str], ct_term_vo: CTTermNameVO
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if self._ct_term_name_vo != ct_term_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_term_name_vo = ct_term_vo

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

    def set_new_order(self, codelist_uid: str, new_order: int) -> None:
        ct_term_vo = CTTermNameVO.from_input_values(
            codelist_uid=codelist_uid,
            catalogue_name=self.ct_term_vo.catalogue_name,
            name=self.name,
            name_sentence_case=self.ct_term_vo.name_sentence_case,
            order=new_order,
            # passing always True callbacks, as we can't change catalogue
            # in scope of CTTermName or CTTermAttributes, it can be only changed via CTTermRoot
            codelist_exists_callback=lambda _: True,
            catalogue_exists_callback=lambda _: True,
        )
        self._ct_term_name_vo = ct_term_vo
