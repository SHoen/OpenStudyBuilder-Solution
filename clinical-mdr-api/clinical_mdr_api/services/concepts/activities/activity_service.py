from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR, ActivityVO
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.models.activities.activity import (
    Activity,
    ActivityEditInput,
    ActivityInput,
    ActivityVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class ActivityService(ConceptGenericService[ActivityAR]):
    aggregate_class = ActivityAR
    version_class = ActivityVersion
    repository_interface = ActivityRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityAR
    ) -> Activity:
        return Activity.from_activity_ar(
            activity_ar=item_ar,
            find_activity_subgroup_by_uid=self._repos.activity_sub_group_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivityInput, library
    ) -> _AggregateRootType:
        return ActivityAR.from_input_values(
            author=self.user_initials,
            concept_vo=ActivityVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_sub_group=concept_input.activitySubGroup,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_name_callback=self._repos.activity_repository.concept_exists_by_name,
            activity_sub_group_exists=self._repos.activity_sub_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self, item: ActivityAR, concept_edit_input: ActivityEditInput
    ) -> ActivityAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=ActivityVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.nameSentenceCase,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_sub_group=concept_edit_input.activitySubGroup,
            ),
            concept_exists_by_name_callback=self._repos.activity_repository.concept_exists_by_name,
            activity_sub_group_exists=self._repos.activity_sub_group_repository.final_concept_exists,
        )
        return item
