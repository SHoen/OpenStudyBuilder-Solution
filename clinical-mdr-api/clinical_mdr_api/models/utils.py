import re
from copy import copy
from typing import Any, Callable, Dict, Generic, Iterable, Sequence, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import conint, create_model
from pydantic.generics import GenericModel

from clinical_mdr_api.config import STUDY_TIME_UNIT_SUBSET
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR

EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA = {"removeFromWildcard", "source"}

BASIC_TYPE_MAP = {
    "StringProperty": str,
    "BooleanProperty": bool,
    "UniqueIdProperty": str,
    "IntegerProperty": int,
}


def to_lower_camel(string: str) -> str:
    split = string.split("_")
    return "".join(
        split[wn].capitalize() if wn > 0 else split[wn].casefold()
        for wn in range(0, len(split))
    )


def from_duration_object_to_value_and_unit(
    duration: str,
    find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
):
    duration_code = duration[-1].lower()
    # cut off the first 'P' and last unit letter
    duration_value = int(duration[1:-1])

    all_study_time_units, _ = find_all_study_time_units(subset=STUDY_TIME_UNIT_SUBSET)
    # We are using a callback here and this function returns objects as an item list, hence we need to unwrap i
    found_unit = None
    # find unit extracted from iso duration string (duration_code) and find it in the set of all age units
    for unit in all_study_time_units:
        if unit.name[0].lower() == duration_code:
            found_unit = unit
            break
    return duration_value, found_unit


class BaseModel(PydanticBaseModel):
    @classmethod
    def from_orm(cls, obj):
        """We override this method to allow flattening on nested models.

        It is now possible to declare a source property on a Field()
        call to specify the location where this method should get a
        field's value from.

        NOTE: we still have an issue with nested models

        """
        for name, field in cls.__fields__.items():
            source = field.field_info.extra.get("source")
            if field.field_info.extra.get("excludeFromOrm"):
                continue
            if not source:
                if issubclass(field.type_, BaseModel):
                    # get out of recursion
                    if field.type_ is cls:
                        continue
                    # added copy to not override properties in main obj
                    value = field.type_.from_orm(copy(obj))
                    # if some value of nested model is initialized then set the whole nested object
                    if any(value.dict().values()):
                        setattr(obj, name, value)
                    # if all values of nested model are None set the whole object to None
                    else:
                        setattr(obj, name, None)
                # Quick fix to provide default None value to fields that allow it
                # Not the best place to do this...
                elif field.field_info.default is Ellipsis and not hasattr(obj, name):
                    setattr(obj, name, None)
                continue
            if "." in source:
                parts = source.split(".")
                source = parts[-1]
                node = obj
                parts = parts[:-1]
                for _, part in enumerate(parts):
                    if part not in node._relations.keys():
                        # it means that the field is Optional and None was set to be a default value
                        if field.field_info.default is None:
                            node = None
                            break
                        raise RuntimeError(
                            f"{part} is not present in node relations (did you forget to fetch it?)"
                        )
                    node = node._relations[part]
            else:
                node = obj
            if node is not None:
                value = getattr(node, source)
            else:
                value = None
            if issubclass(field.type_, BaseModel):
                value = field.type_.from_orm(node._relations[source])
            setattr(obj, name, value)
        return super().from_orm(obj)

    class Config:
        # Configuration applies to all our models #

        @staticmethod
        def schema_extra(schema: Dict[str, Any], _: Type) -> None:
            """Exclude some custom internal attributes of Fields (properties) from the schema definitions"""
            for prop in schema.get("properties", {}).values():
                for attr in EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA:
                    prop.pop(attr, None)


def booltostr(b: bool, true_format: str = "Yes"):
    """
    Convert a boolean to a string representation of truth.
    True values are 'y', 'Yes', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'No', 'no', 'f', 'false', 'off', and '0'.
    Raises ValueError if 'true_format' is anything else than True values.

    b: boolean value to convert to string.
    true_format: format of the string representation of truth. Only True values allowed.
    """

    if true_format in ("y", "Yes", "yes", "t", "true", "on", "1"):
        if b:
            return true_format
        if true_format == "Yes":
            return "No"
        if true_format == "yes":
            return "no"
        if true_format == "y":
            return "n"
        if true_format == "true":
            return "false"
        if true_format == "t":
            return "f"
        if true_format == "on":
            return "off"
        if true_format == "1":
            return "0"
    raise ValueError(f"Invalid true format {true_format}")


def snake_to_camel(name):
    name = "".join(word.title() for word in name.split("_"))
    name = f"{name[0].lower()}{name[1:]}"
    return name


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def snake_case_data(datadict, privates=False):
    return_value = {}
    for key, value in datadict.items():
        if privates:
            new_key = f"_{camel_to_snake(key)}"
        else:
            new_key = camel_to_snake(key)
        return_value[new_key] = value
    return return_value


def camel_case_data(datadict):
    return_value = {}
    for key, value in datadict.items():
        return_value[snake_to_camel(key)] = value
    return return_value


def pydantic_model_factory(neomodel_root: type, neomodel_value: type):
    root_definition = neomodel_root.get_definition()
    value_definition = neomodel_value.get_definition()
    pydantic_definition = {}
    for name, value in value_definition.items():
        camelName = snake_to_camel(name)
        pydantic_definition[camelName] = (BASIC_TYPE_MAP[value.__class__.__name__], ...)

    create_model_name = neomodel_root.__name__.replace("Root", "CreateInput")
    basic_model_name = neomodel_root.__name__.replace("Root", "Model")
    create_py_model = create_model(create_model_name, **pydantic_definition)
    for name, value in root_definition.items():
        camelName = snake_to_camel(name)
        pydantic_definition[camelName] = (BASIC_TYPE_MAP[value.__class__.__name__], ...)
    pydantic_model = create_model(basic_model_name, **pydantic_definition)
    return pydantic_model, create_py_model


def isAttributeInModel(attribute: str, model: BaseModel) -> bool:
    """
    Checks if given string is an attribute defined in a model (in the Pydantic sense).
    This works for the model's own attributes and inherited attributes.
    """
    return attribute in model.__fields__.keys()


T = TypeVar("T")


class CustomPage(GenericModel, Generic[T]):
    items: Sequence[T]
    total: conint(ge=0)  # type: ignore
    page: conint(ge=0)  # type: ignore
    size: conint(ge=0)  # type: ignore

    @classmethod
    def create(
        cls, items: Sequence[T], total: int, page: int, size: int
    ) -> "CustomPage":

        return cls(total=total, items=items, page=page, size=size)


class GenericFilteringReturn(GenericModel, Generic[T]):
    items: Sequence[T]
    total_count: conint(ge=0)  # type: ignore

    @classmethod
    def create(cls, items: Sequence[T], total_count: int) -> "GenericFilteringReturn":

        return cls(items=items, total_count=total_count)


class InfiniteIntegerField(int):
    """
    Integer field allowing a 'inf' and '-inf' literals to describe plus and minus infinity.
    Additionally accepts 'n/a' literal to describe null value.
    """

    INF_LITERAL = "inf"
    NEG_INF_LITERAL = "-inf"
    NOT_APPLICABLE_LITERAL = "n/a"

    def __init__(self, v):
        if isinstance(v, str):
            self.string_value = v
        elif isinstance(v, int):
            self.string_value = str(v)
            super().__init__(v)
        else:
            raise TypeError("Invalid value")

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            if v == cls.INF_LITERAL:
                return float("inf")
            if v == cls.NEG_INF_LITERAL:
                return float("-inf")
            if v == cls.NOT_APPLICABLE_LITERAL:
                return ""
            return int(v)
        if isinstance(v, int):
            return v
        if v is None:
            return v
        raise ValueError("Unknown Type")
