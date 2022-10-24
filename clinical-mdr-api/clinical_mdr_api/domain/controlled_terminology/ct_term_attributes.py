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
class CTTermAttributesVO:
    """
    The CTTermAttributesVO acts as the value object for a single CTTerm attribute
    """

    codelist_uid: str
    catalogue_name: str
    concept_id: Optional[str]
    code_submission_value: Optional[str]
    name_submission_value: Optional[str]
    preferred_term: Optional[str]
    definition: Optional[str]

    @classmethod
    def from_repository_values(
        cls,
        codelist_uid: str,
        catalogue_name: str,
        concept_id: Optional[str],
        code_submission_value: Optional[str],
        name_submission_value: Optional[str],
        preferred_term: Optional[str],
        definition: Optional[str],
    ) -> "CTTermAttributesVO":
        ct_term_attributes_vo = cls(
            codelist_uid=codelist_uid,
            catalogue_name=catalogue_name,
            concept_id=concept_id,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attributes_vo

    @classmethod
    def from_input_values(
        cls,
        codelist_uid: str,
        catalogue_name: str,
        code_submission_value: Optional[str],
        name_submission_value: Optional[str],
        preferred_term: Optional[str],
        definition: Optional[str],
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
        term_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
        term_exists_by_code_submission_value_callback: Callable[
            [str], bool
        ] = lambda _: False,
    ) -> "CTTermAttributesVO":

        if not codelist_exists_callback(codelist_uid):
            raise ValueError(
                f"There is no codelist identified by provided codelist uid ({codelist_uid})"
            )
        if not catalogue_exists_callback(catalogue_name):
            raise ValueError(
                f"There is no catalogue identified by provided catalogue name ({catalogue_name})"
            )
        if term_exists_by_name_callback(name_submission_value):
            raise ValueError(
                f"CTTermAttributes with name ({name_submission_value}) already exists"
            )
        if term_exists_by_code_submission_value_callback(code_submission_value):
            raise ValueError(
                f"CTTermAttributes with code_submission_value ({code_submission_value}) already exists"
            )

        ct_term_attribute_vo = cls(
            codelist_uid=codelist_uid,
            catalogue_name=catalogue_name,
            concept_id=None,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attribute_vo


@dataclass
class CTTermAttributesAR(LibraryItemAggregateRootBase):
    _ct_term_attributes_vo: CTTermAttributesVO

    @property
    def name(self) -> str:
        return self._ct_term_attributes_vo.name_submission_value

    @property
    def ct_term_vo(self) -> CTTermAttributesVO:
        return self._ct_term_attributes_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "CTTermAttributesAR":
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_attributes_vo=ct_term_attributes_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "CTTermAttributesAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        ar = cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_term_attributes_vo=ct_term_attributes_vo,
        )
        return ar

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        ct_term_vo: CTTermAttributesVO,
        term_exists_by_name_callback: Callable[[str], bool],
        term_exists_by_code_submission_value_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if (
            term_exists_by_name_callback(ct_term_vo.name_submission_value)
            and self.ct_term_vo.name_submission_value
            != ct_term_vo.name_submission_value
        ):
            raise ValueError(
                f"CTTermAttributes with name ({ct_term_vo.name_submission_value}) already exists."
            )
        if (
            term_exists_by_code_submission_value_callback(
                ct_term_vo.code_submission_value
            )
            and self.ct_term_vo.code_submission_value
            != ct_term_vo.code_submission_value
        ):
            raise ValueError(
                f"CTTermAttributes with code_submission_value ({ct_term_vo.code_submission_value}) already exists."
            )
        if self._ct_term_attributes_vo != ct_term_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._ct_term_attributes_vo = ct_term_vo

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
