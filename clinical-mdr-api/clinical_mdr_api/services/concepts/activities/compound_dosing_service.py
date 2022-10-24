from clinical_mdr_api.domain.concepts.activities.compound_dosing import (
    CompoundDosingAR,
    CompoundDosingVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.compound_dosing_repository import (
    CompoundDosingRepository,
)
from clinical_mdr_api.models.activities.compound_dosing import (
    CompoundDosing,
    CompoundDosingCreateInput,
    CompoundDosingEditInput,
    CompoundDosingVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class CompoundDosingService(ConceptGenericService[CompoundDosingAR]):
    aggregate_class = CompoundDosingAR
    version_class = CompoundDosingVersion
    repository_interface = CompoundDosingRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CompoundDosingAR
    ) -> CompoundDosing:
        return CompoundDosing.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_sub_group_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: CompoundDosingCreateInput, library
    ) -> _AggregateRootType:
        return CompoundDosingAR.from_input_values(
            author=self.user_initials,
            concept_vo=CompoundDosingVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                topic_code=concept_input.topicCode,
                adam_param_code=concept_input.adamParamCode,
                legacy_description=concept_input.legacyDescription,
                sdtm_variable_uid=concept_input.sdtmVariable,
                sdtm_variable_name=None,
                sdtm_subcat_uid=concept_input.sdtmSubcat,
                sdtm_subcat_name=None,
                sdtm_cat_uid=concept_input.sdtmCat,
                sdtm_cat_name=None,
                sdtm_domain_uid=concept_input.sdtmDomain,
                sdtm_domain_name=None,
                activity_uids=concept_input.activities,
                activity_type="compound-dosings",
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            compound_dosing_exists_by_name_callback=self.repository.concept_exists_by_name,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            activity_hierarchy_exists_by_uid_callback=self._repos.activity_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self, item: CompoundDosingAR, concept_edit_input: CompoundDosingEditInput
    ) -> CompoundDosingAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=CompoundDosingVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.nameSentenceCase,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                topic_code=concept_edit_input.topicCode,
                adam_param_code=concept_edit_input.adamParamCode,
                legacy_description=concept_edit_input.legacyDescription,
                sdtm_variable_uid=concept_edit_input.sdtmVariable,
                sdtm_variable_name=None,
                sdtm_subcat_uid=concept_edit_input.sdtmSubcat,
                sdtm_subcat_name=None,
                sdtm_cat_uid=concept_edit_input.sdtmCat,
                sdtm_cat_name=None,
                sdtm_domain_uid=concept_edit_input.sdtmDomain,
                sdtm_domain_name=None,
                activity_uids=concept_edit_input.activities,
                activity_type="compound-dosings",
            ),
            concept_exists_by_name_callback=self.repository.concept_exists_by_name,
            activity_hierarchy_exists_by_uid_callback=self._repos.activity_repository.final_concept_exists,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
        )
        return item
