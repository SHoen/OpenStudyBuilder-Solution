from abc import ABC
from typing import Optional, Sequence

from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.odm_common_models import OdmXmlExtensionRelationPostInput
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class OdmGenericService(ConceptGenericService[_AggregateRootType], ABC):
    def fail_if_non_present_tags_are_used_by_current_odm_element_attributes(
        self,
        attribute_uids: Optional[Sequence[str]],
        input_tags: Sequence[OdmXmlExtensionRelationPostInput],
    ):
        (
            odm_xml_extension_attribute_ars,
            _,
        ) = self._repos.odm_xml_extension_attribute_repository.find_all(
            filter_by={"uid": {"v": attribute_uids, "op": "eq"}}
        )

        odm_xml_extension_attribute_tag_uids = {
            odm_xml_extension_attribute_ar.concept_vo.xml_extension_tag_uid
            for odm_xml_extension_attribute_ar in odm_xml_extension_attribute_ars
        }

        if not odm_xml_extension_attribute_tag_uids <= {
            input_tag.uid for input_tag in input_tags
        }:
            raise BusinessLogicException(
                "Cannot remove an OdmXmlExtensionTag whose attributes are connected to this ODM element."
            )

    def fail_if_these_attributes_cannot_be_added(
        self,
        input_attributes: Sequence[OdmXmlExtensionRelationPostInput],
        tag_uids: Optional[Sequence[str]] = None,
    ):
        (
            odm_xml_extension_attribute_ars,
            _,
        ) = self._repos.odm_xml_extension_attribute_repository.find_all(
            filter_by={
                "uid": {
                    "v": [input_attribute.uid for input_attribute in input_attributes],
                    "op": "eq",
                }
            }
        )

        for odm_xml_extension_attribute_ar in odm_xml_extension_attribute_ars:
            if odm_xml_extension_attribute_ar:
                if (
                    tag_uids
                    and odm_xml_extension_attribute_ar.concept_vo.xml_extension_tag_uid
                    not in tag_uids
                ):
                    raise BusinessLogicException(
                        f"OdmXmlExtensionAttribute identified by ({odm_xml_extension_attribute_ar.uid})"
                        " cannot not be added as an xml extension tag attribute."
                    )

                if (
                    not tag_uids
                    and not odm_xml_extension_attribute_ar.concept_vo.xml_extension_uid
                ):
                    raise BusinessLogicException(
                        f"OdmXmlExtensionAttribute identified by ({odm_xml_extension_attribute_ar.uid})"
                        " cannot not be added as an xml extension attribute."
                    )
