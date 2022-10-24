from dataclasses import dataclass
from typing import AbstractSet, Callable, Optional, Sequence

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)


@dataclass(frozen=True)
class CTCodelistAttributesVO:
    """
    The CTCodelistAttributesVO acts as the value object for a single CTCodelist attribute
    """

    name: Optional[str]
    catalogue_name: str
    parent_codelist_uid: Optional[str]
    child_codelist_uids: Optional[Sequence[str]]
    submission_value: Optional[str]
    preferred_term: Optional[str]
    definition: Optional[str]
    extensible: Optional[bool]

    @classmethod
    def from_repository_values(
        cls,
        name: Optional[str],
        catalogue_name: str,
        parent_codelist_uid: Optional[str],
        child_codelist_uids: Optional[Sequence[str]],
        submission_value: Optional[str],
        preferred_term: Optional[str],
        definition: Optional[str],
        extensible: Optional[bool],
    ) -> "CTCodelistAttributesVO":
        ct_codelist_attribute_vo = cls(
            name=name,
            catalogue_name=catalogue_name,
            parent_codelist_uid=parent_codelist_uid,
            child_codelist_uids=child_codelist_uids,
            submission_value=submission_value,
            preferred_term=preferred_term,
            definition=definition,
            extensible=extensible,
        )

        return ct_codelist_attribute_vo

    @classmethod
    def from_input_values(
        cls,
        name: Optional[str],
        catalogue_name: str,
        parent_codelist_uid: Optional[str],
        submission_value: Optional[str],
        preferred_term: Optional[str],
        definition: Optional[str],
        extensible: Optional[bool],
        catalogue_exists_callback: Callable[[str], bool],
        codelist_exists_by_uid_callback: Callable[[str], bool] = lambda _: False,
        codelist_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
        codelist_exists_by_submission_value_callback: Callable[
            [str], bool
        ] = lambda _: False,
        child_codelist_uids: Optional[str] = None,
    ) -> "CTCodelistAttributesVO":
        if (
            not codelist_exists_by_uid_callback(parent_codelist_uid)
            and parent_codelist_uid
        ):
            raise ValueError(
                f"There is no codelist identified by provided parent codelist uid ({parent_codelist_uid})"
            )

        if not catalogue_exists_callback(catalogue_name):
            raise ValueError(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )
        if codelist_exists_by_name_callback(name):
            raise ValueError(f"CTCodelistAttributes with name ({name}) already exists")
        if codelist_exists_by_submission_value_callback(submission_value):
            raise ValueError(
                f"CTCodelistAttributes with submission_value ({submission_value}) already exists"
            )

        ct_codelist_attribute_vo = cls(
            name=name,
            parent_codelist_uid=parent_codelist_uid,
            child_codelist_uids=child_codelist_uids,
            catalogue_name=catalogue_name,
            submission_value=submission_value,
            preferred_term=preferred_term,
            definition=definition,
            extensible=extensible,
        )

        return ct_codelist_attribute_vo


@dataclass
class CTCodelistAttributesAR(LibraryItemAggregateRootBase):
    _ct_codelist_attributes_vo: CTCodelistAttributesVO

    @property
    def name(self) -> str:
        return self._ct_codelist_attributes_vo.name

    @property
    def ct_codelist_vo(self) -> CTCodelistAttributesVO:
        return self._ct_codelist_attributes_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_codelist_attributes_vo: CTCodelistAttributesVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "CTCodelistAttributesAR":
        ct_codelist_ar = cls(
            _uid=uid,
            _ct_codelist_attributes_vo=ct_codelist_attributes_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_codelist_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_codelist_attributes_vo: CTCodelistAttributesVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "CTCodelistAttributesAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_codelist_attributes_vo=ct_codelist_attributes_vo,
        )
        return ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        ct_codelist_vo: CTCodelistAttributesVO,
        codelist_exists_by_name_callback: Callable[[str], bool],
        codelist_exists_by_submission_value_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        # if codelist_exists_by_name_callback(ct_codelist_vo.name, self.uid):
        if (
            codelist_exists_by_name_callback(ct_codelist_vo.name)
            and self.name != ct_codelist_vo.name
        ):
            raise ValueError(
                f"CTCodelistAttributes with name ({ct_codelist_vo.name}) already exists."
            )
        if (
            codelist_exists_by_submission_value_callback(
                ct_codelist_vo.submission_value
            )
            and self.ct_codelist_vo.submission_value != ct_codelist_vo.submission_value
        ):
            raise ValueError(
                f"CTCodelistAttributes with submission_value ({ct_codelist_vo.submission_value}) already exists."
            )
        if self._ct_codelist_attributes_vo != ct_codelist_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_codelist_attributes_vo = ct_codelist_vo

    def create_new_version(self, author: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author=author)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self.library.is_editable:
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
