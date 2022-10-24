from typing import Optional, cast

from clinical_mdr_api.domain.library.objectives import ObjectiveAR
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.library.generic_template_object_repository import (
    GenericTemplateBasedObjectRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.objective import (
    ObjectiveRoot,
    ObjectiveValue,
)
from clinical_mdr_api.domain_repositories.models.objective_template import (
    ObjectiveTemplateRoot,
)


class ObjectiveRepository(GenericTemplateBasedObjectRepository[ObjectiveAR]):
    root_class = ObjectiveRoot
    value_class = ObjectiveValue
    # aggregate_class = ObjectiveAR
    template_class = ObjectiveTemplateRoot

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None
    ) -> ObjectiveAR:
        return cast(
            ObjectiveAR,
            ObjectiveAR.from_repository_values(
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
