from clinical_mdr_api.domain.template_parameters import ParameterTemplateAR, TemplateVO
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.generic_template_repository import (  # type: ignore
    GenericTemplateRepository,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models.generic import (  # type: ignore
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    ParameterTemplateRoot,
    ParameterTemplateValue,
    TemplateParameter,
)


class ParameterTemplateRepository(GenericTemplateRepository[ParameterTemplateAR]):
    root_class = ParameterTemplateRoot
    value_class = ParameterTemplateValue
    aggregate_class = ParameterTemplateAR

    def check_exists_by_name_in_study(self, name: str, study_uid: str) -> bool:
        raise NotImplementedError()

    def _get_template(self, value: VersionValue) -> TemplateVO:
        return TemplateVO(value.template_string)

    def check_usage_count(self, uid: str) -> int:
        return 0
        # itm: VersionRoot = self.root_class.nodes.get(uid=uid)
        # return len(itm.has_template.all())

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: ParameterTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ParameterTemplateValue
    ) -> ParameterTemplateAR:

        pt = root.has_value.get()
        library = root.has_library.get()

        return ParameterTemplateAR.from_repository_values(
            uid=root.uid,
            parameter_name=pt.name,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            template=self._get_template(root, value),
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: ParameterTemplateAR
    ) -> VersionValue:

        for itm in root.has_version.filter(template_string=ar.name):
            return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and latest_draft.template_string == ar.name:
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and latest_final.template_string == ar.name:
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and latest_retired.template_string == ar.name:
            return latest_retired
        new_value = self.value_class(template_string=ar.name)
        self._db_save_node(new_value)
        return new_value

    def _create(self, item: ParameterTemplateAR) -> ParameterTemplateAR:
        """
        Creates new VersionedObject AR, checks possibility based on
        library setting, then creates database representation,
        creates TemplateParameters database objects, recreates AR based
        on created database model and returns created AR.
        Saving into database is necessary due to uid creation process that
        require saving object to database.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        parameter_name: str = item.parameter_name
        root = self.root_class(uid=item.uid)
        self._db_save_node(root)

        tp = TemplateParameter.nodes.get_or_none(name=parameter_name)
        if tp is None:
            tp = TemplateParameter(name=parameter_name)
            self._db_save_node(tp)
        root.has_value.connect(tp)
        root.has_definition.connect(tp)

        library = self._get_library(item.library.name)
        root.has_library.connect(library)

        # value = self.value_class(name=name)
        value = self._get_or_create_value(root=root, ar=item)

        (root, value, _, _, _,) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        return item

    def _is_new_version_necessary(
        self, ar: _AggregateRootType, value: VersionValue
    ) -> bool:
        return ar.name != value.template_string

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        pass
