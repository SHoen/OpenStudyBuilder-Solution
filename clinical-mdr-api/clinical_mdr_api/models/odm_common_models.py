from typing import Callable, Optional

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase


class OdmXmlExtensionRelationPostInput(BaseModel):
    uid: str
    value: str


class OdmXmlExtensionSimpleModel(BaseModel):
    @classmethod
    def from_odm_xml_extension_uid(
        cls,
        uid: str,
        find_odm_xml_extension_by_uid: Callable[[str], Optional[ConceptARBase]],
    ) -> Optional["OdmXmlExtensionSimpleModel"]:

        if uid is not None:
            odm_xml_extension = find_odm_xml_extension_by_uid(uid)

            if odm_xml_extension is not None:
                simple_odm_xml_extension_model = cls(
                    uid=uid,
                    name=odm_xml_extension.concept_vo.name,
                    prefix=odm_xml_extension.concept_vo.prefix,
                    namespace=odm_xml_extension.concept_vo.namespace,
                )
            else:
                simple_odm_xml_extension_model = cls(
                    uid=uid, name=None, prefix=None, namespeace=None
                )
        else:
            simple_odm_xml_extension_model = None
        return simple_odm_xml_extension_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    prefix: Optional[str] = Field(None, title="prefix", description="")
    namespace: Optional[str] = Field(None, title="namespace", description="")


class OdmXmlExtensionAttributeSimpleModel(BaseModel):
    @classmethod
    def from_odm_xml_extension_attribute_uid(
        cls,
        uid: str,
        find_odm_xml_extension_attribute_by_uid: Callable[
            [str], Optional[ConceptARBase]
        ],
    ) -> Optional["OdmXmlExtensionAttributeSimpleModel"]:

        if uid is not None:
            odm_xml_extension_attribute = find_odm_xml_extension_attribute_by_uid(uid)

            if odm_xml_extension_attribute is not None:
                simple_odm_xml_extension_attribute_model = cls(
                    uid=uid,
                    name=odm_xml_extension_attribute.concept_vo.name,
                )
            else:
                simple_odm_xml_extension_attribute_model = cls(uid=uid, name=None)
        else:
            simple_odm_xml_extension_attribute_model = None
        return simple_odm_xml_extension_attribute_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")


class OdmXmlExtensionTagSimpleModel(BaseModel):
    @classmethod
    def from_odm_xml_extension_tag_uid(
        cls,
        uid: str,
        find_odm_xml_extension_tag_by_uid: Callable[[str], Optional[ConceptARBase]],
    ) -> Optional["OdmXmlExtensionTagSimpleModel"]:

        if uid is not None:
            odm_xml_extension_tag = find_odm_xml_extension_tag_by_uid(uid)

            if odm_xml_extension_tag is not None:
                simple_odm_xml_extension_tag_model = cls(
                    uid=uid,
                    name=odm_xml_extension_tag.concept_vo.name,
                )
            else:
                simple_odm_xml_extension_tag_model = cls(uid=uid, name=None)
        else:
            simple_odm_xml_extension_tag_model = None
        return simple_odm_xml_extension_tag_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
