from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.exceptions import NotFoundException
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityEditInput,
    ActivityFromRequestInput,
    ActivityInput,
    ActivityOverview,
    ActivityVersion,
)
from clinical_mdr_api.services._utils import is_library_editable, normalize_string
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
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivityInput, library
    ) -> _AggregateRootType:
        return ActivityAR.from_input_values(
            author=self.user_initials,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_input.activity_groupings
                ]
                if concept_input.activity_groupings
                else [],
                request_rationale=concept_input.request_rationale,
                is_data_collected=concept_input.is_data_collected,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self, item: ActivityAR, concept_edit_input: ActivityEditInput
    ) -> ActivityAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_edit_input.nci_concept_id,
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.activity_group_uid,
                        activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
                    )
                    for activity_grouping in concept_edit_input.activity_groupings
                ]
                if concept_edit_input.activity_groupings
                else [],
                request_rationale=concept_edit_input.request_rationale,
                is_data_collected=concept_edit_input.is_data_collected,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        return item

    @db.transaction
    def replace_requested_activity_with_sponsor(
        self, sponsor_activity_input: ActivityFromRequestInput
    ) -> Activity:
        if not self._repos.library_repository.library_exists(
            normalize_string(sponsor_activity_input.library_name)
        ):
            raise exceptions.BusinessLogicException(
                f"There is no library identified by provided library name ({sponsor_activity_input.library_name})"
            )

        library_vo = LibraryVO.from_input_values_2(
            library_name=sponsor_activity_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=sponsor_activity_input.activity_request_uid, for_update=True
        )
        if activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL:
            raise exceptions.BusinessLogicException(
                f"To update the following Activity Request {activity_request_ar.name} to Sponsor Activity it should be in Final state"
            )
        activity_request_ar.inactivate(
            author=self.user_initials,
            change_description="Inactivate Requested Activity as Sponsor Activity was created",
        )
        self.repository.save(activity_request_ar)

        concept_ar = self._create_aggregate_root(
            concept_input=sponsor_activity_input, library=library_vo
        )
        concept_ar.approve(
            author=self.user_initials,
            change_description="Approve Sponsor Activity created from Requested Activity",
        )
        self.repository.save(concept_ar)
        self.repository.replace_request_with_sponsor_activity(
            activity_request_uid=sponsor_activity_input.activity_request_uid,
            sponsor_activity_uid=concept_ar.uid,
        )
        return self._transform_aggregate_root_to_pydantic_model(concept_ar)

    def get_activity_overview(self, activity_uid: str) -> ActivityOverview:
        if not self.repository.exists_by("uid", activity_uid, True):
            raise NotFoundException(
                f"Cannot find Activity with the following uid ({activity_uid})"
            )
        overview = self._repos.activity_repository.get_activity_overview(
            uid=activity_uid
        )
        return ActivityOverview.from_repository_input(overview=overview)
