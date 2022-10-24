from datetime import datetime
from time import time
from typing import Dict, Optional, Sequence, Union
from xml.dom.minidom import Document

from clinical_mdr_api.domain._utils import get_iso_lang_data
from clinical_mdr_api.domain.concepts.odms.odm_xml_definition import (
    V1,
    V2,
    Attribute,
    Tag,
)
from clinical_mdr_api.domain.concepts.utils import OdmExportTo, TargetType
from clinical_mdr_api.models.odm_form import OdmForm
from clinical_mdr_api.models.odm_item import OdmItem
from clinical_mdr_api.models.odm_item_group import OdmItemGroup
from clinical_mdr_api.services.odm_data_extractor import OdmDataExtractor


class OdmXmlExporterService:
    odm_data_extractor: OdmDataExtractor
    xml_document: Document
    odm: Union[V1.ODM, V2.Oam]
    used_xml_extensions: Optional[Dict[str, dict]] = None
    allowed_extensions: Optional[Sequence[str]]

    ODM_VERSION = "osb:version"
    XML_LANG = "xml:lang"

    def __init__(
        self,
        target_uid: str,
        target_type: TargetType,
        export_to: OdmExportTo,
        allowed_extensions: Optional[Sequence[str]],
        stylesheet: str,
        unit_definition_service,
    ):
        self.odm_data_extractor = OdmDataExtractor(
            target_uid, target_type, unit_definition_service
        )
        self.allowed_extensions = allowed_extensions

        if self.used_xml_extensions is None:
            self.used_xml_extensions = {}

        if not self.allowed_extensions:
            for uid, ext in self.odm_data_extractor.odm_xml_extensions.items():
                self.used_xml_extensions[uid] = ext

        self.odm = self._create_odm_object(export_to)
        self.xml_document = Document()
        if stylesheet:
            self.xml_document.appendChild(
                self.xml_document.createProcessingInstruction(
                    "xml-stylesheet", f'type="text/xsl" href="{stylesheet}"'
                )
            )

    def get_odm_xml(self):
        return self._generate_odm_xml(self.odm, self.xml_document).toprettyxml(
            encoding="utf-8"
        )

    def _generate_odm_xml(self, odm_element, current_xml_element):
        if hasattr(odm_element, "_custom_tag_name") and isinstance(
            odm_element._custom_tag_name, str
        ):
            new_xml_element = self.xml_document.createElement(
                odm_element._custom_tag_name
            )
        else:
            new_xml_element = self.xml_document.createElement(
                odm_element.__class__.__name__
            )

        attributes = odm_element.__dict__.items()

        for attribute_name, attribute_value in attributes:
            if isinstance(attribute_value, Attribute):
                new_xml_element.setAttribute(
                    attribute_value.Name, str(attribute_value.Value)
                )
            elif isinstance(attribute_value, str):
                if attribute_name == "_custom_tag_name":
                    continue
                new_xml_element.appendChild(
                    self.xml_document.createTextNode(attribute_value)
                )
            elif isinstance(attribute_value, list):
                for odm_element_from_list in attribute_value:
                    self._generate_odm_xml(odm_element_from_list, new_xml_element)
            else:
                self._generate_odm_xml(attribute_value, new_xml_element)

        current_xml_element.appendChild(new_xml_element)

        return self.xml_document

    def _get_osb_elm_or_none_value(self, elm: Union[Attribute, list, dict]):
        if not self.allowed_extensions or "osb" in self.allowed_extensions:
            return elm

        if isinstance(elm, Attribute):
            setattr(elm, "Value", None)
            return elm

        if isinstance(elm, list):
            return []

        if isinstance(elm, dict):
            return {}

        return None

    def _create_xml_extension_attributes_of(
        self, target: Union[OdmForm, OdmItemGroup, OdmItem]
    ) -> Dict[str, Attribute]:
        attributes = {}

        for xml_extension_attribute in target.xmlExtensionAttributes:
            odm_xml_extension = self.odm_data_extractor.odm_xml_extensions[
                xml_extension_attribute.odmXmlExtensionUid
            ]
            if not self.allowed_extensions or (
                odm_xml_extension["prefix"] in self.allowed_extensions
            ):
                attributes[xml_extension_attribute.name] = Attribute(
                    f"{odm_xml_extension['prefix']}:{xml_extension_attribute.name}",
                    xml_extension_attribute.value,
                )

                self.used_xml_extensions[
                    xml_extension_attribute.odmXmlExtensionUid
                ] = odm_xml_extension

        return attributes

    def _create_xml_extension_tags_of(
        self, target: Union[OdmForm, OdmItemGroup, OdmItem]
    ) -> Dict[str, Tag]:
        tags = {}

        for xml_extension_tag in target.xmlExtensionTags:
            odm_xml_extension_tag = self.odm_data_extractor.odm_xml_extension_tags[
                xml_extension_tag.uid
            ]["xmlExtension"]
            if not self.allowed_extensions or (
                odm_xml_extension_tag["prefix"] in self.allowed_extensions
            ):
                tags[xml_extension_tag.name] = Tag(
                    _custom_tag_name=f"{self.odm_data_extractor.odm_xml_extension_tags[xml_extension_tag.uid]['xmlExtension']['prefix']}"
                    f":{xml_extension_tag.name}",
                    _string=xml_extension_tag.value,
                    **{
                        xmlExtensionTagAttribute.name: Attribute(
                            # pylint:disable=line-too-long
                            f"{self.odm_data_extractor.odm_xml_extension_tags[xmlExtensionTagAttribute.odmXmlExtensionTagUid]['xmlExtension']['prefix']}:{xmlExtensionTagAttribute.name}",
                            xmlExtensionTagAttribute.value,
                        )
                        for xmlExtensionTagAttribute in target.xmlExtensionTagAttributes
                        if xmlExtensionTagAttribute.odmXmlExtensionTagUid
                        == xml_extension_tag.uid
                    },
                )

                self.used_xml_extensions[
                    odm_xml_extension_tag["uid"]
                ] = odm_xml_extension_tag

        return tags

    def _create_odm_object(self, export_to: OdmExportTo):
        if export_to == OdmExportTo.V1:
            return self._create_odm_v1_object()
        if export_to == OdmExportTo.V2:
            return self._create_odm_v2_object()

        raise NotImplementedError("Requested export system not supported")

    def _create_odm_v1_object(self):
        def create_odm_form_def():
            return [
                V1.FormDef(
                    OID=Attribute("OID", form.oid),
                    Name=Attribute("Name", form.name),
                    Repeating=Attribute("Repeating", form.repeating),
                    **self._get_osb_elm_or_none_value(
                        {"Version": Attribute(self.ODM_VERSION, form.version)}
                    ),
                    **self._create_xml_extension_attributes_of(form),
                    **self._create_xml_extension_tags_of(form),
                    Description=V1.Description(
                        [
                            V1.TranslatedText(
                                description.description,
                                Lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        q=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_osb_elm_or_none_value(
                                    {
                                        "Version": Attribute(
                                            self.ODM_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in form.descriptions
                            if description.description
                        ]
                    ),
                    Alias=[
                        V1.Alias(
                            Name=Attribute("Name", alias.name),
                            Context=Attribute("Context", alias.context),
                            **self._get_osb_elm_or_none_value(
                                {"Version": Attribute(self.ODM_VERSION, alias.version)}
                            ),
                        )
                        for alias in form.aliases
                    ],
                    ItemGroupRef=[
                        V1.ItemGroupRef(
                            ItemGroupOID=Attribute("ItemGroupOID", item_group.oid),
                            Mandatory=Attribute("Mandatory", item_group.mandatory),
                            OrderNumber=Attribute(
                                "OrderNumber", item_group.orderNumber
                            ),
                            CollectionExceptionConditionOID=Attribute(
                                "CollectionExceptionConditionOID",
                                item_group.collectionExceptionConditionOid,
                            ),
                            **self._get_osb_elm_or_none_value(
                                {"Locked": Attribute("osb:locked", item_group.locked)}
                            ),
                        )
                        for item_group in form.itemGroups
                    ],
                )
                for form in self.odm_data_extractor.odm_forms
            ]

        def create_odm_item_group_def():
            SDTM_MSG_COLOURS = ["#bfffff", "#ffff96", "#96ff96", "#ffbf9c"]

            return [
                V1.ItemGroupDef(
                    OID=Attribute("OID", item_group.oid),
                    Name=Attribute("Name", item_group.name),
                    Purpose=Attribute("Purpose", item_group.purpose),
                    Repeating=Attribute("Repeating", item_group.repeating),
                    SASDatasetName=Attribute(
                        "SASDatasetName", item_group.sasDatasetName
                    ),
                    Domain=Attribute(
                        "Domain",
                        "|".join(
                            [
                                f"{sdtm_domain.codeSubmissionValue}:{sdtm_domain.preferredTerm}"
                                for sdtm_domain in item_group.sdtmDomains
                            ]
                        ),
                    )
                    if item_group.sdtmDomains
                    else "",
                    **self._get_osb_elm_or_none_value(
                        {"Version": Attribute(self.ODM_VERSION, item_group.version)}
                    ),
                    **self._create_xml_extension_attributes_of(item_group),
                    **self._create_xml_extension_tags_of(item_group),
                    osbDomainColor=self._get_osb_elm_or_none_value(
                        [
                            V1.osbDomainColor(
                                f"{sdtm_domain.codeSubmissionValue}:{SDTM_MSG_COLOURS[idx]};"
                            )
                            for idx, sdtm_domain in enumerate(item_group.sdtmDomains)
                        ]
                    )
                    if item_group.sdtmDomains
                    else [],
                    Description=V1.Description(
                        [
                            V1.TranslatedText(
                                description.description,
                                Lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        q=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_osb_elm_or_none_value(
                                    {
                                        "Version": Attribute(
                                            self.ODM_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item_group.descriptions
                            if description.description
                        ]
                    ),
                    Alias=[
                        V1.Alias(
                            Name=Attribute("Name", alias.name),
                            Context=Attribute("Context", alias.context),
                            **self._get_osb_elm_or_none_value(
                                {"Version": Attribute(self.ODM_VERSION, alias.version)}
                            ),
                        )
                        for alias in item_group.aliases
                    ],
                    ItemRef=[
                        V1.ItemRef(
                            ItemOID=Attribute("ItemOID", item.oid),
                            Mandatory=Attribute("Mandatory", item.mandatory),
                            OrderNumber=Attribute("OrderNumber", item.orderNumber),
                            CollectionExceptionConditionOID=Attribute(
                                "CollectionExceptionConditionOID",
                                item.collectionExceptionConditionOid,
                            ),
                            **self._get_osb_elm_or_none_value(
                                {
                                    "Sdv": Attribute("osb:sdv", item.sdv),
                                    "Locked": Attribute("osb:locked", item.locked),
                                }
                            ),
                        )
                        for item in item_group.items
                    ],
                )
                for item_group in self.odm_data_extractor.odm_item_groups
            ]

        def create_odm_item_def():
            return [
                V1.ItemDef(
                    OID=Attribute("OID", item.oid),
                    Name=Attribute("Name", item.name),
                    Origin=Attribute("Origin", item.origin),
                    DataType=Attribute("DataType", item.datatype.lower()),
                    Length=Attribute("Length", item.length),
                    SASFieldName=Attribute("SASFieldName", item.sasFieldName),
                    SDSVarName=Attribute("SDSVarName", item.sdsVarName),
                    **self._get_osb_elm_or_none_value(
                        {"Version": Attribute(self.ODM_VERSION, item.version)}
                    ),
                    **self._create_xml_extension_attributes_of(item),
                    **self._create_xml_extension_tags_of(item),
                    Alias=[
                        V1.Alias(
                            Name=Attribute("Name", alias.name),
                            Context=Attribute("Context", alias.context),
                            **self._get_osb_elm_or_none_value(
                                {"Version": Attribute(self.ODM_VERSION, alias.version)}
                            ),
                        )
                        for alias in item.aliases
                    ],
                    Description=V1.Description(
                        [
                            V1.TranslatedText(
                                description.description,
                                Lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        q=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_osb_elm_or_none_value(
                                    {
                                        "Version": Attribute(
                                            self.ODM_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item.descriptions
                            if description.description
                        ]
                    ),
                    Question=V1.Question(
                        [
                            V1.TranslatedText(
                                description.name,
                                Lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        q=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_osb_elm_or_none_value(
                                    {
                                        "Version": Attribute(
                                            self.ODM_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in item.descriptions
                            if description.name
                        ]
                    ),
                    CodeListRef=V1.CodeListRef(
                        CodeListOID=Attribute(
                            "CodeListOID",
                            f"{item.codelist.submissionValue}@{item.oid}"
                            if item.codelist
                            else None,
                        )
                    ),
                    MeasurementUnitRef=[
                        V1.MeasurementUnitRef(
                            MeasurementUnitOID=Attribute(
                                "MeasurementUnitOID", unit_definition.name
                            )
                        )
                        for unit_definition in item.unitDefinitions
                    ],
                )
                for item in self.odm_data_extractor.odm_items
            ]

        def create_odm_condition_def():
            return [
                V1.ConditionDef(
                    OID=Attribute("OID", condition.oid),
                    Name=Attribute("Name", condition.name),
                    **self._get_osb_elm_or_none_value(
                        {"Version": Attribute(self.ODM_VERSION, condition.version)}
                    ),
                    FormalExpression=[
                        V1.FormalExpression(
                            _string=formal_expression.expression,
                            Context=Attribute("Context", formal_expression.context),
                            **self._get_osb_elm_or_none_value(
                                {
                                    "Version": Attribute(
                                        self.ODM_VERSION, formal_expression.version
                                    )
                                }
                            ),
                        )
                        for formal_expression in condition.formalExpressions
                    ],
                    Alias=[
                        V1.Alias(
                            Name=Attribute("Name", alias.name),
                            Context=Attribute("Context", alias.context),
                            **self._get_osb_elm_or_none_value(
                                {"Version": Attribute(self.ODM_VERSION, alias.version)}
                            ),
                        )
                        for alias in condition.aliases
                    ],
                    Description=V1.Description(
                        [
                            V1.TranslatedText(
                                description.description,
                                Lang=Attribute(
                                    self.XML_LANG,
                                    get_iso_lang_data(
                                        q=description.language, return_key="639-1"
                                    ),
                                ),
                                **self._get_osb_elm_or_none_value(
                                    {
                                        "Version": Attribute(
                                            self.ODM_VERSION, description.version
                                        )
                                    }
                                ),
                            )
                            for description in condition.descriptions
                            if description.description
                        ]
                    ),
                )
                for condition in self.odm_data_extractor.odm_conditions
            ]

        def create_odm_codelist():
            codelists = []

            for codelist in self.odm_data_extractor.codelists:
                items = self.odm_data_extractor.get_items_by_codelist_uid(
                    codelist.codelistUid
                )

                for item in items:
                    term_uids = [term.termUid for term in item.terms]

                    codelists.append(
                        V1.CodeList(
                            OID=Attribute(
                                "OID", f"{codelist.submissionValue}@{item.oid}"
                            ),
                            Name=Attribute("Name", codelist.codelistUid),
                            DataType=Attribute("DataType", "string"),
                            SASFormatName=Attribute(
                                "SASFormatName", codelist.submissionValue
                            ),
                            CodeListItem=[
                                V1.CodeListItem(
                                    CodedValue=Attribute(
                                        "CodedValue",
                                        codelist_item["codeSubmissionValue"],
                                    ),
                                    Decode=V1.Decode(
                                        V1.TranslatedText(
                                            codelist_item["nciPreferredName"],
                                            Attribute(
                                                self.XML_LANG,
                                                get_iso_lang_data(
                                                    q="eng", return_key="639-1"
                                                ),
                                            ),
                                        )
                                    ),
                                    **self._get_osb_elm_or_none_value(
                                        {
                                            "OID": Attribute(
                                                "osb:OID", codelist_item["termUid"]
                                            )
                                        }
                                    ),
                                )
                                for codelist_item in self.odm_data_extractor.ct_terms
                                if codelist.codelistUid == codelist_item["codelistUid"]
                                and codelist_item["termUid"] in term_uids
                            ],
                        )
                    )

            return codelists

        def create_odm_measurement_unit():
            unit_definition_uids = []
            unit_definitions = []
            for unit_definition in self.odm_data_extractor.unit_definitions:
                if unit_definition.ucum is not None:
                    if unit_definition.ucum.termUid in unit_definition_uids:
                        continue
                    unit_definition_uids.append(unit_definition.ucum.termUid)
                    unit_definitions.append(
                        V1.MeasurementUnit(
                            OID=Attribute("OID", unit_definition.name),
                            Name=Attribute("Name", unit_definition.ucum.termUid),
                            Symbol=V1.Symbol(
                                V1.TranslatedText(
                                    unit_definition.name,
                                    Lang=Attribute(
                                        self.XML_LANG,
                                        get_iso_lang_data(q="eng", return_key="639-1"),
                                    ),
                                )
                            ),
                        )
                    )

            return unit_definitions

        return V1.ODM(
            OdmNS=Attribute("xmlns:odm", "http://www.cdisc.org/ns/odm/v1.3"),
            ODMVersion=Attribute("ODMVersion", "1.3.2"),
            FileType=Attribute("FileType", "Snapshot"),
            FileOID=Attribute("FileOID", f"OID.{int(time() * 1_000)}"),
            CreationDateTime=Attribute("CreationDateTime", datetime.now()),
            Granularity=Attribute("Granularity", "All"),
            Study=V1.Study(
                OID=Attribute(
                    "OID",
                    f"{self.odm_data_extractor.target_name}-{self.odm_data_extractor.target_uid}",
                ),
                MetaDataVersion=V1.MetaDataVersion(
                    OID=Attribute("OID", "MDV.0.1"),
                    Name=Attribute("Name", "MDV.0.1"),
                    Description=Attribute("Description", "Draft version"),
                    FormDef=create_odm_form_def(),
                    ItemGroupDef=create_odm_item_group_def(),
                    ItemDef=create_odm_item_def(),
                    ConditionDef=create_odm_condition_def(),
                    CodeList=create_odm_codelist(),
                ),
                BasicDefinitions=V1.BasicDefinitions(
                    MeasurementUnit=create_odm_measurement_unit()
                ),
                GlobalVariables=V1.GlobalVariables(
                    ProtocolName=V1.ProtocolName(self.odm_data_extractor.target_name),
                    StudyName=V1.StudyName(self.odm_data_extractor.target_name),
                    StudyDescription=V1.StudyDescription(
                        self.odm_data_extractor.target_name
                    ),
                ),
            ),
            **{
                used_xml_extension["prefix"]: Attribute(
                    f"xmlns:{used_xml_extension['prefix']}",
                    used_xml_extension["namespace"],
                )
                for used_xml_extension in self.used_xml_extensions.values()
                if not self.allowed_extensions
                or used_xml_extension["prefix"] in self.allowed_extensions
            },
        )

    def _create_odm_v2_object(self):
        return V2.Oam(
            Aliases=[
                V2.TranslatedText("XYZ", Attribute("123", "321")),
                V2.TranslatedText("ZYX", Attribute("123", "321")),
            ],
            Texts=[
                V2.Alias(Attribute("A", "1"), Attribute("B", "2")),
                V2.Alias(Attribute("C", "3"), Attribute("D", "4")),
            ],
        )
