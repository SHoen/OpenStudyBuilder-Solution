from typing import Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_get_all_query_utils import (
    create_term_attributes_aggregate_instances_from_cypher_result,
    create_term_filter_statement,
    create_term_name_aggregate_instances_from_cypher_result,
    format_term_filter_sort_keys,
    list_term_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.models.ct_stats import TermCount
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class CTTermAggregatedRepository:

    generic_alias_clause = """
        DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, codelist_root, has_term
        ORDER BY has_term.order, term_name_value.name
        WITH DISTINCT term_root, term_attributes_root, term_attributes_value, term_name_root, term_name_value, 
        codelist_root, has_term,
        head([(catalogue:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue]) AS catalogue,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library,
        head([(term_attributes_root)-[ld:LATEST_DRAFT]->(term_attributes_value) | ld]) AS ld_attributes,
        head([(term_attributes_root)-[lf:LATEST_FINAL]->(term_attributes_value) | lf]) AS lf_attributes,
        head([(term_attributes_root)-[lr:LATEST_RETIRED]->(term_attributes_value) | lr]) AS lr_attributes,
        head([(term_attributes_root)-[hv:HAS_VERSION]->(term_attributes_value) | hv]) AS hv_attributes,
        head([(term_name_root)-[ld:LATEST_DRAFT]->(term_name_value) | ld]) AS ld_name,
        head([(term_name_root)-[lf:LATEST_FINAL]->(term_name_value) | lf]) AS lf_name,
        head([(term_name_root)-[lr:LATEST_RETIRED]->(term_name_value) | lr]) AS lr_name,
        head([(term_name_root)-[hv:HAS_VERSION]->(term_name_value) | hv]) AS hv_name
        CALL apoc.case(
            [
                ld_attributes IS NOT NULL AND ld_attributes.end_date IS NULL, 'RETURN ld_attributes AS rel',
                lf_attributes IS NOT NULL AND lf_attributes.end_date IS NULL, 'RETURN lf_attributes AS rel',
                lr_attributes IS NOT NULL AND lr_attributes.end_date IS NULL, 'RETURN lr_attributes AS rel',
                ld_attributes IS NULL AND lf_attributes IS NULL AND lr_attributes IS NULL, 'RETURN hv_attributes AS rel'
            ],
            '',
            {ld_attributes:ld_attributes, lf_attributes:lf_attributes, lr_attributes:lr_attributes, hv_attributes:hv_attributes})
        YIELD value as rel_data_attributes
        CALL apoc.case(
            [
                ld_name IS NOT NULL AND ld_name.end_date IS NULL, 'RETURN ld_name AS rel',
                lf_name IS NOT NULL AND lf_name.end_date IS NULL, 'RETURN lf_name AS rel',
                lr_name IS NOT NULL AND lr_name.end_date IS NULL, 'RETURN lr_name AS rel',
                ld_name IS NULL AND lf_name IS NULL AND lr_name IS NULL, 'RETURN hv_name as rel'
            ],
            '',
            {ld_name:ld_name, lf_name:lf_name, lr_name:lr_name, hv_name:hv_name})
        YIELD value as rel_data_name
        WITH
            term_root.uid AS term_uid,
            codelist_root.uid AS codelist_uid,
            catalogue.name AS catalogue_name,
            term_attributes_value AS value_node_attributes,
            term_name_value AS value_node_name,
            has_term.order AS order,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            {
                start_date: rel_data_attributes.rel.start_date,
                end_date: NULL,
                status: rel_data_attributes.rel.status,
                version: rel_data_attributes.rel.version,
                change_description: rel_data_attributes.rel.change_description,
                user_initials: rel_data_attributes.rel.user_initials
            } AS rel_data_attributes,
            {
                start_date: rel_data_name.rel.start_date,
                end_date: NULL,
                status: rel_data_name.rel.status,
                version: rel_data_name.rel.version,
                change_description: rel_data_name.rel.change_description,
                user_initials: rel_data_name.rel.user_initials
            } AS rel_data_name
    """

    def _create_term_aggregate_instances_from_cypher_result(
        self, term_dict: dict
    ) -> Tuple[CTTermNameAR, CTTermAttributesAR]:
        """
        Method creates a tuple of CTTermNameAR and CTTermAttributesAR objects for one CTTermRoot node.
        The term_dict is a find_all_aggregated_result method result for one CTTermRoot node.

        :param term_dict:
        :return (CTTermNameAR, CTTermAttributesAR):
        """

        term_name_ar = create_term_name_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=True
        )
        term_attributes_ar = (
            create_term_attributes_aggregate_instances_from_cypher_result(
                term_dict=term_dict, is_aggregated_query=True
            )
        )
        return term_name_ar, term_attributes_ar

    def find_all_aggregated_result(
        self,
        codelist_uid: Optional[str] = None,
        codelist_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[Tuple[CTTermNameAR, CTTermAttributesAR]]:
        """
        Method runs a cypher query to fetch all data related to the CTTermName* and CTTermAttributes*.
        It allows to filter the query output by codelist_uid, codelist_name, library and package.
        It returns the array of Tuples where each tuple is consists of CTTermNameAR and CTTermAttributesAR objects.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_uid:
        :param codelist_name:
        :param library:
        :param package:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[Tuple[CTTermNameAR, CTTermAttributesAR]]:
        """
        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library=library,
            package=package,
        )

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
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

        terms_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attributes_names):
                term_dictionary[attribute_name] = term_property
            terms_ars.append(
                self._create_term_aggregate_instances_from_cypher_result(
                    term_dictionary
                )
            )

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(items=terms_ars, total_count=_total_count)

    def get_distinct_headers(
        self,
        field_name: str,
        codelist_uid: Optional[str] = None,
        codelist_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ) -> Sequence:
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of result_count.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param codelist_uid:
        :param codelist_name:
        :param library:
        :param package:
        :param search_string:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param result_count: Max number of values to return. Default 10
        :return Sequence:
        """
        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library=library,
            package=package,
        )

        # Aliases clause
        alias_clause = self.generic_alias_clause

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        if search_string != "":
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
            wildcard_properties_list=list_term_wildcard_properties(),
            format_filter_sort_keys=format_term_filter_sort_keys,
        )

        header_query = query.build_header_query(
            header_alias=format_term_filter_sort_keys(field_name),
            result_count=result_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, _ = db.cypher_query(query=header_query, params=query.parameters)

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def _generate_generic_match_clause(
        self,
        codelist_uid: Optional[str] = None,
        codelist_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
    ) -> Tuple[str, dict]:
        if package:
            match_clause = """
            MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
            [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[:LATEST]->(term_name_value:CTTermNameValue)
            """
        else:
            match_clause = """
            MATCH (term_name_value:CTTermNameValue)<-[:LATEST]-(term_name_root:CTTermNameRoot)<-[:HAS_NAME_ROOT]-(term_root:CTTermRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(term_attributes_root:CTTermAttributesRoot)-[:LATEST]->(term_attributes_value:CTTermAttributesValue)
            """

        filter_query_parameters = {}
        if library or package:
            # Build specific filtering for package and library
            # This is separate from generic filtering as the list of filters is predefined
            # We can therefore do this filtering in an efficient way in the Cypher MATCH clause
            filter_statements, filter_query_parameters = create_term_filter_statement(
                library=library, package=package
            )
            match_clause += filter_statements

        match_clause += (
            " MATCH (codelist_root:CTCodelistRoot)-[has_term:HAS_TERM]->(term_root) "
        )

        if codelist_uid or codelist_name:
            # Build spefic filtering for codelist
            # This is done separately from library and package as we first need to match codelist_root
            (
                codelist_filter_statements,
                codelist_filter_query_parameters,
            ) = create_term_filter_statement(
                codelist_uid=codelist_uid, codelist_name=codelist_name
            )
            match_clause += codelist_filter_statements
            filter_query_parameters.update(codelist_filter_query_parameters)

        return match_clause, filter_query_parameters

    def count_all(self) -> Sequence[TermCount]:
        """
        Returns the count of CT Terms in the database, grouped by Library

        :return: Sequence[TermCount] - count of CT Terms
        """
        query = """
            MATCH (n:CTTermRoot)<-[:CONTAINS_TERM]-(l:Library)
            RETURN l.name as libraryName, count(n) as count
            """

        result, _ = db.cypher_query(query)
        return [TermCount(libraryName=item[0], count=item[1]) for item in result]

    def get_change_percentage(self) -> float:
        """
        Returns the percentage of CT Terms with more than one version

        :return: float - percentage
        """
        query = """
            MATCH (r:CTTermNameRoot)-->(v:CTTermNameValue)
            RETURN CASE count(r)
                WHEN 0 THEN 0
                ELSE (count(v)-count(r))/count(r)
                END AS percentage
            """

        result, _ = db.cypher_query(query)
        return result[0][0] if len(result) > 0 else 0.0

    def close(self) -> None:
        pass
