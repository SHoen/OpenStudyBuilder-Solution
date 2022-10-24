import re
from typing import Callable, Dict, List, Optional, Sequence

from pydantic import BaseModel, Field, validator

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
    OdmXmlExtensionAttributeSimpleModel,
    OdmXmlExtensionSimpleModel,
    OdmXmlExtensionTagSimpleModel,
)


class OdmXmlExtensionTag(ConceptModel):
    xmlExtension: Optional[OdmXmlExtensionSimpleModel]
    parentXmlExtensionTag: Optional[OdmXmlExtensionTagSimpleModel]
    childXmlExtensionTags: Optional[Sequence[OdmXmlExtensionTagSimpleModel]]
    xmlExtensionAttributes: Optional[Sequence[OdmXmlExtensionAttributeSimpleModel]]
    possibleActions: List[str]

    @classmethod
    def from_odm_xml_extension_tag_ar(
        cls,
        odm_xml_extension_tag_ar: OdmXmlExtensionTagAR,
        find_odm_xml_extension_by_uid: Callable[[str], Optional[OdmXmlExtensionAR]],
        find_odm_xml_extension_tag_by_uid: Callable[
            [str], Optional[OdmXmlExtensionTagAR]
        ],
        find_odm_xml_extension_attribute_by_uid: Callable[
            [str], Optional[OdmXmlExtensionAttributeAR]
        ],
    ) -> "OdmXmlExtensionTag":
        return cls(
            uid=odm_xml_extension_tag_ar._uid,
            name=odm_xml_extension_tag_ar.concept_vo.name,
            libraryName=odm_xml_extension_tag_ar.library.name,
            startDate=odm_xml_extension_tag_ar.item_metadata.start_date,
            endDate=odm_xml_extension_tag_ar.item_metadata.end_date,
            status=odm_xml_extension_tag_ar.item_metadata.status.value,
            version=odm_xml_extension_tag_ar.item_metadata.version,
            changeDescription=odm_xml_extension_tag_ar.item_metadata.change_description,
            userInitials=odm_xml_extension_tag_ar.item_metadata.user_initials,
            xmlExtension=OdmXmlExtensionSimpleModel.from_odm_xml_extension_uid(
                uid=odm_xml_extension_tag_ar.concept_vo.xml_extension_uid,
                find_odm_xml_extension_by_uid=find_odm_xml_extension_by_uid,
            ),
            parentXmlExtensionTag=OdmXmlExtensionTagSimpleModel.from_odm_xml_extension_tag_uid(
                uid=odm_xml_extension_tag_ar.concept_vo.parent_xml_extension_tag_uid,
                find_odm_xml_extension_tag_by_uid=find_odm_xml_extension_tag_by_uid,
            ),
            childXmlExtensionTags=sorted(
                [
                    OdmXmlExtensionTagSimpleModel.from_odm_xml_extension_tag_uid(
                        uid=child_xml_extension_tag_uid,
                        find_odm_xml_extension_tag_by_uid=find_odm_xml_extension_tag_by_uid,
                    )
                    for child_xml_extension_tag_uid in odm_xml_extension_tag_ar.concept_vo.child_xml_extension_tag_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionAttributes=sorted(
                [
                    OdmXmlExtensionAttributeSimpleModel.from_odm_xml_extension_attribute_uid(
                        uid=xml_extension_attribute_uid,
                        find_odm_xml_extension_attribute_by_uid=find_odm_xml_extension_attribute_by_uid,
                    )
                    for xml_extension_attribute_uid in odm_xml_extension_tag_ar.concept_vo.xml_extension_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_xml_extension_tag_ar.get_possible_actions()]
            ),
        )


class OdmXmlExtensionTagRelationModel(BaseModel):
    @classmethod
    def from_uid(
        cls,
        uid: str,
        odm_element_uid: str,
        odm_element_type: RelationType,
        find_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], Optional[OdmXmlExtensionTagRelationVO]
        ],
    ) -> Optional["OdmXmlExtensionTagRelationModel"]:

        if uid is not None:
            odm_xml_extension_tag_ref_vo = find_by_uid_with_odm_element_relation(
                uid, odm_element_uid, odm_element_type
            )
            if odm_xml_extension_tag_ref_vo is not None:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=odm_xml_extension_tag_ref_vo.name,
                    value=odm_xml_extension_tag_ref_vo.value,
                )
            else:
                odm_xml_extension_tag_ref_model = cls(
                    uid=uid,
                    name=None,
                    value=None,
                )
        else:
            odm_xml_extension_tag_ref_model = None
        return odm_xml_extension_tag_ref_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    value: Optional[str] = Field(None, title="value", description="")


class OdmXmlExtensionTagPostInput(ConceptPostInput):
    xmlExtensionUid: str
    parentXmlExtensionTagUid: Optional[str]

    @validator("name")
    # pylint:disable=no-self-argument
    def name_may_only_contain_letters(cls, v):
        if re.search("[^a-zA-Z]", v):
            raise ValueError("may only contain letters")
        return v


class OdmXmlExtensionTagPatchInput(ConceptPatchInput):
    ...


class OdmXmlExtensionTagVersion(OdmXmlExtensionTag):
    """
    Class for storing OdmXmlExtensionTag and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )