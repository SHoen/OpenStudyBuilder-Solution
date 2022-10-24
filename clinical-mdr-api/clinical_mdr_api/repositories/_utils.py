import functools
import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from dateutil.parser import isoparse
from neomodel import Q
from pydantic import BaseModel, Field, validator
from pydantic.types import T, conlist
from six import class_types

from clinical_mdr_api import exceptions
from clinical_mdr_api.models.ct_term import SimpleTermModel

# Re-used regex
nestedRegex = re.compile(r"\.")

log = logging.getLogger(__name__)


class ComparisonOperator(Enum):
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "co"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL_TO = "ge"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL_TO = "le"
    BETWEEN = "bw"


comparison_operator_to_neomodel = {
    ComparisonOperator.EQUALS: "",
    ComparisonOperator.NOT_EQUALS: "__ne",
    ComparisonOperator.CONTAINS: "__contains",
    ComparisonOperator.GREATER_THAN: "__gt",
    ComparisonOperator.GREATER_THAN_OR_EQUAL_TO: "__gte",
    ComparisonOperator.LESS_THAN: "__lt",
    ComparisonOperator.LESS_THAN_OR_EQUAL_TO: "__lte",
}


data_type_filters = {
    str: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.CONTAINS,
    ],
    int: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
    ],
    float: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
    ],
    datetime: [
        ComparisonOperator.EQUALS,
        ComparisonOperator.NOT_EQUALS,
        ComparisonOperator.GREATER_THAN,
        ComparisonOperator.GREATER_THAN_OR_EQUAL_TO,
        ComparisonOperator.LESS_THAN,
        ComparisonOperator.LESS_THAN_OR_EQUAL_TO,
        ComparisonOperator.BETWEEN,
    ],
    bool: [ComparisonOperator.EQUALS],
}


def get_wildcard_filter(filter_elem, model: BaseModel):
    """
    Creates the wildcard filter for all string properties also nested one.
    The wildcard filter is a 'contains' case insensitive filter that is combined by OR operator with other properties.
    :param filter_elem:
    :param model:
    :return:
    """
    wildcard_filter = []
    for name, field in model.__fields__.items():
        source = field.field_info.extra.get("source")
        if source is not None:
            if "." in source:
                field_name = source.replace(".", "__")
            else:
                field_name = source
        else:
            field_name = name
        if issubclass(field.type_, BaseModel):
            q_obj = get_wildcard_filter(filter_elem=filter_elem, model=field.type_)
            wildcard_filter.append(q_obj)
        elif field.type_ is str and not name in ["possibleActions"]:
            q_obj = Q(**{f"{field_name}__icontains": filter_elem.v[0]})
            wildcard_filter.append(q_obj)
    return functools.reduce(lambda filter1, filter2: filter1 | filter2, wildcard_filter)


def get_embedded_field(fields: list, model: BaseModel):
    """
    Return the embedded field to filter by. For instance we can obtain 'flowchartGroup.name' filter clause
    from the client which means that we want to filter by the name property in the flowchartGroup nested model.
    :param fields:
    :param model:
    :return:
    """
    if len(fields) == 1:
        return model.__fields__.get(fields[0])
    return get_embedded_field(fields[1:], model=model.__fields__.get(fields[0]).type_)


def transform_filters_into_neomodel(filter_by: Union[dict, None], model: BaseModel):
    neomodel_filters = {}
    wildcard_filters = []
    filters = FilterDict(elements=filter_by)
    for prop, filter_elem in filters.elements.items():
        if prop == "*":
            wildcard_filters.append(
                get_wildcard_filter(filter_elem=filter_elem, model=model)
            )
        else:
            # if property is a nested property, for instance flowchartGroup.name we have to get underlying
            # 'name' property to filter by.
            if "." in prop:
                field = get_embedded_field(fields=prop.split("."), model=model)
            else:
                field = model.__fields__.get(prop)

            if field is not None:
                source = field.field_info.extra.get("source")
                if source is not None:
                    if "." in source:
                        field_name = source.replace(".", "__")
                    else:
                        field_name = source
                else:
                    field_name = prop

                # get the list of possible filters for a given field type
                possible_filters = data_type_filters.get(field.type_)

                # if possible filter list is None it means that data type of the filter field is not listed
                # in the data_type_filters configuration
                if possible_filters is None:
                    raise AttributeError(
                        f"Passed not supported data type {field.type_}"
                    )
                if filter_elem.op not in possible_filters:
                    raise AttributeError(
                        f"The following filtering type {filter_elem.op.name} is not supported "
                        f"for the following data type {field.type_}"
                    )
                if len(filter_elem.v) == 1:
                    neomodel_filter = comparison_operator_to_neomodel.get(
                        filter_elem.op
                    )
                    if neomodel_filter is None:
                        raise AttributeError(
                            f"The following operator {filter_elem.op} is not mapped "
                            f"to the neomodel operators"
                        )
                    filter_name = f"{field_name}{neomodel_filter}"
                    filter_value = filter_elem.v[0]
                    if isinstance(filter_value, str) and is_date(filter_value):
                        filter_value = f"datetime({filter_value})"
                    neomodel_filters[filter_name] = filter_value
                else:
                    if filter_elem.op == ComparisonOperator.BETWEEN:
                        filter_elem.v.sort()
                        filter_values = filter_elem.v
                        min_bound = f"{field_name}__gt"
                        max_bound = f"{field_name}__lt"
                        min_bound_value = filter_values[0]
                        max_bound_value = filter_values[1]
                        if isinstance(min_bound_value, str) and is_date(
                            min_bound_value
                        ):
                            min_bound_value = f"datetime({min_bound_value})"
                        neomodel_filters[min_bound] = min_bound_value
                        if isinstance(max_bound_value, str) and is_date(
                            max_bound_value
                        ):
                            max_bound_value = f"datetime({max_bound_value})"
                        neomodel_filters[max_bound] = max_bound_value
                    else:
                        raise AttributeError(
                            f"Not valid operator {filter_elem.op.value} for the following property {prop} of type"
                            f"{type(prop)}"
                        )

            else:
                raise AttributeError("Passed wrong filter field name")
    return neomodel_filters, wildcard_filters


def is_date(string):
    try:
        # changing into isoparse instead of parse as
        # parse was interpreting for instance '1.0' as date
        # and '1.0' is commonly used value in version filtering
        isoparse(string)
        return True
    except ValueError:
        return False


class GenericFilteringReturn:
    def __init__(self, items: Sequence[Any], total_count: int):
        self.items = items
        self.total_count = total_count


class FilterOperator(Enum):
    AND = "and"
    OR = "or"

    @staticmethod
    def from_str(label):
        if label in ("or", "OR"):
            return FilterOperator.OR
        if label in ("and", "AND"):
            return FilterOperator.AND
        raise exceptions.NotFoundException(
            "Filter operator only accepts values of 'and' and 'or'."
        )


class FilterDictElement(BaseModel):
    v: conlist(item_type=T) = Field(
        ...,
        title="search values",
        description="list of values to use as search values. Can be of any type.",
    )
    op: Optional[ComparisonOperator] = Field(
        ComparisonOperator.EQUALS,
        title="comparison operator to apply",
        description="comparison operator from enum, for operations like =, >=, or <",
    )


class FilterDict(BaseModel):
    elements: Dict[str, FilterDictElement] = Field(
        ...,
        title="filters description",
        description="""filters description, with key being the alias to filter
        against, and value is a description object with search values and comparison operator""",
    )

    @validator("elements", pre=True)
    # pylint:disable=no-self-argument
    def _none_as_empty_dict(cls, val):
        if val is None:
            return {}
        return val


class CypherQueryBuilder:
    """
    This class builds two queries : items and totalCount with filtering and pagination capabilities.
    Important note : To provide the filtering and sorting capabilities, this class
    relies on the use of Cypher aliases. Please read the 'Mandatory inputs' section carefully.

    Mandatory inputs :
        match_clause : Basically everything a Cypher query needs to do before a
        RETURN statement : MATCH a pattern, CALL a procedure/subquery, do a WITH processing...
            Note, though, filtering, sorting and pagination will be added
            automatically by the class methods.
        alias_clause : Cypher aliases definition clause ; Similar to what you would
        write in your RETURN statement, but without the RETURN keyword.
            This is processed to set variables on which to apply filtering and sorting.

    Optional inputs :
        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and
        boolean to define sort direction (true=ascending) as values
        page_number : int, number of the page to return. 1-based (will be converted
        to 0-based for Cypher by class methods)
        page_size : int, number of results per page
        filter_by : dict, keys are fieldNames for filter_variable and values are
        objects describing the filtering to execute
            * v = list of values to filter against
            * op = filter operator. Expected values : eq, co (contains), ge, gt, le, lt
            Example : { "name" : { "v": ["Jimbo"], "op": "co" }}
        return_model (class) / wildcard_properties_list (list of strings): when a
        wildcard filtering is requested, we need to extract the list of
            known properties on which to apply filter. This can be done automatically
            from the return model definition ; in some more complex cases
            (e.g. aggregated object with many nested objects), the list cannot be
            extracted directly from the model definition, and has to be provided to this method
        format_filter_sort_keys: Callable. In some cases, the returned model property
        keys differ from the property keys defined in the database.
            To cover these cases, a conversion function can be provided.

    Output properties :
        full_query : Complete cypher query with all clauses. See build_full_query
        method definition for more details.
        count_query : Cypher query with match, filter clauses, and results count. Se
        build_count_query method definition for more details.
        parameters : Parameters object to pass along with the cypher query

    Internal properties :
        filter_clause : str - Generated on class init ; adds filtering on aliases as
        defined in the filter_by dictionary
        sort_clause : str - Generated on class init ; adds sorting on aliases as
        defined in the sort_by dictionary
        pagination_clause : str - Generated on class init ; adds pagination
    """

    def __init__(
        self,
        match_clause: str,
        alias_clause: str,
        page_number: int = 1,
        page_size: int = 0,
        sort_by: Optional[dict] = None,
        filter_by: Optional[FilterDict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
        return_model: class_types = None,
        wildcard_properties_list: Optional[Sequence[str]] = None,
        format_filter_sort_keys: Callable = None,
    ):
        if wildcard_properties_list is None:
            wildcard_properties_list = []

        self.match_clause = match_clause
        self.alias_clause = alias_clause
        self.sort_by = sort_by if sort_by is not None else {}
        self.page_number = page_number
        self.page_size = page_size
        self.filter_by = filter_by
        self.filter_operator = filter_operator
        self.total_count = total_count
        self.return_model = return_model
        self.wildcard_properties_list = wildcard_properties_list
        self.format_filter_sort_keys = format_filter_sort_keys
        self.filter_clause = ""
        self.sort_clause = ""
        self.pagination_clause = ""
        self.parameters = {}

        # Auto-generate internal clauses
        if filter_by and len(self.filter_by.elements) > 0:
            self.build_filter_clause()
        if self.page_size > 0:
            self.build_pagination_clause()
        if self.sort_by:
            self.build_sort_clause()

        # Auto-generate final queries
        self.build_full_query()
        self.build_count_query()

    def build_filter_clause(self) -> None:
        _filter_clause = "WHERE "
        filter_predicates = []

        for key in self.filter_by.elements:
            _alias = key
            _values = self.filter_by.elements[key].v
            _operator = self.filter_by.elements[key].op
            _predicates = []
            _parsed_operator = "="

            if _alias == "*":
                # Parse operator to use in filter for wildcard
                _parsed_operator = " CONTAINS "
                # Only accept requests with default operator (set to equal by FilterDict class) or specified contains operator
                if (
                    ComparisonOperator(_operator) != ComparisonOperator.EQUALS
                    and ComparisonOperator(_operator) != ComparisonOperator.CONTAINS
                ):
                    raise exceptions.NotFoundException(
                        "Only the default 'contains' operator is supported for wildcard filtering."
                    )
            else:
                # Parse operator to use in filter for the current label
                if ComparisonOperator(_operator) == ComparisonOperator.CONTAINS:
                    _parsed_operator = " CONTAINS "
                elif ComparisonOperator(_operator) == ComparisonOperator.GREATER_THAN:
                    _parsed_operator = ">"
                elif (
                    ComparisonOperator(_operator)
                    == ComparisonOperator.GREATER_THAN_OR_EQUAL_TO
                ):
                    _parsed_operator = ">="
                elif ComparisonOperator(_operator) == ComparisonOperator.LESS_THAN:
                    _parsed_operator = "<"
                elif (
                    ComparisonOperator(_operator)
                    == ComparisonOperator.LESS_THAN_OR_EQUAL_TO
                ):
                    _parsed_operator = "<="

            # Parse filter clauses for the current label
            # 'Between' operator works differently from the others
            if ComparisonOperator(_operator) == ComparisonOperator.BETWEEN:
                if len(_values) == 2:
                    if _alias != "*":
                        # If necessary, replace key using return-model-to-cypher fieldname mapping
                        if self.format_filter_sort_keys:
                            _alias = self.format_filter_sort_keys(_alias)
                        _values.sort()
                        _query_param_prefix = f"{self.escape_alias(_alias)}"
                        _predicate = f"${_query_param_prefix}_0<={_alias}<=${_query_param_prefix}_1"
                        # If the provided value can be parsed as a date, also add a predicate with a datetime casting on the Neo4j side
                        if is_date(_values[0]) and is_date(_values[1]):
                            _date_predicate = f"datetime(${_query_param_prefix}_0)<={_alias}<=datetime(${_query_param_prefix}_1)"
                            _predicate += f" OR {_date_predicate}"
                        filter_predicates.append(_predicate)
                        self.parameters[f"{_query_param_prefix}_0"] = _values[0]
                        self.parameters[f"{_query_param_prefix}_1"] = _values[1]
                    else:
                        exceptions.NotFoundException(
                            "Between operator not supported with wildcard filtering"
                        )
                else:
                    exceptions.NotFoundException(
                        "For between operator to work, exactly 2 values must be provided"
                    )
            else:
                # If necessary, replace key using return-model-to-cypher fieldname mapping
                if self.format_filter_sort_keys and not _alias == "*":
                    _alias = self.format_filter_sort_keys(_alias)
                # An empty _values list means that the returned item's property value should be null
                if len(_values) == 0:
                    if _alias == "*":
                        return exceptions.InternalErrorException(
                            "Wildcard filtering not supported with null values"
                        )
                    _predicates.append(f"{_alias} IS NULL")
                else:
                    for index, el in enumerate(_values):
                        # If filter is a wildcard
                        if _alias == "*":
                            # Wildcard filtering only accepts a search value of type string
                            if isinstance(el, str):
                                # If a list of wildcard properties is provided, use it
                                if len(self.wildcard_properties_list) > 0:
                                    for db_property in self.wildcard_properties_list:
                                        _predicates.append(
                                            f"toLower({db_property}){_parsed_operator}$wildcard_{index}"
                                        )
                                # If not, then extract list of properties from return model
                                elif self.return_model:
                                    for (
                                        attribute,
                                        attrDesc,
                                    ) in self.return_model.__fields__.items():
                                        # Wildcard filtering only searches in properties of type string
                                        if attrDesc.type_ is str and not attribute in [
                                            "possibleActions"
                                        ]:
                                            # name=$name_0 with name_0 defined in parameter objects
                                            if self.format_filter_sort_keys:
                                                attribute = (
                                                    self.format_filter_sort_keys(
                                                        attribute
                                                    )
                                                )
                                            _predicates.append(
                                                f"toLower({attribute}){_parsed_operator}$wildcard_{index}"
                                            )
                                        # Wildcard filtering for SimpleTermModel
                                        elif attrDesc.type_ is SimpleTermModel:
                                            # name=$name_0 with name_0 defined in parameter objects
                                            if self.format_filter_sort_keys:
                                                attribute = (
                                                    self.format_filter_sort_keys(
                                                        attribute
                                                    )
                                                )
                                            if attrDesc.sub_fields is None:
                                                # if field is just SimpleTermModel compare wildcard filter
                                                # with name property of SimpleTermModel
                                                _predicates.append(
                                                    f"toLower({attribute}.name){_parsed_operator}$wildcard_{index}"
                                                )
                                            else:
                                                # if field is an array of SimpleTermModels
                                                _predicates.append(
                                                    f"$wildcard_{index} IN [attr in {attribute} | toLower(attr.name)]"
                                                )
                                # If none are provided, raise an exception
                                else:
                                    raise exceptions.InternalErrorException(
                                        "Wildcard filtering not properly covered for this object"
                                    )
                                self.parameters[f"wildcard_{index}"] = el.lower()
                            else:
                                raise exceptions.NotFoundException(
                                    "Wildcard filtering only supports a search value of type string"
                                )
                        else:
                            # name=$name_0 with name_0 defined in parameter objects
                            # . for nested properties will be replaced by _
                            _query_param_name = f"{self.escape_alias(_alias)}_{index}"
                            if (
                                self.return_model
                                and issubclass(self.return_model, BaseModel)
                                and self.return_model.__fields__.get(_alias)
                                and self.return_model.__fields__.get(_alias).type_
                                is SimpleTermModel
                            ):
                                attrDesc = self.return_model.__fields__.get(_alias)
                                # name=$name_0 with name_0 defined in parameter objects
                                if attrDesc.sub_fields is None:
                                    # if field is just SimpleTermModel compare wildcard filter
                                    # with name property of SimpleTermModel
                                    _predicates.append(
                                        f"toLower({_alias}.name){_parsed_operator}${_query_param_name}"
                                    )
                                else:
                                    # if field is an array of SimpleTermModels
                                    _predicates.append(
                                        f"any(attr in {_alias} WHERE toLower(attr.name) CONTAINS ${_query_param_name})"
                                    )
                                self.parameters[f"{_query_param_name}"] = el.lower()
                            elif (
                                isinstance(el, str)
                                and ComparisonOperator(_operator)
                                == ComparisonOperator.CONTAINS
                            ):
                                _predicates.append(
                                    f"toLower(toString({_alias})){_parsed_operator}${_query_param_name}"
                                )
                                self.parameters[f"{_query_param_name}"] = el.lower()
                            else:
                                _predicates.append(
                                    f"{_alias}{_parsed_operator}${_query_param_name}"
                                )
                                # If the provided value is a string that can be parsed as a date,
                                # also add a predicate with a datetime casting on the Neo4j side
                                # It is necessary to check if it is a string because the value could also be a boolean here
                                if isinstance(el, str) and is_date(el):
                                    _predicates.append(
                                        f"{_alias}{_parsed_operator}datetime(${_query_param_name})"
                                    )
                                self.parameters[_query_param_name] = el

                # If multiple values, will create a clause with OR, between ()
                _predicate = " OR ".join(_predicates)
                if len(_values) > 1 or _alias == "*":
                    _predicate = f"({_predicate})"

                # Add to list of predicates
                filter_predicates.append(_predicate)

        # Set clause
        self.filter_clause = (
            _filter_clause
            + f" {self.filter_operator.value.upper()} ".join(list(filter_predicates))
        )

        return None

    def build_pagination_clause(self) -> None:
        # Set clause
        self.pagination_clause = "SKIP $page_number * $page_size LIMIT $page_size"

        # Add corresponding parameters
        self.parameters["page_number"] = self.page_number - 1
        self.parameters["page_size"] = self.page_size

    def build_sort_clause(self) -> None:
        _sort_clause = "ORDER BY "
        # Add list of order by statements parsed from dict
        # If necessary, replace key using return-model-to-cypher fieldname mapping
        sort_by_statements = map(
            lambda key: f"{self.format_filter_sort_keys(key) if self.format_filter_sort_keys else key} "
            + ("ASC" if self.sort_by[key] else "DESC"),
            self.sort_by.keys(),
        )

        # Set clause
        self.sort_clause = _sort_clause + ",".join(list(sort_by_statements))

    def build_full_query(self) -> None:
        """
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN * to return results as is
            > ORDER BY to sort results using aliases
            > SKIP * LIMIT * to paginate results
        """
        _with_alias_clause = f"WITH {self.alias_clause}"
        _return_clause = "RETURN *"

        # Set clause
        self.full_query = " ".join(
            [
                self.match_clause,
                _with_alias_clause,
                self.filter_clause,
                _return_clause,
                self.sort_clause,
                self.pagination_clause,
            ]
        )

    def build_count_query(self) -> None:
        """
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN results count
        """
        _with_alias_clause = f"WITH {self.alias_clause}"
        _return_count_clause = "RETURN count(*) AS totalCount"

        # Set clause
        self.count_query = " ".join(
            [
                self.match_clause,
                _with_alias_clause,
                self.filter_clause,
                _return_count_clause,
            ]
        )

    def build_header_query(self, header_alias: str, result_count: int) -> str:
        """
        Mandatory inputs :
            * header_alias - Alias of the header for which to get possible values, as defined in the alias clause
            * result_count - Number of results to return
        The generated query will have the following pattern :
            MATCH caller-provided (and WITH, CALL, ... any custom pattern matching necessary)
            > WITH alias_clause caller-provided
            > WHERE filter_clause using aliases
            > RETURN list of possible headers for given alias, ordered, with a limit
        """
        _with_alias_clause = f"WITH {self.alias_clause}"
        # Escape header_alias to plan for nested properties as a . character would make Cypher fail
        _escaped_header_alias = self.escape_alias(header_alias)
        _return_header_clause = f"""WITH DISTINCT {header_alias} AS
        {_escaped_header_alias} ORDER BY {_escaped_header_alias} LIMIT {result_count} RETURN collect(DISTINCT {_escaped_header_alias}) AS values"""

        return " ".join(
            [
                self.match_clause,
                _with_alias_clause,
                self.filter_clause,
                _return_header_clause,
            ]
        )

    def escape_alias(self, alias: str) -> str:
        """
        Escapes alias to prevent Cypher failures.
            * Replaces . for nested properties by _
        """
        return re.sub(nestedRegex, "_", alias)


def sb_clear_cache(caches: List[str] = None):
    """
    Decorator that will clear the specified caches after the wrapped function execution.
    """
    if caches is None:
        caches = []

    def decorator(function):
        @functools.wraps(function)
        def wrapper(self, *args, **kwargs):
            try:
                result = function(self, *args, **kwargs)
                return result
            finally:
                for cache_name in caches:
                    cache = getattr(self, cache_name, None)
                    if cache:
                        log.info(
                            "Clear cache '%s.%s' of size: %s",
                            self.__class__.__name__,
                            cache_name,
                            cache.currsize,
                        )
                        cache.clear()

        return wrapper

    return decorator
