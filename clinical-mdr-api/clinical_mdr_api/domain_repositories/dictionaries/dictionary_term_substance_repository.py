from typing import Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
    DictionaryTermSubstanceVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.dictionaries.dictionary_term_repository import (
    DictionaryTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.models import DictionaryCodelist
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)


class DictionaryTermSubstanceRepository(
    DictionaryTermGenericRepository[DictionaryTermSubstanceAR]
):
    def _create_new_value_node(
        self, library_name: str, ar: _AggregateRootType
    ) -> VersionValue:
        value_node = super()._create_new_value_node(library_name=library_name, ar=ar)

        value_node.save()

        if ar.dictionary_term_vo.pclass_uid is not None:
            value_node.has_pclass.connect(
                DictionaryTermRoot.nodes.get(uid=ar.dictionary_term_vo.pclass_uid)
            )

        return value_node

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
    ) -> DictionaryTermSubstanceAR:
        major, minor = term_dict.get("version").split(".")
        return DictionaryTermSubstanceAR.from_repository_values(
            uid=term_dict.get("termUid"),
            dictionary_term_vo=DictionaryTermSubstanceVO.from_repository_values(
                codelist_uid=term_dict.get("codelistUid"),
                dictionary_id=term_dict.get("dictionaryId"),
                name=term_dict.get("name"),
                name_sentence_case=term_dict.get("nameSentenceCase"),
                abbreviation=term_dict.get("abbreviation"),
                definition=term_dict.get("definition"),
                pclass_uid=term_dict.get("pclassUid"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=term_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: term_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=term_dict.get("changeDescription"),
                status=LibraryItemStatus(term_dict.get("status")),
                author=term_dict.get("userInitials"),
                start_date=convert_to_datetime(value=term_dict.get("startDate")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> DictionaryTermSubstanceAR:
        dictionary_codelist_root = root.has_term.single()
        library = dictionary_codelist_root.has_library.get_or_none()
        return DictionaryTermSubstanceAR.from_repository_values(
            uid=root.uid,
            dictionary_term_vo=DictionaryTermSubstanceVO.from_repository_values(
                codelist_uid=dictionary_codelist_root.uid,
                dictionary_id=value.dictionary_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                abbreviation=value.abbreviation,
                definition=value.definition,
                pclass_uid=self._get_uid_or_none(value.has_pclass.get_or_none()),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def generic_match_clause(self):
        return """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot)
            -[:HAS_TERM|HAD_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)
            
            WHERE EXISTS {
            (dictionary_codelist_root)-[LATEST_FINAL]->(DictionaryCodelistValue {name: $codelist_name})
            }   
            """

    def specific_alias_clause(self) -> str:
        return """
            WITH *,
                head([(dictionary_term_value)-[:HAS_PCLASS]->(pclass_dict_term_root:DictionaryTermRoot) | pclass_dict_term_root.uid]) AS pclassUid
            """

    def find_all(
        self,
        codelist_uid: str = None,
        sort_by: Optional[dict] = None,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
        codelist_name: str = None,
    ) -> Tuple[Sequence[DictionaryTermSubstanceAR], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_name:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause()

        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=DictionaryCodelist,
        )

        query.parameters.update({"codelist_name": codelist_name})
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )
        extracted_items = self._retrieve_terms_from_cypher_res(
            result_array, attributes_names
        )

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )

        return extracted_items, total_amount

    def _has_data_changed(self, ar: DictionaryTermSubstanceAR, value: VersionValue):
        parent_data_modified = super()._has_data_changed(ar=ar, value=value)

        relation_changed = ar.dictionary_term_vo.pclass_uid != self._get_uid_or_none(
            value.has_pclass.get_or_none()
        )

        return parent_data_modified or relation_changed
