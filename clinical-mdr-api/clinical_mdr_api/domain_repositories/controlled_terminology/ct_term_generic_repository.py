from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Optional, Sequence, Tuple, cast

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import db

from clinical_mdr_api import config, models
from clinical_mdr_api.domain.controlled_terminology.utils import TermParentType
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_get_all_query_utils import (
    create_term_filter_statement,
    format_term_filter_sort_keys,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    ControlledTerminology,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)


class CTTermGenericRepository(LibraryItemRepositoryImplBase[_AggregateRootType], ABC):
    root_class = type
    value_class = type
    relationship_from_root = type
    cache_store_item_by_uid: TTLCache = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )

    generic_alias_clause = """
        DISTINCT term_root, term_ver_root, term_ver_value, codelist_root, has_term
        ORDER BY has_term.order, term_ver_value.name
        WITH DISTINCT codelist_root, has_term, term_root, term_ver_root, term_ver_value,
        head([(catalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue]) AS catalogue,
        head([(lib)-[:CONTAINS_TERM]->(term_root) | lib]) AS library,
        head([(term_ver_root)-[ld:LATEST_DRAFT]->(term_ver_value) | ld]) AS ld,
        head([(term_ver_root)-[lf:LATEST_FINAL]->(term_ver_value) | lf]) AS lf,
        head([(term_ver_root)-[lr:LATEST_RETIRED]->(term_ver_value) | lr]) AS lr,
        head([(term_ver_root)-[hv:HAS_VERSION]->(term_ver_value) | hv]) AS hv
        CALL apoc.case(
            [
                ld IS NOT NULL AND ld.end_date IS NULL, 'RETURN ld as rel',
                lf IS NOT NULL AND lf.end_date IS NULL, 'RETURN lf as rel',
                lr IS NOT NULL AND lr.end_date IS NULL, 'RETURN lr as rel',
                ld IS NULL AND lf IS NULL AND lr IS NULL, 'RETURN hv as rel'
            ],
            '',
            {ld:ld, lf:lf, lr:lr, hv:hv})
        YIELD value as rel_data
        WITH
            term_root.uid AS term_uid,
            codelist_root.uid AS codelist_uid,
            catalogue.name AS catalogue_name,
            term_ver_value AS value_node,
            has_term.order AS order,
            library.name AS library_name,
            library.is_editable AS is_library_editable,
            {
                start_date: rel_data.rel.start_date,
                end_date: NULL,
                status: rel_data.rel.status,
                version: rel_data.rel.version,
                change_description: rel_data.rel.change_description,
                user_initials: rel_data.rel.user_initials
            } AS rel_data
        """

    def generate_uid(self) -> str:
        return CTTermRoot.get_next_free_uid_and_increment_counter()

    def term_specific_exists_by_uid(self, uid: str) -> bool:
        """
        Returns True or False depending on if there exists a term with a final version for a given uid
        :return:
        """
        query = """
            MATCH (term_ver_root:CTTermRoot {uid: $uid})
            RETURN term_ver_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0

    def term_specific_order_by_uid(self, uid: str) -> int:
        """
        Returns the latest final version order number if a order number exists for a given term uid
        :return:
        """
        query = """
            MATCH (term_ver_root:CTTermRoot {uid: $uid})<-[has_term:HAS_TERM]-(codelist_root:CTCodelistRoot)
            RETURN has_term.order as order
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ControlledTerminology,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: ControlledTerminology,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
    ) -> _AggregateRootType:
        """
        Creates aggregate root instances from cypher query result.
        :param terms_dict:
        :return _AggregateRootType:
        """
        raise NotImplementedError

    def term_exists(self, term_uid: str) -> bool:
        query = """
            MATCH (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_ver_value:CTTermNameValue)
            RETURN term_root
            """
        result, _ = db.cypher_query(query, {"uid": term_uid})
        if len(result) > 0 and len(result[0]) > 0:
            return True
        return False

    def get_term_attributes_by_codelist_uids(self, codelist_uids: list):
        query = """
            MATCH (codelist:CTCodelistRoot)-[:HAS_TERM]->(term_root:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(term_attr_root:CTTermAttributesRoot)-[:LATEST]->(term_attr_value:CTTermAttributesValue)
            WHERE codelist.uid in $codelist_uids
            RETURN term_root.uid as termUid, codelist.uid as codelistUid, term_attr_value.code_submission_value as codeSubmissionValue, term_attr_value.preferred_term as nciPreferredName
            """

        items, prop_names = db.cypher_query(query, {"codelist_uids": codelist_uids})

        return items, prop_names

    def find_all(
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
    ) -> GenericFilteringReturn[_AggregateRootType]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Terms aggregates.

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
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        if self.relationship_from_root not in CTTermRoot.__dict__:
            raise ValueError(
                f"The relationship of type {self.relationship_from_root} "
                f"was not found in CTTermRoot object"
            )

        # Build match_clause
        match_clause, filter_query_parameters = self._generate_generic_match_clause(
            codelist_uid=codelist_uid,
            codelist_name=codelist_name,
            library=library,
            package=package,
        )

        # Build alias_clause
        alias_clause = self.generic_alias_clause

        _return_model = (
            models.CTTermAttributes
            if self.is_repository_related_to_attributes()
            else models.CTTermName
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
            return_model=_return_model,
            format_filter_sort_keys=format_term_filter_sort_keys,
        )
        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )
        extracted_items = self._retrieve_term_from_cypher_res(
            result_array, attributes_names
        )

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_count = count_result[0][0] if len(count_result) > 0 and total_count else 0

        return GenericFilteringReturn.create(
            items=extracted_items, total_count=total_count
        )

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

    def _retrieve_term_from_cypher_res(
        self, result_array, attribute_names
    ) -> Iterable[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        terms_ars = []
        for term in result_array:
            term_dictionary = {}
            for term_property, attribute_name in zip(term, attribute_names):
                term_dictionary[attribute_name] = term_property
            terms_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(term_dictionary)
            )

        return terms_ars

    def get_template_criteria_type(
        self, root_class: type, template_uid: str
    ) -> _AggregateRootType:
        """
        This method returns the criteria type for the template with provided uid.

        :param root_class: The class of the root node for the template
        :param template_uid: UID of the template
        :return _AggregateRootType:
        """
        template = root_class.nodes.get(uid=template_uid)
        criteria_type_node = template.has_type.single()
        criteria_type = self.find_by_uid(term_uid=criteria_type_node.uid)
        return criteria_type

    def get_template_categories(
        self, root_class: type, template_uid: str
    ) -> Optional[Sequence[_AggregateRootType]]:
        """
        This method returns the categories for the template with provided uid.

        :param root_class: The class of the root node for the template
        :param template_uid: UID of the template
        :return Sequence[_AggregateRootType]:
        """
        template = root_class.nodes.get(uid=template_uid)
        category_nodes = template.has_category.all()
        if category_nodes:
            categories = []
            for node in category_nodes:
                category = self.find_by_uid(term_uid=node.uid)
                categories.append(category)
            return sorted(categories, key=lambda c: c.uid)
        return None

    def get_template_sub_categories(
        self, root_class: type, template_uid: str
    ) -> Optional[Sequence[_AggregateRootType]]:
        """
        This method returns the sub_categories for the template with provided uid.

        :param root_class: The class of the root node for the template
        :param template_uid: UID of the template
        :return Sequence[_AggregateRootType]:
        """
        template = root_class.nodes.get(uid=template_uid)
        sub_category_nodes = template.has_sub_category.all()
        if sub_category_nodes:
            sub_categories = []
            for node in sub_category_nodes:
                category = self.find_by_uid(term_uid=node.uid)
                sub_categories.append(category)
            return sorted(sub_categories, key=lambda c: c.uid)
        return None

    def hashkey_ct_term(
        self,
        term_uid: str,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid method will be misses.
        """
        return hashkey(
            str(self.__class__),
            term_uid,
            version,
            status,
            at_specific_date,
            for_update,
        )

    @cached(cache=cache_store_item_by_uid, key=hashkey_ct_term)
    def find_by_uid(
        self,
        term_uid: str,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
    ) -> Optional[_AggregateRootType]:

        ct_term_root: CTTermRoot = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_root is None:
            return None
        # pylint:disable=unnecessary-dunder-call
        ct_term_version_root_node = ct_term_root.__getattribute__(
            self.relationship_from_root
        ).single()
        term_ar = self.find_by_uid_2(
            str(ct_term_version_root_node.id),
            version=version,
            status=status,
            at_specific_date=at_specific_date,
            for_update=for_update,
        )

        return term_ar

    def get_all_versions(self, term_uid: str) -> Optional[Iterable[_AggregateRootType]]:
        ct_term_root: CTTermRoot = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_root is not None:
            # pylint:disable=unnecessary-dunder-call
            ct_term_ver_root_node = ct_term_root.__getattribute__(
                self.relationship_from_root
            ).single()
            versions = self.get_all_versions_2(str(ct_term_ver_root_node.id))
            return versions
        return None

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _is_repository_related_to_ct(self) -> bool:
        return True

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def add_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
    ) -> None:
        """
        Method adds term identified by parent_uid as a parent type to the term identified by the term_uid.
        Adding a parent type means creating a HAS_PARENT_TYPE or HAS_PARENT_SUB_TYPE
        relationship from CTTermRoot identified by the term_uid to the CTTermRoot identified by the parent_uid.
        :param term_uid:
        :param parent_uid:
        :param relationship_type:
        :return None:
        """
        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=term_uid)

        if relationship_type == TermParentType.PARENT_TYPE:
            parent_node = ct_term_root_node.has_parent_type.get_or_none()
        elif relationship_type == TermParentType.VALID_FOR_EPOCH_TYPE:
            parent_node = ct_term_root_node.valid_for_epoch_type.get_or_none(
                uid=parent_uid
            )
        else:
            parent_node = ct_term_root_node.has_parent_sub_type.get_or_none()

        if parent_node is not None:
            raise ValueError(
                f"The term identified by ({term_uid}) already has a "
                f"parent type node identified by ({parent_node.uid}) "
                f"with the relationship of type ({relationship_type.value})"
            )

        ct_term_root_parent_node = CTTermRoot.nodes.get_or_none(uid=parent_uid)

        if relationship_type == TermParentType.PARENT_TYPE:
            ct_term_root_node.has_parent_type.connect(ct_term_root_parent_node)
        elif relationship_type == TermParentType.VALID_FOR_EPOCH_TYPE:
            ct_term_root_node.valid_for_epoch_type.connect(ct_term_root_parent_node)
        else:
            ct_term_root_node.has_parent_sub_type.connect(ct_term_root_parent_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def remove_parent(
        self, term_uid: str, parent_uid: str, relationship_type: TermParentType
    ) -> None:
        """
        Method removes term parent type from the term identified by the term_uid.
        Removing a parent type means deleting a HAS_PARENT_TYPE or HAS_PARENT_SUB_TYPE
        relationship from CTTermRoot identified by the term_uid to the parent type CTTermRoot node.
        :param term_uid:
        :param parent_uid:
        :param relationship_type:
        :return None:
        """
        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=term_uid)

        if relationship_type == TermParentType.PARENT_TYPE:
            parent_node = ct_term_root_node.has_parent_type.get_or_none()
        elif relationship_type == TermParentType.VALID_FOR_EPOCH_TYPE:
            parent_node = ct_term_root_node.valid_for_epoch_type.get_or_none(
                uid=parent_uid
            )
        else:
            parent_node = ct_term_root_node.has_parent_sub_type.get_or_none()

        if parent_node is None:
            raise ValueError(
                f"The term identified by ({term_uid}) has no defined parent type node"
                f" identified by ({parent_uid}) with the relationship of type ({relationship_type.value})"
            )
        if relationship_type == TermParentType.PARENT_TYPE:
            ct_term_root_node.has_parent_type.disconnect(parent_node)
        elif relationship_type == TermParentType.VALID_FOR_EPOCH_TYPE:
            ct_term_root_node.valid_for_epoch_type.disconnect(parent_node)
        else:
            ct_term_root_node.has_parent_sub_type.disconnect(parent_node)

    @abstractmethod
    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        raise NotImplementedError

    def find_uid_by_name(self, name: str) -> Optional[str]:
        cypher_query = f"""
            MATCH (term_root:CTTermRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(or:{self.root_class.__label__})-
            [:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{name: $name}})
            RETURN term_root.uid
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})
        if len(items) > 0:
            return items[0][0]
        return None

    def _generate_generic_match_clause(
        self,
        codelist_uid: Optional[str] = None,
        codelist_name: Optional[str] = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
    ) -> Tuple[str, dict]:
        if package:
            if self.is_repository_related_to_attributes():
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                [:CONTAINS_ATTRIBUTES]->(term_ver_value:CTTermAttributesValue)<-[]-(term_ver_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(term_root:CTTermRoot)
                """
            else:
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_TERM]->(:CTPackageTerm)-
                [:CONTAINS_ATTRIBUTES]->(term_attributes_value:CTTermAttributesValue)<-[]-(term_attributes_root:CTTermAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_ver_value:CTTermNameValue)
                """
        else:
            match_clause = f"""
            MATCH (term_root:CTTermRoot)-[:{cast(str, self.relationship_from_root).upper()}]->(term_ver_root)-[:LATEST_FINAL]->(term_ver_value)
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
