"""
Utility module to store the common parts of terms get all and specific term get all requests.
"""
from typing import Optional, Sequence, Tuple

from pydantic.main import BaseModel

from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
    CTCodelistAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.models.ct_codelist_attributes import CTCodelistAttributes
from clinical_mdr_api.models.ct_codelist_name import CTCodelistName
from clinical_mdr_api.models.ct_term_attributes import CTTermAttributes
from clinical_mdr_api.models.ct_term_name import CTTermName
from clinical_mdr_api.models.utils import camel_to_snake

# Properties always on root level, even in aggregated mode (names + attributes)
term_root_level_properties = ["termUid", "catalogueName", "codelistUid", "libraryName"]
codelist_root_level_properties = ["catalogueName", "codelistUid", "libraryName"]


def create_term_filter_statement(
    codelist_uid: Optional[str] = None,
    codelist_name: Optional[str] = None,
    library: Optional[str] = None,
    package: Optional[str] = None,
) -> Tuple[str, dict]:
    """
    Method creates filter string from demanded filter option.

    :param codelist_uid:
    :param codelist_name:
    :param library:
    :param package:
    :return str:
    """
    filter_parameters = []
    filter_query_parameters = {}
    if codelist_uid:
        filter_by_codelist_uid = """
                codelist_root.uid=$codelist_uid"""
        filter_parameters.append(filter_by_codelist_uid)
        filter_query_parameters["codelist_uid"] = codelist_uid
    if codelist_name:
        filter_by_codelist_name = """
                head([(codelist_root)-[:HAS_NAME_ROOT]->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST]->
                (codelist_ver_value:CTCodelistNameValue) | codelist_ver_value.name])=$codelist_name  
                """
        filter_parameters.append(filter_by_codelist_name)
        filter_query_parameters["codelist_name"] = codelist_name
    if library:
        filter_by_library_name = """
                head([(library:Library)-[:CONTAINS_TERM]->(term_root) | library.name])=$library_name"""
        filter_parameters.append(filter_by_library_name)
        filter_query_parameters["library_name"] = library
    if package:
        filter_by_package = """
                package.name=$package_name"""
        filter_parameters.append(filter_by_package)
        filter_query_parameters["package_name"] = package
    filter_statements = " AND ".join(filter_parameters)
    filter_statements = (
        "WHERE " + filter_statements if len(filter_statements) > 0 else ""
    )
    return filter_statements, filter_query_parameters


def create_term_name_aggregate_instances_from_cypher_result(
    term_dict: dict, is_aggregated_query: bool = False
) -> CTTermNameAR:
    """
    Method CTTermNameAR instance from the cypher query output.

    :param term_dict:
    :param is_aggregated_query:
    :return CTTermNameAR:
    """
    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_name"

    rel_data = term_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    library_name = term_dict.get("library_name")
    term_name_ar = CTTermNameAR.from_repository_values(
        uid=term_dict.get("term_uid"),
        ct_term_name_vo=CTTermNameVO.from_repository_values(
            codelist_uid=term_dict.get("codelist_uid"),
            name=term_dict.get(f"value_node{specific_suffix}").get("name"),
            name_sentence_case=term_dict.get(f"value_node{specific_suffix}").get(
                "name_sentence_case"
            ),
            order=term_dict.get("order"),
            catalogue_name=term_dict.get("catalogue_name"),
        ),
        library=LibraryVO.from_input_values_2(
            library_name=library_name,
            is_library_editable_callback=(
                lambda _: term_dict.get("is_library_editable")
            ),
        )
        if library_name
        else None,
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author=rel_data.get("user_initials"),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return term_name_ar


def create_term_attributes_aggregate_instances_from_cypher_result(
    term_dict: dict, is_aggregated_query: bool = False
) -> CTTermAttributesAR:
    """
    Method CTTermAttributesAR instance from the cypher query output.

    :param term_dict:
    :param is_aggregated_query:
    :return CTTermAttributesAR:
    """
    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_attributes"

    rel_data = term_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    library_name = term_dict.get("library_name")
    term_attributes_ar = CTTermAttributesAR.from_repository_values(
        uid=term_dict.get("term_uid"),
        ct_term_attributes_vo=CTTermAttributesVO.from_repository_values(
            codelist_uid=term_dict.get("codelist_uid"),
            concept_id=term_dict.get(f"value_node{specific_suffix}").get("concept_id"),
            code_submission_value=term_dict.get(f"value_node{specific_suffix}").get(
                "code_submission_value"
            ),
            name_submission_value=term_dict.get(f"value_node{specific_suffix}").get(
                "name_submission_value"
            ),
            preferred_term=term_dict.get(f"value_node{specific_suffix}").get(
                "preferred_term"
            ),
            definition=term_dict.get(f"value_node{specific_suffix}").get("definition"),
            catalogue_name=term_dict.get("catalogue_name"),
        ),
        library=LibraryVO.from_input_values_2(
            library_name=library_name,
            is_library_editable_callback=(
                lambda _: term_dict.get("is_library_editable")
            ),
        )
        if library_name
        else None,
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author=rel_data.get("user_initials"),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return term_attributes_ar


def format_term_filter_sort_keys(key: str, prefix: str = None) -> str:
    """
    Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

    :param key: Fieldname to map
    :param prefix: In the case of nested properties, name of nested object
    :return str:
    """
    # Always root level properties
    if key in term_root_level_properties:
        return camel_to_snake(key)
    # Possibly nested properties
    # name property
    if key in ["sponsorPreferredName", "nciPreferredName"]:
        return f"value_node_{prefix}.name" if prefix else "value_node.name"
    if key == "sponsorPreferredNameSentenceCase":
        return (
            f"value_node_{prefix}.name_sentence_case"
            if prefix
            else "value_node.name_sentence_case"
        )
    if key in [
        "codeSubmissionValue",
        "nameSubmissionValue",
        "definition",
        "conceptId",
    ]:
        return (
            f"value_node_{prefix}.{camel_to_snake(key)}"
            if prefix
            else f"value_node.{camel_to_snake(key)}"
        )
    # Property coming from relationship
    if key in [
        "startDate",
        "endDate",
        "status",
        "version",
        "changeDescription",
        "userInitials",
    ]:
        return (
            f"rel_data_{prefix}.{camel_to_snake(key)}"
            if prefix
            else f"rel_data.{camel_to_snake(key)}"
        )
    # Nested field names -> recursive call with prefix
    if key.startswith("name.") or key.startswith("attributes."):
        prefix = key.split(".")[0]
        suffix = key.split(".")[1]
        if suffix == "order":
            return "order"
        return format_term_filter_sort_keys(suffix, prefix)
    # All other cases are simple camel_to_snake conversion
    return camel_to_snake(key)


def list_term_wildcard_properties(
    is_aggregated: bool = True, target_model: BaseModel = None
) -> Sequence[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the database and/or Cypher query
    :param is_aggregated: bool.
    :param target_model: Used to define a specific target model, ie name or attributes.
        is_aggregated & undefined target_model = Root aggregated object
    :return: List of strings, representing property names
    """
    property_list = []
    # Root level, aggregated object
    if is_aggregated and not target_model:
        property_list += list_term_wildcard_properties(True, CTTermName)
        property_list += list_term_wildcard_properties(True, CTTermAttributes)
    else:
        if is_aggregated:
            prefix = "name" if target_model == CTTermName else "attributes"
            for attribute, attrDesc in target_model.__fields__.items():
                # Wildcard filtering only searches in properties of type string
                if (
                    attrDesc.type_ is str
                    and not attribute in ["possibleActions"]
                    and not attrDesc.field_info.extra.get("removeFromWildcard", False)
                ):
                    property_list.append(
                        format_term_filter_sort_keys(attribute, prefix)
                    )
        else:
            for attribute, attrDesc in target_model.__fields__.items():
                # Wildcard filtering only searches in properties of type string
                if (
                    attrDesc.type_ is str
                    and not attribute in ["possibleActions"]
                    and not attrDesc.field_info.extra.get("removeFromWildcard", False)
                ):
                    property_list.append(format_term_filter_sort_keys(attribute))
    return list(set(property_list))


def create_codelist_filter_statement(
    catalogue_name: Optional[str] = None,
    library: Optional[str] = None,
    package: Optional[str] = None,
) -> Tuple[str, dict]:
    """
    Method creates filter string from demanded filter option.

    :param catalogue_name:
    :param library:
    :param package:
    :return str:
    """
    filter_parameters = []
    filter_query_parameters = {}
    if catalogue_name:
        filter_by_catalogue = """
        $catalogue_name IN [(catalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue.name]"""
        filter_parameters.append(filter_by_catalogue)
        filter_query_parameters["catalogue_name"] = catalogue_name
    if package:
        filter_by_package_name = "package.name=$package_name"
        filter_parameters.append(filter_by_package_name)
        filter_query_parameters["package_name"] = package
    if library:
        filter_by_library_name = """
        head([(library:Library)-[:CONTAINS_CODELIST]->(codelist_root) | library.name])=$library_name"""
        filter_parameters.append(filter_by_library_name)
        filter_query_parameters["library_name"] = library
    filter_statements = " AND ".join(filter_parameters)
    filter_statements = (
        "WHERE " + filter_statements if len(filter_statements) > 0 else ""
    )
    return filter_statements, filter_query_parameters


def create_codelist_name_aggregate_instances_from_cypher_result(
    codelist_dict: dict, is_aggregated_query: bool = False
) -> CTCodelistNameAR:
    """
    Method CTCodelistNameAR instance from the cypher query output.

    :param codelist_dict:
    :param is_aggregated_query:
    :return CTCodelistNameAR:
    """

    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_name"

    rel_data = codelist_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    codelist_name_ar = CTCodelistNameAR.from_repository_values(
        uid=codelist_dict.get("codelist_uid"),
        ct_codelist_name_vo=CTCodelistNameVO.from_repository_values(
            name=codelist_dict.get(f"value_node{specific_suffix}").get("name"),
            catalogue_name=codelist_dict.get("catalogue_name"),
            is_template_parameter="TemplateParameter"
            in codelist_dict.get(f"value_node{specific_suffix}").labels,
        ),
        library=LibraryVO.from_input_values_2(
            library_name=codelist_dict.get("library_name"),
            is_library_editable_callback=(
                lambda _: codelist_dict.get("is_library_editable")
            ),
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author=rel_data.get("user_initials"),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return codelist_name_ar


def create_codelist_attributes_aggregate_instances_from_cypher_result(
    codelist_dict: dict, is_aggregated_query: bool = False
) -> CTCodelistAttributesAR:
    """
    Method CTCodelistAttributesAR instance from the cypher query output.

    :param codelist_dict:
    :param is_aggregated_query:
    :return CTCodelistAttributesAR:
    """

    specific_suffix = ""
    if is_aggregated_query:
        specific_suffix = "_attributes"

    rel_data = codelist_dict[f"rel_data{specific_suffix}"]
    major, minor = rel_data.get("version").split(".")

    codelist_attributes_ar = CTCodelistAttributesAR.from_repository_values(
        uid=codelist_dict.get("codelist_uid"),
        ct_codelist_attributes_vo=CTCodelistAttributesVO.from_repository_values(
            name=codelist_dict.get(f"value_node{specific_suffix}").get("name"),
            parent_codelist_uid=codelist_dict.get("parent_codelist_uid"),
            child_codelist_uids=codelist_dict.get("child_codelist_uids"),
            catalogue_name=codelist_dict.get("catalogue_name"),
            submission_value=codelist_dict.get(f"value_node{specific_suffix}").get(
                "submission_value"
            ),
            preferred_term=codelist_dict.get(f"value_node{specific_suffix}").get(
                "preferred_term"
            ),
            definition=codelist_dict.get(f"value_node{specific_suffix}").get(
                "definition"
            ),
            extensible=codelist_dict.get(f"value_node{specific_suffix}").get(
                "extensible"
            ),
        ),
        library=LibraryVO.from_input_values_2(
            library_name=codelist_dict.get("library_name"),
            is_library_editable_callback=(
                lambda _: codelist_dict.get("is_library_editable")
            ),
        ),
        item_metadata=LibraryItemMetadataVO.from_repository_values(
            change_description=rel_data.get("change_description"),
            status=LibraryItemStatus(rel_data.get("status")),
            author=rel_data.get("user_initials"),
            start_date=convert_to_datetime(value=rel_data.get("start_date")),
            end_date=None,
            major_version=int(major),
            minor_version=int(minor),
        ),
    )

    return codelist_attributes_ar


def format_codelist_filter_sort_keys(key: str, prefix: str = None) -> str:
    """
    Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

    :param key: Fieldname to map
    :param prefix: In the case of nested properties, name of nested object
    :return str:
    """
    # Always root level properties
    if key in codelist_root_level_properties:
        return camel_to_snake(key)
    # Possibly nested properties
    # name property
    if key == "nciPreferredName":
        return (
            f"value_node_{prefix}.preferred_term"
            if prefix
            else "value_node.preferred_term"
        )
    if key == "templateParameter":
        return "is_template_parameter"
    if key in ["name", "definition", "submissionValue", "extensible"]:
        return (
            f"value_node_{prefix}.{camel_to_snake(key)}"
            if prefix
            else f"value_node.{camel_to_snake(key)}"
        )
    # Property coming from relationship
    if key in [
        "startDate",
        "endDate",
        "status",
        "version",
        "changeDescription",
        "userInitials",
    ]:
        return (
            f"rel_data_{prefix}.{camel_to_snake(key)}"
            if prefix
            else f"rel_data.{camel_to_snake(key)}"
        )
    # Nested field names -> recursive call with prefix
    if key.startswith("name.") or key.startswith("attributes."):
        prefix = key.split(".")[0]
        suffix = key.split(".")[1]
        return format_codelist_filter_sort_keys(suffix, prefix)
    # All other cases are simple camel_to_snake conversion
    return camel_to_snake(key)


def list_codelist_wildcard_properties(
    is_aggregated: bool = True, target_model: BaseModel = None
) -> Sequence[str]:
    """
    Returns a list of properties on which to apply wildcard filtering, formatted as defined in the database and/or Cypher query
    :param is_aggregated: bool.
    :param target_model: Used to define a specific target model, ie name or attributes.
        is_aggregated & undefined target_model = Root aggregated object
    :return: List of strings, representing property names
    """
    property_list = []
    # Root level, aggregated object
    if is_aggregated and not target_model:
        property_list += list_codelist_wildcard_properties(True, CTCodelistName)
        property_list += list_codelist_wildcard_properties(True, CTCodelistAttributes)
    else:
        if is_aggregated:
            prefix = "name" if target_model == CTCodelistName else "attributes"
            for attribute, attrDesc in target_model.__fields__.items():
                # Wildcard filtering only searches in properties of type string
                if (
                    attrDesc.type_ is str
                    and not attribute in ["possibleActions"]
                    # remove fields that shouldn't be included in wildcard filter
                    and not attrDesc.field_info.extra.get("removeFromWildcard", False)
                ):
                    property_list.append(
                        format_codelist_filter_sort_keys(attribute, prefix)
                    )
        else:
            for attribute, attrDesc in target_model.__fields__.items():
                # Wildcard filtering only searches in properties of type string
                if (
                    attrDesc.type_ is str
                    and not attribute in ["possibleActions"]
                    # remove fields that shouldn't be included in wildcard filter
                    and not attrDesc.field_info.extra.get("removeFromWildcard", False)
                ):
                    property_list.append(format_codelist_filter_sort_keys(attribute))
    return list(set(property_list))
