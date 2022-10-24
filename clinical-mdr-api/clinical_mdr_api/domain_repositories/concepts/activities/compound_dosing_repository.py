from typing import Optional

from clinical_mdr_api.domain.concepts.activities.compound_dosing import (
    CompoundDosingAR,
    CompoundDosingVO,
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
    CompoundDosingRoot,
    CompoundDosingValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.models.activities.compound_dosing import CompoundDosing


class CompoundDosingRepository(ActivityInstanceRepository):
    root_class = CompoundDosingRoot
    value_class = CompoundDosingValue
    return_model = CompoundDosing

    def _create_new_value_node(self, ar: _AggregateRootType) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        return value_node

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        are_activity_instance_props_changed = super()._has_data_changed(
            ar=ar, value=value
        )
        return are_activity_instance_props_changed

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> CompoundDosingAR:
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
        return CompoundDosingAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=CompoundDosingVO.from_repository_values(
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
    ) -> CompoundDosingAR:
        sdtm_variable = self._get_sdtm_variable(value)
        sdtm_subcat = self._get_sdtm_subcat(value)
        sdtm_cat = self._get_sdtm_cat(value)
        sdtm_domain = self._get_sdtm_domain(value)
        return CompoundDosingAR.from_repository_values(
            uid=root.uid,
            concept_vo=CompoundDosingVO.from_repository_values(
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
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )
