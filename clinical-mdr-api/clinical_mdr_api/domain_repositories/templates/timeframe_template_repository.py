from typing import Optional

from clinical_mdr_api.domain.templates.timeframe_templates import TimeframeTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.generic_template_repository import (
    GenericTemplateRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.timeframe_template import (
    TimeframeTemplateRoot,
    TimeframeTemplateValue,
)


class TimeframeTemplateRepository(GenericTemplateRepository[TimeframeTemplateAR]):
    root_class = TimeframeTemplateRoot
    value_class = TimeframeTemplateValue
    # aggregate_class = TimeframeTemplateAR

    def check_exists_by_name_in_study(self, name: str, study_uid: str) -> bool:
        raise NotImplementedError()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None,
        counts: InstantiationCountsVO = None
    ) -> TimeframeTemplateAR:
        return TimeframeTemplateAR.from_repository_values(
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
