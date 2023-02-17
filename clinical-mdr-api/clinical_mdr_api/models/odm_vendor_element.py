import re
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from clinical_mdr_api.domain.concepts.odms.vendor_attribute import OdmVendorAttributeAR
from clinical_mdr_api.domain.concepts.odms.vendor_element import (
    OdmVendorElementAR,
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domain.concepts.odms.vendor_namespace import OdmVendorNamespaceAR
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.odm_common_models import (
    OdmVendorAttributeSimpleModel,
    OdmVendorNamespaceSimpleModel,
)


class OdmVendorElement(ConceptModel):
    vendor_namespace: OdmVendorNamespaceSimpleModel
    vendor_attributes: List[OdmVendorAttributeSimpleModel]
    possible_actions: List[str]

    @classmethod
    def from_odm_vendor_element_ar(
        cls,
        odm_vendor_element_ar: OdmVendorElementAR,
        find_odm_vendor_namespace_by_uid: Callable[
            [str], Optional[OdmVendorNamespaceAR]
        ],
        find_odm_vendor_attribute_by_uid: Callable[
            [str], Optional[OdmVendorAttributeAR]
        ],
    ) -> "OdmVendorElement":
        return cls(
            uid=odm_vendor_element_ar._uid,
            name=odm_vendor_element_ar.concept_vo.name,
            library_name=odm_vendor_element_ar.library.name,
            start_date=odm_vendor_element_ar.item_metadata.start_date,
            end_date=odm_vendor_element_ar.item_metadata.end_date,
            status=odm_vendor_element_ar.item_metadata.status.value,
            version=odm_vendor_element_ar.item_metadata.version,
            change_description=odm_vendor_element_ar.item_metadata.change_description,
            user_initials=odm_vendor_element_ar.item_metadata.user_initials,
            vendor_namespace=OdmVendorNamespaceSimpleModel.from_odm_vendor_namespace_uid(
                uid=odm_vendor_element_ar.concept_vo.vendor_namespace_uid,
                find_odm_vendor_namespace_by_uid=find_odm_vendor_namespace_by_uid,
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeSimpleModel.from_odm_vendor_attribute_uid(
                        uid=vendor_attribute_uid,
                        find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                    )
                    for vendor_attribute_uid in odm_vendor_element_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possible_actions=sorted(
                [_.value for _ in odm_vendor_element_ar.get_possible_actions()]
            ),
        )


class OdmVendorElementRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], Optional[OdmVendorElementRelationVO]
        ],
    ) -> Optional["OdmVendorElementRelationModel"]:

        if uid is not None:
            odm_vendor_element_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type
            )
            if odm_vendor_element_ref_vo is not None:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=odm_vendor_element_ref_vo.name,
                    value=odm_vendor_element_ref_vo.value,
                )
            else:
                odm_vendor_element_ref_model = cls(
                    uid=uid,
                    name=None,
                    value=None,
                )
        else:
            odm_vendor_element_ref_model = None
        return odm_vendor_element_ref_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    value: Optional[str] = Field(None, title="value", description="")


class OdmVendorElementPostInput(ConceptPostInput):
    vendor_namespace_uid: str

    @validator("name")
    @classmethod
    def name_may_only_contain_letters(cls, v):
        if re.search("[^a-zA-Z]", v):
            raise ValueError("may only contain letters")
        return v


class OdmVendorElementPatchInput(ConceptPatchInput):
    ...


class OdmVendorElementVersion(OdmVendorElement):
    """
    Class for storing OdmVendorElement and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
    )