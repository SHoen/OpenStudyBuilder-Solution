import re
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator

from clinical_mdr_api.domain.concepts.odms.xml_extension import OdmXmlExtensionAR
from clinical_mdr_api.domain.concepts.odms.xml_extension_attribute import (
    OdmXmlExtensionAttributeAR,
)
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import (
    OdmXmlExtensionTagAR,
    OdmXmlExtensionTagRelationVO,
)
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.odm_common_models import (
    OdmXmlExtensionSimpleModel,
    OdmXmlExtensionTagSimpleModel,
)


class OdmXmlExtensionAttribute(ConceptModel):
    xmlExtension: Optional[OdmXmlExtensionSimpleModel]
    xmlExtensionTag: Optional[OdmXmlExtensionTagSimpleModel]
    possibleActions: List[str]

    @classmethod
    def from_odm_xml_extension_attribute_ar(
        cls,
        odm_xml_extension_attribute_ar: OdmXmlExtensionAttributeAR,
        find_odm_xml_extension_by_uid: Callable[[str], Optional[OdmXmlExtensionAR]],
        find_odm_xml_extension_tag_by_uid: Callable[
            [str], Optional[OdmXmlExtensionTagAR]
        ],
    ) -> "OdmXmlExtensionAttribute":
        return cls(
            uid=odm_xml_extension_attribute_ar._uid,
            name=odm_xml_extension_attribute_ar.concept_vo.name,
            libraryName=odm_xml_extension_attribute_ar.library.name,
            startDate=odm_xml_extension_attribute_ar.item_metadata.start_date,
            endDate=odm_xml_extension_attribute_ar.item_metadata.end_date,
            status=odm_xml_extension_attribute_ar.item_metadata.status.value,
            version=odm_xml_extension_attribute_ar.item_metadata.version,
            changeDescription=odm_xml_extension_attribute_ar.item_metadata.change_description,
            userInitials=odm_xml_extension_attribute_ar.item_metadata.user_initials,
            xmlExtension=OdmXmlExtensionSimpleModel.from_odm_xml_extension_uid(
                uid=odm_xml_extension_attribute_ar.concept_vo.xml_extension_uid,
                find_odm_xml_extension_by_uid=find_odm_xml_extension_by_uid,
            ),
            xmlExtensionTag=OdmXmlExtensionTagSimpleModel.from_odm_xml_extension_tag_uid(
                uid=odm_xml_extension_attribute_ar.concept_vo.xml_extension_tag_uid,
                find_odm_xml_extension_tag_by_uid=find_odm_xml_extension_tag_by_uid,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_xml_extension_attribute_ar.get_possible_actions()]
            ),
        )


class OdmXmlExtensionAttributeRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool], Optional[OdmXmlExtensionTagRelationVO]
        ],
        xml_extension_tag_attribute: bool = True,
    ) -> Optional["OdmXmlExtensionAttributeRelationModel"]:

        if uid is not None:
            odm_xml_extension_attribute_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type, xml_extension_tag_attribute
            )
            if odm_xml_extension_attribute_ref_vo is not None:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=odm_xml_extension_attribute_ref_vo.name,
                    value=odm_xml_extension_attribute_ref_vo.value,
                    odmXmlExtensionUid=odm_xml_extension_attribute_ref_vo.odm_xml_extension_uid,
                )
            else:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=None,
                    value=None,
                    odmXmlExtensionUid=None,
                )
        else:
            odm_xml_extension_tag_ref_model = None
        return odm_xml_extension_tag_ref_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    value: Optional[str] = Field(None, title="value", description="")
    odmXmlExtensionUid: Optional[str] = Field(None, title="value", description="")


class OdmXmlExtensionTagAttributeRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool], Optional[OdmXmlExtensionTagRelationVO]
        ],
        xml_extension_tag_attribute: bool = True,
    ) -> Optional["OdmXmlExtensionTagAttributeRelationModel"]:

        if uid is not None:
            odm_xml_extension_tag_attribute_ref_vo = (
                find_by_uid_with_odm_element_relation(
                    uid, odm_element_uid, odm_element_type, xml_extension_tag_attribute
                )
            )
            if odm_xml_extension_tag_attribute_ref_vo is not None:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=odm_xml_extension_tag_attribute_ref_vo.name,
                    value=odm_xml_extension_tag_attribute_ref_vo.value,
                    odmXmlExtensionTagUid=odm_xml_extension_tag_attribute_ref_vo.odm_xml_extension_tag_uid,
                )
            else:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=None,
                    value=None,
                    odmXmlExtensionTagUid=None,
                )
        else:
            odm_xml_extension_tag_ref_model = None
        return odm_xml_extension_tag_ref_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    value: Optional[str] = Field(None, title="value", description="")
    odmXmlExtensionTagUid: Optional[str] = Field(None, title="value", description="")


class OdmXmlExtensionAttributePostInput(ConceptPostInput):
    xmlExtensionUid: Optional[str]
    xmlExtensionTagUid: Optional[str]

    @validator("name")
    # pylint:disable=no-self-argument
    def name_may_only_contain_letters(cls, v):
        if re.search("[^a-zA-Z]", v):
            raise ValueError("may only contain letters")
        return v

    @root_validator()
    # pylint:disable=no-self-argument
    def one_and_only_one_of_the_two_uids_must_be_present(cls, values):
        if (not values["xmlExtensionTagUid"] and not values["xmlExtensionUid"]) or (
            values["xmlExtensionTagUid"] and values["xmlExtensionUid"]
        ):
            raise ValueError(
                "Either xmlExtensionUid or xmlExtensionTagUid must be provided"
            )

        return values


class OdmXmlExtensionAttributePatchInput(ConceptPatchInput):
    ...


class OdmXmlExtensionAttributeVersion(OdmXmlExtensionAttribute):
    """
    Class for storing OdmXmlExtensionAttribute and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
