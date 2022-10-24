from typing import Optional, Sequence, Tuple

from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import TemplateVO
from clinical_mdr_api.domain_repositories.library.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.models.objective_template import (
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models import ObjectiveTemplate, ObjectiveTemplateVersion
from clinical_mdr_api.models.ct_term import CTTermNameAndAttributes
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.objective_template import (
    ObjectiveTemplateCreateInput,
    ObjectiveTemplateEditGroupingsInput,
    ObjectiveTemplateWithCount,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_template_service import (
    GenericTemplateService,  # type: ignore
)


class ObjectiveTemplateService(GenericTemplateService[ObjectiveTemplateAR]):
    aggregate_class = ObjectiveTemplateAR
    version_class = ObjectiveTemplateVersion
    repository_interface = ObjectiveTemplateRepository
    object_repository_interface = ObjectiveRepository
    root_node_class = ObjectiveTemplateRoot

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ObjectiveTemplateAR
    ) -> ObjectiveTemplate:
        item_ar = self._set_default_parameter_values(item_ar)
        cls = (
            ObjectiveTemplateWithCount
            if item_ar.counts is not None
            else ObjectiveTemplate
        )
        return cls.from_objective_template_ar(item_ar)

    def get_all(
        self,
        status: Optional[str] = None,
        return_study_count: bool = True,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[ObjectiveTemplate]:
        all_items = super().get_all(status, return_study_count)

        # The get_all method is only using neomodel, without Cypher query
        # Therefore, the filtering will be done in this service layer
        filtered_items = service_level_generic_filtering(
            items=all_items,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )

        return filtered_items

    def _create_ar_from_input_values(
        self, template: ObjectiveTemplateCreateInput
    ) -> ObjectiveTemplateAR:
        default_parameter_values = self._create_default_parameter_entries(
            template_name=template.name,
            default_parameter_values=template.defaultParameterValues,
        )

        template_vo, library_vo = self._create_template_vo(
            template, default_parameter_values
        )

        # Get groupings for templates from database
        indications, categories = self._get_groupings(template)

        # Process item to save
        try:
            item = ObjectiveTemplateAR.from_input_values(
                template_value_exists_callback=self.get_check_exists_callback(
                    template=template
                ),
                author=self.user_initials,
                editable_instance=template.editableInstance,
                template=template_vo,
                library=library_vo,
                generate_uid_callback=self.repository.generate_uid_callback,
                confirmatory_testing=template.confirmatoryTesting,
                indications=indications,
                categories=categories,
            )
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

        return item

    @db.transaction
    def patch_groupings(
        self, uid: str, groupings: ObjectiveTemplateEditGroupingsInput
    ) -> ObjectiveTemplate:
        try:
            if groupings.indicationUids is not None:
                self.repository.patch_indications(uid, groupings.indicationUids)
            if groupings.categoryUids is not None:
                self.repository.patch_categories(uid, groupings.categoryUids)
            self.repository.patch_confirmatory_testing(
                uid, groupings.confirmatoryTesting
            )
        finally:
            self.repository.close()

        return self.get_by_uid(uid)

    def _set_default_parameter_values(
        self, item: ObjectiveTemplateAR
    ) -> ObjectiveTemplateAR:
        """This method fetches and sets the default parameter values for the template

        Args:
            item (ObjectiveTemplateAR): The template for which to fetch default parameter values
        """
        # Get default parameter values
        default_parameter_values = self.repository.get_default_parameter_values(
            item.uid
        )

        return ObjectiveTemplateAR(
            _uid=item.uid,
            _editable_instance=item.editable_instance,
            _library=item.library,
            _item_metadata=item.item_metadata,
            _counts=item.counts,
            _study_count=item.study_count,
            _confirmatory_testing=item.confirmatory_testing,
            _template=TemplateVO(
                name=item.template_value.name,
                name_plain=item.template_value.name_plain,
                default_parameter_values=default_parameter_values,
                guidance_text=item.template_value.guidance_text,
            ),
        )

    def _set_groupings(self, item: ObjectiveTemplate) -> None:
        """
        This method fetches and sets the grouping properties to a template.
        """
        # Get indications
        indications = (
            self._repos.dictionary_term_generic_repository.get_template_indications(
                self.root_node_class, item.uid
            )
        )
        if indications:
            item.indications = [
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in indications
            ]
        # Get categories
        category_names = self._repos.ct_term_name_repository.get_template_categories(
            self.root_node_class, item.uid
        )
        category_attributes = (
            self._repos.ct_term_attributes_repository.get_template_categories(
                self.root_node_class, item.uid
            )
        )
        if category_names and category_attributes:
            item.categories = [
                CTTermNameAndAttributes.from_ct_term_ars(
                    ct_term_name_ar=category_name,
                    ct_term_attributes_ar=category_attribute,
                )
                for category_name, category_attribute in zip(
                    category_names, category_attributes
                )
            ]

    def _get_groupings(
        self, template: BaseModel
    ) -> Tuple[
        Sequence[DictionaryTermAR], Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]]
    ]:
        indications: Sequence[DictionaryTermAR] = []
        categories: Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]] = []

        # Fetch the indication objects with corresponding uid from the database
        # It will be needed to save the template, and in the return model
        if template.indicationUids and len(template.indicationUids) > 0:
            for uid in template.indicationUids:
                indication = self._repos.dictionary_term_generic_repository.find_by_uid(
                    term_uid=uid
                )
                indications.append(indication)

        # Fetch the category objects with corresponding uid from the database
        # It will be needed to save the template, and in the return model
        if template.categoryUids and len(template.categoryUids) > 0:
            for uid in template.categoryUids:
                category_name = self._repos.ct_term_name_repository.find_by_uid(
                    term_uid=uid
                )
                category_attributes = (
                    self._repos.ct_term_attributes_repository.find_by_uid(term_uid=uid)
                )
                category = (category_name, category_attributes)
                categories.append(category)

        return indications, categories
