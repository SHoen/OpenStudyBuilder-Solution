from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
)
from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.models.activities.activity_sub_group import (
    ActivitySubGroup,
    ActivitySubGroupEditInput,
    ActivitySubGroupInput,
    ActivitySubGroupVersion,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)


class ActivitySubGroupService(ConceptGenericService[ActivitySubGroupAR]):
    aggregate_class = ActivitySubGroupAR
    repository_interface = ActivitySubGroupRepository
    version_class = ActivitySubGroupVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivitySubGroupAR
    ) -> ActivitySubGroup:
        return ActivitySubGroup.from_activity_ar(
            activity_sub_group_ar=item_ar,
            find_activity_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivitySubGroupInput, library
    ) -> ActivitySubGroupAR:
        return ActivitySubGroupAR.from_input_values(
            author=self.user_initials,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_group=concept_input.activityGroup,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_sub_group_exists_by_name_callback=self._repos.activity_sub_group_repository.concept_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self,
        item: ActivitySubGroupAR,
        concept_edit_input: ActivitySubGroupEditInput,
    ) -> ActivitySubGroupAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.nameSentenceCase,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_group=concept_edit_input.activityGroup,
            ),
            concept_exists_by_name_callback=self._repos.activity_sub_group_repository.concept_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        return item
