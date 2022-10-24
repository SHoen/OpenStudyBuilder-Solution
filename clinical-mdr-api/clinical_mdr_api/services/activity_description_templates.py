from typing import Optional, Sequence, Tuple

from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.templates.activity_description_template import (
    ActivityDescriptionTemplateAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import TemplateVO
from clinical_mdr_api.domain_repositories.models.activity_description_template import (
    ActivityDescriptionTemplateRoot,
)
from clinical_mdr_api.domain_repositories.templates.activity_description_template_repository import (
    ActivityDescriptionTemplateRepository,
)
from clinical_mdr_api.models.activities.activity import Activity
from clinical_mdr_api.models.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.activities.activity_sub_group import ActivitySubGroup
from clinical_mdr_api.models.activity_description_template import (
    ActivityDescriptionTemplate,
    ActivityDescriptionTemplateCreateInput,
    ActivityDescriptionTemplateEditGroupingsInput,
    ActivityDescriptionTemplateVersion,
    ActivityDescriptionTemplateWithCount,
)
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_template_service import GenericTemplateService


class ActivityDescriptionTemplateService(
    GenericTemplateService[ActivityDescriptionTemplateAR]
):
    aggregate_class = ActivityDescriptionTemplateAR
    version_class = ActivityDescriptionTemplateVersion
    repository_interface = ActivityDescriptionTemplateRepository
    root_node_class = ActivityDescriptionTemplateRoot

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityDescriptionTemplateAR
    ) -> ActivityDescriptionTemplate:
        item_ar = self._set_default_parameter_values(item_ar)
        cls = (
            ActivityDescriptionTemplateWithCount
            if item_ar.counts is not None
            else ActivityDescriptionTemplate
        )
        return cls.from_activity_description_template_ar(
            item_ar,
            find_activity_subgroup_by_uid=self._repos.activity_sub_group_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def get_all(
        self,
        status: Optional[str] = None,
        return_study_count: bool = True,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[ActivityDescriptionTemplate]:

        all_items = super().get_all(status, return_study_count)

        # The get_all method is only using neomodel, without Cypher query
        # Therefore, the filtering will be done in this service layer
        filtered_items = service_level_generic_filtering(
            items=all_items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    def _create_ar_from_input_values(
        self, template: ActivityDescriptionTemplateCreateInput
    ) -> ActivityDescriptionTemplateAR:
        default_parameter_values = self._create_default_parameter_entries(
            template_name=template.name,
            default_parameter_values=template.defaultParameterValues,
        )

        template_vo, library_vo = self._create_template_vo(
            template, default_parameter_values
        )

        # Get groupings for templates from database
        (
            indications,
            activities,
            activity_groups,
            activity_sub_groups,
        ) = self._get_groupings(template)

        # Process item to save
        try:
            item = ActivityDescriptionTemplateAR.from_input_values(
                template_value_exists_callback=(
                    lambda _template_vo: self.repository.check_exists_by_name(
                        _template_vo.name
                    )
                ),
                author=self.user_initials,
                editable_instance=template.editableInstance,
                template=template_vo,
                library=library_vo,
                generate_uid_callback=self.repository.generate_uid_callback,
                indications=indications,
                activities=activities,
                activity_groups=activity_groups,
                activity_sub_groups=activity_sub_groups,
            )
        except ValueError as e:
            raise exceptions.ValidationException(e.args[0])

        return item

    @db.transaction
    def patch_groupings(
        self, uid: str, groupings: ActivityDescriptionTemplateEditGroupingsInput
    ) -> ActivityDescriptionTemplate:
        try:
            if groupings.indicationUids is not None:
                self.repository.patch_indications(uid, groupings.indicationUids)
            if groupings.activityUids is not None:
                self.repository.patch_activities(uid, groupings.activityUids)
            if groupings.activityGroupUids is not None:
                self.repository.patch_activity_groups(uid, groupings.activityGroupUids)
            if groupings.activitySubGroupUids is not None:
                self.repository.patch_activity_sub_groups(
                    uid, groupings.activitySubGroupUids
                )
        finally:
            self.repository.close()

        return self.get_by_uid(uid)

    def _set_default_parameter_values(
        self, item: ActivityDescriptionTemplateAR
    ) -> ActivityDescriptionTemplateAR:
        """This method fetches and sets the default parameter values for the template

        Args:
            item (ActivityDescriptionTemplateAR): The template for which to fetch default parameter values
        """
        # Get default parameter values
        default_parameter_values = self.repository.get_default_parameter_values(
            item.uid
        )

        return ActivityDescriptionTemplateAR(
            _uid=item.uid,
            _editable_instance=item.editable_instance,
            _library=item.library,
            _item_metadata=item.item_metadata,
            _counts=item.counts,
            _study_count=item.study_count,
            _indications=item.indications,
            _activities=item.activities,
            _activity_groups=item.activity_groups,
            _activity_sub_groups=item.activity_sub_groups,
            _template=TemplateVO(
                name=item.template_value.name,
                name_plain=item.template_value.name_plain,
                default_parameter_values=default_parameter_values,
                guidance_text=item.template_value.guidance_text,
            ),
        )

    def _set_groupings(self, item: ActivityDescriptionTemplate) -> None:
        """
        This method fetches and sets the grouping properties to a template.
        """
        # Get indications
        indications = (
            self._repos.dictionary_term_generic_repository.get_template_indications(
                self.root_node_class, item.uid
            )
        )
        if indications:
            item.indications = [
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in indications
            ]
        # Get activities
        activities = self._repos.activity_repository.get_template_activities(
            self.root_node_class, item.uid
        )
        if activities:
            item.activities = [
                Activity.from_activity_ar(
                    activity,
                    self._repos.activity_sub_group_repository.find_by_uid_2,
                    self._repos.activity_group_repository.find_by_uid_2,
                )
                for activity in activities
            ]
        # Get activity groups
        activity_groups = (
            self._repos.activity_group_repository.get_template_activity_groups(
                self.root_node_class, item.uid
            )
        )
        if activity_groups:
            item.activityGroups = [
                ActivityGroup.from_activity_ar(activity) for activity in activity_groups
            ]
        # Get activity subGroups
        activity_sub_groups = (
            self._repos.activity_sub_group_repository.get_template_activity_sub_groups(
                self.root_node_class, item.uid
            )
        )
        if activity_sub_groups:
            item.activitySubGroups = [
                ActivitySubGroup.from_activity_ar(
                    activity, self._repos.activity_group_repository.find_by_uid_2
                )
                for activity in activity_sub_groups
            ]

    def _get_groupings(
        self, template: BaseModel
    ) -> Tuple[
        Sequence[DictionaryTermAR],
        Sequence[ActivityAR],
        Sequence[ActivityGroupAR],
        Sequence[ActivitySubGroupAR],
    ]:
        indications: Sequence[DictionaryTermAR] = []
        activities: Sequence[ActivityAR] = []
        activity_groups: Sequence[ActivityGroupAR] = []
        activity_sub_groups: Sequence[ActivitySubGroupAR] = []

        if template.indicationUids and len(template.indicationUids) > 0:
            for uid in template.indicationUids:
                indication = self._repos.dictionary_term_generic_repository.find_by_uid(
                    term_uid=uid
                )
                indications.append(indication)

        if template.activityUids and len(template.activityUids) > 0:
            for uid in template.activityUids:
                activity = self._repos.activity_repository.find_by_uid_2(uid=uid)
                activities.append(activity)

        if template.activityGroupUids and len(template.activityGroupUids) > 0:
            for uid in template.activityGroupUids:
                activity_group = self._repos.activity_group_repository.find_by_uid_2(
                    uid=uid
                )
                activity_groups.append(activity_group)

        if template.activitySubGroupUids and len(template.activitySubGroupUids) > 0:
            for uid in template.activitySubGroupUids:
                activity_sub_group = (
                    self._repos.activity_sub_group_repository.find_by_uid_2(uid=uid)
                )
                activity_sub_groups.append(activity_sub_group)

        return indications, activities, activity_groups, activity_sub_groups
