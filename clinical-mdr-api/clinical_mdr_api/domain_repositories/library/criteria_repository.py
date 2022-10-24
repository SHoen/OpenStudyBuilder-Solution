from datetime import datetime
from typing import Optional, cast

from clinical_mdr_api.domain.library.criteria import CriteriaAR, CriteriaTemplateVO
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.library.generic_template_object_repository import (
    GenericTemplateBasedObjectRepository,
)
from clinical_mdr_api.domain_repositories.models.criteria import (
    CriteriaRoot,
    CriteriaValue,
)
from clinical_mdr_api.domain_repositories.models.criteria_template import (
    CriteriaTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class CriteriaRepository(GenericTemplateBasedObjectRepository[CriteriaAR]):
    root_class = CriteriaRoot
    value_class = CriteriaValue
    template_class = CriteriaTemplateRoot

    def _get_template(
        self, root: VersionRoot, value: VersionValue, date_before: datetime
    ) -> CriteriaTemplateVO:
        parameter_values = self._get_template_parameters(root, value)
        template_object: VersionRoot = root.has_template.get()
        if date_before is None:
            template_value_object: VersionValue = template_object.latest_final.get()
        else:
            template_value_object: VersionValue = template_object.get_final_before(
                date_before
            )
            if template_value_object is None:
                template_value_object: VersionValue = (
                    template_object.get_retired_before(date_before)
                )

        template = CriteriaTemplateVO(
            template_name=template_value_object.name,
            template_uid=template_object.uid,
            guidance_text=template_value_object.guidance_text,
            parameter_values=parameter_values,
        )
        return template

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None
    ) -> CriteriaAR:
        return cast(
            CriteriaAR,
            CriteriaAR.from_repository_values(
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
