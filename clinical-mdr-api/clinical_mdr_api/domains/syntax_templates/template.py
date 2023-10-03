from dataclasses import dataclass
from typing import AbstractSet, Callable, Self, Sequence

from deprecated.classic import deprecated

from clinical_mdr_api.domains._utils import (
    extract_parameters,
    is_syntax_of_template_name_correct,
    strip_html,
)
from clinical_mdr_api.domains.libraries.parameter_term import ParameterTermEntryVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
    VersioningException,
)
from clinical_mdr_api.exceptions import ValidationException


@dataclass(frozen=True)
class TemplateVO:
    """
    Value Object class representing template values
    """

    # template name value
    name: str
    name_plain: str | None = None
    # Optional, default parameter terms
    default_parameter_terms: Sequence[ParameterTermEntryVO] | None = None

    # template guidance text
    guidance_text: str | None = None

    @staticmethod
    def _extract_parameter_names_from_template_string(
        template_string: str,
    ) -> Sequence[str]:
        return extract_parameters(template_string)

    @property
    def parameter_names(self) -> Sequence[str]:
        return self._extract_parameter_names_from_template_string(self.name)

    @classmethod
    def from_input_values_2(
        cls,
        template_name: str,
        parameter_name_exists_callback: Callable[[str], bool],
        default_parameter_terms: Sequence[ParameterTermEntryVO] | None = None,
        guidance_text: str | None = None,
    ) -> Self:
        if not is_syntax_of_template_name_correct(template_name):
            raise ValidationException(
                f"Template string syntax incorrect: {template_name}"
            )
        result = cls(
            name=template_name,
            name_plain=strip_html(template_name),
            guidance_text=guidance_text,
            default_parameter_terms=tuple(default_parameter_terms)
            if default_parameter_terms
            else None,
        )
        for parameter_name in result.parameter_names:
            if not parameter_name_exists_callback(parameter_name):
                raise ValidationException(
                    f"Unknown parameter name in template string: {parameter_name}"
                )
        return result

    @classmethod
    def from_repository_values(
        cls,
        template_name: str,
        template_name_plain: str,
        guidance_text: str | None = None,
    ) -> Self:
        return cls(
            name=template_name,
            name_plain=template_name_plain,
            guidance_text=guidance_text,
        )


@dataclass
class InstantiationCountsVO:
    _count_draft: int = 0
    _count_final: int = 0
    _count_retired: int = 0

    @property
    def count_draft(self):
        return self._count_draft

    @property
    def count_final(self):
        return self._count_final

    @property
    def count_retired(self):
        return self._count_retired

    @property
    def count_total(self):
        return self._count_draft + self._count_final + self._count_retired

    @classmethod
    def from_counts(cls, final: int, draft: int, retired: int):
        return cls(_count_draft=draft, _count_final=final, _count_retired=retired)


@dataclass
class TemplateAggregateRootBase(LibraryItemAggregateRootBase):
    """
    A generic class implementing versioning of templates. It will be
    inherited from by other Template AR classes.
    """

    _sequence_id: str

    _template: TemplateVO | None = None

    _counts: InstantiationCountsVO | None = None

    _study_count: int = 0

    @property
    def sequence_id(self) -> str:
        return self._sequence_id

    @sequence_id.setter
    def sequence_id(self, sequence_id: str) -> None:
        self.__set_sequence_id(sequence_id)

    # Setter for supporting sequence_id creation
    def __set_sequence_id(self, sequence_id: str) -> None:
        self.__raise_error_if_deleted()
        if self._sequence_id is None:
            self._sequence_id = sequence_id
        else:
            raise TypeError("Cannot modify existing sequence_id.")

    @property
    def study_count(self) -> int:
        return self._study_count

    @property
    def name(self) -> str:
        assert self._template is not None
        return self._template.name

    @property
    def name_plain(self) -> str:
        assert self._template is not None
        return self._template.name_plain

    @property
    def guidance_text(self) -> str | None:
        assert self._template is not None
        return self._template.guidance_text

    @property
    def counts(self):
        return self._counts

    @classmethod
    @deprecated
    def from_neomodel(
        cls,
        uid: str,
        sequence_id: str,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls.from_repository_values(
            uid=uid,
            sequence_id=sequence_id,
            template=template,
            library=library,
            item_metadata=item_metadata,
        )

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        sequence_id: str,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: int = 0,
        counts: InstantiationCountsVO | None = None,
    ) -> Self:
        ar = cls(
            _uid=uid,
            _sequence_id=sequence_id,
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
            _study_count=study_count,
            _counts=counts,
        )
        return ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        template: TemplateVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str | None] = (lambda: None),
        next_available_sequence_id_callback: Callable[[str], str | None] = (
            lambda _: None
        ),
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValidationException(
                f"The library with the name='{library.name}' does not allow to create objects."
            )

        generated_uid = generate_uid_callback()

        ar = cls(
            _uid=generated_uid,
            _sequence_id=next_available_sequence_id_callback(generated_uid),
            _item_metadata=item_metadata,
            _library=library,
            _template=template,
        )

        return ar

    @property
    def template_value(self) -> TemplateVO:
        assert self._template is not None
        return self._template

    def edit_draft(
        self, author: str, change_description: str, template: TemplateVO
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        if self.item_metadata.version >= "1.0" and extract_parameters(
            self.name
        ) != extract_parameters(template.name):
            self._raise_versioning_exception()
        if self._template != template:
            super()._edit_draft(change_description=change_description, author=author)
            self._template = template

    def _raise_versioning_exception(self):
        raise VersioningException(
            "You cannot change number or order of template parameters for a previously approved template."
        )

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
