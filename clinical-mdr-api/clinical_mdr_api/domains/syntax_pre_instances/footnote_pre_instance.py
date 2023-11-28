from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.syntax_pre_instances.pre_instance_ar import PreInstanceAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass
class FootnotePreInstanceAR(PreInstanceAR):
    """
    Implementation of FootnotePreInstanceAR. Solely based on Parametrized Template.
    """

    _indications: list[DictionaryTermAR] | None = None

    _activities: list[ActivityAR] | None = None

    _activity_groups: list[ActivityGroupAR] | None = None

    _activity_subgroups: list[ActivitySubGroupAR] | None = None

    @property
    def indications(self) -> list[DictionaryTermAR]:
        return self._indications

    @property
    def activities(self) -> list[ActivityAR]:
        return self._activities

    @property
    def activity_groups(self) -> list[ActivityGroupAR]:
        return self._activity_groups

    @property
    def activity_subgroups(self) -> list[ActivitySubGroupAR]:
        return self._activity_subgroups

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        template: ParametrizedTemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        sequence_id: str,
        study_count: int = 0,
        indications: list[DictionaryTermAR] | None = None,
        activities: list[ActivityAR] | None = None,
        activity_groups: list[ActivityGroupAR] | None = None,
        activity_subgroups: list[ActivitySubGroupAR] | None = None,
    ) -> Self:
        return cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _indications=indications,
            _activities=activities,
            _activity_groups=activity_groups,
            _activity_subgroups=activity_subgroups,
            _study_count=study_count,
        )

    @classmethod
    def from_input_values(
        cls,
        author: str,
        library: LibraryVO,
        template: ParametrizedTemplateVO,
        generate_uid_callback: Callable[[], str] | None = (lambda: None),
        next_available_sequence_id_callback: Callable[[str], str | None] = (
            lambda _: None
        ),
        indications: list[DictionaryTermAR] | None = None,
        activities: list[ActivityAR] | None = None,
        activity_groups: list[ActivityGroupAR] | None = None,
        activity_subgroups: list[ActivitySubGroupAR] | None = None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)

        generated_uid = generate_uid_callback()

        ar = cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(template.template_uid),
            _library=library,
            _template=template,
            _item_metadata=item_metadata,
        )
        ar._indications = indications
        ar._activities = activities
        ar._activity_groups = activity_groups
        ar._activity_subgroups = activity_subgroups

        return ar