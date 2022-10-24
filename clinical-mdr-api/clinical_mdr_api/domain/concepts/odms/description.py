from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass(frozen=True)
class OdmDescriptionVO(ConceptVO):
    language: str
    description: str
    instruction: str
    sponsor_instruction: str

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        language: str,
        description: str,
        instruction: str,
        sponsor_instruction: str,
    ) -> "OdmDescriptionVO":
        return cls(
            name=name,
            language=language,
            description=description,
            instruction=instruction,
            sponsor_instruction=sponsor_instruction,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )


@dataclass
class OdmDescriptionAR(OdmARBase):
    _concept_vo: OdmDescriptionVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmDescriptionVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmDescriptionVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmDescriptionAR":
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
        concept_vo: OdmDescriptionVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "OdmDescriptionAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

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
        concept_vo: OdmDescriptionVO,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
