from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class OdmXmlExtensionVO(ConceptVO):
    name: str
    prefix: str
    namespace: str
    xml_extension_tag_uids: Optional[Sequence[str]]
    xml_extension_attribute_uids: Optional[Sequence[str]]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        prefix: str,
        namespace: str,
        xml_extension_tag_uids: Optional[Sequence[str]] = None,
        xml_extension_attribute_uids: Optional[Sequence[str]] = None,
    ) -> "OdmXmlExtensionVO":
        if xml_extension_tag_uids is None:
            xml_extension_tag_uids = []
        if xml_extension_attribute_uids is None:
            xml_extension_attribute_uids = []

        return cls(
            name=name,
            prefix=prefix,
            namespace=namespace,
            xml_extension_tag_uids=xml_extension_tag_uids,
            xml_extension_attribute_uids=xml_extension_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        previous_prefix: Optional[str] = None,
        previous_namespace: Optional[str] = None,
    ) -> None:

        if (
            concept_exists_by_callback("prefix", self.prefix)
            and previous_prefix != self.prefix
        ) and (
            concept_exists_by_callback("namespace", self.namespace)
            and previous_namespace != self.namespace
        ):
            raise BusinessLogicException(
                f"OdmXmlExtension with prefix ({self.prefix}) and namespace ({self.namespace}) already exists."
            )


@dataclass
class OdmXmlExtensionAR(OdmARBase):
    _concept_vo: OdmXmlExtensionVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmXmlExtensionVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmXmlExtensionVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmXmlExtensionAR":
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
        concept_vo: OdmXmlExtensionVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        concept_exists_by_callback: Callable[[str, str, bool], bool] = lambda _: True,
    ) -> "OdmXmlExtensionAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
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
        concept_vo: OdmXmlExtensionVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        concept_exists_by_callback: Callable[[str, str, bool], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            previous_prefix=self.concept_vo.prefix,
            previous_namespace=self.concept_vo.namespace,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo
