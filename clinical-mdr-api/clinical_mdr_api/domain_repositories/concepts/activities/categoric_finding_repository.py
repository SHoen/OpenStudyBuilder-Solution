from typing import Optional

from clinical_mdr_api.domain.concepts.activities.categoric_finding import (
    CategoricFindingAR,
    CategoricFindingVO,
)
from clinical_mdr_api.domain.concepts.concept_base import _AggregateRootType
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.activities import (
    CategoricFindingRoot,
    CategoricFindingValue,
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
from clinical_mdr_api.models.activities.categoric_finding import CategoricFinding


class CategoricFindingRepository(ActivityInstanceRepository):
    root_class = CategoricFindingRoot
    value_class = CategoricFindingValue
    aggregate_class = CategoricFindingAR
    value_object_class = CategoricFindingVO
    return_model = CategoricFinding

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.value_sas_display_format = ar.concept_vo.value_sas_display_format
        value_node.save()
        if ar.concept_vo.specimen_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_findings_specimen.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.specimen_uid)
            )

        if ar.concept_vo.test_code_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_findings_test_code.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.test_code_uid)
            )

        if ar.concept_vo.categoric_response_value_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_categoric_response_value.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.categoric_response_value_uid)
            )

        if ar.concept_vo.categoric_response_list_uid is not None:
            activity_definition = self._create_activity_definition(value_node)
            activity_definition.has_categoric_response_list.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.categoric_response_list_uid)
            )

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        are_activity_instance_props_changed = super()._has_data_changed(
            ar=ar, value=value
        )

        are_props_changed = (
            ar.concept_vo.value_sas_display_format != value.value_sas_display_format
        )

        are_rels_changed = (
            ar.concept_vo.specimen_uid
            != self._get_uid_or_none(self._get_specimen(value))
            or ar.concept_vo.test_code_uid
            != self._get_uid_or_none(self._get_test_code(value))
            or ar.concept_vo.categoric_response_value_uid
            != self._get_uid_or_none(self._get_categoric_response_value(value))
            or ar.concept_vo.categoric_reponse_list_uid
            != self._get_uid_or_none(self._get_categoric_response_list(value))
        )

        return (
            are_activity_instance_props_changed or are_props_changed or are_rels_changed
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> CategoricFindingAR:
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
                activity_uids=input_dict.get("activities"),
                value_sas_display_format=input_dict.get("valueSasDisplayFormat"),
                specimen_uid=specimen_uid,
                specimen_name=specimen_name,
                test_code_uid=input_dict.get("testCode"),
                categoric_response_value_uid=input_dict.get("categoricResponseValue"),
                categoric_response_list_uid=input_dict.get("categoricResponseList"),
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
    ) -> CategoricFindingAR:
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
                activity_uids=[
                    activity.has_latest_value.get().uid
                    for activity in value.in_hierarchy.all()
                ],
                value_sas_display_format=value.value_sas_display_format,
                specimen_uid=self._get_uid_or_none(specimen),
                specimen_name=self._get_name_or_none(specimen),
                test_code_uid=self._get_uid_or_none(self._get_test_code(value)),
                categoric_response_value_uid=self._get_uid_or_none(
                    self._get_categoric_response_value(value)
                ),
                categoric_response_list_uid=self._get_uid_or_none(
                    self._get_categoric_response_list(value)
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def specific_alias_clause(self) -> str:
        activity_instance_specific = super().specific_alias_clause()
        return (
            activity_instance_specific
            + """
        WITH *,
            concept_value.value_sas_display_format AS valueSasDisplayFormat,

            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_TEST_CODE]->(test_code) | test_code.uid]) AS testCode,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_CATEGORIC_RESPONSE_VALUE]->(categoric_response_value) | 
                categoric_response_value.uid]) AS categoricResponseValue,
            head([(concept_value)-[:DEFINED_BY]->(:ActivityDefinition)-[:HAS_CATEGORIC_RESPONSE_LIST]->(categoric_response_list) | 
                categoric_response_list.uid]) AS categoricResponseList
        """
        )

    def _get_specimen(
        self, value: CategoricFindingValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            specimen = definition.has_findings_specimen.get_or_none()
            if specimen is not None:
                return specimen
        return None

    def _get_test_code(
        self, value: CategoricFindingValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            test_code = definition.has_findings_test_code.get_or_none()
            if test_code is not None:
                return test_code
        return None

    def _get_categoric_response_value(
        self, value: CategoricFindingValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            response_value = definition.has_categoric_response_value.get_or_none()
            if response_value is not None:
                return response_value
        return None

    def _get_categoric_response_list(
        self, value: CategoricFindingValue
    ) -> Optional[ClinicalMdrNodeWithUID]:
        for definition in value.defined_by.all():
            response_list = definition.has_categoric_response_list.get_or_none()
            if response_list is not None:
                return response_list
        return None
