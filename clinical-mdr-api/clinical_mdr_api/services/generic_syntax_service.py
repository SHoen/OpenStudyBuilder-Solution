import abc
from typing import Generic, TypeVar

from neomodel import db
from pydantic import BaseModel

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    ConflictErrorException,
    NotFoundException,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermModel,
    SimpleTermName,
)
from clinical_mdr_api.models.generic_models import SimpleNameModel
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import calculate_diffs, raise_404_if_none

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericSyntaxService(Generic[_AggregateRootType], abc.ABC):
    @abc.abstractmethod
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: _AggregateRootType
    ) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def create(self, template: BaseModel) -> BaseModel:
        raise NotImplementedError

    @abc.abstractmethod
    def edit_draft(self, uid: str, template: BaseModel) -> BaseModel:
        raise NotImplementedError

    aggregate_class: type
    version_class: type
    repository_interface: type
    _repos: MetaRepository
    user_initials: str | None

    def __init__(self, user: str | None = None):
        self.user_initials = user if user is not None else "TODO Initials"
        self._repos = MetaRepository()

    def __del__(self):
        self._repos.close()

    @property
    def repository(self) -> GenericRepository[_AggregateRootType]:
        assert self._repos is not None
        return self.repository_interface()

    @property
    def study_repository(self) -> StudyDefinitionRepository:
        return self._repos.study_definition_repository

    def get_by_uid(
        self,
        uid: str,
        status: str | None = None,
        version: str | None = None,
        return_study_count: bool | None = True,
    ) -> BaseModel:
        item = self.repository.find_by_uid(
            uid,
            status=LibraryItemStatus(status) if status is not None else None,
            version=version,
            return_study_count=return_study_count,
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def get_specific_version(
        self, uid: str, version: str, return_study_count: bool | None = True
    ) -> BaseModel:
        item = self.repository.find_by_uid(
            uid, return_study_count=return_study_count, version=version
        )
        return self._transform_aggregate_root_to_pydantic_model(item)

    def _find_by_uid_or_raise_not_found(
        self,
        uid: str,
        *,
        version: str | None = None,
        status: LibraryItemStatus | None = None,
        for_update: bool = False,
        return_study_count: bool | None = True,
    ) -> _AggregateRootType:
        item = self.repository.find_by_uid(
            uid,
            for_update=for_update,
            version=version,
            status=status,
            return_study_count=return_study_count,
        )
        if item is None:
            raise NotFoundException(
                f"{self.aggregate_class.__name__} with uid {uid} does not exist or there's no version with requested status or version number."
            )
        return item

    @db.transaction
    def retrieve_audit_trail(
        self,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        ars, total = self.repository.retrieve_audit_trail(
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )

        all_items = [self._transform_aggregate_root_to_pydantic_model(ar) for ar in ars]

        return GenericFilteringReturn.create(items=all_items, total=total)

    @db.transaction
    def get_all(
        self,
        status: str | None = None,
        return_study_count: bool | None = True,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.OR,
        total_count: bool = False,
        for_audit_trail: bool = False,
    ) -> GenericFilteringReturn[BaseModel]:
        all_items, total_count = self.repository.get_all(
            status=LibraryItemStatus(status) if status else None,
            return_study_count=return_study_count,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
            for_audit_trail=for_audit_trail,
        )

        return GenericFilteringReturn.create(
            items=[
                self._transform_aggregate_root_to_pydantic_model(item)
                for item in all_items
            ],
            total=total_count,
        )

    def get_distinct_values_for_header(
        self,
        field_name: str,
        status: str | None = None,
        search_string: str | None = "",
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        result_count: int = 10,
    ):
        return self.repository.get_headers(
            field_name=field_name,
            search_string=search_string,
            status=LibraryItemStatus(status) if status else None,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )

    def _parameter_name_exists(self, parameter_name: str) -> bool:
        return self._repos.parameter_repository.parameter_name_exists(parameter_name)

    @db.transaction
    def approve(self, uid: str) -> BaseModel:
        try:
            item = self.repository.find_by_uid(uid, for_update=True)
            uses = self.repository.check_usage_count(uid)
            if uses > 0:
                raise ConflictErrorException(
                    f"Template '{item.name}' is used in {uses} instantiations."
                )
            item.approve(author=self.user_initials)
            self.repository.save(item)

            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def create_new_version(self, uid: str, template: BaseModel) -> BaseModel:
        try:
            template_vo = TemplateVO.from_input_values_2(
                template_name=template.name,
                parameter_name_exists_callback=self._parameter_name_exists,
            )
            item = self.repository.find_by_uid(uid, for_update=True)

            item.create_new_version(
                author=self.user_initials,
                change_description=template.change_description,
                template=template_vo,
            )
            self.repository.save(item)
            return self._transform_aggregate_root_to_pydantic_model(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    @db.transaction
    def inactivate_final(self, uid: str) -> BaseModel:
        item = self.repository.find_by_uid(uid, for_update=True)

        try:
            item.inactivate(author=self.user_initials)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def reactivate_retired(self, uid: str) -> BaseModel:
        item = self.repository.find_by_uid(uid, for_update=True)

        try:
            item.reactivate(author=self.user_initials)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)

    @db.transaction
    def get_version_history(
        self, uid: str, return_study_count: bool | None = True
    ) -> list[BaseModel]:
        if self.version_class is not None:
            all_versions = self.repository.find_by_uid(
                uid=uid, return_study_count=return_study_count, for_audit_trail=True
            )
            versions = [
                self._transform_aggregate_root_to_pydantic_model(_).dict()
                for _ in all_versions
            ]

            return calculate_diffs(versions, self.version_class)

        return []

    @db.transaction
    def get_releases(
        self, uid: str, return_study_count: bool | None = True
    ) -> list[BaseModel]:
        releases = self.repository.find_by_uid(
            uid=uid,
            return_study_count=return_study_count,
            status=LibraryItemStatus.FINAL,
            for_audit_trail=True,
        )
        return [
            self._transform_aggregate_root_to_pydantic_model(item) for item in releases
        ]

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        try:
            item = self.repository.find_by_uid(uid, for_update=True)
            item.soft_delete()
            self.repository.save(item)
        except VersioningException as e:
            raise BusinessLogicException(e.msg) from e

    def _get_indexings(
        self, template: BaseModel
    ) -> tuple[
        list[SimpleTermModel],
        list[SimpleCTTermNameAndAttributes],
        list[SimpleCTTermNameAndAttributes],
        list[SimpleNameModel],
        list[SimpleNameModel],
        list[SimpleNameModel],
        SimpleCTTermNameAndAttributes | None,
    ]:
        indications: list[SimpleTermModel] = []
        categories: list[SimpleCTTermNameAndAttributes] = []
        sub_categories: list[SimpleCTTermNameAndAttributes] = []
        activities: list[SimpleNameModel] = []
        activity_groups: list[SimpleNameModel] = []
        activity_subgroups: list[SimpleNameModel] = []
        template_type: SimpleCTTermNameAndAttributes | None = None

        template_type_term_uid = getattr(template, "type_uid", None)

        if template_type_term_uid is not None:
            template_type_name = self._repos.ct_term_name_repository.find_by_uid(
                term_uid=template_type_term_uid
            )
            raise_404_if_none(
                template_type_name,
                f"Template type with uid '{template_type_term_uid}' does not exist.",
            )
            template_type_attributes = (
                self._repos.ct_term_attributes_repository.find_by_uid(
                    term_uid=template_type_term_uid
                )
            )
            raise_404_if_none(
                template_type_attributes,
                f"Template type with uid '{template_type_term_uid}' does not exist.",
            )
            template_type = SimpleCTTermNameAndAttributes(
                term_uid=template_type_term_uid,
                name=SimpleTermName(
                    sponsor_preferred_name=template_type_name.name,
                    sponsor_preferred_name_sentence_case=template_type_name.ct_term_vo.name_sentence_case,
                ),
                attributes=SimpleTermAttributes(
                    code_submission_value=template_type_attributes.ct_term_vo.code_submission_value,
                    nci_preferred_name=template_type_attributes.ct_term_vo.preferred_term,
                ),
            )

        if (
            getattr(template, "indication_uids", None)
            and len(template.indication_uids) > 0
        ):
            for uid in template.indication_uids:
                indication = self._repos.dictionary_term_generic_repository.find_by_uid(
                    term_uid=uid
                )
                raise_404_if_none(
                    indication,
                    f"Indication with uid '{uid}' does not exist.",
                )
                indications.append(
                    SimpleTermModel(term_uid=indication.uid, name=indication.name)
                )

        if getattr(template, "category_uids", None) and len(template.category_uids) > 0:
            for uid in template.category_uids:
                category_name = self._repos.ct_term_name_repository.find_by_uid(
                    term_uid=uid
                )
                category_attributes = (
                    self._repos.ct_term_attributes_repository.find_by_uid(term_uid=uid)
                )
                raise_404_if_none(
                    category_name,
                    f"Category with uid '{uid}' does not exist.",
                )

                categories.append(
                    SimpleCTTermNameAndAttributes(
                        term_uid=uid,
                        name=SimpleTermName(
                            sponsor_preferred_name=category_name.name,
                            sponsor_preferred_name_sentence_case=category_name.ct_term_vo.name_sentence_case,
                        ),
                        attributes=SimpleTermAttributes(
                            code_submission_value=category_attributes.ct_term_vo.code_submission_value,
                            nci_preferred_name=category_attributes.ct_term_vo.preferred_term,
                        ),
                    )
                )

        if (
            getattr(template, "sub_category_uids", None)
            and len(template.sub_category_uids) > 0
        ):
            for uid in template.sub_category_uids:
                subcategory_name = self._repos.ct_term_name_repository.find_by_uid(
                    term_uid=uid
                )
                subcategory_attributes = (
                    self._repos.ct_term_attributes_repository.find_by_uid(term_uid=uid)
                )
                raise_404_if_none(
                    subcategory_name,
                    f"Subcategory with uid '{uid}' does not exist.",
                )
                sub_categories.append(
                    SimpleCTTermNameAndAttributes(
                        term_uid=uid,
                        name=SimpleTermName(
                            sponsor_preferred_name=subcategory_name.name,
                            sponsor_preferred_name_sentence_case=subcategory_name.ct_term_vo.name_sentence_case,
                        ),
                        attributes=SimpleTermAttributes(
                            code_submission_value=subcategory_attributes.ct_term_vo.code_submission_value,
                            nci_preferred_name=subcategory_attributes.ct_term_vo.preferred_term,
                        ),
                    )
                )

        if getattr(template, "activity_uids", None) and len(template.activity_uids) > 0:
            for uid in template.activity_uids:
                activity = self._repos.activity_repository.find_by_uid_2(uid=uid)
                raise_404_if_none(
                    activity,
                    f"Activity with uid '{uid}' does not exist.",
                )
                activities.append(
                    SimpleNameModel(
                        uid=activity.uid,
                        name=activity.name,
                        name_sentence_case=activity.concept_vo.name_sentence_case,
                    )
                )

        if (
            getattr(template, "activity_group_uids", None)
            and len(template.activity_group_uids) > 0
        ):
            for uid in template.activity_group_uids:
                activity_group = self._repos.activity_group_repository.find_by_uid_2(
                    uid=uid
                )
                raise_404_if_none(
                    activity_group,
                    f"Activity group with uid '{uid}' does not exist.",
                )
                activity_groups.append(
                    SimpleNameModel(
                        uid=activity_group.uid,
                        name=activity_group.name,
                        name_sentence_case=activity_group.concept_vo.name_sentence_case,
                    )
                )

        if (
            getattr(template, "activity_subgroup_uids", None)
            and len(template.activity_subgroup_uids) > 0
        ):
            for uid in template.activity_subgroup_uids:
                activity_subgroup = (
                    self._repos.activity_subgroup_repository.find_by_uid_2(uid=uid)
                )
                raise_404_if_none(
                    activity_subgroup,
                    f"Activity subgroup with uid '{uid}' does not exist.",
                )
                activity_subgroups.append(
                    SimpleNameModel(
                        uid=activity_subgroup.uid,
                        name=activity_subgroup.name,
                        name_sentence_case=activity_subgroup.concept_vo.name_sentence_case,
                    )
                )

        return (
            indications,
            categories,
            sub_categories,
            activities,
            activity_groups,
            activity_subgroups,
            template_type,
        )

    @db.transaction
    def patch_indexings(self, uid: str, indexings: BaseModel) -> BaseModel:
        self.repository.find_by_uid(uid)

        try:
            if getattr(indexings, "indication_uids", None):
                self.repository.patch_indications(uid, indexings.indication_uids)
            if getattr(indexings, "category_uids", None):
                self.repository.patch_categories(uid, indexings.category_uids)
            if getattr(indexings, "sub_category_uids", None):
                self.repository.patch_subcategories(uid, indexings.sub_category_uids)
            if hasattr(indexings, "is_confirmatory_testing"):
                self.repository.patch_is_confirmatory_testing(
                    uid, indexings.is_confirmatory_testing
                )
        finally:
            self.repository.close()

        return self.get_by_uid(uid)
