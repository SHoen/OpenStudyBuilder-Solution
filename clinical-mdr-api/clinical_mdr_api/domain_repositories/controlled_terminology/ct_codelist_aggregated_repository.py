from typing import Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_get_all_query_utils import (
    create_codelist_attributes_aggregate_instances_from_cypher_result,
    create_codelist_filter_statement,
    create_codelist_name_aggregate_instances_from_cypher_result,
    format_codelist_filter_sort_keys,
    list_codelist_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.models.ct_stats import CodelistCount
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
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library,
        head([(codelist_attributes_root)-[ld:LATEST_DRAFT]->(codelist_attributes_value) | ld]) AS ld_attributes,
        head([(codelist_attributes_root)-[lf:LATEST_FINAL]->(codelist_attributes_value) | lf]) AS lf_attributes,
        head([(codelist_attributes_root)-[lr:LATEST_RETIRED]->(codelist_attributes_value) | lr]) AS lr_attributes,
        head([(codelist_attributes_root)-[hv:HAS_VERSION]->(codelist_attributes_value) | hv]) AS hv_attributes,
        head([(codelist_name_root)-[ld:LATEST_DRAFT]->(codelist_name_value) | ld]) AS ld_name,
        head([(codelist_name_root)-[lf:LATEST_FINAL]->(codelist_name_value) | lf]) AS lf_name,
        head([(codelist_name_root)-[lr:LATEST_RETIRED]->(codelist_name_value) | lr]) AS lr_name,
        head([(codelist_name_root)-[hv:HAS_VERSION]->(codelist_name_value) | hv]) AS hv_name
        CALL apoc.case(
            [
                ld_attributes IS NOT NULL AND ld_attributes.end_date IS NULL, 'RETURN ld_attributes as rel',
                lf_attributes IS NOT NULL AND lf_attributes.end_date IS NULL, 'RETURN lf_attributes as rel',
                lr_attributes IS NOT NULL AND lr_attributes.end_date IS NULL, 'RETURN lr_attributes as rel',
                ld_attributes IS NULL AND lf_attributes IS NULL AND lr_attributes IS NULL, 'RETURN hv_attributes as rel'
            ],
            '',
            {ld_attributes:ld_attributes, lf_attributes:lf_attributes, lr_attributes:lr_attributes, hv_attributes:hv_attributes})
        YIELD value as rel_data_attributes
        CALL apoc.case(
            [
                ld_name IS NOT NULL AND ld_name.end_date IS NULL, 'RETURN ld_name as rel',
                lf_name IS NOT NULL AND lf_name.end_date IS NULL, 'RETURN lf_name as rel',
                lr_name IS NOT NULL AND lr_name.end_date IS NULL, 'RETURN lr_name as rel',
                ld_name IS NULL AND lf_name IS NULL AND lr_name IS NULL, 'RETURN hv_name as rel'
            ],
            '',
            {ld_name:ld_name, lf_name:lf_name, lr_name:lr_name, hv_name:hv_name})
        YIELD value as rel_data_name
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

    def _create_codelist_aggregate_instances_from_cypher_result(
        self, codelist_dict: dict
    ) -> Tuple[CTCodelistNameAR, CTCodelistAttributesAR]:
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
        catalogue_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[Tuple[CTCodelistNameAR, CTCodelistAttributesAR]]:
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
        :return GenericFilteringReturn[Tuple[CTCodelistNameAR, CTCodelistAttributesAR]]:
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
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )

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

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(
            items=codelists_ars, total_count=_total_count
        )

    def get_distinct_headers(
        self,
        field_name: str,
        catalogue_name: Optional[str] = None,
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

        header_query = query.build_header_query(
            header_alias=format_codelist_filter_sort_keys(field_name),
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
        package: Optional[str] = None,
    ):
        if package:
            match_clause = """
            MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
            (codelist_attributes_value:CTCodelistAttributesValue)<-[]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
            (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->(codelist_name_root:CTCodelistNameRoot)-[:LATEST]->(codelist_name_value:CTCodelistNameValue)
            """
        else:
            match_clause = """
            MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST]-(codelist_name_root:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-(codelist_root:CTCodelistRoot)
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
            RETURN l.name as libraryName, count(n) as count
            """

        result, _ = db.cypher_query(query)
        return [CodelistCount(libraryName=item[0], count=item[1]) for item in result]

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
