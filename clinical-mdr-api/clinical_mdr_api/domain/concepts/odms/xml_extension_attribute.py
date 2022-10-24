from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.concepts.odms.xml_extension import OdmXmlExtensionAR
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import OdmXmlExtensionTagAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class OdmXmlExtensionAttributeVO(ConceptVO):
    xml_extension_uid: Optional[str]
    xml_extension_tag_uid: Optional[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        xml_extension_uid: Optional[str],
        xml_extension_tag_uid: Optional[str],
    ) -> "OdmXmlExtensionAttributeVO":

        return cls(
            name=name,
            xml_extension_uid=xml_extension_uid,
            xml_extension_tag_uid=xml_extension_tag_uid,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        find_odm_xml_extension_callback: Callable[[str], OdmXmlExtensionAR],
        find_odm_xml_extension_tag_callback: Callable[[str], OdmXmlExtensionTagAR],
    ) -> None:

        if self.xml_extension_uid is not None:
            if not find_odm_xml_extension_callback(self.xml_extension_uid):
                raise BusinessLogicException(
                    f"OdmXmlExtensionAttribute tried to connect to non existing OdmXmlExtension identified by uid ({self.xml_extension_uid})."
                )

        if self.xml_extension_tag_uid is not None:
            if not find_odm_xml_extension_tag_callback(self.xml_extension_tag_uid):
                raise BusinessLogicException(
                    f"OdmXmlExtensionAttribute tried to connect to non existing OdmXmlExtensionTag identified by uid ({self.xml_extension_tag_uid})."
                )


@dataclass
class OdmXmlExtensionAttributeAR(OdmARBase):
    _concept_vo: OdmXmlExtensionAttributeVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmXmlExtensionAttributeVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmXmlExtensionAttributeVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmXmlExtensionAttributeAR":
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
        concept_vo: OdmXmlExtensionAttributeVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        find_odm_xml_extension_callback: Callable[
            [str], Optional[OdmXmlExtensionAR]
        ] = lambda _: False,
        find_odm_xml_extension_tag_callback: Callable[
            [str], Optional[OdmXmlExtensionTagAR]
        ] = lambda _: False,
    ) -> "OdmXmlExtensionAttributeAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            find_odm_xml_extension_callback=find_odm_xml_extension_callback,
            find_odm_xml_extension_tag_callback=find_odm_xml_extension_tag_callback,
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
        concept_vo: OdmXmlExtensionAttributeVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmXmlExtensionAttributeRelationVO:
    uid: str
    name: str
    value: str
    odm_xml_extension_uid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        value: str,
        odm_xml_extension_uid: str,
    ) -> "OdmXmlExtensionAttributeRelationVO":
        return cls(
            uid=uid,
            name=name,
            value=value,
            odm_xml_extension_uid=odm_xml_extension_uid,
        )


@dataclass(frozen=True)
class OdmXmlExtensionAttributeTagRelationVO:
    uid: str
    name: str
    value: str
    odm_xml_extension_tag_uid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        value: str,
        odm_xml_extension_tag_uid: str,
    ) -> "OdmXmlExtensionAttributeTagRelationVO":
        return cls(
            uid=uid,
            name=name,
            value=value,
            odm_xml_extension_tag_uid=odm_xml_extension_tag_uid,
        )
