from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass(frozen=True)
class OdmVendorElementVO(ConceptVO):
    vendor_namespace_uid: str
    vendor_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        vendor_namespace_uid: str,
        vendor_attribute_uids: list[str],
    ) -> Self:
        return cls(
            name=name,
            vendor_namespace_uid=vendor_namespace_uid,
            vendor_attribute_uids=vendor_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        odm_vendor_namespace_exists_by_callback: Callable[[str, str, bool], bool],
        find_odm_vendor_element_callback: Callable[
            [dict], tuple[list["OdmVendorElementAR"], int] | None
        ],
    ) -> None:
        if self.vendor_namespace_uid is not None:
            self.check_concepts_exist(
                [
                    (
                        [self.vendor_namespace_uid],
                        "ODM Vendor Namespace",
                        odm_vendor_namespace_exists_by_callback,
                    )
                ],
                "ODM Vendor Element",
            )

        odm_vendor_element, _ = find_odm_vendor_element_callback(
            filter_by={
                "name": {"v": [self.name], "op": "eq"},
                "vendor_namespace_uid": {"v": [self.vendor_namespace_uid], "op": "eq"},
            }
        )
        if odm_vendor_element:
            raise BusinessLogicException(
                f"ODM Vendor Element with ['name: {self.name}'] already exists."
            )


@dataclass
class OdmVendorElementAR(OdmARBase):
    _concept_vo: OdmVendorElementVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmVendorElementVO:
        return self._concept_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmVendorElementVO,
        library: LibraryVO | None,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
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
        concept_vo: OdmVendorElementVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        odm_vendor_namespace_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_odm_vendor_element_callback: Callable[
            [dict], tuple[list["OdmVendorElementAR"], int] | None
        ] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        concept_vo.validate(
            odm_vendor_namespace_exists_by_callback=odm_vendor_namespace_exists_by_callback,
            find_odm_vendor_element_callback=find_odm_vendor_element_callback,
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
        change_description: str | None,
        concept_vo: OdmVendorElementVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """

        if self._concept_vo != concept_vo:
            super()._edit_draft(change_description=change_description, author=author)
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmVendorElementRelationVO:
    uid: str
    name: str
    value: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        value: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            value=value,
        )
