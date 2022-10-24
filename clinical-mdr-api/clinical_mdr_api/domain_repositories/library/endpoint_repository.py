from typing import Optional, cast

from clinical_mdr_api.domain.library.endpoints import EndpointAR
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.library.generic_template_object_repository import (
    GenericTemplateBasedObjectRepository,
)
from clinical_mdr_api.domain_repositories.models.endpoint import (
    EndpointRoot,
    EndpointValue,
)
from clinical_mdr_api.domain_repositories.models.endpoint_template import (
    EndpointTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class EndpointRepository(GenericTemplateBasedObjectRepository[EndpointAR]):
    root_class = EndpointRoot
    value_class = EndpointValue
    # aggregate_class = EndpointAR
    template_class = EndpointTemplateRoot

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None
    ) -> EndpointAR:
        return cast(
            EndpointAR,
            EndpointAR.from_repository_values(
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
