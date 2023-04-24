from typing import Optional, cast

from clinical_mdr_api.domain.syntax_instances.timeframe import TimeframeAR
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    TimeframeRoot,
    TimeframeTemplateRoot,
    TimeframeValue,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)


class TimeframeRepository(GenericSyntaxInstanceRepository[TimeframeAR]):
    root_class = TimeframeRoot
    value_class = TimeframeValue
    template_class = TimeframeTemplateRoot

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None,
    ) -> TimeframeAR:
        return cast(
            TimeframeAR,
            TimeframeAR.from_repository_values(
                uid=root.uid,
                library=LibraryVO.from_input_values_2(
                    library_name=library.name,
                    is_library_editable_callback=(lambda _: library.is_editable),
                ),
                item_metadata=self._library_item_metadata_vo_from_relation(
                    relationship
                ),
                template=self._get_template(root, value, relationship.start_date),
                study_count=study_count,
            ),
        )