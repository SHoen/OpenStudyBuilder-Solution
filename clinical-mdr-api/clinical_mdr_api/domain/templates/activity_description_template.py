from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domain.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domain.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryItemMetadataVO,
    LibraryVO,
    TemplateAggregateRootBase,
    TemplateVO,
)


@dataclass
class ActivityDescriptionTemplateAR(TemplateAggregateRootBase):
    """
    A specific Activity Description Template AR. It can be used to customize Activity Description Template
    behavior. Inherits generic template versioning behaviors
    """

    _indications: Optional[Sequence[DictionaryTermAR]] = None

    _activities: Optional[Sequence[ActivityAR]] = None

    _activity_groups: Optional[Sequence[ActivityGroupAR]] = None

    _activity_sub_groups: Optional[Sequence[ActivitySubGroupAR]] = None

    @property
    def indications(self) -> Sequence[DictionaryTermAR]:
        return self._indications

    @property
    def activities(self) -> Sequence[ActivityAR]:
        return self._activities

    @property
    def activity_groups(self) -> Sequence[ActivityGroupAR]:
        return self._activity_groups

    @property
    def activity_sub_groups(self) -> Sequence[ActivitySubGroupAR]:
        return self._activity_sub_groups

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: Optional[int] = None,
        counts: Optional[InstantiationCountsVO] = None,
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        activities: Optional[Sequence[ActivityAR]] = None,
        activity_groups: Optional[Sequence[ActivityGroupAR]] = None,
        activity_sub_groups: Optional[Sequence[ActivitySubGroupAR]] = None,
    ) -> "TemplateAggregateRootBase":
        ar = cls(
            _uid=uid,
            _editable_instance=editable_instance,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _indications=indications,
            _activities=activities,
            _activity_groups=activity_groups,
            _activity_sub_groups=activity_sub_groups,
            _study_count=study_count,
            _counts=counts,
        )
        return ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        template_value_exists_callback: Callable[
            [TemplateVO], bool
        ],  # = (lambda _: False),
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        indications: Optional[Sequence[DictionaryTermAR]] = None,
        activities: Optional[Sequence[ActivityAR]] = None,
        activity_groups: Optional[Sequence[ActivityGroupAR]] = None,
        activity_sub_groups: Optional[Sequence[ActivitySubGroupAR]] = None
    ) -> "ActivityDescriptionTemplateAR":
        ar: ActivityDescriptionTemplateAR = super().from_input_values(
            author=author,
            editable_instance=editable_instance,
            template=template,
            library=library,
            template_value_exists_callback=template_value_exists_callback,
            generate_uid_callback=generate_uid_callback,
        )
        ar._indications = indications
        ar._activities = activities
        ar._activity_groups = activity_groups
        ar._activity_sub_groups = activity_sub_groups

        return ar
