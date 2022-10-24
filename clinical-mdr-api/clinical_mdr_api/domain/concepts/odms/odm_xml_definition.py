"""
This file contains classes for all tags and attributes that can be used for generating ODM-XML.

There are some conventions to note:
- Classes defined here are subject to be converted to either an XML Tag or an XML Attribute.
- If a class contains a property called `_custom_tag_name` of type `str` then the name of
  the XML Tag, generated based on this class, will be as specified in `_custom_tag_name`.
- Properties of type `Attribute` of all classes are considered to be XML attributes for the class these properties are present in.
- Properties of type `str` of all classes, except `Attribute` class, are considered to be inner text of the XML Tag, generated based on these classes.
  For the sake of consistency, name such properties `_string`.

E.g. given the following class:
class TranslatedText:
    _custom_tag_name: str
    _string: str
    Lang: Attribute

When we instantiate it:
TranslatedText("_custom_tag_name":"Translation", "_string": "This is inner text", "Lang": Attribute("lang", "en"))
the following will be produced:
<Translation lang="en">This is inner text</Translation>
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence, Union


class Tag:
    _custom_tag_name: str

    def __init__(self, _custom_tag_name, **kwargs):
        self._custom_tag_name = _custom_tag_name

        for name, val in kwargs.items():
            setattr(self, name, val)


@dataclass
class Attribute:
    Name: str
    Value: Optional[Union[str, int, datetime]]


class V1:
    @dataclass
    class TranslatedText:
        _string: str
        Lang: Attribute

        def __init__(self, _string, Lang, **kwargs):
            self._string = _string
            self.Lang = Lang

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class Decode:
        TranslatedText: "V1.TranslatedText"

    class CodeListItem:
        CodedValue: Attribute
        Decode: "V1.Decode"

        def __init__(self, CodedValue, Decode, **kwargs):
            self.CodedValue = CodedValue
            self.Decode = Decode

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class CodeList:
        OID: Attribute
        Name: Attribute
        DataType: Attribute
        SASFormatName: Attribute
        CodeListItem: Sequence["V1.CodeListItem"]

    class Alias:
        Name: Attribute
        Context: Attribute

        def __init__(self, Name, Context, **kwargs):
            self.Name = Name
            self.Context = Context

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class Description:
        TranslatedText: Sequence["V1.TranslatedText"]

    @dataclass
    class Question:
        TranslatedText: Sequence["V1.TranslatedText"]

    @dataclass
    class CodeListRef:
        CodeListOID: Attribute

    @dataclass
    class MeasurementUnitRef:
        MeasurementUnitOID: Attribute

    class FormalExpression:
        _string: str
        Context: Attribute

        def __init__(self, _string, Context, **kwargs):
            self._string = _string
            self.Context = Context

            for name, val in kwargs.items():
                setattr(self, name, val)

    class ConditionDef:
        OID: Attribute
        Name: Attribute
        Description: "V1.Description"
        Alias: Sequence["V1.Alias"]
        FormalExpression: Sequence["V1.FormalExpression"]

        def __init__(self, OID, Name, Description, Alias, FormalExpression, **kwargs):
            self.OID = OID
            self.Name = Name
            self.Description = Description
            self.Alias = Alias
            self.FormalExpression = FormalExpression

            for name, val in kwargs.items():
                setattr(self, name, val)

    class ItemDef:
        OID: Attribute
        Name: Attribute
        Origin: Attribute
        DataType: Attribute
        Length: Attribute
        SASFieldName: Attribute
        SDSVarName: Attribute
        Question: "V1.Question"
        Description: "V1.Description"
        Alias: Sequence["V1.Alias"]
        CodeListRef: "V1.CodeListRef"
        MeasurementUnitRef: Sequence["V1.MeasurementUnitRef"]

        def __init__(
            self,
            OID,
            Name,
            Origin,
            DataType,
            Length,
            SASFieldName,
            SDSVarName,
            Question,
            Description,
            Alias,
            CodeListRef,
            MeasurementUnitRef,
            **kwargs
        ):
            self.OID = OID
            self.Name = Name
            self.Origin = Origin
            self.DataType = DataType
            self.Length = Length
            self.SASFieldName = SASFieldName
            self.SDSVarName = SDSVarName
            self.Question = Question
            self.Description = Description
            self.Alias = Alias
            self.CodeListRef = CodeListRef
            self.MeasurementUnitRef = MeasurementUnitRef

            if not self.CodeListRef.CodeListOID.Value:
                del self.CodeListRef

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class ItemRef:
        ItemOID: Attribute
        Mandatory: Attribute
        OrderNumber: Attribute
        CollectionExceptionConditionOID: Attribute

        def __init__(
            self,
            ItemOID,
            Mandatory,
            OrderNumber,
            CollectionExceptionConditionOID,
            **kwargs
        ):
            self.ItemOID = ItemOID
            self.Mandatory = Mandatory
            self.OrderNumber = OrderNumber
            self.CollectionExceptionConditionOID = CollectionExceptionConditionOID

            if not self.CollectionExceptionConditionOID.Value:
                del self.CollectionExceptionConditionOID

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class osbDomainColor:
        _string: str
        _custom_tag_name: str = "osb:DomainColor"

    class ItemGroupDef:
        OID: Attribute
        Name: Attribute
        Repeating: Attribute
        Purpose: Attribute
        SASDatasetName: Attribute
        Domain: Attribute
        osbDomainColor: Sequence["V1.osbDomainColor"]
        Description: "V1.Description"
        Alias: Sequence["V1.Alias"]
        ItemRef: Sequence["V1.ItemRef"]

        def __init__(
            self,
            OID,
            Name,
            Repeating,
            Purpose,
            SASDatasetName,
            Domain,
            osbDomainColor,
            Description,
            Alias,
            ItemRef,
            **kwargs
        ):
            self.OID = OID
            self.Name = Name
            self.Repeating = Repeating
            self.Purpose = Purpose
            self.SASDatasetName = SASDatasetName
            self.Domain = Domain
            self.osbDomainColor = osbDomainColor
            self.Description = Description
            self.Alias = Alias
            self.ItemRef = ItemRef

            for name, val in kwargs.items():
                setattr(self, name, val)

    class ItemGroupRef:
        ItemGroupOID: Attribute
        Mandatory: Attribute
        OrderNumber: Attribute
        CollectionExceptionConditionOID: Attribute

        def __init__(
            self,
            ItemGroupOID,
            Mandatory,
            OrderNumber,
            CollectionExceptionConditionOID,
            **kwargs
        ):
            self.ItemGroupOID = ItemGroupOID
            self.Mandatory = Mandatory
            self.OrderNumber = OrderNumber
            self.CollectionExceptionConditionOID = CollectionExceptionConditionOID

            if not self.CollectionExceptionConditionOID.Value:
                del self.CollectionExceptionConditionOID

            for name, val in kwargs.items():
                setattr(self, name, val)

    class FormDef:
        OID: Attribute
        Name: Attribute
        Repeating: Attribute
        Description: "V1.Description"
        Alias: Sequence["V1.Alias"]
        ItemGroupRef: Sequence["V1.ItemGroupRef"]

        def __init__(
            self, OID, Name, Repeating, Description, Alias, ItemGroupRef, **kwargs
        ):
            self.OID = OID
            self.Name = Name
            self.Repeating = Repeating
            self.Description = Description
            self.Alias = Alias
            self.ItemGroupRef = ItemGroupRef

            for name, val in kwargs.items():
                setattr(self, name, val)

    @dataclass
    class Symbol:
        TranslatedText: "V1.TranslatedText"

    @dataclass
    class MeasurementUnit:
        OID: Attribute
        Name: Attribute
        Symbol: "V1.Symbol"

    @dataclass
    class MetaDataVersion:
        OID: Attribute
        Name: Attribute
        Description: Attribute
        FormDef: Sequence["V1.FormDef"]
        ItemGroupDef: Sequence["V1.ItemGroupDef"]
        ItemDef: Sequence["V1.ItemDef"]
        ConditionDef: Sequence["V1.ConditionDef"]
        CodeList: Sequence["V1.CodeList"]

    @dataclass
    class BasicDefinitions:
        MeasurementUnit: Sequence["V1.MeasurementUnit"]

    @dataclass
    class ProtocolName:
        _string: str

    @dataclass
    class StudyName:
        _string: str

    @dataclass
    class StudyDescription:
        _string: str

    @dataclass
    class GlobalVariables:
        ProtocolName: "V1.ProtocolName"
        StudyName: "V1.StudyName"
        StudyDescription: "V1.StudyDescription"

    @dataclass
    class Study:
        OID: Attribute
        GlobalVariables: "V1.GlobalVariables"
        BasicDefinitions: "V1.BasicDefinitions"
        MetaDataVersion: "V1.MetaDataVersion"

    @dataclass
    class ODM:
        OdmNS: Attribute
        ODMVersion: Attribute
        FileType: Attribute
        FileOID: Attribute
        CreationDateTime: Attribute
        Granularity: Attribute
        Study: "V1.Study"

        def __init__(
            self,
            OdmNS,
            ODMVersion,
            FileType,
            FileOID,
            CreationDateTime,
            Granularity,
            Study,
            **kwargs
        ):
            self.OdmNS = OdmNS
            self.ODMVersion = ODMVersion
            self.FileType = FileType
            self.FileOID = FileOID
            self.CreationDateTime = CreationDateTime
            self.Granularity = Granularity
            self.Study = Study

            for name, val in kwargs.items():
                setattr(self, name, val)


class V2:
    @dataclass
    class TranslatedText:
        _string: str
        Lang: Attribute

    @dataclass
    class Alias:
        Name: Attribute
        Context: Attribute

    @dataclass
    class Oam:
        Aliases: Sequence["V2.TranslatedText"]
        Texts: Sequence["V2.Alias"]
