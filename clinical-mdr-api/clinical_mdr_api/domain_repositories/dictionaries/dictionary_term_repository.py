from abc import ABC
from datetime import datetime
from typing import Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain.dictionaries.dictionary_term import (
    DictionaryTermAR,
    DictionaryTermVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.dictionary import (
    DictionaryCodelistRoot,
    DictionaryTermRoot,
    DictionaryTermValue,
    MEDRTTermRoot,
    MEDRTTermValue,
    SnomedTermRoot,
    SnomedTermValue,
    UCUMTermRoot,
    UCUMTermValue,
    UNIITermRoot,
    UNIITermValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.models import DictionaryCodelist
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)


class DictionaryTermGenericRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType], ABC
):
    root_class = DictionaryTermRoot
    value_class = DictionaryTermValue
    specific_root_class_mapping = {
        "snomed": SnomedTermRoot,
        "med-rt": MEDRTTermRoot,
        "unii": UNIITermRoot,
        "ucum": UCUMTermRoot,
    }
    specific_value_class_mapping = {
        "snomed": SnomedTermValue,
        "med-rt": MEDRTTermValue,
        "unii": UNIITermValue,
        "ucum": UCUMTermValue,
    }

    def generate_uid(self) -> str:
        return DictionaryTermRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
    ) -> DictionaryTermAR:
        major, minor = term_dict.get("version").split(".")
        return DictionaryTermAR.from_repository_values(
            uid=term_dict.get("termUid"),
            dictionary_term_vo=DictionaryTermVO.from_repository_values(
                codelist_uid=term_dict.get("codelistUid"),
                dictionary_id=term_dict.get("dictionaryId"),
                name=term_dict.get("name"),
                name_sentence_case=term_dict.get("nameSentenceCase"),
                abbreviation=term_dict.get("abbreviation"),
                definition=term_dict.get("definition"),
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
    ) -> DictionaryTermAR:
        dictionary_codelist_root = root.has_term.single()
        library = dictionary_codelist_root.has_library.get_or_none()
        return DictionaryTermAR.from_repository_values(
            uid=root.uid,
            dictionary_term_vo=DictionaryTermVO.from_repository_values(
                codelist_uid=dictionary_codelist_root.uid,
                dictionary_id=value.dictionary_id,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                abbreviation=value.abbreviation,
                definition=value.definition,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def generic_match_clause(self):
        return """MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})
            -[:HAS_TERM|HAD_TERM]->(dictionary_term_root:DictionaryTermRoot)-[:LATEST]->(dictionary_term_value)"""

    def generic_alias_clause(self):
        return """
            DISTINCT dictionary_codelist_root, dictionary_term_root, dictionary_term_value,
            head([(library:Library)-[:CONTAINS_DICTIONARY_CODELIST]->(dictionary_codelist_root) | library]) AS library,
            head([(dictionary_term_root)-[ld:LATEST_DRAFT]->(dictionary_term_value) | ld]) AS ld,
            head([(dictionary_term_root)-[lf:LATEST_FINAL]->(dictionary_term_value) | lf]) AS lf,
            head([(dictionary_term_root)-[lr:LATEST_RETIRED]->(dictionary_term_value) | lr]) AS lr,
            head([(dictionary_term_root)-[hv:HAS_VERSION]->(dictionary_term_value) | hv]) AS hv
            WITH
                dictionary_term_value,
                dictionary_codelist_root.uid as codelistUid,
                dictionary_term_root.uid AS termUid,
                dictionary_term_value.dictionary_id as dictionaryId,
                dictionary_term_value.name AS name,
                dictionary_term_value.name_sentence_case as nameSentenceCase,
                dictionary_term_value.abbreviation as abbreviation,
                dictionary_term_value.definition AS definition,
                library.name AS libraryName,
                library.is_editable AS is_library_editable,
                ld, lf, lr, hv
                CALL apoc.case(
                 [
                   ld IS NOT NULL AND ld.end_date IS NULL, 'RETURN ld as version_rel',
                   lf IS NOT NULL AND lf.end_date IS NULL, 'RETURN lf as version_rel',
                   lr IS NOT NULL AND lr.end_date IS NULL, 'RETURN lr as version_rel',
                   ld IS NULL AND lf IS NULL AND lr IS NULL, 'RETURN hv as version_rel'
                 ],
                 '',
                 {ld:ld, lf:lf, lr:lr, hv:hv})
                 yield value
            WITH 
                dictionary_term_value,
                codelistUid,
                termUid,
                dictionaryId,
                name,
                nameSentenceCase,
                abbreviation,
                definition,
                libraryName,
                is_library_editable,
                value.version_rel.start_date AS startDate,
                value.version_rel.status AS status,
                value.version_rel.version AS version,
                value.version_rel.change_description AS changeDescription,
                value.version_rel.user_initials AS userInitials
        """

    def specific_alias_clause(self) -> str:
        """
        Method should be overridden in subclass repository
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """
        return ""

    def find_all(
        self,
        codelist_uid: str = None,
        sort_by: Optional[dict] = None,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> Tuple[Sequence[DictionaryTermAR], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param codelist_uid:
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

        query.parameters.update({"codelist_uid": codelist_uid})
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

    def _retrieve_terms_from_cypher_res(
        self, result_array, attribute_names
    ) -> Sequence[DictionaryTermAR]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        term_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attribute_names):
                term_dictionary[attribute_name] = term_property
            term_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(term_dictionary)
            )

        return term_ars

    def get_distinct_headers(
        self,
        codelist_uid: str,
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ) -> Sequence[str]:

        # Match clause
        match_clause = self.generic_match_clause()

        # Aliases clause
        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()

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
        )

        query.parameters.update({"codelist_uid": codelist_uid})
        header_query = query.build_header_query(
            header_alias=field_name, result_count=result_count
        )
        result_array, _ = db.cypher_query(query=header_query, params=query.parameters)

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def get_template_indications(
        self, root_class: type, template_uid: str
    ) -> Optional[Sequence[DictionaryTermAR]]:
        """
        This method returns the indications for the template with provided uid

        :param root_class: The class of the root node for the template
        :param template_uid: UID of the template
        :return Sequence[DictionaryTermAR]:
        """
        template = root_class.nodes.get(uid=template_uid)
        indication_nodes = template.has_indication.all()
        if indication_nodes:
            indications = []
            for node in indication_nodes:
                indication = self.find_by_uid(term_uid=node.uid)
                indications.append(indication)
            return indications
        return None

    def find_by_uid(
        self, term_uid: str, for_update: Optional[bool] = False
    ) -> DictionaryTermAR:
        """
        This method returns the Dictionary Term with provided uid

        :param term_uid: UID of Dictionary Term to get
        :param for_update:
        :return DictionaryTermAR:
        """
        return self.find_by_uid_2(uid=term_uid, for_update=for_update)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _create(self, item: DictionaryTermAR) -> DictionaryTermAR:
        """
        Creates new DictionaryTerm versioned object, checks possibility based on library setting,
        then creates database representation.
        Creates DictionaryTermRoot and DictionaryTermValue database objects,
        recreates AR based on created database model and returns created AR.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        dictionary_codelist = DictionaryCodelistRoot.nodes.get_or_none(
            uid=item.dictionary_term_vo.codelist_uid
        )

        library = dictionary_codelist.has_library.get_or_none()
        library_name = library.name.lower()
        if library_name not in self.specific_root_class_mapping:
            raise ValueError(
                f"Unknown specific type ({library_name}) of dictionary term."
            )

        root = self.specific_root_class_mapping[library_name](uid=item.uid)

        value = self._create_new_value_node(library_name=library_name, ar=item)

        self._db_save_node(root)

        (root, value, _, _, _,) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        dictionary_codelist.has_term.connect(
            root,
            {
                "start_date": datetime.now(),
                "end_date": None,
                "user_initials": item.item_metadata.user_initials,
            },
        )

        library = self._get_library(item.library.name)
        root.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    def _new_version_necessary(self, ar: DictionaryTermAR, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: DictionaryTermRoot, ar: DictionaryTermAR
    ) -> DictionaryTermValue:
        items = root.has_version.filter(
            name=ar.name,
            dictionary_id=ar.dictionary_term_vo.dictionary_id,
            name_sentence_case=ar.dictionary_term_vo.name_sentence_case,
            abbreviation=ar.dictionary_term_vo.abbreviation,
            definition=ar.dictionary_term_vo.definition,
        )
        for itm in items:
            return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired

        library = root.has_library.get_or_none()
        library_name = library.name.lower()
        new_value = self._create_new_value_node(library_name=library_name, ar=ar)
        self._db_save_node(new_value)
        return new_value

    def _create_new_value_node(
        self, library_name: str, ar: _AggregateRootType
    ) -> VersionValue:
        return self.specific_value_class_mapping[library_name](
            name=ar.name,
            dictionary_id=ar.dictionary_term_vo.dictionary_id,
            name_sentence_case=ar.dictionary_term_vo.name_sentence_case,
            abbreviation=ar.dictionary_term_vo.abbreviation,
            definition=ar.dictionary_term_vo.definition,
        )

    def _has_data_changed(self, ar: DictionaryTermAR, value: VersionValue):
        return (
            ar.name != value.name
            or ar.dictionary_term_vo.dictionary_id != value.dictionary_id
            or ar.dictionary_term_vo.name_sentence_case != value.name_sentence_case
            or ar.dictionary_term_vo.abbreviation != value.abbreviation
            or ar.dictionary_term_vo.definition != value.definition
        )

    def _maintain_parameters(
        self, versioned_object: DictionaryTermAR, root: VersionRoot, value: VersionValue
    ) -> None:
        maintain_template_parameter_query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid: $codelist_uid})-[:LATEST]->
                (dictionary_codelist_value:TemplateParameter)
            WITH dictionary_codelist_root, dictionary_codelist_value
            MATCH (dictionary_term_root:DictionaryTermRoot {uid: $term_uid})-[:LATEST]->(dictionary_term_value)
            MERGE (dictionary_codelist_value)-[hv:HAS_VALUE]->(dictionary_term_root)
            SET dictionary_term_root:TemplateParameterValueRoot
            SET dictionary_term_value:TemplateParameterValue
        """
        db.cypher_query(
            maintain_template_parameter_query,
            {
                "codelist_uid": versioned_object.dictionary_term_vo.codelist_uid,
                "term_uid": versioned_object.uid,
            },
        )

    def term_exists(self, term_uid: str) -> bool:
        query = """
            MATCH (dictionary_term_root:DictionaryTermRoot {uid: $uid})-[:LATEST_FINAL]->(dictionary_term_value)
            RETURN dictionary_term_root
            """
        result, _ = db.cypher_query(query, {"uid": term_uid})
        return len(result) > 0 and len(result[0]) > 0

    def term_exists_by_name(self, term_name: str, codelist_uid: str) -> bool:
        query = """
            MATCH (dictionary_codelist_root:DictionaryCodelistRoot {uid:$codelist_uid})-[:HAS_TERM]->
            (dictionary_term_root)-[:LATEST_FINAL]->(dictionary_term_value:DictionaryTermValue {name: $term_name})
            RETURN dictionary_term_root
            """
        result, _ = db.cypher_query(
            query, {"term_name": term_name, "codelist_uid": codelist_uid}
        )
        return len(result) > 0 and len(result[0]) > 0
