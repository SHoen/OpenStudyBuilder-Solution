from typing import Callable, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domain.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domain.concepts.odms.item import (
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
)
from clinical_mdr_api.domain.concepts.odms.xml_extension_attribute import (
    OdmXmlExtensionAttributeRelationVO,
    OdmXmlExtensionAttributeTagRelationVO,
)
from clinical_mdr_api.domain.concepts.odms.xml_extension_tag import (
    OdmXmlExtensionTagRelationVO,
)
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.activities.activity import ActivityHierarchySimpleModel
from clinical_mdr_api.models.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.ct_codelist_attributes import (
    CTCodelistAttributesSimpleModel,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.odm_xml_extension_attribute import (
    OdmXmlExtensionAttributeRelationModel,
    OdmXmlExtensionTagAttributeRelationModel,
)
from clinical_mdr_api.models.odm_xml_extension_tag import (
    OdmXmlExtensionTagRelationModel,
)


class OdmItemTermRelationshipModel(BaseModel):
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: str,
        find_term_with_item_relation_by_item_uid: Callable[
            [str], Optional[OdmItemTermVO]
        ],
    ) -> Optional["OdmItemTermRelationshipModel"]:
        simple_term_model = None
        if term_uid is not None:
            term = find_term_with_item_relation_by_item_uid(uid=uid, term_uid=term_uid)

            if term is not None:
                simple_term_model = cls(
                    termUid=term_uid,
                    name=term.name,
                    mandatory=term.mandatory,
                    order=term.order,
                )
            else:
                simple_term_model = cls(
                    termUid=term_uid, name=None, mandatory=None, order=None
                )
        else:
            simple_term_model = None
        return simple_term_model

    termUid: str = Field(..., title="termUid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    mandatory: Optional[bool] = Field(None, title="mandatory", description="")
    order: Optional[int] = Field(None, title="order", description="")


class OdmItemUnitDefinitionWithRelationship(BaseModel):
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: str,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], Optional[ConceptARBase]],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], Optional[OdmItemUnitDefinitionVO]
        ],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
    ) -> Optional["OdmItemUnitDefinitionWithRelationship"]:
        if uid is not None:
            unit_definition_rel = find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            unit_definition = find_unit_definition_by_uid(unit_definition_uid)

            if unit_definition is not None and unit_definition_rel is not None:
                if unit_definition.concept_vo.ucum_name is None:
                    ucum = SimpleTermModel.from_ct_code(
                        c_code=unit_definition.concept_vo.ucum_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                    )
                else:
                    ucum = SimpleTermModel(
                        termUid=unit_definition.concept_vo.ucum_uid,
                        name=unit_definition.concept_vo.ucum_name,
                    )

                ct_units = []
                for ct_unit in unit_definition.concept_vo.ct_units:
                    if ct_unit.name is None:
                        controlled_terminology_unit = SimpleTermModel.from_ct_code(
                            c_code=ct_unit.uid, find_term_by_uid=find_term_by_uid
                        )
                    else:
                        controlled_terminology_unit = SimpleTermModel(
                            termUid=ct_unit.uid, name=ct_unit.name
                        )
                    ct_units.append(controlled_terminology_unit)

                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=unit_definition.concept_vo.name,
                    mandatory=unit_definition_rel.mandatory,
                    order=unit_definition_rel.order,
                    ucum=ucum,
                    ctUnits=ct_units,
                )
            else:
                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=None,
                    mandatory=None,
                    order=None,
                    ucum=None,
                    ctUnits=None,
                )
        else:
            simple_unit_definition_model = None
        return simple_unit_definition_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    mandatory: Optional[bool] = Field(None, title="mandatory", description="")
    order: Optional[int] = Field(None, title="order", description="")
    ucum: Optional[SimpleTermModel] = Field(None, title="ucum", description="")
    ctUnits: Optional[Sequence[SimpleTermModel]] = Field(
        None, title="ucumName", description=""
    )


class OdmItem(ConceptModel):
    oid: Optional[str]
    prompt: Optional[str]
    datatype: Optional[str]
    length: Optional[int]
    significantDigits: Optional[int]
    sasFieldName: Optional[str]
    sdsVarName: Optional[str]
    origin: Optional[str]
    comment: Optional[str]
    descriptions: Optional[Sequence[OdmDescriptionSimpleModel]]
    aliases: Optional[Sequence[OdmAliasSimpleModel]]
    unitDefinitions: Optional[Sequence[OdmItemUnitDefinitionWithRelationship]]
    codelist: Optional[CTCodelistAttributesSimpleModel]
    terms: Optional[Sequence[OdmItemTermRelationshipModel]]
    activities: Optional[Sequence[ActivityHierarchySimpleModel]]
    xmlExtensionTags: Optional[Sequence[OdmXmlExtensionTagRelationModel]]
    xmlExtensionAttributes: Optional[Sequence[OdmXmlExtensionAttributeRelationModel]]
    xmlExtensionTagAttributes: Optional[
        Sequence[OdmXmlExtensionTagAttributeRelationModel]
    ]
    possibleActions: List[str]

    @classmethod
    def from_odm_item_ar(
        cls,
        odm_item_ar: OdmItemAR,
        find_odm_description_by_uid: Callable[[str], Optional[OdmDescriptionAR]],
        find_odm_alias_by_uid: Callable[[str], Optional[OdmAliasAR]],
        find_unit_definition_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], Optional[OdmItemUnitDefinitionVO]
        ],
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
        find_term_by_uid: Callable[[str], Optional[CTTermNameAR]],
        find_codelist_attribute_by_codelist_uid: Callable[
            [str], Optional[CTCodelistAttributesAR]
        ],
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], Optional[OdmItemTermVO]
        ],
        find_activity_by_uid: Callable[[str], Optional[ActivityAR]],
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
    ) -> "OdmItem":
        return cls(
            uid=odm_item_ar._uid,
            oid=odm_item_ar.concept_vo.oid,
            name=odm_item_ar.concept_vo.name,
            prompt=odm_item_ar.concept_vo.prompt,
            datatype=odm_item_ar.concept_vo.datatype,
            length=odm_item_ar.concept_vo.length,
            significantDigits=odm_item_ar.concept_vo.significant_digits,
            sasFieldName=odm_item_ar.concept_vo.sas_field_name,
            sdsVarName=odm_item_ar.concept_vo.sds_var_name,
            origin=odm_item_ar.concept_vo.origin,
            comment=odm_item_ar.concept_vo.comment,
            libraryName=odm_item_ar.library.name,
            startDate=odm_item_ar.item_metadata.start_date,
            endDate=odm_item_ar.item_metadata.end_date,
            status=odm_item_ar.item_metadata.status.value,
            version=odm_item_ar.item_metadata.version,
            changeDescription=odm_item_ar.item_metadata.change_description,
            userInitials=odm_item_ar.item_metadata.user_initials,
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_item_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name,
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_item_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name,
            ),
            unitDefinitions=sorted(
                [
                    OdmItemUnitDefinitionWithRelationship.from_unit_definition_uid(
                        uid=odm_item_ar._uid,
                        unit_definition_uid=unit_definition_uid,
                        find_unit_definition_by_uid=find_unit_definition_by_uid,
                        find_unit_definition_with_item_relation_by_item_uid=find_unit_definition_with_item_relation_by_item_uid,
                        find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for unit_definition_uid in odm_item_ar.concept_vo.unit_definition_uids
                ],
                key=lambda item: item.name,
            ),
            codelist=CTCodelistAttributesSimpleModel.from_codelist_uid(
                uid=odm_item_ar.concept_vo.codelist_uid,
                find_codelist_attribute_by_codelist_uid=find_codelist_attribute_by_codelist_uid,
            ),
            terms=sorted(
                [
                    OdmItemTermRelationshipModel.from_odm_item_uid(
                        uid=odm_item_ar._uid,
                        term_uid=term_uid,
                        find_term_with_item_relation_by_item_uid=find_term_with_item_relation_by_item_uid,
                    )
                    for term_uid in odm_item_ar.concept_vo.term_uids
                ],
                key=lambda item: item.name,
            ),
            activities=sorted(
                [
                    ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_uid,
                        find_activity_by_uid=find_activity_by_uid,
                    )
                    for activity_uid in odm_item_ar.concept_vo.activity_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionTags=sorted(
                [
                    OdmXmlExtensionTagRelationModel.from_uid(
                        uid=xml_extension_tag_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_tag_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_uid in odm_item_ar.concept_vo.xml_extension_tag_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionAttributes=sorted(
                [
                    OdmXmlExtensionAttributeRelationModel.from_uid(
                        uid=xml_extension_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                        xml_extension_tag_attribute=False,
                    )
                    for xml_extension_attribute_uid in odm_item_ar.concept_vo.xml_extension_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            xmlExtensionTagAttributes=sorted(
                [
                    OdmXmlExtensionTagAttributeRelationModel.from_uid(
                        uid=xml_extension_tag_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_xml_extension_attribute_by_uid_with_odm_element_relation,
                    )
                    for xml_extension_tag_attribute_uid in odm_item_ar.concept_vo.xml_extension_tag_attribute_uids
                ],
                key=lambda item: item.name,
            ),
            possibleActions=sorted(
                [_.value for _ in odm_item_ar.get_possible_actions()]
            ),
        )


class OdmItemRefModel(BaseModel):
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        item_group_uid: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], Optional[OdmItemRefVO]
        ],
    ) -> Optional["OdmItemRefModel"]:

        if uid is not None:
            odm_item_ref_vo = find_odm_item_by_uid_with_item_group_relation(
                uid, item_group_uid
            )

            if odm_item_ref_vo is not None:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=odm_item_ref_vo.oid,
                    name=odm_item_ref_vo.name,
                    orderNumber=odm_item_ref_vo.order_number,
                    mandatory=odm_item_ref_vo.mandatory,
                    dataEntryRequired=odm_item_ref_vo.data_entry_required,
                    sdv=odm_item_ref_vo.sdv,
                    locked=odm_item_ref_vo.locked,
                    keySequence=odm_item_ref_vo.key_sequence,
                    methodOid=odm_item_ref_vo.method_oid,
                    imputationMethodOid=odm_item_ref_vo.imputation_method_oid,
                    role=odm_item_ref_vo.role,
                    roleCodelistOid=odm_item_ref_vo.role_codelist_oid,
                    collectionExceptionConditionOid=odm_item_ref_vo.collection_exception_condition_oid,
                )
            else:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    orderNumber=None,
                    mandatory=None,
                    dataEntryRequired=None,
                    sdv=None,
                    locked=None,
                    keySequence=None,
                    methodOid=None,
                    imputationMethodOid=None,
                    role=None,
                    roleCodelistOid=None,
                    collectionExceptionConditionOid=None,
                )
        else:
            odm_item_ref_model = None
        return odm_item_ref_model

    uid: str = Field(..., title="uid", description="")
    oid: Optional[str] = Field(None, title="oid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    orderNumber: Optional[int] = Field(None, title="orderNumber", description="")
    mandatory: Optional[str] = Field(None, title="mandatory", description="")
    dataEntryRequired: Optional[str] = Field(
        None, title="dataEntryRequired", description=""
    )
    sdv: Optional[str] = Field(None, title="sdv", description="")
    locked: Optional[str] = Field(None, title="locked", description="")
    keySequence: Optional[str] = Field(None, title="keySequence", description="")
    methodOid: Optional[str] = Field(None, title="methodOid", description="")
    imputationMethodOid: Optional[str] = Field(
        None, title="imputationMethodOid", description=""
    )
    role: Optional[str] = Field(None, title="role", description="")
    roleCodelistOid: Optional[str] = Field(
        None, title="roleCodelistOid", description=""
    )
    collectionExceptionConditionOid: Optional[str] = Field(
        None, title="collectionExceptionConditionOid", description=""
    )


class OdmItemTermRelationshipInput(BaseModel):
    uid: str
    mandatory: bool = True
    order: Optional[int] = 999999


class OdmItemUnitDefinitionRelationshipInput(BaseModel):
    uid: str
    mandatory: bool = True
    order: Optional[int] = 999999


class OdmItemPostInput(ConceptPostInput):
    oid: Optional[str]
    datatype: str
    prompt: Optional[str]
    length: Optional[int]
    significantDigits: Optional[int]
    sasFieldName: Optional[str]
    sdsVarName: Optional[str]
    origin: Optional[str]
    comment: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]
    codelistUid: Optional[str]
    unitDefinitions: Sequence[OdmItemUnitDefinitionRelationshipInput] = []
    terms: Sequence[OdmItemTermRelationshipInput] = []


class OdmItemWithRelationsPostInput(ConceptPostInput):
    oid: Optional[str]
    datatype: str
    prompt: Optional[str]
    length: Optional[int]
    significantDigits: Optional[int]
    sasFieldName: Optional[str]
    sdsVarName: Optional[str]
    origin: Optional[str]
    comment: Optional[str]
    descriptions: Sequence[Union[OdmDescriptionPostInput, str]]
    aliasUids: Sequence[str]
    codelistUid: Optional[str]
    unitDefinitions: Sequence[OdmItemUnitDefinitionRelationshipInput] = []
    terms: Sequence[OdmItemTermRelationshipInput] = []


class OdmItemPatchInput(ConceptPatchInput):
    oid: Optional[str]
    prompt: Optional[str]
    datatype: Optional[str]
    length: Optional[int]
    significantDigits: Optional[int]
    sasFieldName: Optional[str]
    sdsVarName: Optional[str]
    origin: Optional[str]
    comment: Optional[str]
    descriptionUids: Sequence[str]
    aliasUids: Sequence[str]
    unitDefinitions: Sequence[OdmItemUnitDefinitionRelationshipInput]
    codelistUid: Optional[str]
    terms: Sequence[OdmItemTermRelationshipInput]


class OdmItemWithRelationsPatchInput(ConceptPatchInput):
    oid: Optional[str]
    datatype: Optional[str]
    prompt: Optional[str]
    length: Optional[int]
    significantDigits: Optional[int]
    sasFieldName: Optional[str]
    sdsVarName: Optional[str]
    origin: Optional[str]
    comment: Optional[str]
    descriptions: Sequence[
        Union[OdmDescriptionBatchPatchInput, OdmDescriptionPostInput]
    ]
    aliasUids: Sequence[str]
    unitDefinitions: Sequence[OdmItemUnitDefinitionRelationshipInput]
    codelistUid: Optional[str]
    terms: Sequence[OdmItemTermRelationshipInput]


class OdmItemActivityPostInput(BaseModel):
    uid: str


class OdmItemVersion(OdmItem):
    """
    Class for storing OdmItem and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
