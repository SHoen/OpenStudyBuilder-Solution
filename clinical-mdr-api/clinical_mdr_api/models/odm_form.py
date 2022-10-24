from typing import Callable, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domain.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domain.concepts.odms.form import OdmFormAR, OdmFormRefVO
from clinical_mdr_api.domain.concepts.odms.item_group import OdmItemGroupRefVO
from clinical_mdr_api.domain.concepts.odms.xml_extension_attribute import (
    OdmXmlExtensionAttributeRelationVO,
    OdmXmlExtensionAttributeTagRelationVO,
)
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import (
    OdmXmlExtensionTagRelationVO,
)
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.models.activities.activity import ActivityHierarchySimpleModel
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.ct_term import SimpleCTTermAttributes
from clinical_mdr_api.models.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.odm_item_group import OdmItemGroupRefModel
from clinical_mdr_api.models.odm_xml_extension_attribute import (
    OdmXmlExtensionAttributeRelationModel,
    OdmXmlExtensionTagAttributeRelationModel,
)
from clinical_mdr_api.models.odm_xml_extension_tag import (
    OdmXmlExtensionTagRelationModel,
)
from clinical_mdr_api.models.utils import booltostr


class OdmForm(ConceptModel):
    oid: Optional[str]
    repeating: Optional[str]
    sdtmVersion: Optional[str]
    scope: Optional[SimpleCTTermAttributes]
    descriptions: Sequence[OdmDescriptionSimpleModel]
    aliases: Optional[Sequence[OdmAliasSimpleModel]]
    activityGroups: Optional[Sequence[ActivityHierarchySimpleModel]]
    itemGroups: Optional[Sequence[OdmItemGroupRefModel]]
    xmlExtensionTags: Optional[Sequence[OdmXmlExtensionTagRelationModel]]
    xmlExtensionAttributes: Optional[Sequence[OdmXmlExtensionAttributeRelationModel]]
    xmlExtensionTagAttributes: Optional[
        Sequence[OdmXmlExtensionTagAttributeRelationModel]
    ]
    possibleActions: List[str]

    @classmethod
    def from_odm_form_ar(
        cls,
        odm_form_ar: OdmFormAR,
        find_term_callback: Callable[[str], Optional[CTTermAttributesAR]],
        find_odm_description_by_uid: Callable[[str], Optional[OdmDescriptionAR]],
        find_odm_alias_by_uid: Callable[[str], Optional[OdmAliasAR]],
        find_activity_group_by_uid: Callable[[str], Optional[ActivityGroupAR]],
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str], Optional[OdmItemGroupRefVO]
        ],
        find_odm_xml_extension_tag_by_uid_with_odm_element_relation: Callable[
            [str, str, str], Optional[OdmXmlExtensionTagRelationVO]
        ],
        find_odm_xml_extension_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, str, str],
            Union[
                OdmXmlExtensionAttributeRelationVO,
                OdmXmlExtensionAttributeTagRelationVO,
                None,
            ],
        ],
    ) -> "OdmForm":
        return cls(
            uid=odm_form_ar._uid,
            oid=odm_form_ar.concept_vo.oid,
            name=odm_form_ar.concept_vo.name,
            sdtmVersion=odm_form_ar.concept_vo.sdtm_version,
            repeating=booltostr(odm_form_ar.concept_vo.repeating),
            libraryName=odm_form_ar.library.name,
            startDate=odm_form_ar.item_metadata.start_date,
            endDate=odm_form_ar.item_metadata.end_date,
            status=odm_form_ar.item_metadata.status.value,
            version=odm_form_ar.item_metadata.version,
            changeDescription=odm_form_ar.item_metadata.change_description,
            userInitials=odm_form_ar.item_metadata.user_initials,
            scope=SimpleCTTermAttributes.from_term_uid(
                uid=odm_form_ar.concept_vo.scope_uid,
                find_term_by_uid=find_term_callback,
            ),
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_form_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_form_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            activityGroups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_group_uid,
                        find_activity_by_uid=find_activity_group_by_uid,
                    )
                    for activity_group_uid in odm_form_ar.concept_vo.activity_group_uids
                ],
                key=lambda item: item.name,
            ),
            itemGroups=sorted(
                [
                    OdmItemGroupRefModel.from_odm_item_group_uid(
                        uid=item_group_uid,
                        form_uid=odm_form_ar._uid,
                        find_odm_item_group_by_uid_with_form_relation=find_odm_item_group_by_uid_with_form_relation,
                    )
                    for item_group_uid in odm_form_ar.concept_vo.item_group_uids
                ],
                key=lambda item: item.orderNumber,
            ),
            xmlExtensionTags=sorted(
                [
                    OdmXmlExtensionTagRelationModel.from_uid(
                        uid=xml_extension_tag_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_tag_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_uid in odm_form_ar.concept_vo.xml_extension_tag_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionAttributes=sorted(
                [
                    OdmXmlExtensionAttributeRelationModel.from_uid(
                        uid=xml_extension_attribute_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                        xml_extension_tag_attribute=False,
                    )
                    for xml_extension_attribute_uid in odm_form_ar.concept_vo.xml_extension_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionTagAttributes=sorted(
                [
                    OdmXmlExtensionTagAttributeRelationModel.from_uid(
                        uid=xml_extension_tag_attribute_uid,
                        odm_element_uid=odm_form_ar._uid,
                        odm_element_type=RelationType.FORM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_attribute_uid in odm_form_ar.concept_vo.xml_extension_tag_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_form_ar.get_possible_actions()]
            ),
        )


class OdmFormRefModel(BaseModel):
    @classmethod
    def from_odm_form_uid(
        cls,
        uid: str,
        template_uid: str,
        find_odm_form_by_uid_with_template_relation: Callable[
            [str, str], Optional[OdmFormRefVO]
        ],
    ) -> Optional["OdmFormRefModel"]:

        if uid is not None:
            odm_form_ref_vo = find_odm_form_by_uid_with_template_relation(
                uid, template_uid
            )
            if odm_form_ref_vo is not None:
                odm_form_ref_model = cls(
                    uid=uid,
                    name=odm_form_ref_vo.name,
                    orderNumber=odm_form_ref_vo.order_number,
                    mandatory=odm_form_ref_vo.mandatory,
                    locked=odm_form_ref_vo.locked,
                    collectionExceptionConditionOid=odm_form_ref_vo.collection_exception_condition_oid,
                )
            else:
                odm_form_ref_model = cls(
                    uid=uid,
                    name=None,
                    orderNumber=None,
                    mandatory=None,
                    locked=None,
                    collectionExceptionConditionOid=None,
                )
        else:
            odm_form_ref_model = None
        return odm_form_ref_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    orderNumber: Optional[int] = Field(None, title="orderNumber", description="")
    mandatory: Optional[str] = Field(None, title="mandatory", description="")
    locked: Optional[str] = Field(None, title="locked", description="")
    collectionExceptionConditionOid: Optional[str] = Field(
        None, title="collectionExceptionConditionOid", description=""
    )


class OdmFormPostInput(ConceptPostInput):
    oid: Optional[str]
    sdtmVersion: Optional[str]
    repeating: str
    scopeUid: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]


class OdmFormWithRelationsPostInput(ConceptPostInput):
    oid: Optional[str]
    sdtmVersion: Optional[str]
    repeating: str
    scopeUid: Optional[str]
    descriptions: Sequence[Union[OdmDescriptionPostInput, str]]
    aliasUids: Sequence[str]


class OdmFormPatchInput(ConceptPatchInput):
    oid: Optional[str]
    sdtmVersion: Optional[str]
    repeating: Optional[str]
    scopeUid: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]


class OdmFormWithRelationsPatchInput(ConceptPatchInput):
    oid: Optional[str]
    sdtmVersion: Optional[str]
    repeating: Optional[str]
    scopeUid: Optional[str]
    descriptions: Sequence[
        Union[OdmDescriptionBatchPatchInput, OdmDescriptionPostInput]
    ]
    aliasUids: Sequence[str]


class OdmFormItemGroupPostInput(BaseModel):
    uid: str
    orderNumber: int
    mandatory: str
    locked: str = "No"
    collectionExceptionConditionOid: Optional[str]


class OdmFormActivityGroupPostInput(BaseModel):
    uid: str


class OdmFormVersion(OdmForm):
    """
    Class for storing OdmForm and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
