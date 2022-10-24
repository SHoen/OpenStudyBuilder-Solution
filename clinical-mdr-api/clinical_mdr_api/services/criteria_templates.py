from typing import Optional, Sequence, Tuple

from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.templates.criteria_template import CriteriaTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    TemplateVO,
    VersioningException,
)
from clinical_mdr_api.domain_repositories.library.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.models.criteria_template import (
    CriteriaTemplateRoot,
)
from clinical_mdr_api.domain_repositories.templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.exceptions import BusinessLogicException, ValidationException
from clinical_mdr_api.models.criteria_template import (
    CriteriaTemplate,
    CriteriaTemplateCreateInput,
    CriteriaTemplateEditGroupingsInput,
    CriteriaTemplateEditInput,
    CriteriaTemplateVersion,
    CriteriaTemplateWithCount,
)
from clinical_mdr_api.models.ct_term import CTTermNameAndAttributes
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import service_level_generic_filtering
from clinical_mdr_api.services.generic_template_service import GenericTemplateService


class CriteriaTemplateService(GenericTemplateService[CriteriaTemplateAR]):
    aggregate_class = CriteriaTemplateAR
    version_class = CriteriaTemplateVersion
    repository_interface = CriteriaTemplateRepository
    object_repository_interface = CriteriaRepository
    root_node_class = CriteriaTemplateRoot

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaTemplateAR
    ) -> CriteriaTemplate:
        item_ar = self._set_default_parameter_values(item_ar)
        cls = (
            CriteriaTemplateWithCount
            if item_ar.study_count is not None
            else CriteriaTemplate
        )
        return cls.from_criteria_template_ar(item_ar)

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
    ) -> GenericFilteringReturn[CriteriaTemplate]:
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
        self, template: CriteriaTemplateCreateInput
    ) -> CriteriaTemplateAR:
        default_parameter_values = self._create_default_parameter_entries(
            template_name=template.name,
            default_parameter_values=template.defaultParameterValues,
        )

        template_vo, library_vo = self._create_template_vo(
            template, default_parameter_values
        )

        # Get groupings for templates from database
        criteria_type, indications, categories, sub_categories = self._get_groupings(
            template
        )

        # Process item to save
        try:
            item = CriteriaTemplateAR.from_input_values(
                template_value_exists_callback=self.get_check_exists_callback(
                    template=template
                ),
                author=self.user_initials,
                editable_instance=template.editableInstance,
                template=template_vo,
                library=library_vo,
                generate_uid_callback=self.repository.generate_uid_callback,
                indications=indications,
                criteria_type=criteria_type,
                categories=categories,
                sub_categories=sub_categories,
            )
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

        return item

    @db.transaction
    def edit_draft(
        self, uid: str, template: CriteriaTemplateEditInput
    ) -> CriteriaTemplate:
        try:
            item = self._find_by_uid_or_raise_not_found(uid, for_update=True)

            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                template_guidance_text=template.guidanceText,
                parameter_name_exists_callback=self._parameter_name_exists,
            )

            item.edit_draft(
                author=self.user_initials,
                change_description=template.changeDescription,
                template=template_vo,
            )

            # Save item
            self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def patch_groupings(
        self, uid: str, groupings: CriteriaTemplateEditGroupingsInput
    ) -> CriteriaTemplate:
        try:
            if groupings.indicationUids is not None:
                self.repository.patch_indications(uid, groupings.indicationUids)
            if groupings.categoryUids is not None:
                self.repository.patch_categories(uid, groupings.categoryUids)
            if groupings.subCategoryUids is not None:
                self.repository.patch_sub_categories(uid, groupings.subCategoryUids)
        finally:
            self.repository.close()

        return self.get_by_uid(uid)

    def _set_default_parameter_values(
        self, item: CriteriaTemplateAR
    ) -> CriteriaTemplateAR:
        """This method fetches and sets the default parameter values for the template

        Args:
            item (CriteriaTemplateAR): The template for which to fetch default parameter values
        """
        # Get default parameter values
        default_parameter_values = self.repository.get_default_parameter_values(
            item.uid
        )

        return CriteriaTemplateAR(
            _uid=item.uid,
            _editable_instance=item.editable_instance,
            _library=item.library,
            _item_metadata=item.item_metadata,
            _counts=item.counts,
            _study_count=item.study_count,
            _indications=item.indications,
            _type=item.type,
            _categories=item.categories,
            _sub_categories=item.sub_categories,
            _template=TemplateVO(
                name=item.template_value.name,
                name_plain=item.template_value.name_plain,
                default_parameter_values=default_parameter_values,
                guidance_text=item.template_value.guidance_text,
            ),
        )

    def _set_groupings(self, item: CriteriaTemplate) -> None:
        """
        This method fetches and sets the grouping properties to a template.
        """
        # Get type
        criteria_type_name = (
            self._repos.ct_term_name_repository.get_template_criteria_type(
                self.root_node_class, item.uid
            )
        )
        criteria_type_attributes = (
            self._repos.ct_term_attributes_repository.get_template_criteria_type(
                self.root_node_class, item.uid
            )
        )
        if criteria_type_name is not None and criteria_type_attributes is not None:
            item.type = CTTermNameAndAttributes.from_ct_term_ars(
                ct_term_name_ar=criteria_type_name,
                ct_term_attributes_ar=criteria_type_attributes,
            )
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
        # Get sub_categories
        sub_category_names = (
            self._repos.ct_term_name_repository.get_template_sub_categories(
                self.root_node_class, item.uid
            )
        )
        sub_category_attributes = (
            self._repos.ct_term_attributes_repository.get_template_sub_categories(
                self.root_node_class, item.uid
            )
        )
        if sub_category_names and sub_category_attributes:
            item.subCategories = [
                CTTermNameAndAttributes.from_ct_term_ars(
                    ct_term_name_ar=category_name,
                    ct_term_attributes_ar=category_attribute,
                )
                for category_name, category_attribute in zip(
                    sub_category_names, sub_category_attributes
                )
            ]

    def _get_groupings(
        self, template: BaseModel, template_uid: Optional[str] = None
    ) -> Tuple[
        Optional[Tuple[CTTermNameAR, CTTermAttributesAR]],
        Sequence[DictionaryTermAR],
        Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]],
        Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]],
    ]:
        criteria_type: Optional[Tuple[CTTermNameAR, CTTermAttributesAR]] = None
        indications: Sequence[DictionaryTermAR] = []
        categories: Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]] = []
        sub_categories: Sequence[Tuple[CTTermNameAR, CTTermAttributesAR]] = []

        if hasattr(template, "typeUid") and template.typeUid is not None:
            criteria_type_term_uid = template.typeUid
        else:
            criteria_type_term_uid = (
                self._repos.criteria_template_repository.get_criteria_type_uid(
                    template_uid
                )
            )
        if criteria_type_term_uid is not None:
            criteria_type_name = self._repos.ct_term_name_repository.find_by_uid(
                term_uid=criteria_type_term_uid
            )
            criteria_type_attributes = (
                self._repos.ct_term_attributes_repository.find_by_uid(
                    term_uid=criteria_type_term_uid
                )
            )
            criteria_type = (criteria_type_name, criteria_type_attributes)

        if template.indicationUids and len(template.indicationUids) > 0:
            for uid in template.indicationUids:
                indication = self._repos.dictionary_term_generic_repository.find_by_uid(
                    term_uid=uid
                )
                indications.append(indication)

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

        if template.subCategoryUids and len(template.subCategoryUids) > 0:
            for uid in template.subCategoryUids:
                category_name = self._repos.ct_term_name_repository.find_by_uid(
                    term_uid=uid
                )
                category_attributes = (
                    self._repos.ct_term_attributes_repository.find_by_uid(term_uid=uid)
                )
                category = (category_name, category_attributes)
                sub_categories.append(category)

        return criteria_type, indications, categories, sub_categories
