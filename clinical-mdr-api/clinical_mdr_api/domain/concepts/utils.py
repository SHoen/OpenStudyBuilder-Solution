from enum import Enum

ENG_LANGUAGE = "ENG"


class RelationType(Enum):
    """
    Enum for type of relationship
    """

    ACTIVITY = "activity"
    ACTIVITY_GROUP = "activity_group"
    ACTIVITY_SUB_GROUP = "activity_subgroup"
    ITEM_GROUP = "item_group"
    ITEM = "item"
    FORM = "form"
    TERM = "term"
    UNIT_DEFINITION = "unit_definition"
    XML_EXTENSION_TAG = "xml_extension_tag"
    XML_EXTENSION_ATTRIBUTE = "xml_extension_attribute"
    XML_EXTENSION_TAG_ATTRIBUTE = "xml_extension_tag_attribute"


class TargetType(Enum):
    """
    Enum for ODM target types
    """

    TEMPLATE = "template"
    STUDY = "study"
    FORM = "form"
    ITEM_GROUP = "item_group"
    ITEM = "item"
