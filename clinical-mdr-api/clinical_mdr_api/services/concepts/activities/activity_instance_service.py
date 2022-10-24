from typing import Sequence

from pydantic.main import BaseModel

from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.models.activities.activity_instance import ActivityInstance
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class ActivityInstanceService(ConceptGenericService[ActivityInstanceAR]):
    aggregate_class = ActivityInstanceAR
    repository_interface = ActivityInstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceAR
    ) -> ActivityInstance:
        return ActivityInstance.from_activity_ar(
            activity_ar=item_ar,
            find_activity_hierarchy_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_activity_subgroup_by_uid=self._repos.activity_sub_group_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: BaseModel, library: LibraryVO
    ) -> _AggregateRootType:
        raise NotImplementedError()

    def _edit_aggregate(
        self, item: _AggregateRootType, concept_edit_input: BaseModel
    ) -> _AggregateRootType:
        raise NotImplementedError()

    def get_version_history(self, uid: str) -> Sequence[BaseModel]:
        raise NotImplementedError()
