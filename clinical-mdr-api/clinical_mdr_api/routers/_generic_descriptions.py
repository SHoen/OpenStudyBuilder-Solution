SORT_BY = (
    "Optionally, a dictionary of fieldNames and isAscending boolean.\n\n"
    "Default: {} (no sorting)\n\n"
    "Functionality: sorts the results. First by first key with direction indicated by value, then second key, etc...\n\n"
    'Example: {"topicCode": true, "name": false}'
)

PAGE_NUMBER = (
    "Optionally, the page number of the results to display.\n\n"
    "Functionality : provided together with pageSize, selects a page to retrieve for paginated results."
    "Errors: pageSize not provided, pageNumber must be equal or greater than 1."
)

PAGE_SIZE = (
    "Optionally, the number of results to display per page.\n\n"
    "Default: 0 (all data)\n\n"
    "Functionality: provided together with pageNumber, selects the number of results per page.\n\n"
    "Errors: pageNumber not provided."
)

FILTERS = (
    "Optionally, a dictionary of fieldNames and searchStrings with a choice of operators.\n\n"
    "Default: {} (no filtering)\n\n"
    "Functionality: filters the return values based on the provided search strings and operators.\n\n"
    """The expected format is the following :
    {"labelName":{"v":[list of values to filter against], "op":"comparison operator"}, "otherLabelName":{...}}\n\n"""
    "If a list of values is provided for a given labelName, it will execute an OR on these values.\n\n"
    """Supported comparison operators are the following : eq (default, =), ne (not equals), co (string contains), ge (greater or equal to),
    gt (greater than), le (less or equal to), lt (less than), bw (between - exactly two values are required).\n\n"""
    'Note that this is not just for string filtering. For example, this works as filter : {"isGlobalStandard": {"v": [false]}}\n\n'
    """Wildcard filtering is also supported. To do this, provide * as labelName, with
    the same structure for values and operator : {"*":{"v":["searchString"]}}\n\n"""
    "Wildcard only supports searching strings, on labels of type string ; with a contains operator (set as default in this case).\n\n"
    'Finally, you can filter on items that have an empty value for a field. To achieve this, just set the "v" list to the empty array [].\n\n'
)

OPERATOR = (
    "Optionally, if the filter must be done on several fields, the and/or operator to use.\n\n"
    "Default: and (all field names have to match their filter).\n\n"
    "Functionality: and/or apply to all fields. 'and' will require filters to match, 'or' will require any filters to match.\n\n"
)

FILTERS_EXAMPLE = """{"name":{ "v": ["Jimbo", "Jumbo"], "op": "co" },
"startDate": {"v": ["2021-04-01T12:00:00+00.000"], "op": "ge"}, "*":{ "v": ["wildcardSearch"], "op": "co" }}"""

TOTAL_COUNT = (
    "Optionally, a boolean.\n\n"
    "Functionality: retrieve a total count of the number of returned elements in the context of paginated results.\n\n"
)

HEADER_FIELD_NAME = (
    "The field name for which to lookup possible values in the database.\n\n"
    "Functionality: searches for possible values (aka 'headers') of this field in the database."
    "Errors: invalid field name specified"
)

HEADER_SEARCH_STRING = """Optionally, a (part of the) text for a given field.
The query result will be values of the field that contain the provided search string."""

HEADER_RESULT_COUNT = "Optionally, the number of results to return. Default = 10."
