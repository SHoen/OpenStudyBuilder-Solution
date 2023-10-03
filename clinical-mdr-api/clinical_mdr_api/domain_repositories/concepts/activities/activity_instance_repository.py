from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    convert_to_datetime,
    to_relation_trees,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityInstanceRoot,
    ActivityInstanceValue,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityItemRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceGroupingVO,
    ActivityInstanceVO,
    SimpleActivityItemVO,
)
from clinical_mdr_api.domains.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)


class ActivityInstanceRepository(ConceptGenericRepository[ActivityInstanceAR]):
    root_class = ActivityInstanceRoot
    value_class = ActivityInstanceValue
    aggregate_class = ActivityInstanceAR
    value_object_class = ActivityInstanceVO
    return_model = ActivityInstance

    def _get_name_or_none(self, node):
        if node is None:
            return None
        name_root = node.has_name_root.get_or_none()
        if name_root is None:
            return None
        name_value = name_root.has_latest_value.get_or_none()
        if name_value is None:
            return None
        return name_value.name

    def _create_new_value_node(self, ar: _AggregateRootType) -> ActivityInstanceValue:
        value_node: ActivityInstanceValue = super()._create_new_value_node(ar=ar)
        value_node.topic_code = ar.concept_vo.topic_code
        value_node.adam_param_code = ar.concept_vo.adam_param_code
        value_node.legacy_description = ar.concept_vo.legacy_description

        value_node.save()

        for activity_grouping in ar.concept_vo.activity_groupings:
            # find related ActivityGrouping node
            activity_grouping_node = to_relation_trees(
                ActivityGrouping.nodes.filter(
                    in_subgroup__in_group__has_latest_value__uid=activity_grouping.activity_group_uid,
                    in_subgroup__has_group__has_latest_value__uid=activity_grouping.activity_subgroup_uid,
                    has_grouping__has_latest_value__uid=activity_grouping.activity_uid,
                )
            ).distinct()
            if len(activity_grouping_node) == 0:
                raise BusinessLogicException(
                    f"The ActivityValidGroup node wasn't found for subgroup ({activity_grouping.activity_subgroup_uid}) "
                    f"and group ({activity_grouping.activity_group_uid})"
                )
            activity_grouping_node = activity_grouping_node[0]
            # link ActivityInstanceValue with ActivityGrouping node
            value_node.has_activity.connect(activity_grouping_node)

        activity_instance_class = ActivityInstanceClassRoot.nodes.get(
            uid=ar.concept_vo.activity_instance_class_uid
        )
        value_node.activity_instance_class.connect(activity_instance_class)

        for activity_item_uid in (
            activity_item.uid for activity_item in ar.concept_vo.activity_items
        ):
            activity_item_value = ActivityItemRoot.nodes.get(
                uid=activity_item_uid
            ).has_latest_value.get()
            value_node.contains_activity_item.connect(activity_item_value)
        return value_node

    def _has_data_changed(
        self, ar: ActivityInstanceAR, value: ActivityInstanceValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.topic_code != value.topic_code
            or ar.concept_vo.adam_param_code != value.adam_param_code
            or ar.concept_vo.legacy_description != value.legacy_description
        )

        activity_subgroup_uids = []
        activity_group_uids = []
        activity_grouping_nodes = value.has_activity.all()
        for activity_grouping_node in activity_grouping_nodes:
            activity_valid_group_nodes = activity_grouping_node.in_subgroup.all()
            for activity_valid_group_node in activity_valid_group_nodes:
                activity_subgroup_uids.append(
                    activity_valid_group_node.has_group.get().has_version.single().uid
                )
                activity_group_uids.append(
                    activity_valid_group_node.in_group.get().has_version.single().uid
                )

        activity_item_uids = [
            node.has_version.single().uid for node in value.contains_activity_item.all()
        ]
        are_rels_changed = (
            ar.concept_vo.activity_instance_class_uid
            != value.activity_instance_class.get().uid
            or sorted(
                [
                    activity_grouping.activity_group_uid
                    for activity_grouping in ar.concept_vo.activity_groupings
                ]
            )
            != sorted(activity_group_uids)
            or sorted(
                [
                    activity_grouping.activity_subgroup_uid
                    for activity_grouping in ar.concept_vo.activity_groupings
                ]
            )
            != sorted(activity_subgroup_uids)
            or sorted(
                [activity_item.uid for activity_item in ar.concept_vo.activity_items]
            )
            != sorted(activity_item_uids)
        )
        return are_concept_properties_changed or are_props_changed or are_rels_changed

    def _get_item_name_and_uid(
        self, item: dict, key: str
    ) -> tuple[str | None, str | None]:
        item_value = item.get(key)
        if item_value is None:
            return (None, None)
        name = item_value.get("name")
        uid = item_value.get("uid")
        return (name, uid)

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityInstanceAR:
        major, minor = input_dict.get("version").split(".")
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=self.value_object_class.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                activity_instance_class_uid=input_dict.get(
                    "activity_instance_class"
                ).get("uid"),
                activity_instance_class_name=input_dict.get(
                    "activity_instance_class"
                ).get("name"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                topic_code=input_dict.get("topic_code"),
                adam_param_code=input_dict.get("adam_param_code"),
                legacy_description=input_dict.get("legacy_description"),
                activity_groupings=[
                    ActivityInstanceGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group_uid"),
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup_uid"
                        ),
                        activity_uid=activity_grouping.get("activity_uid"),
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                activity_items=[
                    SimpleActivityItemVO.from_repository_values(
                        uid=activity_item.get("uid"),
                        name=activity_item.get("name"),
                        activity_item_class_uid=activity_item.get(
                            "activity_item_class_uid"
                        ),
                        activity_item_class_name=activity_item.get(
                            "activity_item_class_name"
                        ),
                    )
                    for activity_item in input_dict.get("activity_items", [])
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("user_initials"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: ActivityInstanceValue,
    ) -> ActivityInstanceAR:
        activity_instance_class = value.activity_instance_class.get()
        activity_items = value.contains_activity_item.all()
        activity_item_vos = []
        for activity_item in activity_items:
            activity_item_root = activity_item.has_version.single()
            activity_item_class_root = (
                activity_item_root.has_activity_item_class.get_or_none()
            )
            activity_item_vos.append(
                SimpleActivityItemVO.from_repository_values(
                    uid=activity_item_root.uid,
                    name=activity_item.name,
                    activity_item_class_uid=activity_item_class_root.uid,
                    activity_item_class_name=activity_item_class_root.has_latest_value.get_or_none().name,
                )
            )
        activity_groupings_nodes = value.has_activity.all()
        activity_groupings = []
        for activity_grouping in activity_groupings_nodes:
            activity_valid_groups = activity_grouping.in_subgroup.all()
            for activity_valid_group in activity_valid_groups:
                activity_groupings.append(
                    {
                        "activity_group_uid": activity_valid_group.in_group.get()
                        .has_version.single()
                        .uid,
                        "activity_subgroup_uid": activity_valid_group.has_group.get()
                        .has_version.single()
                        .uid,
                        "activity_uid": activity_grouping.has_grouping.get()
                        .has_version.single()
                        .uid,
                    }
                )
        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            concept_vo=self.value_object_class.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                activity_instance_class_uid=activity_instance_class.uid,
                activity_instance_class_name=activity_instance_class.has_latest_value.get().name,
                definition=value.definition,
                abbreviation=value.abbreviation,
                topic_code=value.topic_code,
                adam_param_code=value.adam_param_code,
                legacy_description=value.legacy_description,
                activity_groupings=[
                    ActivityInstanceGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group_uid"),
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup_uid"
                        ),
                        activity_uid=activity_grouping.get("activity_uid"),
                    )
                    for activity_grouping in activity_groupings
                ],
                activity_items=activity_item_vos,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self) -> str:
        return """
        WITH *,
            concept_value.topic_code AS topic_code,
            concept_value.adam_param_code AS adam_param_code,
            concept_value.legacy_description AS legacy_description,
            
            head([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
                | {uid:activity_instance_class_root.uid, name:activity_instance_class_value.name}]) AS activity_instance_class,
            [(concept_value)-[:CONTAINS_ACTIVITY_ITEM]->
            (activity_item_value:ActivityItemValue)<-[:HAS_VERSION]-(activity_item_root:ActivityItemRoot)
            <-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
                | {
                    uid:activity_item_root.uid, 
                    name:activity_item_value.name,
                    activity_item_class_uid:activity_item_class_root.uid,
                    activity_item_class_name:activity_item_class_value.name
                }] AS activity_items,
            apoc.coll.toSet([(concept_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
             | {
                 activity_uid: head([(activity_grouping)<-[:HAS_GROUPING]-(activity_value)<-[:HAS_VERSION]-(activity_root) | activity_root.uid]),
                 activity_subgroup_uid:activity_subgroup_root.uid, 
                 activity_group_uid: head([(activity_valid_group)-[:IN_GROUP]->(:ActivityGroupValue)
                 <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid])
             }]) AS activity_groupings
        """

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = (
                "size([(concept_value)-[:HAS_ACTIVITY]->(:ActivityGrouping)<-[:HAS_GROUPING]-(activity_hierarchy_value) "
                "WHERE activity_hierarchy_value.name IN $activity_names | activity_hierarchy_value.name]) > 0"
            )
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_instance_class_names") is not None:
            instance_class_names = kwargs.get("activity_instance_class_names")
            filter_by_instance_classes = (
                "size([(concept_value)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)"
                "-[:LATEST]->(instance_class_value:ActivityInstanceClassValue)"
                "WHERE instance_class_value.name IN $activity_instance_class_names | instance_class_value.name]) > 0"
            )
            filter_parameters.append(filter_by_instance_classes)
            filter_query_parameters[
                "activity_instance_class_names"
            ] = instance_class_names
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def get_activity_instance_overview(self, uid: str) -> dict:
        query = """
        MATCH (activity_instance_root:ActivityInstanceRoot {uid:$uid})-[:LATEST]->(activity_instance_value:ActivityInstanceValue)
        WITH activity_instance_root,activity_instance_value,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]) AS instance_library_name,
            head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) 
            | activity_instance_class_value]) AS activity_instance_class
        WITH *,
            [(activity_instance_value)-[:HAS_ACTIVITY]->(activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue) | 
                {
                    activity_value: activity_value,
                    activity_library_name: head([(activity_value:ActivityValue)<-[:HAS_VERSION]-(activity_root:ActivityRoot)<-[:CONTAINS_CONCEPT]-(library) 
                    | library.name]),
                    activity_subgroup_value:head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->
                    (activity_valid_group:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) 
                        | activity_subgroup_value]), 
                    activity_group_value:head([(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group)-[:IN_GROUP]->(activity_group_value) 
                        | activity_group_value])
                }
            ] AS hierarchy,
            apoc.coll.toSet([(activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->(activity_item_value)<-[:HAS_VERSION]-(activity_item_root)
            <-[HAS_ACTIVITY_ITEM]-(activity_item_class_root)-[:LATEST]->(activity_item_class_value) | 
            {
                name: activity_item_value.name,
                activity_item_class: activity_item_class_value,
                activity_item_class_role: head([(activity_item_class_value)-[:HAS_ROLE]->()-[:HAS_NAME_ROOT]->()-[:LATEST]->(role_value) | role_value.name]),
                activity_item_class_data_type: head([(activity_item_class_value)-[:HAS_DATA_TYPE]->()-[:HAS_NAME_ROOT]->()-[:LATEST]->(data_type_value) | data_type_value.name]),
                activity_item: activity_item_value,
                ct_term: head([(activity_item_value)-[:HAS_CT_TERM]->(term_root)-[:HAS_NAME_ROOT]->(term_name_root)-[:LATEST]->(term_name_value) | term_name_value]),
                unit_definition: head([(activity_item_value)-[:HAS_UNIT_DEFINITION]->(unit_definition_root)-[:LATEST]->(unit_definition_value) | unit_definition_value])
            }
            ]) AS activity_items
        WITH DISTINCT 
            activity_instance_value,
            instance_library_name,
            activity_instance_class,
            hierarchy,
            apoc.coll.sortMaps(activity_items, '^name') as activity_items
        RETURN *
        """
        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": uid}
        )
        if len(result_array) != 1:
            raise exceptions.BusinessLogicException(
                f"The overview query returned broken data: {result_array}"
            )
        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop
        return overview_dict
