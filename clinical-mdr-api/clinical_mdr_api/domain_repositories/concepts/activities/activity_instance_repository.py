from typing import Optional, Tuple

from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceVO,
)
from clinical_mdr_api.domain.concepts.concept_base import _AggregateRootType
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
    ActivityDefinition,
    ActivityInstanceRoot,
    ActivityInstanceValue,
    ActivityRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.models.activities.activity_instance import ActivityInstance


class ActivityInstanceRepository(ConceptGenericRepository[ActivityInstanceAR]):

    root_class = ActivityInstanceRoot
    value_class = ActivityInstanceValue
    aggregate_class = ActivityInstanceAR
    value_object_class = ActivityInstanceVO
    return_model = ActivityInstance

    def _get_uid_or_none(self, node):
        return node.uid if node is not None else None

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

    def _create_activity_definition(
        self, value_node: VersionValue
    ) -> ActivityDefinition:
        activity_definition = ActivityDefinition()
        activity_definition.save()
        value_node.defined_by.connect(activity_definition)
        return activity_definition

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.topic_code = ar.concept_vo.topic_code
        value_node.adam_param_code = ar.concept_vo.adam_param_code
        value_node.legacy_description = ar.concept_vo.legacy_description

        value_node.save()

        # TODO : Update when distinction between ActivityDefinition and ActivityCollection is defined
        if ar.concept_vo.sdtm_variable_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_sdtm_variable.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.sdtm_variable_uid)
            )

        # TODO : Uncomment when distinction between ActivityDefinition and ActivityCollection is defined
        # if ar.concept_vo.cdash_variable_uid is not None:
        #     activity_definition = self._create_activity_definition(value_node)
        #     activity_definition.has_cdash_variable.connect(
        #         CTTermRoot.nodes.get(uid=ar.concept_vo.cdash_variable_uid)
        #     )

        if ar.concept_vo.sdtm_subcat_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_sdtm_subcat.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.sdtm_subcat_uid)
            )

        if ar.concept_vo.sdtm_cat_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_sdtm_cat.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.sdtm_cat_uid)
            )

        if ar.concept_vo.sdtm_domain_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_sdtm_domain.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.sdtm_domain_uid)
            )

        for activity_uid in ar.concept_vo.activity_uids:
            activity_hierarchy_value = ActivityRoot.nodes.get(
                uid=activity_uid
            ).has_latest_value.get()
            value_node.in_hierarchy.connect(activity_hierarchy_value)
        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.topic_code != value.topic_code
            or ar.concept_vo.adam_param_code != value.adam_param_code
            or ar.concept_vo.legacy_description != value.legacy_description
        )

        activity_uids = [
            activity.has_latest_value.get().uid for activity in value.in_hierarchy.all()
        ]

        are_rels_changed = (
            ar.concept_vo.sdtm_variable_uid
            != self._get_uid_or_none(self._get_sdtm_variable(value))
            or ar.concept_vo.sdtm_subcat_uid
            != self._get_uid_or_none(self._get_sdtm_subcat(value))
            or ar.concept_vo.sdtm_cat_uid
            != self._get_uid_or_none(self._get_sdtm_cat(value))
            or ar.concept_vo.sdtm_domain_uid
            != self._get_uid_or_none(self._get_sdtm_domain(value))
            or ar.concept_vo.activity_uids != activity_uids
        )
        return are_concept_properties_changed or are_props_changed or are_rels_changed

    def _get_item_name_and_uid(
        self, item: dict, key: str
    ) -> Tuple[Optional[str], Optional[str]]:
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
        sdtm_variable_name, sdtm_variable_uid = self._get_item_name_and_uid(
            input_dict, "sdtmVariable"
        )
        sdtm_subcat_name, sdtm_subcat_uid = self._get_item_name_and_uid(
            input_dict, "sdtmSubcat"
        )
        sdtm_cat_name, sdtm_cat_uid = self._get_item_name_and_uid(input_dict, "sdtmCat")
        sdtm_domain_name, sdtm_domain_uid = self._get_item_name_and_uid(
            input_dict, "sdtmDomain"
        )
        specimen_name, specimen_uid = self._get_item_name_and_uid(
            input_dict, "specimen"
        )
        return self.aggregate_class.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=self.value_object_class.from_repository_values(
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("nameSentenceCase"),
                activity_type=input_dict.get("type"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                topic_code=input_dict.get("topicCode"),
                adam_param_code=input_dict.get("adamParamCode"),
                legacy_description=input_dict.get("legacyDescription"),
                sdtm_variable_uid=sdtm_variable_uid,
                sdtm_variable_name=sdtm_variable_name,
                sdtm_subcat_uid=sdtm_subcat_uid,
                sdtm_subcat_name=sdtm_subcat_name,
                sdtm_cat_uid=sdtm_cat_uid,
                sdtm_cat_name=sdtm_cat_name,
                sdtm_domain_uid=sdtm_domain_uid,
                sdtm_domain_name=sdtm_domain_name,
                activity_uids=input_dict.get("activities", {}),
                specimen_uid=specimen_uid,
                specimen_name=specimen_name,
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
    ) -> ActivityInstanceAR:
        sdtm_variable = self._get_sdtm_variable(value)
        sdtm_subcat = self._get_sdtm_subcat(value)
        sdtm_cat = self._get_sdtm_cat(value)
        sdtm_domain = self._get_sdtm_domain(value)
        specimen = self._get_specimen(value)
        return self.aggregate_class.from_repository_values(
            uid=root.uid,
            concept_vo=self.value_object_class.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                activity_type=value.activity_type(),
                definition=value.definition,
                abbreviation=value.abbreviation,
                topic_code=value.topic_code,
                adam_param_code=value.adam_param_code,
                legacy_description=value.legacy_description,
                sdtm_variable_uid=self._get_uid_or_none(sdtm_variable),
                sdtm_subcat_uid=self._get_uid_or_none(sdtm_subcat),
                sdtm_cat_uid=self._get_uid_or_none(sdtm_cat),
                sdtm_domain_uid=self._get_uid_or_none(sdtm_domain),
                sdtm_variable_name=self._get_name_or_none(sdtm_variable),
                sdtm_subcat_name=self._get_name_or_none(sdtm_subcat),
                sdtm_cat_name=self._get_name_or_none(sdtm_cat),
                sdtm_domain_name=self._get_name_or_none(sdtm_domain),
                specimen_uid=self._get_uid_or_none(specimen),
                specimen_name=self._get_name_or_none(specimen),
                activity_uids=[
                    activity.has_latest_value.get().uid
                    for activity in value.in_hierarchy.all()
                ],
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
            concept_value.topic_code AS topicCode,
            concept_value.adam_param_code AS adamParamCode,
            concept_value.legacy_description AS legacyDescription,
            
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:TABULATED_IN]->(sdtm_variable_term)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) | {uid:sdtm_variable_term.uid, name: value.name}]) AS sdtmVariable,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_SUBCAT]->(sdtm_subcat_term)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) | {uid:sdtm_subcat_term.uid, name: value.name}]) AS sdtmSubcat,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_CAT]->(sdtm_cat_term)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) | {uid:sdtm_cat_term.uid, name: value.name}]) AS sdtmCat,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_DOMAIN]->(sdtm_domain_term)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) | {uid:sdtm_domain_term.uid, name: value.name}]) AS sdtmDomain,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SPECIMEN]->(specimen_term)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) | {uid:specimen_term.uid, name: value.name}]) AS specimen,
            [(concept_value)-[:IN_HIERARCHY]->(activity_hierarchy_value)<-[:LATEST]-(activity_hierarchy_root) 
                | activity_hierarchy_root.uid] AS activities
        """

    def create_query_filter_statement(
        self, library: Optional[str] = None, **kwargs
    ) -> Tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        # TODO Add sdtmDomain, sdtmVariable, sdtmCat, sdtmSubcat
        if kwargs.get("activityNames") is not None:
            activity_names = kwargs.get("activityNames")
            filter_by_activity_names = """
            size([(concept_value)-[:IN_HIERARCHY]->(activity_hierarchy_value) WHERE activity_hierarchy_value.name IN $activity_names | activity_hierarchy_value.name]) > 0"""
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("specimenNames") is not None:
            specimen_names = kwargs.get("specimenNames")
            filter_by_specimen_names = """
            size([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SPECIMEN]->(sp)-[:HAS_NAME_ROOT]->(nameroot)-[:LATEST]->(name) WHERE name.name IN $specimen_names | name.name]) > 0"""
            filter_parameters.append(filter_by_specimen_names)
            filter_query_parameters["specimen_names"] = specimen_names
        if kwargs.get("sdtmVariableNames") is not None:
            sdtm_variable_names = kwargs.get("sdtmVariableNames")
            filter_by_sdtm_variable_names = """
            size([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:TABULATED_IN]->(sdtm_var)-[:HAS_NAME_ROOT]->(nameroot)-[:LATEST]->(name) WHERE name.name IN $sdtm_variable_names | name.name]) > 0"""
            filter_parameters.append(filter_by_sdtm_variable_names)
            filter_query_parameters["sdtm_variable_names"] = sdtm_variable_names
        if kwargs.get("sdtmCatergoryNames") is not None:
            sdtm_category_names = kwargs.get("sdtmCatergoryNames")
            filter_by_sdtm_category_names = """
            size([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_CAT]->(sdtm_cat)-[:HAS_NAME_ROOT]->(nameroot)-[:LATEST]->(name) WHERE name.name IN $sdtm_category_names | name.name]) > 0"""
            filter_parameters.append(filter_by_sdtm_category_names)
            filter_query_parameters["sdtm_category_names"] = sdtm_category_names
        if kwargs.get("sdtmSubCatergoryNames") is not None:
            sdtm_sub_category_names = kwargs.get("sdtmSubCatergoryNames")
            filter_by_sdtm_sub_category_names = """
            size([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_SUBCAT]->(sdtm_cat)-[:HAS_NAME_ROOT]->(nameroot)-[:LATEST]->(name) WHERE name.name IN $sdtm_sub_category_names | name.name]) > 0"""
            filter_parameters.append(filter_by_sdtm_sub_category_names)
            filter_query_parameters["sdtm_sub_category_names"] = sdtm_sub_category_names
        if kwargs.get("sdtmDomainNames") is not None:
            sdtm_domain_names = kwargs.get("sdtmDomainNames")
            filter_by_sdtm_domain_names = """
            size([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_SDTM_DOMAIN]->(sdtm_domain)-[:HAS_NAME_ROOT]->(nameroot)-[:LATEST]->(name) WHERE name.name IN $sdtm_domain_names | name.name]) > 0"""
            filter_parameters.append(filter_by_sdtm_domain_names)
            filter_query_parameters["sdtm_domain_names"] = sdtm_domain_names
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

    def _get_sdtm_domain(
        self, value: ActivityInstanceValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            domain = definition.has_sdtm_domain.get_or_none()
            if domain is not None:
                return domain
        return None

    def _get_sdtm_cat(
        self, value: ActivityInstanceValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            cat = definition.has_sdtm_cat.get_or_none()
            if cat is not None:
                return cat
        return None

    def _get_sdtm_subcat(
        self, value: ActivityInstanceValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            subcat = definition.has_sdtm_subcat.get_or_none()
            if subcat is not None:
                return subcat
        return None

    def _get_sdtm_variable(
        self, value: ActivityInstanceValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            variable = definition.has_sdtm_variable.get_or_none()
            if variable is not None:
                return variable
        return None

    def _get_specimen(
        self, value: ActivityInstanceValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            specimen = definition.has_findings_specimen.get_or_none()
            if specimen is not None:
                return specimen
        return None
