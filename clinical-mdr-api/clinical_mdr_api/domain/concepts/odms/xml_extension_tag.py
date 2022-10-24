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
class OdmXmlExtensionTagVO(ConceptVO):
    xml_extension_uid: str
    parent_xml_extension_tag_uid: Optional[str]
    child_xml_extension_tag_uids: Optional[Sequence[str]]
    xml_extension_attribute_uids: Optional[Sequence[str]]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        xml_extension_uid: str,
        parent_xml_extension_tag_uid: Optional[str],
        child_xml_extension_tag_uids: Optional[Sequence[str]] = None,
        xml_extension_attribute_uids: Optional[Sequence[str]] = None,
    ) -> "OdmXmlExtensionTagVO":
        if child_xml_extension_tag_uids is None:
            child_xml_extension_tag_uids = []
        if xml_extension_attribute_uids is None:
            xml_extension_attribute_uids = []

        return cls(
            name=name,
            xml_extension_uid=xml_extension_uid,
            parent_xml_extension_tag_uid=parent_xml_extension_tag_uid,
            child_xml_extension_tag_uids=child_xml_extension_tag_uids,
            xml_extension_attribute_uids=xml_extension_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        odm_xml_extension_exists_by_callback: Callable[[str, str, bool], bool],
    ) -> None:

        if (
            self.xml_extension_uid is not None
            and not odm_xml_extension_exists_by_callback(
                "uid", self.xml_extension_uid, True
            )
        ):
            raise BusinessLogicException(
                f"OdmXmlExtensionTag tried to connect to non existing OdmXmlExtension identified by uid ({self.xml_extension_uid})."
            )

        if (
            self.parent_xml_extension_tag_uid is not None
            and not concept_exists_by_callback(
                "uid", self.parent_xml_extension_tag_uid, True
            )
        ):
            raise BusinessLogicException(
                f"OdmXmlExtensionTag tried to connect to non existing OdmXmlExtensionTag identified by uid ({self.parent_xml_extension_tag_uid})."
            )


@dataclass
class OdmXmlExtensionTagAR(OdmARBase):
    _concept_vo: OdmXmlExtensionTagVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmXmlExtensionTagVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmXmlExtensionTagVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmXmlExtensionTagAR":
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
        concept_vo: OdmXmlExtensionTagVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        concept_exists_by_callback: Callable[[str, str], bool] = lambda _: True,
        odm_xml_extension_exists_by_callback: Callable[
            [str, str], bool
        ] = lambda _: False,
    ) -> "OdmXmlExtensionTagAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            odm_xml_extension_exists_by_callback=odm_xml_extension_exists_by_callback,
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
        concept_vo: OdmXmlExtensionTagVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmXmlExtensionTagRelationVO:
    uid: str
    name: str
    value: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        value: str,
    ) -> "OdmXmlExtensionTagRelationVO":
        return cls(
            uid=uid,
            name=name,
            value=value,
        )
