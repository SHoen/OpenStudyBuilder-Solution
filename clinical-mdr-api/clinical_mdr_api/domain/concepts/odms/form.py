from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.utils import booltostr


@dataclass(frozen=True)
class OdmFormVO(ConceptVO):
    oid: str
    repeating: bool
    sdtm_version: str
    scope_uid: str
    description_uids: Sequence[str]
    alias_uids: Optional[Sequence[str]]
    activity_group_uids: Optional[Sequence[str]]
    item_group_uids: Optional[Sequence[str]]
    xml_extension_attribute_uids: Optional[Sequence[str]]
    xml_extension_tag_uids: Optional[Sequence[str]]
    xml_extension_tag_attribute_uids: Optional[Sequence[str]]

    @classmethod
    def from_repository_values(
        cls,
        oid: str,
        name: str,
        sdtm_version: str,
        repeating: bool,
        scope_uid: str,
        description_uids: Sequence[str],
        alias_uids: Optional[Sequence[str]],
        activity_group_uids: Optional[Sequence[str]] = None,
        item_group_uids: Optional[Sequence[str]] = None,
        xml_extension_tag_uids: Optional[Sequence[str]] = None,
        xml_extension_attribute_uids: Optional[Sequence[str]] = None,
        xml_extension_tag_attribute_uids: Optional[Sequence[str]] = None,
    ) -> "OdmFormVO":
        if activity_group_uids is None:
            activity_group_uids = []
        if item_group_uids is None:
            item_group_uids = []
        if xml_extension_tag_uids is None:
            xml_extension_tag_uids = []
        if xml_extension_attribute_uids is None:
            xml_extension_attribute_uids = []
        if xml_extension_tag_attribute_uids is None:
            xml_extension_tag_attribute_uids = []

        return cls(
            oid=oid,
            name=name,
            sdtm_version=sdtm_version,
            repeating=repeating,
            scope_uid=scope_uid,
            description_uids=description_uids,
            alias_uids=alias_uids,
            activity_group_uids=activity_group_uids,
            item_group_uids=item_group_uids,
            xml_extension_tag_uids=xml_extension_tag_uids,
            xml_extension_attribute_uids=xml_extension_attribute_uids,
            xml_extension_tag_attribute_uids=xml_extension_tag_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        concept_exists_by_callback: Callable[[str, str, bool], bool],
        find_term_callback: Callable[[str], CTTermAttributesAR],
        odm_description_exists_by_callback: Callable[[str, str, bool], bool],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        previous_name: Optional[str] = None,
        previous_oid: Optional[str] = None,
    ) -> None:

        if concept_exists_by_callback("name", self.name) and previous_name != self.name:
            raise BusinessLogicException(
                f"OdmForm with name ({self.name}) already exists."
            )

        if concept_exists_by_callback("oid", self.oid) and previous_oid != self.oid:
            raise BusinessLogicException(
                f"OdmForm with OID ({self.oid}) already exists."
            )

        if self.scope_uid is not None and not find_term_callback(self.scope_uid):
            raise BusinessLogicException(
                f"OdmItem tried to connect to non existing CTTerm identified by uid ({self.scope_uid})."
            )

        for description_uid in self.description_uids:
            desc = odm_description_exists_by_callback("uid", description_uid, True)
            if not desc:
                raise BusinessLogicException(
                    f"OdmForm tried to connect to non existing OdmDescription identified by uid ({description_uid})."
                )

        for alias_uid in self.alias_uids:
            if not odm_alias_exists_by_callback("uid", alias_uid, True):
                raise BusinessLogicException(
                    f"OdmForm tried to connect to non existing OdmAlias identified by uid ({alias_uid})."
                )


@dataclass
class OdmFormAR(OdmARBase):
    _concept_vo: OdmFormVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmFormVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmFormVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmFormAR":
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
        concept_vo: OdmFormVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        concept_exists_by_callback: Callable[[str, str, bool], bool] = lambda _: True,
        find_term_callback: Callable[[str], bool] = lambda _: False,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda _: False,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda _: False,
    ) -> "OdmFormAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_term_callback=find_term_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
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
        concept_vo: OdmFormVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        concept_exists_by_callback: Callable[[str, str, bool], bool] = None,
        find_term_callback: Callable[[str], bool] = None,
        odm_description_exists_by_callback: Callable[[str, str, bool], bool] = None,
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            find_term_callback=find_term_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            previous_name=self.name,
            previous_oid=self._concept_vo.oid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmFormRefVO:
    uid: str
    name: str
    template_uid: str
    order_number: int
    mandatory: bool
    locked: bool
    collection_exception_condition_oid: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        template_uid: str,
        order_number: int,
        mandatory: bool,
        locked: bool,
        collection_exception_condition_oid: str,
    ) -> "OdmFormRefVO":
        return cls(
            uid=uid,
            name=name,
            template_uid=template_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            locked=booltostr(locked),
            collection_exception_condition_oid=collection_exception_condition_oid,
        )
