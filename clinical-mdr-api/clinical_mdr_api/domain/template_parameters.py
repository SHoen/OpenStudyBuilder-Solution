from dataclasses import dataclass
from typing import AbstractSet

from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
    TemplateVO,
)


@dataclass
class ParameterTemplateAR(LibraryItemAggregateRootBase):
    _template: TemplateVO
    _library: LibraryVO
    parameter_name: str

    @property
    def template_value(self):
        return self._template

    @property
    def library(self):
        return self._library

    @property
    def name(self):
        return self._template.name

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        template: TemplateVO,
        parameter_name: str,
        library: LibraryVO,
        **kwargs
    ) -> "ParameterTemplateAR":
        # noinspection PyArgumentList
        return cls(
            _uid=None,  # type: ignore
            parameter_name=parameter_name,
            _template=template,
            _library=library,
            _item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author=author
            ),
            **kwargs
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        uid: str,
        template: TemplateVO,
        library: LibraryVO,
        parameter_name: str,
        item_metadata: LibraryItemMetadataVO,
        **kwargs
    ) -> "ParameterTemplateAR":
        # noinspection PyArgumentList
        return cls(
            _uid=uid,  # type: ignore
            _template=template,
            _library=library,
            parameter_name=parameter_name,
            _item_metadata=item_metadata,
            **kwargs
        )

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if (
            self._item_metadata.status == LibraryItemStatus.DRAFT
            and self._item_metadata.major_version == 0
        ):
            return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
        if self._item_metadata.status == LibraryItemStatus.DRAFT:
            return {ObjectAction.APPROVE, ObjectAction.EDIT}
        if self._item_metadata.status == LibraryItemStatus.FINAL:
            return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
        if self._item_metadata.status == LibraryItemStatus.RETIRED:
            return {ObjectAction.REACTIVATE}
        return frozenset()

    def edit_draft(
        self, author: str, change_description: str, template: TemplateVO
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if self._template != template:
            super()._edit_draft(change_description=change_description, author=author)
            self._template = template

    def create_new_version(
        self, author: str, change_description: str, template: TemplateVO
    ) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(
            change_description=change_description, author=author
        )
        self._template = template
