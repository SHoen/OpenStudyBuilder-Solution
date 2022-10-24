from typing import Optional

from clinical_mdr_api.domain.concepts.odms.template import OdmTemplateAR, OdmTemplateVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmTemplateRoot,
    OdmTemplateValue,
)
from clinical_mdr_api.models import OdmTemplate


class TemplateRepository(OdmGenericRepository[OdmTemplateAR]):
    root_class = OdmTemplateRoot
    value_class = OdmTemplateValue
    return_model = OdmTemplate

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> OdmTemplateAR:
        return OdmTemplateAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmTemplateVO.from_repository_values(
                name=value.name,
                oid=value.oid,
                effective_date=value.effective_date,
                retired_date=value.retired_date,
                description=value.description,
                form_uids=[form.uid for form in root.form_ref.all()],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> _AggregateRootType:
        major, minor = input_dict.get("version").split(".")
        odm_form_ar = OdmTemplateAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=OdmTemplateVO.from_repository_values(
                name=input_dict.get("name"),
                oid=input_dict.get("oid"),
                effective_date=input_dict.get("effectiveDate"),
                retired_date=input_dict.get("retiredDate"),
                description=input_dict.get("description"),
                form_uids=input_dict.get("formUids"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("changeDescription"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("userInitials"),
                start_date=convert_to_datetime(value=input_dict.get("startDate")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_form_ar

    def specific_alias_clause(self, only_specific_status: list = None) -> str:
        if not only_specific_status:
            only_specific_status = ["LATEST"]

        return f"""
        WITH *,
        concept_value.oid AS oid,
        concept_value.effective_date AS effectiveDate,
        concept_value.retired_date AS retiredDate,
        concept_value.description AS description,

        [(concept_value)<-[:{"|".join(only_specific_status)}]-(:OdmTemplateRoot)-[fref:FORM_REF]->(fr:OdmFormRoot)-[:LATEST]->(fv:OdmFormValue) | {{uid: fr.uid, name: fv.name, order: fref.order, mandatory: fref.mandatory, collection_exception_condition_oid: fref.collection_exception_condition_oid}}] AS forms
        
        WITH *,
        [form in forms | form.uid] AS formUids
        """

    def _create_new_value_node(self, ar: OdmTemplateAR) -> OdmTemplateValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.oid = ar.concept_vo.oid
        value_node.effective_date = ar.concept_vo.effective_date
        value_node.retired_date = ar.concept_vo.retired_date
        value_node.description = ar.concept_vo.description

        return value_node

    def _has_data_changed(self, ar: OdmTemplateAR, value: OdmTemplateValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.oid != value.oid
            or ar.concept_vo.effective_date != value.effective_date
            or ar.concept_vo.retired_date != value.retired_date
            or ar.concept_vo.description != value.description
        )
