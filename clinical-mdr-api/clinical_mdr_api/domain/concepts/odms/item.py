from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.concept_base import ConceptVO
from clinical_mdr_api.domain.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.utils import GenericFilteringReturn, booltostr


@dataclass(frozen=True)
class OdmItemVO(ConceptVO):
    oid: str
    prompt: str
    datatype: str
    length: int
    significant_digits: int
    sas_field_name: str
    sds_var_name: str
    origin: str
    comment: Optional[str]
    description_uids: Sequence[str]
    alias_uids: Optional[Sequence[str]]
    unit_definition_uids: Optional[Sequence[str]]
    codelist_uid: Optional[str]
    term_uids: Optional[Sequence[str]]
    activity_uids: Optional[Sequence[str]]
    xml_extension_attribute_uids: Optional[Sequence[str]]
    xml_extension_tag_uids: Optional[Sequence[str]]
    xml_extension_tag_attribute_uids: Optional[Sequence[str]]

    @classmethod
    def from_repository_values(
        cls,
        oid: str,
        name: str,
        prompt: str,
        datatype: str,
        length: int,
        significant_digits: int,
        sas_field_name: str,
        sds_var_name: str,
        origin: str,
        comment: Optional[str],
        description_uids: Sequence[str],
        alias_uids: Optional[Sequence[str]],
        unit_definition_uids: Optional[Sequence[str]],
        codelist_uid: Optional[str],
        term_uids: Optional[Sequence[str]],
        activity_uids: Optional[Sequence[str]] = None,
        xml_extension_tag_uids: Optional[Sequence[str]] = None,
        xml_extension_attribute_uids: Optional[Sequence[str]] = None,
        xml_extension_tag_attribute_uids: Optional[Sequence[str]] = None,
    ) -> "OdmItemVO":
        if activity_uids is None:
            activity_uids = []
        if xml_extension_tag_uids is None:
            xml_extension_tag_uids = []
        if xml_extension_attribute_uids is None:
            xml_extension_attribute_uids = []
        if xml_extension_tag_attribute_uids is None:
            xml_extension_tag_attribute_uids = []

        return cls(
            oid=oid,
            name=name,
            prompt=prompt,
            datatype=datatype,
            length=length,
            significant_digits=significant_digits,
            sas_field_name=sas_field_name,
            sds_var_name=sds_var_name,
            origin=origin,
            comment=comment,
            description_uids=description_uids,
            alias_uids=alias_uids,
            unit_definition_uids=unit_definition_uids,
            codelist_uid=codelist_uid,
            term_uids=term_uids,
            activity_uids=activity_uids,
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
        odm_description_exists_by_callback: Callable[[str, str, bool], bool],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        unit_definition_exists_by_callback: Callable[[str, str, bool], bool],
        find_codelist_attribute_callback: Callable[[str], CTTermAttributesAR],
        find_all_terms_callback: Callable[[str], GenericFilteringReturn[CTTermNameAR]],
        previous_name: Optional[str] = None,
        previous_oid: Optional[str] = None,
    ) -> None:

        if concept_exists_by_callback("name", self.name) and previous_name != self.name:
            raise BusinessLogicException(
                f"OdmItem with name ({self.name}) already exists."
            )

        if concept_exists_by_callback("oid", self.oid) and previous_oid != self.oid:
            raise BusinessLogicException(
                f"OdmItem with OID ({self.oid}) already exists."
            )

        for description_uid in self.description_uids:
            desc = odm_description_exists_by_callback("uid", description_uid, True)
            if not desc:
                raise BusinessLogicException(
                    f"OdmItem tried to connect to non existing OdmDescription identified by uid ({description_uid})."
                )

        for alias_uid in self.alias_uids:
            if not odm_alias_exists_by_callback("uid", alias_uid, True):
                raise BusinessLogicException(
                    f"OdmItem tried to connect to non existing OdmAlias identified by uid ({alias_uid})."
                )

        for unit_definition_uid in self.unit_definition_uids:
            if not unit_definition_exists_by_callback("uid", unit_definition_uid, True):
                raise BusinessLogicException(
                    f"OdmItem tried to connect to non existing UnitDefinition identified by uid ({unit_definition_uid})."
                )

        if self.codelist_uid is not None:
            if not find_codelist_attribute_callback(self.codelist_uid):
                raise BusinessLogicException(
                    f"OdmItem tried to connect to non existing Codelist identified by uid ({self.codelist_uid})."
                )

        if self.term_uids:
            if not self.codelist_uid:
                raise BusinessLogicException(
                    "To add terms you need to specify a codelist"
                )

            codelist_term_uids = [
                term.uid
                for term in find_all_terms_callback(
                    codelist_uid=self.codelist_uid
                ).items
            ]

            for term_uid in self.term_uids:
                if term_uid not in codelist_term_uids:
                    raise BusinessLogicException(
                        f"The term identified by uid ({term_uid}) doesn't belong to the specified codelist identified by uid ({self.codelist_uid})"
                    )


@dataclass
class OdmItemAR(OdmARBase):
    _concept_vo: OdmItemVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmItemVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmItemVO,
        library: Optional[LibraryVO],
        item_metadata: LibraryItemMetadataVO,
    ) -> "OdmItemAR":
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
        concept_vo: OdmItemVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        concept_exists_by_callback: Callable[[str, str, bool], bool] = lambda _: True,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda _: False,
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda _: False,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda _: False,
        find_codelist_attribute_callback: Callable[
            [str], CTTermAttributesAR
        ] = lambda _: False,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR]
        ] = lambda _: False,
    ) -> "OdmItemAR":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
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
        concept_vo: OdmItemVO,
        concept_exists_by_name_callback: Callable[[str], bool] = None,
        concept_exists_by_callback: Callable[[str, str, bool], bool] = None,
        odm_description_exists_by_callback: Callable[[str, str, bool], bool] = None,
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool] = None,
        unit_definition_exists_by_callback: Callable[[str, str, bool], bool] = None,
        find_codelist_attribute_callback: Callable[[str], CTTermAttributesAR] = None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR]
        ] = None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            concept_exists_by_callback=concept_exists_by_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            previous_name=self.name,
            previous_oid=self._concept_vo.oid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmItemRefVO:
    uid: str
    oid: str
    name: str
    item_group_uid: str
    order_number: int
    mandatory: bool
    data_entry_required: bool
    sdv: bool
    locked: bool
    key_sequence: str
    method_oid: str
    imputation_method_oid: str
    role: str
    role_codelist_oid: str
    collection_exception_condition_oid: Optional[str]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        item_group_uid: str,
        order_number: int,
        mandatory: bool,
        data_entry_required: bool,
        sdv: bool,
        locked: bool,
        key_sequence: str,
        method_oid: str,
        imputation_method_oid: str,
        role: str,
        role_codelist_oid: str,
        collection_exception_condition_oid: Optional[str] = None,
    ) -> "OdmItemRefVO":
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            item_group_uid=item_group_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            data_entry_required=booltostr(data_entry_required),
            sdv=booltostr(sdv),
            locked=booltostr(locked),
            key_sequence=key_sequence,
            method_oid=method_oid,
            imputation_method_oid=imputation_method_oid,
            role=role,
            role_codelist_oid=role_codelist_oid,
            collection_exception_condition_oid=collection_exception_condition_oid,
        )


@dataclass(frozen=True)
class OdmItemTermVO:
    uid: str
    name: str
    mandatory: bool
    order: int

    @classmethod
    def from_repository_values(
        cls, uid: str, name: str, mandatory: bool, order: int
    ) -> "OdmItemTermVO":
        return cls(uid=uid, name=name, mandatory=mandatory, order=order)


@dataclass(frozen=True)
class OdmItemUnitDefinitionVO:
    uid: str
    name: str
    mandatory: bool
    order: int

    @classmethod
    def from_repository_values(
        cls, uid: str, name: str, mandatory: bool, order: int
    ) -> "OdmItemUnitDefinitionVO":
        return cls(uid=uid, name=name, mandatory=mandatory, order=order)
