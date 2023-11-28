import re
from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domains.syntax_templates.template import (
    InstantiationCountsVO,
    TemplateAggregateRootBase,
    TemplateVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)


@dataclass
class FootnoteTemplateAR(TemplateAggregateRootBase):
    """
    A specific Footnote Template AR. It can be used to customize Footnote Template
    behavior. Inherits generic template versioning behaviors
    """

    _type: tuple[CTTermNameAR, CTTermAttributesAR] = ()

    _indications: list[DictionaryTermAR] | None = None

    _activities: list[ActivityAR] | None = None

    _activity_groups: list[ActivityGroupAR] | None = None

    _activity_subgroups: list[ActivitySubGroupAR] | None = None

    @property
    def type(self) -> tuple[CTTermNameAR, CTTermAttributesAR] | None:
        return self._type

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
        sequence_id: str,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
        footnote_type: tuple[CTTermNameAR, CTTermAttributesAR] | None = None,
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
            _type=footnote_type,
            _indications=indications,
            _activities=activities,
            _activity_groups=activity_groups,
            _activity_subgroups=activity_subgroups,
            _study_count=study_count,
            _counts=counts,
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        template: TemplateVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        next_available_sequence_id_callback: Callable[
            [str, str | None, str | None, LibraryVO | None], str | None
        ] = (lambda uid, prefix, type_uid, library: None),
        footnote_type: tuple[CTTermNameAR, CTTermAttributesAR] | None = None,
        indications: list[DictionaryTermAR] | None = None,
        activities: list[ActivityAR] | None = None,
        activity_groups: list[ActivityGroupAR] | None = None,
        activity_subgroups: list[ActivitySubGroupAR] | None = None,
    ) -> Self:
        footnote_type_name = re.sub(
            "footnote",
            "",
            footnote_type[0].name,
            flags=re.IGNORECASE,
        )

        ar: FootnoteTemplateAR = super().from_input_values(
            author=author,
            template=template,
            library=library,
            generate_uid_callback=generate_uid_callback,
        )
        ar._sequence_id = next_available_sequence_id_callback(
            uid=ar._uid,
            prefix="F"
            + "".join([char for char in footnote_type_name if char.isupper()]),
            type_uid=footnote_type[0].uid,
            library=library,
        )
        ar._type = footnote_type
        ar._indications = indications
        ar._activities = activities
        ar._activity_groups = activity_groups
        ar._activity_subgroups = activity_subgroups

        return ar
