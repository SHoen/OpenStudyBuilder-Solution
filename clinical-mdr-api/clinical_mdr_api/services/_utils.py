import functools
import re
from collections.abc import Hashable
from dataclasses import dataclass
from time import time
from typing import (
    AbstractSet,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Set,
    TypeVar,
)

from pydantic import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain._utils import extract_parameters

# noinspection PyProtectedMember
from clinical_mdr_api.domain.simple_dictionaries._simple_dictionary_item_base import (
    SimpleDictionaryItemBase,
)
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.models.simple_dictionary_item import SimpleDictionaryItem
from clinical_mdr_api.models.template_parameter import (
    ComplexTemplateParameter,
    TemplateParameter,
    TemplateParameterValue,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    FilterDict,
    FilterOperator,
)


def get_term_uid_or_none(field):
    return field.termUid if field else None


def get_unit_def_uid_or_none(field):
    return field.uid if field else None


def get_input_or_new_value(
    input_field: str, prefix: str, output_field: str, sep: str = "."
):
    """
    Returns input_field if not empty, otherwise a new value based on prefix
    and the first letters of each word of output_field and time in seconds from epoch
    """
    if input_field:
        return input_field

    if not isinstance(output_field, str):
        raise ValueError(f"Expected type str but found {type(output_field)}")

    splitted = output_field.split()
    if len(splitted) > 1:
        initials = "".join([s[0] for s in splitted])
    else:
        initials = output_field[::2].upper()

    return f"{prefix}{initials}{sep}{int(time())}"


def strip_suffix(string: str, suffix: str = "Root") -> str:
    if string.endswith(suffix):
        return string[: -len(suffix)]
    return string


def object_diff(objt1, objt2=None):
    """
    Calculate difference table between pydantic objects
    """
    if objt2 is None:
        return {}
    return {name: objt1[name] != objt2[name] for name in objt1.keys()}


def get_otv(version_object_class, ot, ot2=None):
    """
    Creates object of the version_object_class extending object ot
    with the differences with object ot2
    """

    changes = object_diff(ot, ot2) if ot2 is not None else {}
    return version_object_class(changes=changes, **ot)


def calculate_diffs(result_list, version_object_class):
    """
    Calculates differences in a list of results and push the comparison results
    to a version_object_class object.
    Returns list of version_class_objects
    """

    if len(result_list) == 0:
        return []
    otv = get_otv(version_object_class, result_list[-1])
    return_list = [otv]
    for i in reversed(range(len(result_list) - 1)):
        item = result_list[i]
        otv = get_otv(version_object_class, item, result_list[i + 1])
        return_list.append(otv)

    return list(reversed(return_list))


def camel_to_snake(name: str) -> str:
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def json_model_from_simple_dictionary_item_ar(
    item_ar: SimpleDictionaryItemBase,
) -> SimpleDictionaryItem:
    return SimpleDictionaryItem(
        code=item_ar.code, name=item_ar.name, definition=item_ar.definition
    )


def fill_missing_values_in_base_model_from_reference_base_model(
    base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
) -> None:
    """
    Method fills missing values in the PATCH payload when only partial payload is sent by client.
    It takes the values from the model object based on the domain object.
    :param base_model_with_missing_values: BaseModel
    :param reference_base_model: BaseModel
    :return None:
    """
    for field_name in base_model_with_missing_values.__fields_set__:
        if isinstance(
            getattr(base_model_with_missing_values, field_name), BaseModel
        ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
            fill_missing_values_in_base_model_from_reference_base_model(
                getattr(base_model_with_missing_values, field_name),
                getattr(reference_base_model, field_name),
            )

    fields_to_assign_with_none = []
    fields_to_assign_with_previous_value = []
    # The following for loop iterates over all fields that are not present in the partial payload but are available
    # in the reference model and are available in the model that contains missing values
    for field_name in (
        reference_base_model.__fields_set__
        - base_model_with_missing_values.__fields_set__
    ).intersection(base_model_with_missing_values.__fields__):
        if field_name.endswith("Code") and not field_name.endswith("NullValueCode"):
            # both value field and null value code field not exists in the base (coming) set
            if (
                re.sub("Code", "", field_name) + "NullValueCode"
                not in base_model_with_missing_values.__fields_set__
            ):
                fields_to_assign_with_previous_value.append(field_name)
            # value field doesn't exist and null value field exist in the base (coming) set
            elif (
                re.sub("Code", "", field_name) + "NullValueCode"
                in base_model_with_missing_values.__fields_set__
            ):
                fields_to_assign_with_none.append(field_name)
        # value field doesn't exist and null value code exist in the base (coming) set but value is not code field
        elif (
            field_name + "NullValueCode"
            in base_model_with_missing_values.__fields_set__
        ):
            fields_to_assign_with_none.append(field_name)
        else:
            fields_to_assign_with_previous_value.append(field_name)
    for field_name in fields_to_assign_with_none:
        setattr(base_model_with_missing_values, field_name, None)
    for field_name in fields_to_assign_with_previous_value:
        setattr(
            base_model_with_missing_values,
            field_name,
            getattr(reference_base_model, field_name),
        )


@dataclass(frozen=True)
class FieldsDirective:
    _included_fields: AbstractSet[str]
    _excluded_fields: AbstractSet[str]
    _nested_fields_directives: Mapping[str, "FieldsDirective"]

    @classmethod
    def _from_include_and_exclude_spec_sets(
        cls, include_spec_set: AbstractSet[str], exclude_spec_set: AbstractSet[str]
    ) -> "FieldsDirective":

        _included_fields: Set[str] = set()
        _excluded_fields: Set[str] = set()
        _nested_include_specs: MutableMapping[str, Set[str]] = {}
        _nested_exclude_specs: MutableMapping[str, Set[str]] = {}

        for field_spec in include_spec_set - exclude_spec_set:
            dot_position_in_field_spec = field_spec.find(".")
            if dot_position_in_field_spec < 0:
                _included_fields.add(field_spec)
            else:
                spec_before_dot = field_spec[0:dot_position_in_field_spec]
                spec_after_dot = field_spec[dot_position_in_field_spec + 1 :]
                _included_fields.add(
                    spec_before_dot
                )  # directive to include subfields implicitly includes containing field as well
                if spec_before_dot not in _nested_include_specs:
                    _nested_include_specs[spec_before_dot] = set()
                _nested_include_specs[spec_before_dot].add(spec_after_dot)

        for field_spec in exclude_spec_set:
            dot_position_in_field_spec = field_spec.find(".")
            if dot_position_in_field_spec < 0:
                _excluded_fields.add(field_spec)
            else:
                spec_before_dot = field_spec[0:dot_position_in_field_spec]
                spec_after_dot = field_spec[dot_position_in_field_spec + 1 :]
                if spec_before_dot not in _nested_exclude_specs:
                    _nested_exclude_specs[spec_before_dot] = set()
                _nested_exclude_specs[spec_before_dot].add(spec_after_dot)

        _nested_fields_directives: MutableMapping[str, FieldsDirective] = {}
        for nested_field in _nested_include_specs.keys() | _nested_exclude_specs.keys():
            _nested_fields_directives[
                nested_field
            ] = cls._from_include_and_exclude_spec_sets(
                include_spec_set=_nested_include_specs[nested_field]
                if nested_field in _nested_include_specs
                else set(),
                exclude_spec_set=_nested_exclude_specs[nested_field]
                if nested_field in _nested_exclude_specs
                else set(),
            )

        return cls(
            _excluded_fields=_excluded_fields,
            _included_fields=_included_fields,
            _nested_fields_directives=_nested_fields_directives,
        )

    @classmethod
    def from_fields_query_parameter(
        cls, fields_query_parameter: Optional[str]
    ) -> "FieldsDirective":
        if fields_query_parameter is None:
            fields_query_parameter = ""
        fields_query_parameter = "".join(
            fields_query_parameter.split()
        )  # easy way to remove all white space

        include_specs_set: Set[str] = set()
        exclude_specs_set: Set[str] = set()

        for field_spec in fields_query_parameter.split(sep=","):
            if len(field_spec) < 1:
                continue
            exclude_spec = False
            if field_spec[0] == "-":
                exclude_spec = True
            if field_spec[0] == "-" or field_spec[0] == "+":
                field_spec = field_spec[1:]
            if len(field_spec) < 1:
                continue
            if exclude_spec:
                exclude_specs_set.add(field_spec)
            else:
                include_specs_set.add(field_spec)

        return cls._from_include_and_exclude_spec_sets(
            include_spec_set=include_specs_set, exclude_spec_set=exclude_specs_set
        )

    def is_field_included(self, field_path: str) -> bool:
        dot_position_in_field_path = field_path.find(".")
        if dot_position_in_field_path > 0:
            # in case of checking on child we recurse to nested field directive
            path_before_dot = field_path[0:dot_position_in_field_path]
            path_after_dot = field_path[dot_position_in_field_path + 1 :]
            if not self.is_field_included(path_before_dot):
                # if parent not included, anything below is also not included
                return False
            return self.get_fields_directive_for_children_of_field(
                path_before_dot
            ).is_field_included(path_after_dot)

        if field_path in self._excluded_fields:  # excludes takes precedence
            return False
        if len(self._included_fields) == 0:
            return (
                True  # when lacking any include spec we assume everything is included
            )
        return field_path in self._included_fields

    def get_fields_directive_for_children_of_field(
        self, field_path: str
    ) -> "FieldsDirective":
        dot_position_in_field_path = field_path.find(".")
        if dot_position_in_field_path > 0:
            path_before_dot = field_path[0:dot_position_in_field_path]
            path_after_dot = field_path[dot_position_in_field_path + 1 :]
            if not self.is_field_included(path_before_dot):
                raise ValueError(
                    "Cannot get fields directive for children of the field which is not included"
                )
            if path_before_dot not in self._nested_fields_directives:
                # if there's no specific we return "anything goes" directive
                return _ANYTHING_GOES_FIELDS_DIRECTIVE
            # other wise we recurse for specific directive
            return self._nested_fields_directives[
                path_before_dot
            ].get_fields_directive_for_children_of_field(path_after_dot)

        if not self.is_field_included(field_path):
            raise ValueError(
                "Cannot get fields directive for children of the field which is not included"
            )
        if field_path not in self._nested_fields_directives:
            # if there's no specific we return "anything goes" directive
            return _ANYTHING_GOES_FIELDS_DIRECTIVE
        # other wise we recurse for specific directive
        return self._nested_fields_directives[field_path]


_ANYTHING_GOES_FIELDS_DIRECTIVE = FieldsDirective.from_fields_query_parameter(None)

_SomeBaseModelSubtype = TypeVar("_SomeBaseModelSubtype", bound=BaseModel)


def filter_base_model_using_fields_directive(
    input_base_model: _SomeBaseModelSubtype, fields_directive: FieldsDirective
) -> _SomeBaseModelSubtype:
    args_dict_for_result_object = {}
    for field_name in input_base_model.__fields_set__:
        if fields_directive.is_field_included(field_name):
            field_value = getattr(input_base_model, field_name)
            if isinstance(field_value, BaseModel):
                field_value = filter_base_model_using_fields_directive(
                    input_base_model=field_value,
                    fields_directive=fields_directive.get_fields_directive_for_children_of_field(
                        field_name
                    ),
                )
            args_dict_for_result_object[field_name] = field_value
    return input_base_model.__class__(**args_dict_for_result_object)


def create_duration_object_from_api_input(
    value: int,
    unit: str,
    find_duration_name_by_code: Callable[[str], Optional[UnitDefinitionAR]],
) -> Optional[str]:
    """
    The following function transforms the API duration input to the iso duration format.
    For instance the following input: {value: 5, unit: Hour} will be transformed into 'P5H'.
    However, the function has to be prepared if the name of the term will be changed from the 'Hour' to 'hour' or 'Hour(s)'
    :param value:
    :param unit:
    :param find_duration_name_by_code:
    :return:
    """
    unit_definition_ar = find_duration_name_by_code(unit) if unit is not None else None
    if unit_definition_ar is not None:
        duration_unit = unit_definition_ar.name
        duration = f"P{str(value)}{duration_unit[0].upper()}"
        return duration
    return None


def normalize_string(s: Optional[str]) -> Optional[str]:
    """
    Removes leading and trailing whitespaces.
    Returns None if the resulting string is empty. Else returns the resulting string.

    :param s: The string that is intended to be normalized.
    :return: None or normalized string
    """
    if s is not None:
        s = s.strip()
    return None if s == "" else s


def service_level_generic_filtering(
    items: list,
    filter_by: Optional[dict] = None,
    filter_operator: FilterOperator = FilterOperator.AND,
    sort_by: Optional[dict] = None,
    total_count: bool = False,
    page_number: int = 1,
    page_size: int = 0,
) -> GenericFilteringReturn:
    if sort_by is None:
        sort_by = {}
    if filter_by is None:
        filter_by = {}

    filters = FilterDict(elements=filter_by)
    if filter_operator == FilterOperator.AND:
        # Start from full list, then only keep items that match filter elements, one by one
        filtered_items = items
        # The list will decrease after each step (aka filtering out)
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            filtered_items = list(
                filter(
                    lambda x: filter_aggregated_items(x, key, _values, _operator),
                    filtered_items,
                )
            )
    elif filter_operator == FilterOperator.OR:
        # Start from full list, then add items that match filter elements, one by one
        _filtered_items = []
        # The list will increase after each step
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            matching_items = list(
                filter(
                    lambda x: filter_aggregated_items(x, key, _values, _operator), items
                )
            )
            _filtered_items += matching_items
        # Finally, deduplicate list
        uids = set()
        filtered_items = []
        for item in _filtered_items:
            if item.uid not in uids:
                filtered_items.append(item)
                uids.add(item.uid)
    else:
        raise ValueError(f"Invalid filter_operator: {filter_operator}")
    # Do sorting
    for sort_key, sort_order in sort_by.items():
        filtered_items.sort(
            key=lambda x: extract_nested_key_value(x, sort_key), reverse=not sort_order
        )
    # Do count
    count = len(filtered_items) if total_count else 0
    # Do pagination
    if page_size > 0:
        filtered_items = filtered_items[
            (page_number - 1) * page_size : page_number * page_size
        ]

    return GenericFilteringReturn.create(items=filtered_items, total_count=count)


def service_level_generic_header_filtering(
    items: list,
    field_name: str,
    filter_operator: FilterOperator = FilterOperator.AND,
    search_string: str = "",
    filter_by: Optional[dict] = None,
    result_count: int = 10,
) -> list:
    if filter_by is None:
        filter_by = {}

    # Add header field name to filter_by, to filter with a CONTAINS pattern
    if search_string != "":
        filter_by[field_name] = {
            "v": [search_string],
            "op": ComparisonOperator.CONTAINS,
        }
    filters = FilterDict(elements=filter_by)
    if filter_operator == FilterOperator.AND:
        # Start from full list, then only keep items that match filter elements, one by one
        filtered_items = items
        # The list will decrease after each step (aka filtering out)
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            filtered_items = list(
                filter(
                    lambda x: filter_aggregated_items(x, key, _values, _operator),
                    filtered_items,
                )
            )
    else:
        # Start from full list, then add items that match filter elements, one by one
        _filtered_items = []
        # The list will increase after each step
        for key in filters.elements:
            _values = filters.elements[key].v
            _operator = filters.elements[key].op
            matching_items = list(
                filter(
                    lambda x: filter_aggregated_items(x, key, _values, _operator), items
                )
            )
            _filtered_items += matching_items
        # Finally, deduplicate list
        uids = set()
        filtered_items = []
        for item in _filtered_items:
            if item.uid not in uids:
                filtered_items.append(item)
                uids.add(item.uid)
    # Limit results returned
    filtered_items = filtered_items[:result_count]
    # Return values for field_name

    extracted_values = []
    for item in filtered_items:
        extracted_value = extract_nested_key_value(item, field_name)
        # The extracted value can be
        # * A list when the property associated with key is a list of objects
        # ** (e.g. categories.name.sponsorPreferredName for an Objective Template)
        if isinstance(extracted_value, list):
            # Merge lists
            extracted_values = extracted_values + extracted_value
        # * A single value when the property associated with key is a simple property
        # Skip if None
        elif extracted_value is not None:
            # Append element to list
            extracted_values.append(extracted_value)

    # Transform into a set in order to remove duplicates, then cast back to list
    if extracted_values and isinstance(extracted_values[0], Hashable):
        return list(set(extracted_values))
    unique_extracted_values = []
    for extracted_value in extracted_values:
        name = extracted_value.name
        if name not in unique_extracted_values:
            unique_extracted_values.append(name)
    return unique_extracted_values


def extract_nested_key_value(term, key):
    return rgetattr(term, key)


def extract_properties_for_wildcard(item, prefix: str = ""):
    output = []
    if prefix:
        prefix += "."
    # item can be None - ignore if it is
    if item:
        # We only want to extract the property keys from one of the items in the list
        if isinstance(item, list) and len(item) > 0:
            return extract_properties_for_wildcard(item[0], prefix[:-1])
        # Otherwise, let's iterate over all the attributes of the single item we have
        for attribute, attrDesc in item.__fields__.items():
            # The attribute might be a non-class dictionary
            # In that case, we extract the first value and make a recursive call on it
            if (
                isinstance(getattr(item, attribute), dict)
                and len(getattr(item, attribute)) > 0
            ):
                output = output + extract_properties_for_wildcard(
                    list(getattr(item, attribute).values())[0], attribute
                )
            # An attribute can be a nested class, which will inherit from Pydantic's BaseModel
            # In that case, we do a recursive call and add the attribute key of the class as a prefix, like "nestedClass."
            # Checking for isinstance of type will make sure that the attribute is a class before checking if it is a subclass
            elif isinstance(attrDesc.type_, type) and issubclass(
                attrDesc.type_, BaseModel
            ):
                output = output + extract_properties_for_wildcard(
                    getattr(item, attribute), prefix=prefix + attribute
                )
            # Or a "plain" attribute
            else:
                output.append(prefix + attribute)
    return output


def filter_aggregated_items(item, filter_key, filter_values, filter_operator):
    if filter_key == "*":
        # Only accept requests with default operator (set to equal by FilterDict class) or specified contains operator
        if (
            ComparisonOperator(filter_operator) != ComparisonOperator.EQUALS
            and ComparisonOperator(filter_operator) != ComparisonOperator.CONTAINS
        ):
            raise exceptions.NotFoundException(
                "Only the default 'contains' operator is supported for wildcard filtering."
            )
        property_list = extract_properties_for_wildcard(item)
        property_list_filter_match = [
            filter_aggregated_items(
                item, _key, filter_values, ComparisonOperator.CONTAINS
            )
            for _key in property_list
        ]

        return True in property_list_filter_match

    _item_value_for_key = extract_nested_key_value(item, filter_key)

    # The property associated with the filter key can be inside a list
    # e.g., categories.name.sponsorPreferredName for Objective Templates
    # In these cases, a list of values will be returned here
    # Filtering then becomes "if any of the values matches with the operator"
    if isinstance(_item_value_for_key, list):
        for _val in _item_value_for_key:
            # Return true as soon as any value matches with the operator
            if apply_filter_operator(_val, filter_operator, filter_values):
                return True
        return False
    return apply_filter_operator(_item_value_for_key, filter_operator, filter_values)


def apply_filter_operator(
    value, operator: ComparisonOperator, filter_values: Sequence
) -> bool:
    if len(filter_values) > 0:
        if ComparisonOperator(operator) == ComparisonOperator.EQUALS:
            return value in filter_values
        if ComparisonOperator(operator) == ComparisonOperator.CONTAINS:
            return any(str(_v).lower() in str(value).lower() for _v in filter_values)
        if ComparisonOperator(operator) == ComparisonOperator.GREATER_THAN:
            return str(value) > filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.GREATER_THAN_OR_EQUAL_TO:
            return str(value) >= filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.LESS_THAN:
            return str(value) < filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.LESS_THAN_OR_EQUAL_TO:
            return str(value) <= filter_values[0]
        if ComparisonOperator(operator) == ComparisonOperator.BETWEEN:
            filter_values.sort()
            return (
                filter_values[0].lower()
                <= str(value).lower()
                <= filter_values[1].lower()
            )
    # An empty filter_values list means that the returned item's property value should be null
    if ComparisonOperator(operator) == ComparisonOperator.EQUALS:
        return value is None
    return exceptions.InternalErrorException(
        "Filtering on a null value can be only be used with the 'equal' operator."
    )


# Recursive getattr to access properties in nested objects
def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        if isinstance(obj, list):
            return [_getattr(element, attr, *args) for element in obj]
        if isinstance(obj, dict):
            return [_getattr(element, attr, *args) for element in obj.values()]
        return getattr(obj, attr, *args) if hasattr(obj, attr) else None

    return functools.reduce(_getattr, [obj] + attr.split("."))


def process_complex_parameters(parameters, parameter_repository):
    return_parameters = []
    for _, item in enumerate(parameters):
        item_values = []
        if item["definition"] is not None:
            param_names = extract_parameters(item["template"])
            params = []
            for param_name in param_names:
                param_value_list = []
                if param_name != "NumericValue":
                    param = parameter_repository.get_parameter_including_values(
                        param_name
                    )
                    if param is not None:
                        for val in param["values"]:
                            if val["uid"] is not None:
                                tpv = TemplateParameterValue(
                                    name=val["name"], uid=val["uid"], type=val["type"]
                                )
                                param_value_list.append(tpv)
                tp = TemplateParameter(name=param_name, values=param_value_list)
                params.append(tp)
            return_parameters.append(
                ComplexTemplateParameter(
                    name=item["name"], format=item["template"], parameters=params
                )
            )
        else:
            for v in item["values"]:
                if v["uid"] is not None:
                    tpv = TemplateParameterValue(
                        name=v["name"], uid=v["uid"], type=v["type"]
                    )
                    item_values.append(tpv)
            return_parameters.append(
                TemplateParameter(name=item["name"], values=item_values)
            )
    return return_parameters


def calculate_diffs_history(
    get_all_object_versions: Callable,
    transform_all_to_history_model: Callable,
    study_uid: str,
    version_object_class,
):
    selection_history = get_all_object_versions(study_uid=study_uid)
    unique_list_uids = list({x.uid for x in selection_history})
    unique_list_uids.sort()
    # list of all study_elements
    data = []
    ith_selection_history = []
    for i_unique in unique_list_uids:
        ith_selection_history = []
        # gather the selection history of the i_unique Uid
        for x in selection_history:
            if x.uid == i_unique:
                ith_selection_history.append(x)
        ith_selection_history = sorted(
            ith_selection_history,
            key=lambda ith_selection: ith_selection.start_date,
            reverse=True,
        )
        versions = [
            transform_all_to_history_model(_).dict() for _ in ith_selection_history
        ]
        if not data:
            data = calculate_diffs(versions, version_object_class)
        else:
            data.extend(calculate_diffs(versions, version_object_class))
    return data
