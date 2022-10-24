from typing import Callable, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domain.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domain.concepts.odms.item import OdmItemRefVO
from clinical_mdr_api.domain.concepts.odms.item_group import (
    OdmItemGroupAR,
    OdmItemGroupRefVO,
)
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
from clinical_mdr_api.models.odm_item import OdmItemRefModel
from clinical_mdr_api.models.odm_xml_extension_attribute import (
    OdmXmlExtensionAttributeRelationModel,
    OdmXmlExtensionTagAttributeRelationModel,
)
from clinical_mdr_api.models.odm_xml_extension_tag import (
    OdmXmlExtensionTagRelationModel,
)
from clinical_mdr_api.models.utils import booltostr


class OdmItemGroup(ConceptModel):
    oid: Optional[str]
    repeating: Optional[str]
    isReferenceData: Optional[str]
    sasDatasetName: Optional[str]
    origin: Optional[str]
    purpose: Optional[str]
    comment: Optional[str]
    descriptions: Optional[Sequence[OdmDescriptionSimpleModel]]
    aliases: Optional[Sequence[OdmAliasSimpleModel]]
    sdtmDomains: Optional[Sequence[SimpleCTTermAttributes]]
    activitySubGroups: Optional[Sequence[ActivityHierarchySimpleModel]]
    items: Optional[Sequence[OdmItemRefModel]]
    xmlExtensionTags: Optional[Sequence[OdmXmlExtensionTagRelationModel]]
    xmlExtensionAttributes: Optional[Sequence[OdmXmlExtensionAttributeRelationModel]]
    xmlExtensionTagAttributes: Optional[
        Sequence[OdmXmlExtensionTagAttributeRelationModel]
    ]
    possibleActions: List[str]

    @classmethod
    def from_odm_item_group_ar(
        cls,
        odm_item_group_ar: OdmItemGroupAR,
        find_odm_description_by_uid: Callable[[str], Optional[OdmDescriptionAR]],
        find_odm_alias_by_uid: Callable[[str], Optional[OdmAliasAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermAttributesAR]],
        find_activity_sub_group_by_uid: Callable[[str], Optional[ActivitySubGroupAR]],
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], Optional[OdmItemRefVO]
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
    ) -> "OdmItemGroup":
        return cls(
            uid=odm_item_group_ar._uid,
            oid=odm_item_group_ar.concept_vo.oid,
            name=odm_item_group_ar.concept_vo.name,
            repeating=booltostr(odm_item_group_ar.concept_vo.repeating),
            isReferenceData=booltostr(odm_item_group_ar.concept_vo.is_reference_data),
            sasDatasetName=odm_item_group_ar.concept_vo.sas_dataset_name,
            origin=odm_item_group_ar.concept_vo.origin,
            purpose=odm_item_group_ar.concept_vo.purpose,
            comment=odm_item_group_ar.concept_vo.comment,
            libraryName=odm_item_group_ar.library.name,
            startDate=odm_item_group_ar.item_metadata.start_date,
            endDate=odm_item_group_ar.item_metadata.end_date,
            status=odm_item_group_ar.item_metadata.status.value,
            version=odm_item_group_ar.item_metadata.version,
            changeDescription=odm_item_group_ar.item_metadata.change_description,
            userInitials=odm_item_group_ar.item_metadata.user_initials,
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_item_group_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_item_group_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            sdtmDomains=sorted(
                [
                    SimpleCTTermAttributes.from_term_uid(
                        uid=sdtm_domain_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for sdtm_domain_uid in odm_item_group_ar.concept_vo.sdtm_domain_uids
                ],
                key=lambda item: item.codeSubmissionValue,
            ),
            activitySubGroups=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_sub_group_uid,
                        find_activity_by_uid=find_activity_sub_group_by_uid,
                    )
                    for activity_sub_group_uid in odm_item_group_ar.concept_vo.activity_sub_group_uids
                ],
                key=lambda item: item.name,
            ),
            items=sorted(
                [
                    OdmItemRefModel.from_odm_item_uid(
                        uid=item_uid,
                        item_group_uid=odm_item_group_ar._uid,
                        find_odm_item_by_uid_with_item_group_relation=find_odm_item_by_uid_with_item_group_relation,
                    )
                    for item_uid in odm_item_group_ar.concept_vo.item_uids
                ],
                key=lambda item: item.orderNumber,
            ),
            xmlExtensionTags=sorted(
                [
                    OdmXmlExtensionTagRelationModel.from_uid(
                        uid=xml_extension_tag_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_tag_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_uid in odm_item_group_ar.concept_vo.xml_extension_tag_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionAttributes=sorted(
                [
                    OdmXmlExtensionAttributeRelationModel.from_uid(
                        uid=xml_extension_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                        xml_extension_tag_attribute=False,
                    )
                    for xml_extension_attribute_uid in odm_item_group_ar.concept_vo.xml_extension_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionTagAttributes=sorted(
                [
                    OdmXmlExtensionTagAttributeRelationModel.from_uid(
                        uid=xml_extension_tag_attribute_uid,
                        odm_element_uid=odm_item_group_ar._uid,
                        odm_element_type=RelationType.ITEM_GROUP,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_attribute_uid in odm_item_group_ar.concept_vo.xml_extension_tag_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_item_group_ar.get_possible_actions()]
            ),
        )


class OdmItemGroupRefModel(BaseModel):
    @classmethod
    def from_odm_item_group_uid(
        cls,
        uid: str,
        form_uid: str,
        find_odm_item_group_by_uid_with_form_relation: Callable[
            [str, str], Optional[OdmItemGroupRefVO]
        ],
    ) -> Optional["OdmItemGroupRefModel"]:

        if uid is not None:
            odm_item_group_ref_vo = find_odm_item_group_by_uid_with_form_relation(
                uid, form_uid
            )
            if odm_item_group_ref_vo is not None:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=odm_item_group_ref_vo.oid,
                    name=odm_item_group_ref_vo.name,
                    orderNumber=odm_item_group_ref_vo.order_number,
                    mandatory=odm_item_group_ref_vo.mandatory,
                    locked=odm_item_group_ref_vo.locked,
                    collectionExceptionConditionOid=odm_item_group_ref_vo.collection_exception_condition_oid,
                )
            else:
                odm_item_group_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    orderNumber=None,
                    mandatory=None,
                    collectionExceptionConditionOid=None,
                )
        else:
            odm_item_group_ref_model = None
        return odm_item_group_ref_model

    uid: str = Field(..., title="uid", description="")
    oid: Optional[str] = Field(None, title="oid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    orderNumber: Optional[int] = Field(None, title="orderNumber", description="")
    mandatory: Optional[str] = Field(None, title="mandatory", description="")
    locked: Optional[str] = Field(None, title="locked", description="")
    collectionExceptionConditionOid: Optional[str] = Field(
        None, title="collectionExceptionConditionOid", description=""
    )


class OdmItemGroupPostInput(ConceptPostInput):
    oid: Optional[str]
    repeating: str
    isReferenceData: Optional[str]
    sasDatasetName: Optional[str]
    origin: Optional[str]
    purpose: Optional[str]
    comment: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]
    sdtmDomainUids: Sequence[str]


class OdmItemGroupWithRelationsPostInput(ConceptPostInput):
    oid: Optional[str]
    repeating: str
    isReferenceData: Optional[str]
    sasDatasetName: Optional[str]
    origin: Optional[str]
    purpose: Optional[str]
    comment: Optional[str]
    descriptions: Sequence[Union[OdmDescriptionPostInput, str]]
    aliasUids: Sequence[str]
    sdtmDomainUids: Sequence[str]


class OdmItemGroupPatchInput(ConceptPatchInput):
    oid: Optional[str]
    repeating: Optional[str]
    isReferenceData: Optional[str]
    sasDatasetName: Optional[str]
    origin: Optional[str]
    purpose: Optional[str]
    comment: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]
    sdtmDomainUids: Sequence[str]


class OdmItemGroupWithRelationsPatchInput(ConceptPatchInput):
    oid: Optional[str]
    repeating: Optional[str]
    isReferenceData: Optional[str]
    sasDatasetName: Optional[str]
    origin: Optional[str]
    purpose: Optional[str]
    comment: Optional[str]
    descriptions: Sequence[
        Union[OdmDescriptionBatchPatchInput, OdmDescriptionPostInput]
    ]
    aliasUids: Sequence[str]
    sdtmDomainUids: Sequence[str]


class OdmItemGroupActivitySubGroupPostInput(BaseModel):
    uid: str


class OdmItemGroupItemPostInput(BaseModel):
    uid: str
    orderNumber: int
    mandatory: str
    dataEntryRequired: str
    sdv: str
    locked: str = "No"
    keySequence: str
    methodOid: str
    imputationMethodOid: str
    role: str
    roleCodelistOid: str
    collectionExceptionConditionOid: Optional[str]


class OdmItemGroupVersion(OdmItemGroup):
    """
    Class for storing OdmItemGroup and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
