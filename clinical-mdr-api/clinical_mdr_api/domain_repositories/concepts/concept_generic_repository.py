from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.concepts.utils import RelationType
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.utils import (
    list_concept_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmXmlExtensionAttributeRoot,
    OdmXmlExtensionTagRoot,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)
from clinical_mdr_api.repositories._utils import (
    ComparisonOperator,
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)
from clinical_mdr_api.services._utils import strip_suffix


class ConceptGenericRepository(LibraryItemRepositoryImplBase[_AggregateRootType], ABC):

    root_class = type
    value_class = type
    return_model = type

    @abstractmethod
    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abstractmethod
    def specific_alias_clause(self) -> str:
        """
        Methods is overridden in the ConceptGenericRepository subclasses
        and it contains matches and traversals specific for domain object represented by subclass repository.
        :return str:
        """

    def specific_header_match_clause(self) -> Optional[str]:
        return None

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        return self.value_class(
            name=ar.concept_vo.name,
            name_sentence_case=ar.concept_vo.name_sentence_case,
            definition=ar.concept_vo.definition,
            abbreviation=ar.concept_vo.abbreviation,
        )

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        return (
            ar.concept_vo.name != value.name
            or ar.concept_vo.name_sentence_case != value.name_sentence_case
            or ar.concept_vo.definition != value.definition
            or ar.concept_vo.abbreviation != value.abbreviation
        )

    def generate_uid(self) -> str:
        return self.root_class.get_next_free_uid_and_increment_counter()

    def generic_match_clause(self):
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__
        return f"""CYPHER runtime=slotted MATCH (concept_root:{concept_label})-[:LATEST]->(concept_value:{concept_value_label})"""

    def generic_alias_clause(self):
        return """
            DISTINCT concept_root, concept_value,
            head([(concept_root)-[ld:LATEST_DRAFT]->(concept_value) | ld]) AS ld,
            head([(concept_root)-[lf:LATEST_FINAL]->(concept_value) | lf]) AS lf,
            head([(concept_root)-[lr:LATEST_RETIRED]->(concept_value) | lr]) AS lr,
            head([(concept_root)-[hv:HAS_VERSION]->(concept_value) | hv]) AS hv,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            WITH
                concept_root.uid AS uid,
                concept_value as concept_value,
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
                uid,
                concept_value.name AS name,
                case 
                    when (concept_value:ReminderValue) then "reminders"
                    when (concept_value:CompoundValue) then "compounds"
                    when (concept_value:CompoundDosingValue) then "compound-dosings"
                    when (concept_value:SpecialPurposeValue) then "special-purposes"
                    when (concept_value:RatingScaleValue) then "rating-scales"
                    when (concept_value:LaboratoryActivityValue) then "laboratory-activities"
                    when (concept_value:CategoricFindingValue) then "categoric-findings"
                    when (concept_value:NumericFindingValue) then "numeric-findings"
                    when (concept_value:TextualFindingValue) then "textual-findings"
                    when (concept_value:EventValue) then "events"
                    else ""
                end as type,
                concept_value.name_sentence_case AS nameSentenceCase,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterValue THEN true ELSE false END AS templateParameter,
                libraryName,
                is_library_editable,
                value.version_rel.start_date AS startDate,
                value.version_rel.status AS status,
                value.version_rel.version AS version,
                value.version_rel.change_description AS changeDescription,
                value.version_rel.user_initials AS userInitials,
                concept_value
        """

    def create_query_filter_statement(
        self, library: Optional[str] = None, **kwargs
    ) -> Tuple[str, dict]:
        # pylint: disable=unused-argument
        filter_parameters = []
        filter_query_parameters = {}
        if library:
            filter_by_library_name = """
            head([(library:Library)-[:CONTAINS_CONCEPT]->(concept_root) | library.name])=$library_name"""
            filter_parameters.append(filter_by_library_name)
            filter_query_parameters["library_name"] = library
        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

    def find_all(
        self,
        library: Optional[str] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
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
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause()

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

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

    def _retrieve_concepts_from_cypher_res(
        self, result_array, attribute_names
    ) -> Sequence[_AggregateRootType]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        concept_ars = []
        for concept in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(concept, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            concept_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary
                )
            )

        return concept_ars

    def get_distinct_headers(
        self,
        field_name: str,
        search_string: Optional[str] = "",
        library: Optional[str] = None,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
        **kwargs,
    ) -> Sequence:
        # pylint: disable=unused-argument
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of result_count.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param library:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param result_count: Max number of values to return. Default 10
        :return Sequence:
        """
        # Match clause
        match_clause = self.generic_match_clause()
        if self.specific_header_match_clause():
            match_clause += self.specific_header_match_clause()

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        # Aliases clause
        alias_clause = self.generic_alias_clause() + self.specific_alias_clause()

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
            return_model=self.return_model,
            wildcard_properties_list=list_concept_wildcard_properties(
                self.return_model
            ),
        )

        query.parameters.update(filter_query_parameters)

        header_query = query.build_header_query(
            header_alias=field_name, result_count=result_count
        )
        result_array, _ = db.cypher_query(query=header_query, params=query.parameters)

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.uid is not None and item.repository_closure_data is None:
            self._create(item)
        elif item.uid is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)

    def _soft_delete(self, uid: str) -> None:
        label = self.root_class.__label__
        db.cypher_query(
            f"""
            MATCH (otr:{label} {{uid: $uid}})-[latest:LATEST_DRAFT|LATEST_RETIRED]->(otv)
            WHERE NOT (otr)-[:LATEST_FINAL|HAS_VERSION {{version:'Final'}}]->()
            CREATE (otr)-[v:HAS_VERSION]->(otv)
            SET v = latest,
                v.end_date = datetime(apoc.date.toISO8601(datetime().epochSeconds, 's'))
            SET otr:Deleted{label}
            REMOVE otr:{label}
            """,
            {"uid": uid},
        )

    def final_concept_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        return len(result) > 0 and len(result[0]) > 0

    def concept_exists_by_name(self, name: str) -> bool:
        return self.exists_by("name", name)

    def _is_new_version_necessary(self, ar: ConceptARBase, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
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
        new_value = self._create_new_value_node(ar=ar)
        self._db_save_node(new_value)
        return new_value

    @classmethod
    def is_concept_node_a_tp(cls, concept_node: VersionValue) -> bool:
        labels = concept_node.labels()
        for label in labels:
            if "TemplateParameterValue" in label:
                return True
        return False

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:

        if versioned_object.concept_vo.is_template_parameter:
            # neomodel can't add custom label to already existing node, we have to manage that by executing cypher query
            template_parameter_name = self.root_class.__name__[
                : len(self.root_class.__name__) - len("Root")
            ]
            # we want to initiate a Comparator TemplateParameter type with the same template parameter values as we do
            # for Compound TemplateParameter
            if template_parameter_name == "Compound":
                template_parameter_names = [template_parameter_name, "Comparator"]
            else:
                template_parameter_names = [template_parameter_name]
            for template_param_name in template_parameter_names:
                query = """
                    MATCH (template_parameter:TemplateParameter {name:$template_parameter_name})
                    MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                    SET concept_root:TemplateParameterValueRoot
                    SET concept_value:TemplateParameterValue
                    MERGE (template_parameter)-[:HAS_VALUE]->(concept_root)
                """
                db.cypher_query(
                    query,
                    {
                        "uid": versioned_object.uid,
                        "template_parameter_name": template_param_name,
                    },
                )
                TemplateParameterValueRoot.generate_node_uids_if_not_present()

    @classmethod
    def _get_origin_and_relation_node(
        cls, uid: str, relation_uid: Optional[str], relationship_type: RelationType
    ):
        root_class_node = cls.root_class.nodes.get_or_none(uid=uid)

        if relationship_type == RelationType.ACTIVITY_GROUP:
            relation_node = ActivityGroupRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_activity_group
        elif relationship_type == RelationType.ACTIVITY_SUB_GROUP:
            relation_node = ActivitySubGroupRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_activity_sub_group
        elif relationship_type == RelationType.ACTIVITY:
            relation_node = ActivityRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_activity
        elif relationship_type == RelationType.ITEM_GROUP:
            relation_node = OdmItemGroupRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.item_group_ref
        elif relationship_type == RelationType.ITEM:
            relation_node = OdmItemRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.item_ref
        elif relationship_type == RelationType.FORM:
            relation_node = OdmFormRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.form_ref
        elif relationship_type == RelationType.TERM:
            relation_node = CTTermRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_codelist_term
        elif relationship_type == RelationType.UNIT_DEFINITION:
            relation_node = UnitDefinitionRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_unit_definition
        elif relationship_type == RelationType.XML_EXTENSION_TAG:
            relation_node = OdmXmlExtensionTagRoot.nodes.get_or_none(uid=relation_uid)
            origin = root_class_node.has_xml_extension_tag
        elif relationship_type == RelationType.XML_EXTENSION_ATTRIBUTE:
            relation_node = OdmXmlExtensionAttributeRoot.nodes.get_or_none(
                uid=relation_uid
            )
            origin = root_class_node.has_xml_extension_attribute
        elif relationship_type == RelationType.XML_EXTENSION_TAG_ATTRIBUTE:
            relation_node = OdmXmlExtensionAttributeRoot.nodes.get_or_none(
                uid=relation_uid
            )
            origin = root_class_node.has_xml_extension_tag_attribute
        else:
            raise exceptions.BusinessLogicException("Invalid relation type.")

        if not relation_node and relation_uid:
            raise exceptions.BusinessLogicException(
                f"The object with uid ({relation_uid}) does not exist."
            )

        return origin, relation_node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def add_relation(
        self,
        uid: str,
        relation_uid: str,
        relationship_type: RelationType,
        parameters: dict = None,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        origin.disconnect(relation_node)

        if isinstance(parameters, dict):
            origin.connect(relation_node, parameters)
        else:
            origin.connect(relation_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def remove_relation(
        self,
        uid: str,
        relation_uid: Optional[str],
        relationship_type: RelationType,
        disconnect_all: bool = False,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        if disconnect_all:
            origin.disconnect_all()
        else:
            origin.disconnect(relation_node)

    def has_active_relationships(
        self, uid: str, relationships: list, all_exist: bool = False
    ) -> bool:
        """
        Checks if the node has active relationships.

        :param uid: The uid of the node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :param all_exist: If True, all provided relationships must exist on the node. If False, at least one of the provided relationships must exist.
        :return: Returns True, if the relationships exist, otherwise False.
        """
        root = self.root_class.nodes.get_or_none(uid=uid)

        try:
            if not all_exist:
                for relationship in relationships:
                    if getattr(root, relationship):
                        return True

                return False
            for relationship in relationships:
                if not getattr(root, relationship):
                    return False

            return True
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc

    def get_active_relationships(
        self, uid: str, relationships: list
    ) -> Dict[str, List[str]]:
        """
        Returns a key-pair value of target node's name and a list of uids of nodes connected to source node.

        :param uid: The uid of the source node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :return: Returns a dict.
        """
        source_node = self.root_class.nodes.get_or_none(uid=uid)

        try:
            rs: dict[str, List[str]] = {}
            for relationship in relationships:
                rel = getattr(source_node, relationship)
                if rel:
                    for target_node in rel.all():
                        target_node_without_suffix = strip_suffix(target_node.__label__)
                        if target_node_without_suffix not in rs:
                            rs[target_node_without_suffix] = [target_node.uid]
                        else:
                            rs[target_node_without_suffix].append(target_node.uid)
            return rs
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc
