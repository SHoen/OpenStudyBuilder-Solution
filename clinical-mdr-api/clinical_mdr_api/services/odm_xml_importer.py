from distutils.util import strtobool
from time import time
from typing import Optional, Union
from xml.dom import minicompat, minidom

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain._utils import get_iso_lang_data
from clinical_mdr_api.domain.concepts.utils import ENG_LANGUAGE, RelationType
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryVO,
    VersioningException,
)
from clinical_mdr_api.models import (
    OdmConditionPostInput,
    OdmDescriptionPostInput,
    OdmFormalExpressionPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPostInput,
    OdmItemGroupItemPostInput,
    OdmItemGroupPostInput,
    OdmItemPostInput,
    OdmItemUnitDefinitionRelationshipInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import normalize_string
from clinical_mdr_api.services.ct_codelist_attributes import CTCodelistAttributesService
from clinical_mdr_api.services.odm_conditions import OdmConditionService
from clinical_mdr_api.services.odm_descriptions import OdmDescriptionService
from clinical_mdr_api.services.odm_formal_expressions import OdmFormalExpressionService
from clinical_mdr_api.services.odm_forms import OdmFormService
from clinical_mdr_api.services.odm_item_groups import OdmItemGroupService
from clinical_mdr_api.services.odm_items import OdmItemService


class OdmXmlImporterService:
    _repos: MetaRepository
    odm_form_service: OdmFormService
    odm_item_group_service: OdmItemGroupService
    odm_item_service: OdmItemService
    odm_condition_service: OdmConditionService
    odm_formal_expression_service: OdmFormalExpressionService
    odm_description_service: OdmDescriptionService
    ct_codelist_attributes_service: CTCodelistAttributesService

    user_initials: Optional[str]

    xml_document: minidom.Document
    form_defs: minicompat.NodeList
    item_group_defs: minicompat.NodeList
    item_defs: minicompat.NodeList
    condition_defs: minicompat.NodeList
    codelists: minicompat.NodeList
    measurement_units: minicompat.NodeList

    db_forms: list = []
    db_item_groups: list = []
    db_items: list = []
    db_conditions: list = []
    db_codelist_attributes: list = []
    db_unit_definitions: list = []

    def __init__(self, xml: str):
        self._repos = MetaRepository()
        self.odm_form_service = OdmFormService()
        self.odm_item_group_service = OdmItemGroupService()
        self.odm_item_service = OdmItemService()
        self.odm_condition_service = OdmConditionService()
        self.odm_formal_expression_service = OdmFormalExpressionService()
        self.odm_description_service = OdmDescriptionService()
        self.ct_codelist_attributes_service = CTCodelistAttributesService()

        self.user_initials = "TODO user initials"

        self.xml_document = minidom.parseString(xml)
        self._set_def_elements()

    @db.transaction
    def store_odm_xml(self):
        self._set_unit_definitions()
        self._set_codelist_attributes()
        self._create_conditions_with_relations()
        self._create_items_with_relations()
        self._create_item_groups_with_relations()
        self._create_forms_with_relations()

        return {
            "forms": self._get_newly_created_forms(),
            "itemGroups": self._get_newly_created_item_groups(),
            "items": self._get_newly_created_items(),
            "conditions": self._get_newly_created_conditions(),
        }

    def _set_def_elements(self):
        self.measurement_units = self.xml_document.getElementsByTagName(
            "MeasurementUnit"
        )
        self.form_defs = self.xml_document.getElementsByTagName("FormDef")
        self.item_group_defs = self.xml_document.getElementsByTagName("ItemGroupDef")
        self.item_defs = self.xml_document.getElementsByTagName("ItemDef")
        self.condition_defs = self.xml_document.getElementsByTagName("ConditionDef")
        self.codelists = self.xml_document.getElementsByTagName("CodeList")

    def _set_unit_definitions(self):
        self.db_unit_definitions, _ = self._repos.unit_definition_repository.find_all(
            filter_by={
                "name": {
                    "v": [
                        measurement_unit.getAttribute("Name")
                        for measurement_unit in self.measurement_units
                    ],
                    "op": "eq",
                }
            },
        )

    def _set_codelist_attributes(self):
        rs = self._repos.ct_codelist_attribute_repository.find_all(
            filter_by={
                "name": {
                    "v": [
                        codelist_def.getAttribute("Name")
                        for codelist_def in self.codelists
                    ],
                    "op": "eq",
                }
            }
        )

        self.db_codelist_attributes = [
            self.ct_codelist_attributes_service._transform_aggregate_root_to_pydantic_model(
                ct_codelist_ar
            )
            for ct_codelist_ar in rs.items
        ]

    def _create_formal_expressions(self, condition_def):
        new_formal_expressions = []
        for formal_expression in condition_def.getElementsByTagName("FormalExpression"):
            self._create(
                self._repos.odm_formal_expression_repository,
                self.odm_formal_expression_service,
                new_formal_expressions,
                OdmFormalExpressionPostInput(
                    context=formal_expression.getAttribute("Context"),
                    expression=formal_expression.firstChild.nodeValue,
                ),
            )
        return new_formal_expressions

    def _create_conditions_with_relations(self):
        for condition_def in self.condition_defs:
            descriptions = self._extract_descriptions(condition_def)

            self._create(
                self._repos.odm_condition_repository,
                self.odm_condition_service,
                self.db_conditions,
                OdmConditionPostInput(
                    oid=condition_def.getAttribute("OID"),
                    name=condition_def.getAttribute("Name"),
                    formalExpressionUids=[
                        fe.uid for fe in self._create_formal_expressions(condition_def)
                    ],
                    descriptionUids=[
                        self._create_description(
                            name=description["name"],
                            description=description["description"],
                            lang=description["lang"],
                        ).uid
                        for description in descriptions
                    ],
                    aliasUids=[],
                ),
            )

    def _create_items_with_relations(self):
        for item_def in self.item_defs:
            descriptions = self._extract_descriptions(item_def)

            unit_definitions = []
            for measurement_unit_ref in item_def.getElementsByTagName(
                "MeasurementUnitRef"
            ):
                for mu in self.measurement_units:
                    if mu.getAttribute("OID") == measurement_unit_ref.getAttribute(
                        "MeasurementUnitOID"
                    ):
                        for dud in self.db_unit_definitions:
                            if dud.name == mu.getAttribute("Name"):
                                unit_definitions.append(
                                    OdmItemUnitDefinitionRelationshipInput(uid=dud.uid)
                                )

            item = self._create(
                self._repos.odm_item_repository,
                self.odm_item_service,
                self.db_items,
                OdmItemPostInput(
                    oid=item_def.getAttribute("OID"),
                    name=item_def.getAttribute("Name"),
                    prompt=item_def.getAttribute("Prompt"),
                    datatype=item_def.getAttribute("DataType"),
                    length=item_def.getAttribute("Length"),
                    sasFieldName=item_def.getAttribute("SASFieldName"),
                    sdsVarName=item_def.getAttribute("SDSVarName"),
                    descriptionUids=[
                        self._create_description(
                            name=description["name"],
                            description=description["description"],
                            lang=description["lang"],
                        ).uid
                        for description in descriptions
                    ],
                    aliasUids=[],
                    unitDefinitions=unit_definitions,
                    codelistUid=next(
                        (
                            dcla.codelistUid
                            for cl in self.codelists
                            if cl.getAttribute("OID")
                            == item_def.getElementsByTagName("CodeListRef")[
                                0
                            ].getAttribute("CodeListOID")
                            for dcla in self.db_codelist_attributes
                            if dcla.name == cl.getAttribute("Name")
                        ),
                        None,
                    ),
                    terms=[],
                ),
            )

            self.odm_item_service._manage_unit_definitions(item.uid, unit_definitions)

    def _create_item_groups_with_relations(self):
        for item_group_def in self.item_group_defs:
            descriptions = self._extract_descriptions(item_group_def)

            rs = self._create(
                self._repos.odm_item_group_repository,
                self.odm_item_group_service,
                self.db_item_groups,
                OdmItemGroupPostInput(
                    oid=item_group_def.getAttribute("OID"),
                    name=item_group_def.getAttribute("Name"),
                    origin=item_group_def.getAttribute("Origin"),
                    repeating=item_group_def.getAttribute("Repeating"),
                    isReferenceData="no",  # missing in odm
                    purpose=item_group_def.getAttribute("Purpose"),
                    sasDatasetName=item_group_def.getAttribute("SASDatasetName"),
                    descriptionUids=[
                        self._create_description(
                            name=description["name"],
                            description=description["description"],
                            lang=description["lang"],
                        ).uid
                        for description in descriptions
                    ],
                    aliasUids=[],
                    sdtmDomainUids=[],
                ),
            )

            self._approve(
                self._repos.odm_item_group_repository, self.odm_item_group_service, rs
            )

            odm_item_group_items = []
            for item_ref in item_group_def.getElementsByTagName("ItemRef"):
                odm_item_group_items.append(
                    OdmItemGroupItemPostInput(
                        uid=next(
                            (
                                di.uid
                                for di in self.db_items
                                if di.oid == item_ref.getAttribute("ItemOID")
                            ),
                            None,
                        ),
                        orderNumber=item_ref.getAttribute("OrderNumber"),
                        mandatory=item_ref.getAttribute("Mandatory"),
                        dataEntryRequired="no",
                        sdv="no",
                        locked="no",
                        keySequence="None",
                        methodOid="None",
                        imputationMethodOid="None",
                        role="None",
                        roleCodelistOid="None",
                        collectionExceptionConditionOid=item_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                    )
                )

            try:
                self._repos.odm_item_group_repository.remove_relation(
                    uid=rs.uid,
                    relation_uid=None,
                    relationship_type=RelationType.ITEM,
                    disconnect_all=True,
                )

                for item in odm_item_group_items:
                    self._repos.odm_item_group_repository.add_relation(
                        uid=rs.uid,
                        relation_uid=item.uid,
                        relationship_type=RelationType.ITEM,
                        parameters={
                            "order_number": item.orderNumber,
                            "mandatory": strtobool(item.mandatory),
                            "key_sequence": item.keySequence,
                            "method_oid": item.methodOid,
                            "imputation_method_oid": item.imputationMethodOid,
                            "role": item.role,
                            "role_codelist_oid": item.roleCodelistOid,
                            "collection_exception_condition_oid": item.collectionExceptionConditionOid,
                        },
                    )
            except ValueError as exception:
                raise exceptions.ValidationException(exception.args[0])

    def _create_forms_with_relations(self):
        for form_def in self.form_defs:
            descriptions = self._extract_descriptions(form_def)

            rs = self._create(
                self._repos.odm_form_repository,
                self.odm_form_service,
                self.db_forms,
                OdmFormPostInput(
                    oid=form_def.getAttribute("OID"),
                    name=form_def.getAttribute("Name"),
                    sdtmVersion="",
                    repeating=form_def.getAttribute("Repeating"),
                    descriptionUids=[
                        self._create_description(
                            name=description["name"],
                            description=description["description"],
                            lang=description["lang"],
                        ).uid
                        for description in descriptions
                    ],
                    aliasUids=[],
                ),
            )

            self._approve(self._repos.odm_form_repository, self.odm_form_service, rs)

            odm_form_item_groups = []
            for item_group_ref in form_def.getElementsByTagName("ItemGroupRef"):
                odm_form_item_groups.append(
                    OdmFormItemGroupPostInput(
                        uid=next(
                            (
                                dig.uid
                                for dig in self.db_item_groups
                                if dig.oid
                                == item_group_ref.getAttribute("ItemGroupOID")
                            ),
                            None,
                        ),
                        orderNumber=item_group_ref.getAttribute("OrderNumber"),
                        mandatory=item_group_ref.getAttribute("Mandatory"),
                        collectionExceptionConditionOid=item_group_ref.getAttribute(
                            "CollectionExceptionConditionOID"
                        ),
                    )
                )

            try:
                self._repos.odm_form_repository.remove_relation(
                    uid=rs.uid,
                    relation_uid=None,
                    relationship_type=RelationType.ITEM_GROUP,
                    disconnect_all=True,
                )

                for item_group in odm_form_item_groups:
                    self._repos.odm_form_repository.add_relation(
                        uid=rs.uid,
                        relation_uid=item_group.uid,
                        relationship_type=RelationType.ITEM_GROUP,
                        parameters={
                            "order_number": item_group.orderNumber,
                            "mandatory": strtobool(item_group.mandatory),
                            "collection_exception_condition_oid": item_group.collectionExceptionConditionOid,
                        },
                    )
            except ValueError as exception:
                raise exceptions.ValidationException(exception.args[0])

    def _create_description(
        self,
        name: Union[str, minidom.Text],
        description: Optional[str] = None,
        instruction: Optional[str] = None,
        lang: str = ENG_LANGUAGE,
    ):
        if isinstance(name, minidom.Text):
            name = name.nodeValue
        else:
            name = f"#{int(time() * 1_000)} {name}"

        if description is None:
            description = "Please update this description"

        if instruction is None:
            instruction = "Please update this instruction"

        concept_input = OdmDescriptionPostInput(
            name=name,
            language=lang,
            description=description,
            instruction=instruction,
        )

        library_vo = self.get_library(concept_input)

        try:
            concept_ar = self.odm_description_service._create_aggregate_root(
                concept_input=concept_input, library=library_vo
            )
            self._repos.odm_description_repository.save(concept_ar)
            return self.odm_description_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
        except ValueError as value_error:
            raise exceptions.ValidationException(value_error.args[0])

    def _extract_descriptions(self, elm):
        description_tag = elm.getElementsByTagName("Description")
        question_tag = elm.getElementsByTagName("Question")
        descriptions = []

        if description_tag:
            for tr in description_tag[0].getElementsByTagName("TranslatedText"):
                lang = tr.getAttribute("xml:lang")
                desc = tr.firstChild.nodeValue

                descriptions.append(
                    {
                        "lang": lang,
                        "name": desc,
                        "description": desc,
                    }
                )

        description_langs = [desc["lang"] for desc in descriptions]
        if question_tag:
            for tr in question_tag[0].getElementsByTagName("TranslatedText"):
                lang = tr.getAttribute("xml:lang")
                name = tr.firstChild

                if lang not in description_langs:
                    descriptions.append(
                        {
                            "lang": lang,
                            "name": name,
                            "description": None,
                        }
                    )
                else:
                    for description in descriptions:
                        if lang == description["lang"]:
                            description["name"] = name
                            break

        for desc in descriptions:
            desc["lang"] = get_iso_lang_data(desc["lang"], "639-1", "639-2/B").upper()

        if not any(description["lang"] == ENG_LANGUAGE for description in descriptions):
            raise ValueError("An English OdmDescription must be provided.")

        return descriptions

    def _get_newly_created_forms(self):
        try:
            rs, _ = self._repos.odm_form_repository.find_all(
                filter_by={
                    "uid": {
                        "v": [form.uid for form in self.db_forms],
                        "op": "eq",
                    }
                },
            )
        except ValueError as e:
            raise exceptions.ValidationException(e)

        return [
            self.odm_form_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_item_groups(self):
        try:
            rs, _ = self._repos.odm_item_group_repository.find_all(
                filter_by={
                    "uid": {
                        "v": [item_group.uid for item_group in self.db_item_groups],
                        "op": "eq",
                    }
                }
            )
        except ValueError as e:
            raise exceptions.ValidationException(e)

        return [
            self.odm_item_group_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_conditions(self):
        try:
            rs, _ = self._repos.odm_condition_repository.find_all(
                filter_by={
                    "uid": {
                        "v": [condition.uid for condition in self.db_conditions],
                        "op": "eq",
                    }
                }
            )
        except ValueError as e:
            raise exceptions.ValidationException(e)

        return [
            self.odm_condition_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def _get_newly_created_items(self):
        try:
            rs, _ = self._repos.odm_item_repository.find_all(
                filter_by={
                    "uid": {
                        "v": [item.uid for item in self.db_items],
                        "op": "eq",
                    }
                }
            )
        except ValueError as e:
            raise exceptions.ValidationException(e)

        return [
            self.odm_item_service._transform_aggregate_root_to_pydantic_model(
                concept_ar
            )
            for concept_ar in rs
        ]

    def get_library(self, concept_input):
        if not self._repos.library_repository.library_exists(
            normalize_string(concept_input.libraryName)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({concept_input.libraryName})"
            )

        return LibraryVO.from_input_values_2(
            library_name=concept_input.libraryName,
            is_library_editable_callback=(
                lambda name: self._repos.library_repository.find_by_name(
                    name
                ).is_editable
                if self._repos.library_repository.find_by_name(name) is not None
                else None
            ),
        )

    def _create(self, repository, service, save_to, concept_input):
        library_vo = self.get_library(concept_input)

        try:
            concept_ar = service._create_aggregate_root(
                concept_input=concept_input, library=library_vo
            )
            repository.save(concept_ar)
            item = service._transform_aggregate_root_to_pydantic_model(concept_ar)
            save_to.append(item)
            return item
        except ValueError as e:
            raise exceptions.ValidationException(e.args[0])

    def _approve(self, repository, service, item):
        try:
            appr = service._find_by_uid_or_raise_not_found(item.uid, for_update=True)
            appr.approve(author=self.user_initials)
            repository.save(appr)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
