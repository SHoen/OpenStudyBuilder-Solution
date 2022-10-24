import re
from typing import Callable, Dict, List, Optional, Sequence

from pydantic import Field, validator

from clinical_mdr_api.domain.concepts.odms.xml_extension import OdmXmlExtensionAR
from clinical_mdr_api.domain.concepts.odms.xml_extension_attribute import (
    OdmXmlExtensionAttributeAR,
)
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import OdmXmlExtensionTagAR
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.odm_common_models import (
    OdmXmlExtensionAttributeSimpleModel,
    OdmXmlExtensionTagSimpleModel,
)


class OdmXmlExtension(ConceptModel):
    prefix: Optional[str]
    namespace: Optional[str]
    xmlExtensionTags: Optional[Sequence[OdmXmlExtensionTagSimpleModel]]
    xmlExtensionAttributes: Optional[Sequence[OdmXmlExtensionAttributeSimpleModel]]
    possibleActions: List[str]

    @classmethod
    def from_odm_xml_extension_ar(
        cls,
        odm_xml_extension_ar: OdmXmlExtensionAR,
        find_odm_xml_extension_tag_by_uid: Callable[
            [str], Optional[OdmXmlExtensionTagAR]
        ],
        find_odm_xml_extension_attribute_by_uid: Callable[
            [str], Optional[OdmXmlExtensionAttributeAR]
        ],
    ) -> "OdmXmlExtension":
        return cls(
            uid=odm_xml_extension_ar._uid,
            name=odm_xml_extension_ar.concept_vo.name,
            prefix=odm_xml_extension_ar.concept_vo.prefix,
            namespace=odm_xml_extension_ar.concept_vo.namespace,
            libraryName=odm_xml_extension_ar.library.name,
            startDate=odm_xml_extension_ar.item_metadata.start_date,
            endDate=odm_xml_extension_ar.item_metadata.end_date,
            status=odm_xml_extension_ar.item_metadata.status.value,
            version=odm_xml_extension_ar.item_metadata.version,
            changeDescription=odm_xml_extension_ar.item_metadata.change_description,
            userInitials=odm_xml_extension_ar.item_metadata.user_initials,
            xmlExtensionTags=sorted(
                [
                    OdmXmlExtensionTagSimpleModel.from_odm_xml_extension_tag_uid(
                        uid=xml_extension_tag_uid,
                        find_odm_xml_extension_tag_by_uid=find_odm_xml_extension_tag_by_uid,
                    )
                    for xml_extension_tag_uid in odm_xml_extension_ar.concept_vo.xml_extension_tag_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionAttributes=sorted(
                [
                    OdmXmlExtensionAttributeSimpleModel.from_odm_xml_extension_attribute_uid(
                        uid=xml_extension_attribute_uid,
                        find_odm_xml_extension_attribute_by_uid=find_odm_xml_extension_attribute_by_uid,
                    )
                    for xml_extension_attribute_uid in odm_xml_extension_ar.concept_vo.xml_extension_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_xml_extension_ar.get_possible_actions()]
            ),
        )


class OdmXmlExtensionPostInput(ConceptPostInput):
    prefix: str
    namespace: str

    @validator("prefix")
    # pylint:disable=no-self-argument
    def prefix_may_only_contain_letters(cls, v):
        if re.search("[^a-zA-Z]", v):
            raise ValueError("may only contain letters")
        return v


class OdmXmlExtensionPatchInput(ConceptPatchInput):
    prefix: str
    namespace: str


class OdmXmlExtensionVersion(OdmXmlExtension):
    """
    Class for storing OdmXmlExtension and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
