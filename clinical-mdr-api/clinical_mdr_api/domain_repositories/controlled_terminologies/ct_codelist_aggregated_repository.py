from typing import Sequence

from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_codelist_attributes_aggregate_instances_from_cypher_result,
    create_codelist_filter_statement,
    create_codelist_name_aggregate_instances_from_cypher_result,
    format_codelist_filter_sort_keys,
    list_codelist_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models.controlled_terminologies.ct_stats import CodelistCount
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class CTCodelistAggregatedRepository:
    generic_alias_clause = """
        DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value
        ORDER BY codelist_root.uid
        WITH DISTINCT codelist_root, codelist_name_root, codelist_name_value, codelist_attributes_root, codelist_attributes_value, 
        head([(cat:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | cat]) AS catalogue,
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library
        CALL {
                WITH codelist_attributes_root, codelist_attributes_value
                MATCH (codelist_attributes_root)-[hv:HAS_VERSION]-(codelist_attributes_value)
                WITH hv 
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_attributes
        }
        CALL {
                WITH codelist_name_root, codelist_name_value
                MATCH (codelist_name_root)-[hv:HAS_VERSION]-(codelist_name_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS rel_data_name
        }
        WITH 
            codelist_root.uid AS codelist_uid,
            head([(codelist_root)-[:HAS_PARENT_CODELIST]->(ccr:CTCodelistRoot) | ccr.uid]) AS parent_codelist_uid,
            [(codelist_root)<-[:HAS_PARENT_CODELIST]-(ccr:CTCodelistRoot) | ccr.uid] AS child_codelist_uids,
            catalogue.name AS catalogue_name,
            codelist_attributes_value AS value_node_attributes,
            codelist_name_value AS value_node_name,
            CASE WHEN codelist_name_value:TemplateParameter THEN true ELSE false END AS is_template_parameter,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            {
                start_date: rel_data_attributes.start_date,
                end_date: NULL,
                status: rel_data_attributes.status,
                version: rel_data_attributes.version,
                change_description: rel_data_attributes.change_description,
                user_initials: rel_data_attributes.user_initials
            } AS rel_data_attributes,
            {
                start_date: rel_data_name.start_date,
                end_date: NULL,
                status: rel_data_name.status,
                version: rel_data_name.version,
                change_description: rel_data_name.change_description,
                user_initials: rel_data_name.user_initials
            } AS rel_data_name
    """

    def _create_codelist_aggregate_instances_from_cypher_result(
        self, codelist_dict: dict
    ) -> tuple[CTCodelistNameAR, CTCodelistAttributesAR]:
        """
        Method creates a tuple of CTCodelistNameAR and CTCodelistAttributesAR objects for one CTCodelistRoot node.
        The term_dict is a find_all_aggregated_result method result for one CTCodelistRoot node.

        :param codelist_dict:
        :return (CTCodelistNameAR, CTCodelistAttributesAR):
        """
        codelist_name_ar = create_codelist_name_aggregate_instances_from_cypher_result(
            codelist_dict=codelist_dict, is_aggregated_query=True
        )
        codelist_attributes_ar = (
            create_codelist_attributes_aggregate_instances_from_cypher_result(
                codelist_dict=codelist_dict, is_aggregated_query=True
            )
        )
        return codelist_name_ar, codelist_attributes_ar

    def find_all_aggregated_result(
        self,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        term_filter: dict | None = None,
    ) -> GenericFilteringReturn[tuple[CTCodelistNameAR, CTCodelistAttributesAR]]:
        """
        Method runs a cypher query to fetch all data related to the CTCodelistName* and CTCodelistttributes*.
        It allows to filter the query output by catalogue_name, library and package.
        It returns the array of Tuples where each tuple is consists of CTCodelistNameAR and CTCodelistAttributesAR objects.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param catalogue_name:
        :param library:
        :param package:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[tuple[CTCodelistNameAR, CTCodelistAttributesAR]]:
        """
        # Build match_clause
        # Build specific filtering for catalogue, package and library
        # This is separate from generic filtering as the list of filters is predefined
        # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
        filter_statements, filter_query_parameters = create_codelist_filter_statement(
            catalogue_name=catalogue_name, library=library, package=package
        )
        match_clause = self._generate_generic_match_clause(
            package=package, term_filter=term_filter
        )
        match_clause += filter_statements

        # Build alias_clause
        alias_clause = self.generic_alias_clause

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            wildcard_properties_list=list_codelist_wildcard_properties(),
            format_filter_sort_keys=format_codelist_filter_sort_keys,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        codelists_ars = []
        for codelist in result_array:
            codelist_dictionary = {}
            for codelist_property, attribute_name in zip(codelist, attributes_names):
                codelist_dictionary[attribute_name] = codelist_property
            codelists_ars.append(
                self._create_codelist_aggregate_instances_from_cypher_result(
                    codelist_dictionary
                )
            )

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn.create(items=codelists_ars, total=total)

    def get_distinct_headers(
        self,
        field_name: str,
        catalogue_name: str | None = None,
        library: str | None = None,
        package: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ) -> Sequence:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of result_count.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param catalogue_name:
        :param library:
        :param package:
        :param search_string:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param result_count: Max number of values to return. Default 10
        :return Sequence:
        """
        # Build match_clause
        # Build specific filtering for catalogue, package and library
        # This is separate from generic filtering as the list of filters is predefined
        # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
        filter_statements, filter_query_parameters = create_codelist_filter_statement(
            catalogue_name=catalogue_name, library=library, package=package
        )
        match_clause = self._generate_generic_match_clause(package=package)
        match_clause += filter_statements

        # Build alias_clause
        alias_clause = self.generic_alias_clause

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        if search_string != "":
            if filter_by is None:
                filter_by = {}
            filter_by[field_name] = {
                "v": [search_string],
                "op": ComparisonOperator.CONTAINS,
            }

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            wildcard_properties_list=list_codelist_wildcard_properties(),
            format_filter_sort_keys=format_codelist_filter_sort_keys,
        )

        query.full_query = query.build_header_query(
            header_alias=format_codelist_filter_sort_keys(field_name),
            result_count=result_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def _generate_generic_match_clause(
        self,
        package: str | None = None,
        term_filter: dict | None = None,
    ):
        match_clause = "MATCH(codelist_root:CTCodelistRoot)"

        if term_filter:
            if "term_uids" not in term_filter:
                raise ValidationException(
                    "term_uids must be provided for term filtering."
                )

            operation_function = "all"
            if "operator" in term_filter and term_filter["operator"] != "and":
                operation_function = "any"

            match_clause += f"""MATCH (codelist_root)-[:HAS_TERM]->(ct_term:CTTermRoot)
            WHERE ct_term.uid IN {term_filter["term_uids"]}
            WITH codelist_root, collect(ct_term.uid) as ct_term_uids
            WHERE {operation_function}(term_uid IN {term_filter["term_uids"]} WHERE term_uid IN ct_term_uids)
            """

        if package:
            match_clause += """
            MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
            (codelist_attributes_value:CTCodelistAttributesValue)<-[]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
            (codelist_root)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[:LATEST]->(codelist_name_value:CTCodelistNameValue)
            """
        else:
            match_clause += """
            MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(codelist_root)
            -[:HAS_ATTRIBUTES_ROOT]->(codelist_attributes_root:CTCodelistAttributesRoot)-[:LATEST]->(codelist_attributes_value:CTCodelistAttributesValue)
            """

        return match_clause

    def count_all(self) -> Sequence[CodelistCount]:
        """
        Returns the count of CT Codelists in the database, grouped by Library

        :return: Sequence[CodelistCount] - count of CT Codelists
        """
        query = """
            MATCH (n:CTCodelistRoot)<-[:CONTAINS_CODELIST]-(l:Library)
            RETURN l.name as library_name, count(n) as count
            """

        result, _ = db.cypher_query(query)
        return [CodelistCount(library_name=item[0], count=item[1]) for item in result]

    def get_change_percentage(self) -> float:
        """
        Returns the percentage of CT Codelists with more than one version

        :return: float - percentage
        """
        query = """
            MATCH (r:CTCodelistNameRoot)-->(v:CTCodelistNameValue)
            RETURN CASE count(r)
                WHEN 0 THEN 0
                ELSE (count(v)-count(r))/count(r)
                END AS percentage
            """

        result, _ = db.cypher_query(query)
        return result[0][0] if len(result) > 0 else 0.0

    def close(self) -> None:
        pass
