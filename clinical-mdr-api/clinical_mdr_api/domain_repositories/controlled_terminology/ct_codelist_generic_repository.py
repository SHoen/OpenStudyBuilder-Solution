from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Optional, Sequence, cast

from neomodel import db

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_get_all_query_utils import (
    create_codelist_filter_statement,
    format_codelist_filter_sort_keys,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CodelistTermRelationship,
    ControlledTerminology,
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)
from clinical_mdr_api.models.ct_codelist_attributes import CTCodelistAttributes
from clinical_mdr_api.models.ct_codelist_name import CTCodelistName
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)


class CTCodelistGenericRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType], ABC
):
    root_class = type
    value_class = type
    relationship_from_root = type

    generic_alias_clause = """
        DISTINCT codelist_root, codelist_ver_root, codelist_ver_value
        ORDER BY codelist_root.uid
        WITH DISTINCT codelist_root, codelist_ver_root, codelist_ver_value, 
        head([(cat)-[:HAS_CODELIST]->(codelist_root) | cat]) AS catalogue,
        head([(lib)-[:CONTAINS_CODELIST]->(codelist_root) | lib]) AS library,
        head([(codelist_ver_root)-[ld:LATEST_DRAFT]->(codelist_ver_value) | ld]) AS ld,
        head([(codelist_ver_root)-[lf:LATEST_FINAL]->(codelist_ver_value) | lf]) AS lf,
        head([(codelist_ver_root)-[lr:LATEST_RETIRED]->(codelist_ver_value) | lr]) AS lr,
        head([(codelist_ver_root)-[hv:HAS_VERSION]->(codelist_ver_value) | hv]) AS hv
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
            codelist_root.uid AS codelist_uid,
            catalogue.name AS catalogue_name,
            head([(codelist_root)-[:HAS_PARENT_CODELIST]->(ccr:CTCodelistRoot) | ccr.uid]) AS parent_codelist_uid,
            [(codelist_root)<-[:HAS_PARENT_CODELIST]-(ccr:CTCodelistRoot) | ccr.uid] AS child_codelist_uids,
            codelist_ver_value AS value_node,
            CASE WHEN codelist_ver_value:TemplateParameter THEN true ELSE false END AS is_template_parameter,
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
        return CTCodelistRoot.get_next_free_uid_and_increment_counter()

    @classmethod
    def is_ct_node_a_tp(cls, ct_value_node) -> bool:
        labels = ct_value_node.labels()
        for label in labels:
            if "TemplateParameter" in label:
                return True
        return False

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
        self, codelist_dict: dict
    ) -> _AggregateRootType:
        """
        Creates aggregate root instances from cypher query result.
        :param codelist_dict:
        :return _AggregateRootType:
        """
        raise NotImplementedError

    @abstractmethod
    def is_repository_related_to_attributes(self) -> bool:
        raise NotImplementedError

    def find_all(
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
    ) -> GenericFilteringReturn[_AggregateRootType]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Codelists aggregates.

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
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        if self.relationship_from_root not in CTCodelistRoot.__dict__:
            raise ValueError(
                f"The relationship of type {self.relationship_from_root} "
                f"was not found in CTCodelistRoot object"
            )

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

        _return_model = (
            CTCodelistAttributes
            if self.is_repository_related_to_attributes()
            else CTCodelistName
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
            format_filter_sort_keys=format_codelist_filter_sort_keys,
        )
        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = db.cypher_query(
            query=query.full_query, params=query.parameters
        )
        extracted_items = self._retrieve_codelists_from_cypher_res(
            result_array, attributes_names
        )

        _total_count = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                _total_count = count_result[0][0]

        return GenericFilteringReturn.create(
            items=extracted_items, total_count=_total_count
        )

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: Optional[str] = "",
        catalogue_name: str = None,
        library: Optional[str] = None,
        package: Optional[str] = None,
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
            if self.is_repository_related_to_attributes():
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (codelist_ver_value:CTCodelistAttributesValue)<-[]-(codelist_ver_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (codelist_root:CTCodelistRoot)
                """
            else:
                match_clause = """
                MATCH (package:CTPackage)-[:CONTAINS_CODELIST]->(:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]->
                (codelist_attributes_value:CTCodelistAttributesValue)<-[]-(codelist_attributes_root:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-
                    (codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->(codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue)
                """
        else:
            match_clause = f"""
            MATCH (codelist_root:CTCodelistRoot)-[:{cast(str, self.relationship_from_root).upper()}]-(codelist_ver_root)-[:LATEST_FINAL]->(codelist_ver_value)
            """

        return match_clause

    def _retrieve_codelists_from_cypher_res(
        self, result_array, attribute_names
    ) -> Iterable[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        codelist_ars = []
        for codelist in result_array:
            codelist_dictionary = {}
            for codelist_property, attribute_name in zip(codelist, attribute_names):
                codelist_dictionary[attribute_name] = codelist_property
            codelist_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    codelist_dictionary
                )
            )

        return codelist_ars

    def find_by_uid(
        self,
        codelist_uid: str,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
    ) -> Optional[_AggregateRootType]:

        ct_codelist_root: CTCodelistRoot = CTCodelistRoot.nodes.get_or_none(
            uid=codelist_uid
        )
        if ct_codelist_root is None:
            return None

        if for_update:
            # Grab write lock on the codelist root, so that no terms can be added it to it while we update it.
            result, _ = db.cypher_query(
                "MATCH (node:CTCodelistRoot) WHERE node.uid = $uid RETURN node",
                {"uid": codelist_uid},
                resolve_objects=True,
            )
            itm = result[0][0]
            if itm is not None:
                itm.__WRITE_LOCK__ = None
                itm.save()

        # pylint:disable=unnecessary-dunder-call
        ct_codelist_name_root_node = ct_codelist_root.__getattribute__(
            self.relationship_from_root
        ).single()
        codelist_ar = self.find_by_uid_2(
            uid=str(ct_codelist_name_root_node.id),
            version=version,
            status=status,
            at_specific_date=at_specific_date,
            for_update=for_update,
        )

        return codelist_ar

    def get_all_versions(
        self, codelist_uid: str
    ) -> Optional[Iterable[_AggregateRootType]]:
        ct_codelist_root: CTCodelistRoot = CTCodelistRoot.nodes.get_or_none(
            uid=codelist_uid
        )
        if ct_codelist_root is not None:
            # pylint:disable=unnecessary-dunder-call
            ct_codelist_name_root_node = ct_codelist_root.__getattribute__(
                self.relationship_from_root
            ).single()
            versions = self.get_all_versions_2(str(ct_codelist_name_root_node.id))
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

    def codelist_exists(self, codelist_uid: str) -> bool:
        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $uid})-[:HAS_NAME_ROOT]->
            (codelist_ver_root:CTCodelistNameRoot)-[:LATEST_FINAL]->(codelist_ver_value:CTCodelistNameValue)
            RETURN codelist_root
            """
        result, _ = db.cypher_query(query, {"uid": codelist_uid})
        if len(result) > 0 and len(result[0]) > 0:
            return True
        return False

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def add_term(
        self, codelist_uid: str, term_uid: str, author: str, order: int
    ) -> None:
        """
        Method adds term identified by term_uid to the codelist identified by codelist_uid.
        Adding a term means creating a HAS_TERM relationship from CTCodelistRoot to CTTermRoot.
        When codelist identified by codelist_uid is a TemplateParameter, then the added term
        will become TemplateParameter value, which means creating HAS_VALUE relationship from
        CTCodelistNameValue to the CTTermNameRoot and labeling CTTermNameRoot as TemplateParameterValueRoot
        and CTTermNameValue as TemplateParameterValue.
        :param codelist_uid:
        :param term_uid:
        :param author:
        :param order:
        :return None:
        """
        ct_codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
        if ct_codelist_node is None:
            raise ValueError(
                f"The codelist identified by {codelist_uid} was not found."
            )

        ct_term_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_node is None:
            raise ValueError(f"The term identified by {term_uid} was not found.")

        for ct_term_end_node in ct_codelist_node.has_term.all():
            if ct_term_end_node.uid == term_uid:
                raise ValueError(
                    f"The codelist identified by {codelist_uid} "
                    f"already has a term identified by {term_uid}"
                )

        ct_codelist_node.has_term.connect(
            ct_term_node,
            {
                "start_date": datetime.now(),
                "end_date": None,
                "user_initials": author,
                "order": order,
            },
        )

        # Validate that the term is removed from a codelist that isn't in a draft state.
        attributes_root = ct_codelist_node.has_attributes_root.get_or_none()
        if attributes_root:
            has_latest_draft = attributes_root.latest_draft.get_or_none() is not None
            if has_latest_draft:
                raise VersioningException(
                    "Term '"
                    + term_uid
                    + "' cannot be added to '"
                    + codelist_uid
                    + "' as the codelist is in a draft state."
                )

        query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                (codelist_ver_value:TemplateParameter)
            WITH codelist_ver_value
            MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
            MERGE (codelist_ver_value)-[hv:HAS_VALUE]->(term_ver_root)
            SET term_ver_root:TemplateParameterValueRoot
            SET term_ver_value:TemplateParameterValue
        """
        db.cypher_query(query, {"codelist_uid": codelist_uid, "term_uid": term_uid})
        TemplateParameterValueRoot.generate_node_uids_if_not_present()

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def remove_term(self, codelist_uid: str, term_uid: str, author: str) -> None:
        """
        Method removes term identified by term_uid from the codelist identified by codelist_uid.
        Removing a term means deleting existing HAS_TERM relationship from CTCodelistRoot to CTTermRoot and
        creating HAD_TERM relationship from CTCodelistRoot to CTTermRoot.
        When term that is being removed is a TemplateParameter value, then also HAS_VALUE relationship from
        CTCodelistNameValue node to the CTTermNameRoot node is deleted. We leave the TemplateParameterValueRoot
        and templateParameterValue labels as other codelist may use that term as TemplateParameter value.
        :param codelist_uid:
        :param term_uid:
        :param author:
        :return None:
        """
        ct_codelist_node = CTCodelistRoot.nodes.get_or_none(uid=codelist_uid)
        if ct_codelist_node is None:
            raise ValueError(
                f"The codelist identified by {codelist_uid} was not found."
            )

        ct_term_node = CTTermRoot.nodes.get_or_none(uid=term_uid)
        if ct_term_node is None:
            raise ValueError(f"The term identified by {term_uid} was not found.")

        for ct_term_end_node in ct_codelist_node.has_term.all():
            if ct_term_end_node.uid == term_uid:
                has_term_relationship: CodelistTermRelationship = (
                    ct_codelist_node.has_term.relationship(ct_term_node)
                )
                ct_codelist_node.has_term.disconnect(ct_term_node)
                ct_codelist_node.had_term.connect(
                    ct_term_node,
                    {
                        "start_date": has_term_relationship.start_date,
                        "end_date": datetime.now(),
                        "user_initials": author,
                        "order": has_term_relationship.order,
                    },
                )

                # Validate that the term is removed from a codelist that isn't in a draft state.
                attributes_root = ct_codelist_node.has_attributes_root.get_or_none()
                if attributes_root:
                    has_latest_draft = (
                        attributes_root.latest_draft.get_or_none() is not None
                    )
                    if has_latest_draft:
                        raise VersioningException(
                            "Term '"
                            + term_uid
                            + "' cannot be removed from '"
                            + codelist_uid
                            + "' as the codelist is in a draft state."
                        )

                query = """
                    MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                        (codelist_ver_value:TemplateParameter)-[r:HAS_VALUE]-(term_ver_root)
                    DELETE r
                """
                db.cypher_query(query, {"codelist_uid": codelist_uid})
                break
        else:
            raise ValueError(
                f"The codelist identified by {codelist_uid} doesn't have a term identified by {term_uid}"
            )

    def _is_repository_related_to_ct(self) -> bool:
        """
        The method created to allow CTCodelistGenericRepository interface to handle filtering by package
        in different way for CTCodelistAttributesRepository and for CTCodelistNameRepository.
        :return bool:
        """
        return True

    def get_codelist_etag_value(self, codelist_uid: str) -> Optional[str]:
        """
        Method created to get etag for codelist identified by codelist_uid
        that can be used to verify if given codelist was changed.
        :param codelist_uid:
        :return str:
        """
        query = f"""
        MATCH (codelist_root:CTCodelistRoot {{uid: $codelist_uid}})-[:{cast(str, self.relationship_from_root).upper()}]-
        (codelist_ver_root)-[:LATEST]-(codelist_ver_value)
        MATCH (codelist_ver_root)-[version]->(codelist_ver_value)
        RETURN max(version.start_date)
        """
        result, _ = db.cypher_query(query, {"codelist_uid": codelist_uid})
        if len(result[0]) > 0 and result[0][0] is not None:
            return str(convert_to_datetime(result[0][0]))
        return None
