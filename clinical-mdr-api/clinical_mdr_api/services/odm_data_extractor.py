from typing import Dict, Optional, Sequence

from clinical_mdr_api.domain.concepts.utils import TargetType
from clinical_mdr_api.models.ct_codelist_attributes import CTCodelistAttributes
from clinical_mdr_api.models.odm_condition import OdmCondition
from clinical_mdr_api.models.odm_form import OdmForm
from clinical_mdr_api.models.odm_item import OdmItem
from clinical_mdr_api.models.odm_item_group import OdmItemGroup
from clinical_mdr_api.models.unit_definition import UnitDefinitionModel
from clinical_mdr_api.services.ct_codelist_attributes import CTCodelistAttributesService
from clinical_mdr_api.services.ct_term_attributes import CTTermAttributesService
from clinical_mdr_api.services.odm_conditions import OdmConditionService
from clinical_mdr_api.services.odm_forms import OdmFormService
from clinical_mdr_api.services.odm_item_groups import OdmItemGroupService
from clinical_mdr_api.services.odm_items import OdmItemService
from clinical_mdr_api.services.odm_templates import OdmTemplateService
from clinical_mdr_api.services.odm_xml_extension_tags import OdmXmlExtensionTagService
from clinical_mdr_api.services.odm_xml_extensions import OdmXmlExtensionService
from clinical_mdr_api.services.unit_definition import UnitDefinitionService


class OdmDataExtractor:
    target_uid: str
    target_name: str

    odm_xml_extensions: Optional[Dict[str, dict]] = None
    odm_xml_extension_tags: Optional[Dict[str, dict]] = None
    odm_forms: Optional[Sequence[OdmForm]] = None
    odm_item_groups: Optional[Sequence[OdmItemGroup]] = None
    odm_items: Optional[Sequence[OdmItem]] = None
    odm_conditions: Optional[Sequence[OdmCondition]] = None
    codelists: Optional[Sequence[CTCodelistAttributes]] = None
    ct_terms: Optional[Sequence[Dict[str, str]]] = None
    unit_definitions: Optional[Sequence[UnitDefinitionModel]] = None

    xml_extension_service: OdmXmlExtensionService
    xml_extension_tag_service: OdmXmlExtensionTagService
    template_service: OdmTemplateService
    form_service: OdmFormService
    item_group_service: OdmItemGroupService
    item_service: OdmItemService
    condition_service: OdmConditionService
    ct_codelist_attributes_service: CTCodelistAttributesService
    ct_term_attributes_service: CTTermAttributesService
    unit_definition_service: UnitDefinitionService

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
        unit_definition_service,
    ):
        self.unit_definition_service = unit_definition_service
        self.xml_extension_service = OdmXmlExtensionService()
        self.xml_extension_tag_service = OdmXmlExtensionTagService()
        self.template_service = OdmTemplateService()
        self.form_service = OdmFormService()
        self.item_group_service = OdmItemGroupService()
        self.item_service = OdmItemService()
        self.condition_service = OdmConditionService()
        self.ct_codelist_attributes_service = CTCodelistAttributesService()
        self.ct_term_attributes_service = CTTermAttributesService()

        if self.odm_xml_extensions is None:
            self.odm_xml_extensions = {}
        if self.odm_xml_extension_tags is None:
            self.odm_xml_extension_tags = {}
        if self.odm_forms is None:
            self.odm_forms = []
        if self.odm_item_groups is None:
            self.odm_item_groups = []
        if self.odm_items is None:
            self.odm_items = []
        if self.odm_conditions is None:
            self.odm_conditions = []
        if self.codelists is None:
            self.codelists = []
        if self.ct_terms is None:
            self.ct_terms = []
        if self.unit_definitions is None:
            self.unit_definitions = []

        if target_type == TargetType.TEMPLATE:
            template = self.template_service.get_by_uid(target_uid)
            self.target_name = template.name
            self.set_forms_of_target(template)
        elif target_type == TargetType.FORM:
            self.odm_forms.append(self.form_service.get_by_uid(target_uid))
            self.target_name = self.odm_forms[0].name
            self.set_item_groups_of_forms(self.odm_forms)
        elif target_type == TargetType.ITEM_GROUP:
            self.odm_item_groups.append(self.item_group_service.get_by_uid(target_uid))
            self.target_name = self.odm_item_groups[0].name
            self.set_items_of_item_groups(self.odm_item_groups)
        elif target_type == TargetType.ITEM:
            self.odm_items.append(self.item_service.get_by_uid(target_uid))
            self.target_name = self.odm_items[0].name
            self.set_unit_definitions_of_items(self.odm_items)
            self.set_codelists_of_items(self.odm_items)
        else:
            raise NotImplementedError("Requested target type not supported")

        self.set_conditions(self.odm_forms, self.odm_item_groups)

        self.target_uid = target_uid

        xml_extensions = self.xml_extension_service.get_all_concepts().items
        self.odm_xml_extensions = {
            xml_extension.uid: {
                "name": xml_extension.name,
                "prefix": xml_extension.prefix,
                "namespace": xml_extension.namespace,
            }
            for xml_extension in xml_extensions
        }

        odm_xml_extension_tag_uids = (
            {tag.uid for form in self.odm_forms for tag in form.xmlExtensionTags}
            | {
                tag.uid
                for item_group in self.odm_item_groups
                for tag in item_group.xmlExtensionTags
            }
            | {tag.uid for item in self.odm_items for tag in item.xmlExtensionTags}
        )
        xml_extension_tags = self.xml_extension_tag_service.get_all_concepts(
            filter_by={"uid": {"v": odm_xml_extension_tag_uids, "op": "eq"}},
        ).items
        self.odm_xml_extension_tags = {
            xml_extension_tag.uid: {
                "name": xml_extension_tag.name,
                "xmlExtension": xml_extension_tag.xmlExtension.__dict__,
                "parentXmlExtensionTag": xml_extension_tag.parentXmlExtensionTag.__dict__
                if xml_extension_tag.parentXmlExtensionTag
                else None,
            }
            for xml_extension_tag in xml_extension_tags
        }

    def set_forms_of_target(self, target):
        self.odm_forms = self.form_service.get_all_concepts(
            filter_by={
                "uid": {
                    "v": [form.uid for form in target.forms],
                    "op": "eq",
                }
            },
            only_specific_status=["LATEST_FINAL", "LATEST_RETIRED"],
        ).items

        self.set_item_groups_of_forms(self.odm_forms)

    def set_item_groups_of_forms(self, forms: Sequence[OdmForm]):
        self.odm_item_groups = self.item_group_service.get_all_concepts(
            filter_by={
                "uid": {
                    "v": [
                        itemGroup.uid for form in forms for itemGroup in form.itemGroups
                    ],
                    "op": "eq",
                }
            },
            only_specific_status=["LATEST_FINAL", "LATEST_RETIRED"],
        ).items

        self.set_items_of_item_groups(self.odm_item_groups)

    def set_items_of_item_groups(self, item_groups: Sequence[OdmItemGroup]):
        self.odm_items = self.item_service.get_all_concepts(
            filter_by={
                "uid": {
                    "v": [
                        item.uid
                        for item_group in item_groups
                        for item in item_group.items
                    ],
                    "op": "eq",
                }
            },
            only_specific_status=["LATEST_FINAL", "LATEST_RETIRED"],
        ).items

        self.set_unit_definitions_of_items(self.odm_items)
        self.set_codelists_of_items(self.odm_items)
        self.set_conditions(self.odm_forms, self.odm_item_groups)

    def set_conditions(self, forms, item_groups):
        oids = [
            item_group.collectionExceptionConditionOid
            for form in forms
            for item_group in form.itemGroups
        ] + [
            item.collectionExceptionConditionOid
            for item_group in item_groups
            for item in item_group.items
        ]

        if oids:
            self.odm_conditions = self.condition_service.get_all_concepts(
                filter_by={"oid": {"v": oids, "op": "eq"}},
                only_specific_status=["LATEST_FINAL", "LATEST_RETIRED"],
            ).items

    def set_unit_definitions_of_items(self, items: Sequence[OdmItem]):
        self.unit_definitions = self.unit_definition_service.get_all(
            library_name=None,
            filter_by={
                "uid": {
                    "v": [
                        unit_definition.uid
                        for item in items
                        for unit_definition in item.unitDefinitions
                    ],
                    "op": "eq",
                }
            },
        ).items

    def set_codelists_of_items(self, items: Sequence[OdmItem]):
        self.codelists = self.ct_codelist_attributes_service.get_all_ct_codelists(
            catalogue_name=None,
            library=None,
            package=None,
            filter_by={
                "codelistUid": {
                    "v": [item.codelist.uid for item in items if item.codelist],
                    "op": "eq",
                }
            },
        ).items

        self.set_terms_of_codelists(self.codelists)

    def set_terms_of_codelists(self, codelists: Sequence[CTCodelistAttributes]):
        self.ct_terms = (
            self.ct_term_attributes_service.get_term_attributes_by_codelist_uids(
                [codelist.codelistUid for codelist in codelists]
            )
        )

    def get_items_by_codelist_uid(self, codelist_uid: str):
        return [
            item
            for item in self.odm_items
            if item.codelist and item.codelist.uid == codelist_uid
        ]
