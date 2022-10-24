from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class OdmAliasVO(ConceptVO):
    context: str

    @classmethod
    def from_repository_values(cls, name: str, context: str) -> "OdmAliasVO":
        return cls(
            name=name,
            context=context,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        odm_alias_exists_by_name_callback: Callable[[str], bool],
        previous_name: Optional[str] = None,
    ) -> None:

        if odm_alias_exists_by_name_callback(self.name) and previous_name != self.name:
            raise BusinessLogicException(
                f"OdmAlias with name ({self.name}) already exists."
            )


@dataclass
class OdmAliasAR(OdmARBase):
    _concept_vo: OdmAliasVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmAliasVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmAliasVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmAliasAR":
        return cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author: str,
        concept_vo: OdmAliasVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        concept_exists_by_name_callback: Callable[[str], bool] = lambda _: True,
    ) -> "OdmAliasAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            odm_alias_exists_by_name_callback=concept_exists_by_name_callback
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )

    def edit_draft(
        self,
        author: str,
        change_description: Optional[str],
        concept_vo: OdmAliasVO,
        concept_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            odm_alias_exists_by_name_callback=concept_exists_by_name_callback,
            previous_name=self.name,
        )
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
