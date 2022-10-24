from typing import Optional, Sequence, Tuple

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR, ActivityVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityRoot,
    ActivitySubGroupRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.models.activities.activity import Activity


class ActivityRepository(ConceptGenericRepository[ActivityAR]):

    root_class = ActivityRoot
    value_class = ActivityValue
    return_model = Activity

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> ActivityAR:
        major, minor = input_dict.get("version").split(".")
        return ActivityAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivityVO.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("nameSentenceCase"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_sub_group=input_dict.get("activitySubGroup").get("uid"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("changeDescription"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("userInitials"),
                start_date=convert_to_datetime(value=input_dict.get("startDate")),
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
    ) -> ActivityAR:
        sub_group_value = value.in_sub_group.get_or_none()
        if sub_group_value is not None:
            sub_group = sub_group_value.has_latest_value.get_or_none().uid
        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_sub_group=sub_group,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return """
        WITH *,
            head([(concept_value)-[:IN_SUB_GROUP]->(activity_sub_group_value:ActivitySubGroupValue)<-[:LATEST]-
            (activity_sub_group_root:ActivitySubGroupRoot) | {uid:activity_sub_group_root.uid, name:activity_sub_group_value.name}]) AS activitySubGroup,
            head([(concept_value)-[:IN_SUB_GROUP]->(:ActivitySubGroupValue)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)<-[:LATEST]-
            (activity_group_root:ActivityGroupRoot) | {uid:activity_group_root.uid, name:activity_group_value.name}]) AS activityGroup
        """

    def create_query_filter_statement(
        self, library: Optional[str] = None, **kwargs
    ) -> Tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activitySubGroupUid") is not None:
            activity_sub_group_uid = kwargs.get("activitySubGroupUid")
            filter_by_activity_sub_group_uid = """
            $activity_sub_group_uid= 
            head([(concept_value)-[:IN_SUB_GROUP]->(activity_sub_group_value:ActivitySubGroupValue)<-[:LATEST]-(activity_sub_group_root:ActivitySubGroupRoot) 
                | activity_sub_group_root.uid])"""
            filter_parameters.append(filter_by_activity_sub_group_uid)
            filter_query_parameters["activity_sub_group_uid"] = activity_sub_group_uid
        if kwargs.get("activityNames") is not None:
            activity_names = kwargs.get("activityNames")
            filter_by_activity_names = "concept_value.name IN $activity_names"
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activitySubGroupNames") is not None:
            activity_sub_group_names = kwargs.get("activitySubGroupNames")
            filter_by_activity_sub_group_names = """
            size([(concept_value)-[:IN_SUB_GROUP]->(v:ActivitySubGroupValue) WHERE v.name IN $activity_sub_group_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_sub_group_names)
            filter_query_parameters[
                "activity_sub_group_names"
            ] = activity_sub_group_names
        if kwargs.get("activityGroupNames") is not None:
            activity_group_names = kwargs.get("activityGroupNames")
            filter_by_activity_group_names = """
            size([(concept_value)-[:IN_SUB_GROUP]->(:ActivitySubGroupValue)
            -[:IN_GROUP]->(v:ActivityGroupValue) WHERE v.name IN $activity_group_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
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

    def _create_new_value_node(self, ar: ActivityAR) -> ActivityValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()
        sub_group_root = ActivitySubGroupRoot.nodes.get_or_none(
            uid=ar.concept_vo.activity_sub_group
        )
        sub_group_value = sub_group_root.has_latest_value.get_or_none()
        value_node.in_sub_group.connect(sub_group_value)
        return value_node

    def _has_data_changed(self, ar: ActivityAR, value: ActivityValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_rels_changed = False
        sub_group = value.in_sub_group.get_or_none()
        if sub_group is not None:
            sub_group_uid = sub_group.has_latest_value.get_or_none().uid
            are_rels_changed = ar.concept_vo.activity_sub_group != sub_group_uid
        return are_concept_properties_changed or are_rels_changed

    def get_template_activities(
        self, root_class: type, template_uid: str
    ) -> Optional[Sequence[ActivityAR]]:
        """
        This method returns the activities for the template with provided uid

        :param root_class: The class of the root node for the template
        :param template_uid: UID of the template
        :return Sequence[ActivityAR]:
        """
        template = root_class.nodes.get(uid=template_uid)
        activity_nodes = template.has_activity.all()
        if activity_nodes:
            activities = []
            for node in activity_nodes:
                activity = self.find_by_uid_2(uid=node.uid)
                activities.append(activity)
            return activities
        return None
