from typing import Optional, Sequence

from clinical_mdr_api.domain.templates.activity_description_template import (
    ActivityDescriptionTemplateAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.generic_template_repository import (
    GenericTemplateRepository,  # type: ignore
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.activity_description_template import (  # type: ignore
    ActivityDescriptionTemplateRoot,
    ActivityDescriptionTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (  # type: ignore
    Library,
    VersionRelationship,
)


class ActivityDescriptionTemplateRepository(
    GenericTemplateRepository[ActivityDescriptionTemplateAR]
):
    root_class = ActivityDescriptionTemplateRoot
    value_class = ActivityDescriptionTemplateValue

    def check_exists_by_name_in_study(self, name: str, study_uid: str) -> bool:
        raise NotImplementedError()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: ActivityDescriptionTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityDescriptionTemplateValue,
        study_count: Optional[int] = None,
        counts: Optional[InstantiationCountsVO] = None,
    ) -> ActivityDescriptionTemplateAR:

        return ActivityDescriptionTemplateAR.from_repository_values(
            uid=root.uid,
            editable_instance=root.editable_instance,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self._get_template(value),
            study_count=study_count,
            counts=counts,
        )

    def _create(
        self, item: ActivityDescriptionTemplateAR
    ) -> ActivityDescriptionTemplateAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Attaching root node to indication nodes
        * Attaching root node to activity, activity group, activity sub group nodes
        """
        item = super()._create(item)
        root = self.root_class.nodes.get(uid=item.uid)

        if item.indications:
            for indication in item.indications:
                indication = self._get_indication(indication.uid)
                root.has_indication.connect(indication)
        if item.activities:
            for activity in item.activities:
                activity = self._get_activity(activity.uid)
                root.has_activity.connect(activity)
        if item.activity_groups:
            for group in item.activity_groups:
                group = self._get_activity_group(group.uid)
                root.has_activity_group.connect(group)
        if item.activity_sub_groups:
            for group in item.activity_sub_groups:
                group = self._get_activity_sub_group(group.uid)
                root.has_activity_sub_group.connect(group)

        return item

    def _get_activity(self, uid: str) -> ActivityRoot:
        # Finds activity in database based on root node uid
        return ActivityRoot.nodes.get(uid=uid)

    def _get_activity_group(self, uid: str) -> ActivityGroupRoot:
        # Finds activity group in database based on root node uid
        return ActivityGroupRoot.nodes.get(uid=uid)

    def _get_activity_sub_group(self, uid: str) -> ActivitySubGroupRoot:
        # Finds activity sub group in database based on root node uid
        return ActivitySubGroupRoot.nodes.get(uid=uid)

    def patch_activities(self, uid: str, activity_uids: Sequence[str]) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity.disconnect_all()
        for activity in activity_uids:
            activity = self._get_activity(activity)
            root.has_activity.connect(activity)

    def patch_activity_groups(
        self, uid: str, activity_group_uids: Sequence[str]
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_group.disconnect_all()
        for group in activity_group_uids:
            group = self._get_activity_group(group)
            root.has_activity_group.connect(group)

    def patch_activity_sub_groups(
        self, uid: str, activity_sub_group_uids: Sequence[str]
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_activity_sub_group.disconnect_all()
        for group in activity_sub_group_uids:
            sub_group = self._get_activity_sub_group(group)
            root.has_activity_sub_group.connect(sub_group)
