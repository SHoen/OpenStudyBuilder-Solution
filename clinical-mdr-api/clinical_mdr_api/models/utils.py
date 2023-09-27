import json
import re
from copy import copy
from typing import Any, Callable, Generic, Iterable, Self, Sequence, Type, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import conint, create_model
from pydantic.generics import GenericModel
from starlette.responses import Response

from clinical_mdr_api.config import STUDY_TIME_UNIT_SUBSET
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)

EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA = {
    "remove_from_wildcard",
    "source",
    "exclude_from_orm",
}

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
        """
        We override this method to allow flattening on nested models.

        It is now possible to declare a source property on a Field()
        call to specify the location where this method should get a
        field's value from.
        """

        def _extract_part_from_node(node_to_extract, path, extract_from_relationship):
            """
            Traverse specified path in the node_to_extract.
            The possible paths for the traversal are stored in the node _relations dictionary.
            """
            if extract_from_relationship:
                path += "_relationship"
            if not hasattr(node_to_extract, "_relations"):
                return None
            if path not in node_to_extract._relations.keys():
                # it means that the field is Optional and None was set to be a default value
                if field.field_info.default is None:
                    return None
                raise RuntimeError(
                    f"{path} is not present in node relations (did you forget to fetch it?)"
                )
            return node_to_extract._relations[path]

        ret = []
        for name, field in cls.__fields__.items():
            source = field.field_info.extra.get("source")
            if field.field_info.extra.get("exclude_from_orm"):
                continue
            if not source:
                if issubclass(field.type_, BaseModel):
                    # get out of recursion
                    if field.type_ is cls:
                        continue
                    # added copy to not override properties in main obj
                    value = field.type_.from_orm(copy(obj))
                    # if some value of nested model is initialized then set the whole nested object
                    if isinstance(value, list):
                        if value:
                            setattr(obj, name, value)
                        else:
                            setattr(obj, name, [])
                    else:
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
            if "." in source or "|" in source:
                orig_source = source
                # split by . that implicates property on node or | that indicates property on the relationship
                parts = re.split(r"[.|]", source)
                source = parts[-1]
                last_traversal = parts[-2]
                node = obj
                parts = parts[:-1]
                for _, part in enumerate(parts):
                    extract_from_relationship = False
                    if part == last_traversal and "|" in orig_source:
                        extract_from_relationship = True
                    # if node is a list of nodes we want to extract property/relationship
                    # from all nodes in list of nodes
                    if isinstance(node, list):
                        return_node = []
                        for n in node:
                            extracted = _extract_part_from_node(
                                node_to_extract=n,
                                path=part,
                                extract_from_relationship=extract_from_relationship,
                            )
                            return_node.extend(extracted)
                        node = return_node
                    else:
                        node = _extract_part_from_node(
                            node_to_extract=node,
                            path=part,
                            extract_from_relationship=extract_from_relationship,
                        )
                    if node is None:
                        break
            else:
                node = obj
            if node is not None:
                # if node is a list we want to
                # extract property from each element of list and return list of property values
                if isinstance(node, list):
                    value = [getattr(n, source) for n in node]
                else:
                    value = getattr(node, source)
            else:
                value = None
            if issubclass(field.type_, BaseModel):
                value = field.type_.from_orm(node._relations[source])
            # if obtained value is a list and field type is not List
            # it means that we are building some list[BaseModel] but its fields are not of list type

            if isinstance(value, list) and not field.sub_fields:
                # if ret array is not instantiated
                # it means that the first property out of the whole list [BaseModel] is being instantiated
                if not ret:
                    for val in value:
                        temp_obj = copy(obj)
                        setattr(temp_obj, name, val)
                        ret.append(temp_obj)
                # if ret exists it means that some properties out of whole list [BaseModel] are already instantiated
                else:
                    for val, item in zip(value, ret):
                        setattr(item, name, val)
            else:
                setattr(obj, name, value)
        # Nothing to return and the value returned by the query
        # is an empty list => return an empty list
        if not ret and isinstance(value, list):
            return []
        # Returning single BaseModel
        if not ret and not isinstance(value, list):
            return super().from_orm(obj)
        # if ret exists it means that the list of BaseModels is being returned
        objs_to_return = []
        for item in ret:
            objs_to_return.append(super().from_orm(item))
        return objs_to_return

    class Config:
        # Configuration applies to all our models #

        @staticmethod
        def schema_extra(schema: dict[str, Any], _: Type) -> None:
            """Exclude some custom internal attributes of Fields (properties) from the schema definitions"""
            for prop in schema.get("properties", {}).values():
                for attr in EXCLUDE_PROPERTY_ATTRIBUTES_FROM_SCHEMA:
                    prop.pop(attr, None)


def strtobool(value: str, default: int | None = None) -> int | None:
    """Convert a string representation of truth to integer 1 (true) or 0 (false).

    Returns 1 for True values: 'y', 'yes', 't', 'true', 'on', '1'.
    Returns 0 for False values: 'n', 'no', 'f', 'false', 'off', '0'.
    Otherwise raises ValueError.

    Reimplemented because of deprecation https://peps.python.org/pep-0632/#migration-advice

    Returns int to remain compatible with Python 3.7 distutils.util.strtobool().
    However, a new parameter `default` has been introduced to the reimplementation.
    If `value` evaluates to False then value of `default` will be returned.
    """

    if not value:
        return default

    val = value.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return 1
    if val in ("n", "no", "f", "false", "off", "0"):
        return 0
    raise ValueError(f"invalid truth value {value:r}")


def booltostr(b: bool | str, true_format: str = "Yes") -> str:
    """
    Converts a boolean value to a string representation.
    True values are 'y', 'Yes', 'yes', 't', 'true', 'on', and '1';
    False values are 'n', 'No', 'no', 'f', 'false', 'off', and '0'.

    Args:
        b (bool | str): The boolean value to convert. If a string is passed, it will be converted to a boolean.
        true_format (str, optional): The string representation of the True value. Defaults to "Yes".

    Returns:
        str: The string representation of the boolean value.

    Raises:
        ValueError: If the true_format argument is invalid.
    """
    if isinstance(b, str):
        b = bool(strtobool(b))

    mapping = {
        "y": "n",
        "Yes": "No",
        "yes": "no",
        "t": "f",
        "true": "false",
        "on": "off",
        "1": "0",
    }

    if true_format in mapping:
        if b:
            return true_format
        return mapping[true_format]
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
        camel_name = snake_to_camel(name)
        pydantic_definition[camel_name] = (
            BASIC_TYPE_MAP[value.__class__.__name__],
            ...,
        )

    create_model_name = neomodel_root.__name__.replace("Root", "CreateInput")
    basic_model_name = neomodel_root.__name__.replace("Root", "Model")
    create_py_model = create_model(create_model_name, **pydantic_definition)
    for name, value in root_definition.items():
        camel_name = snake_to_camel(name)
        pydantic_definition[camel_name] = (
            BASIC_TYPE_MAP[value.__class__.__name__],
            ...,
        )
    pydantic_model = create_model(basic_model_name, **pydantic_definition)
    return pydantic_model, create_py_model


def is_attribute_in_model(attribute: str, model: BaseModel) -> bool:
    """
    Checks if given string is an attribute defined in a model (in the Pydantic sense).
    This works for the model's own attributes and inherited attributes.
    """
    return attribute in model.__fields__.keys()


T = TypeVar("T")


class CustomPage(GenericModel, Generic[T]):
    """
    A generic class used as a return type for paginated queries.

    Attributes:
        items (Sequence[T]): The items returned by the query.
        total (int): The total number of items that match the query.
        page (int): The number of the current page.
        size (int): The maximum number of items per page.
    """

    items: Sequence[T]
    total: conint(ge=0)
    page: conint(ge=0)
    size: conint(ge=0)

    @classmethod
    def create(cls, items: Sequence[T], total: int, page: int, size: int) -> Self:
        return cls(total=total, items=items, page=page, size=size)


class GenericFilteringReturn(GenericModel, Generic[T]):
    """
    A generic class used as a return type for filtered queries.

    Attributes:
        items (Sequence[T]): The items returned by the query.
        total (int): The total number of items that match the query.
    """

    items: Sequence[T]
    total: conint(ge=0)

    @classmethod
    def create(cls, items: Sequence[T], total: int) -> Self:
        return cls(items=items, total=total)


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=4,
            separators=(", ", ": "),
        ).encode("utf-8")
