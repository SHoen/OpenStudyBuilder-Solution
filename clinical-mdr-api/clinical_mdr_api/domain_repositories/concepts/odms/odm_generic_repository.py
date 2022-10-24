from abc import ABC
from typing import Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class OdmGenericRepository(ConceptGenericRepository[_AggregateRootType], ABC):
    def generic_match_clause(self, only_specific_status: list = None):
        if not only_specific_status:
            return super().generic_match_clause()

        return f"""
        CYPHER runtime=slotted MATCH (concept_root:{self.root_class.__label__})-[:{'|'.join(only_specific_status)}]->
        (concept_value:{self.value_class.__label__})
        """

    def find_all(
        self,
        library: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
        only_specific_status: list = None,
        **kwargs,
    ) -> Tuple[Sequence[_AggregateRootType], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :param only_specific_status:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause(only_specific_status)

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        alias_clause = self.generic_alias_clause() + self.specific_alias_clause(
            only_specific_status
        )
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=self.return_model,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )
        extracted_items = self._retrieve_concepts_from_cypher_res(
            result_array, attributes_names
        )

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )

        return extracted_items, total_amount
