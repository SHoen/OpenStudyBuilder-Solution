import abc
import datetime
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import AbstractSet, Any, Callable, Optional, Sequence, Tuple

from deprecated.classic import deprecated

from clinical_mdr_api.domain._utils import (
    extract_parameters,
    is_syntax_of_template_name_correct,
    strip_html,
)
from clinical_mdr_api.domain.library.parameter_value import ParameterValueEntryVO


class VersioningException(Exception):
    def __init__(self, msg, error_code=500, code="unexpected_error"):
        self.error_code = error_code
        self.code = code
        self.msg = msg
        super().__init__(msg)


@dataclass(frozen=True)
class LibraryVO:
    """
    Value object representing Library object. ie. Sponsor, CDISC etc.
    """

    @classmethod
    def from_input_values_2(
        cls,
        library_name: str,
        is_library_editable_callback: Callable[[str], Optional[bool]],
    ) -> "LibraryVO":
        is_library_editable_callback_result: Optional[
            bool
        ] = is_library_editable_callback(library_name)

        if is_library_editable_callback_result is None:
            raise ValueError(
                f"Can't infer if library: {library_name} is editable, "
                f"because the is_editable callback wasn't passed."
            )

        return cls(name=library_name, is_editable=is_library_editable_callback_result)

    @classmethod
    def from_repository_values(
        cls, library_name: str, is_editable: bool
    ) -> "LibraryVO":
        return cls(name=library_name, is_editable=is_editable)

    name: str
    is_editable: bool


class LibraryItemStatus(Enum):
    """
    Enumerator for library item statuses
    """

    FINAL = "Final"
    DRAFT = "Draft"
    RETIRED = "Retired"


class ObjectAction(Enum):
    """
    Enumerator for library item actions that can change library item status
    """

    APPROVE = "approve"
    EDIT = "edit"
    DELETE = "delete"
    NEWVERSION = "newVersion"
    INACTIVATE = "inactivate"
    REACTIVATE = "reactivate"


@dataclass(frozen=True)
class LibraryItemMetadataVO:
    """
    A 'Version' metadata object represents (in the data layer)
    VersionRelationship - it contains all versioning related information
    """

    # Versioning information
    _change_description: str
    _status: LibraryItemStatus
    _author: str
    _start_date: datetime.datetime
    _end_date: Optional[datetime.datetime]

    _major_version: int
    _minor_version: int

    @classmethod
    def get_initial_item_metadata(cls, author: str) -> "LibraryItemMetadataVO":
        return cls(
            _change_description="Initial version",
            _status=LibraryItemStatus.DRAFT,
            _author=author,
            _start_date=datetime.datetime.now(),
            _end_date=None,
            _major_version=0,
            _minor_version=1,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        change_description: str,
        status: LibraryItemStatus,
        author: str,
        start_date: datetime.datetime,
        end_date: Optional[datetime.datetime],
        major_version: int,
        minor_version: int,
    ) -> "LibraryItemMetadataVO":
        assert major_version >= 0
        assert minor_version >= 0
        assert minor_version > 0 or major_version > 0
        return cls(
            _change_description=change_description,
            _status=status,
            _author=author,
            _start_date=start_date,
            _end_date=end_date,
            _major_version=major_version,
            _minor_version=minor_version,
        )

    @property
    def change_description(self):
        return self._change_description

    @property
    def status(self) -> LibraryItemStatus:
        return self._status

    @property
    def user_initials(self) -> str:
        return self._author

    @property
    def start_date(self) -> datetime.datetime:
        return self._start_date

    @property
    def end_date(self) -> Optional[datetime.datetime]:
        return self._end_date

    @property
    def version(self) -> str:
        return f"{self._major_version}.{self._minor_version}"

    @property
    def major_version(self) -> int:
        return self._major_version

    @property
    def minor_version(self) -> int:
        return self._minor_version

    def _get_new_version(self, new_status: LibraryItemStatus) -> Tuple[int, int]:
        """
        Helper method for creating new version label
        changing major and minor versions depending on new status.
        It does not update object version information
        """
        v_major, v_minor = self._major_version, self._minor_version
        if (
            self._status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.FINAL
        ):
            v_major = v_major + 1
            v_minor = 0
        elif (
            self._status == LibraryItemStatus.DRAFT
            and new_status == LibraryItemStatus.DRAFT
        ):
            v_minor = v_minor + 1
        elif (
            self._status in [LibraryItemStatus.FINAL, LibraryItemStatus.RETIRED]
            and new_status == LibraryItemStatus.DRAFT
        ):
            v_minor = 1
        elif (
            self._status == LibraryItemStatus.RETIRED
            and new_status == LibraryItemStatus.RETIRED
        ):
            v_major += 1
        elif (
            self._status == LibraryItemStatus.FINAL
            and new_status == LibraryItemStatus.FINAL
        ):
            v_major += 1
        return v_major, v_minor

    def new_draft_version(
        self, author: str, change_description: str
    ) -> "LibraryItemMetadataVO":
        """
        Creates new object in draft version updating properly all values
        """
        if self._status in [LibraryItemStatus.DRAFT, LibraryItemStatus.FINAL]:
            major, minor = self._get_new_version(LibraryItemStatus.DRAFT)
            return replace(
                self,
                _start_date=datetime.datetime.now(),
                _end_date=None,
                _status=LibraryItemStatus.DRAFT,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("Cannot create new Draft version")

    def new_final_version(
        self, author: str, change_description: str
    ) -> "LibraryItemMetadataVO":
        """
        Creates new object in final version updating properly all values
        """
        if self._status in [LibraryItemStatus.DRAFT, LibraryItemStatus.RETIRED]:
            major, minor = self._get_new_version(LibraryItemStatus.FINAL)
            return replace(
                self,
                _start_date=datetime.datetime.now(),
                _end_date=None,
                _status=LibraryItemStatus.FINAL,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("The object is not in draft status.")

    def new_retired_version(
        self, author: str, change_description: str
    ) -> "LibraryItemMetadataVO":
        """
        Creates new object in retired version updating properly all values
        """
        if self._status in [LibraryItemStatus.FINAL]:
            major, minor = self._get_new_version(LibraryItemStatus.RETIRED)
            return replace(
                self,
                _start_date=datetime.datetime.now(),
                _end_date=None,
                _status=LibraryItemStatus.RETIRED,
                _major_version=major,
                _minor_version=minor,
                _change_description=change_description,
                _author=author,
            )
        raise VersioningException("Cannot retire draft version.")

    # @deprecated
    def new_version_start_date(self, author, change_description, date):
        """
        Creates new object in the same version - used for cascading updates
        """
        major, minor = self._get_new_version(self.status)
        return replace(
            self,
            _start_date=date,
            _major_version=major,
            _minor_version=minor,
            _change_description=change_description,
            _author=author,
        )


class VersioningActionMixin:

    # Setting labels of updated objects
    _NEW_VERSION_LABEL = "New draft created"
    _FINAL_VERSION_LABEL = "Approved version"
    _RETIRED_VERSION_LABEL = "Deactivated version"
    _REACTIVATED_VERSION_LABEL = "Reactivated version"
    # implementations of basic versioning actions
    def approve(
        self, author: str, change_description: str = _FINAL_VERSION_LABEL
    ) -> None:
        """
        Approves the latest draft version and sets the latest version to final.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        new_metadata = self._item_metadata.new_final_version(
            author=author, change_description=change_description
        )
        if self.item_metadata.status != LibraryItemStatus.DRAFT:
            raise VersioningException(
                "Only DRAFT version can be approved.",
                error_code=403,
                code="invalid_status_non_draft",
            )
        self._item_metadata = new_metadata

    def inactivate(
        self, author: str, change_description: str = _RETIRED_VERSION_LABEL
    ) -> None:
        """
        Inactivates latest version.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        self._item_metadata = self._item_metadata.new_retired_version(
            author=author, change_description=change_description
        )

    def reactivate(
        self, author: str, change_description: str = _REACTIVATED_VERSION_LABEL
    ) -> None:
        """
        Reactivates latest retired version and sets the version to draft.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        if self.item_metadata.status != LibraryItemStatus.RETIRED:
            raise VersioningException("Only RETIRED version can be reactivated.")
        new_metadata = self._item_metadata.new_final_version(
            author=author, change_description=change_description
        )
        self._item_metadata = new_metadata

    def _create_new_version(
        self, author: str, change_description: str = _NEW_VERSION_LABEL
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()
        new_metadata = self._item_metadata.new_draft_version(
            author=author, change_description=change_description
        )
        if self.item_metadata.status != LibraryItemStatus.FINAL:
            raise VersioningException(
                "New draft version can be created only for FINAL versions.",
                error_code=403,
                code="invalid_status_non_final",
            )
        self._item_metadata = new_metadata

    def _edit_draft(self, author: str, change_description: str) -> None:
        """
        Edits a draft version of the object, creating a new draft version.
        """
        self.__raise_error_if_deleted()
        self.__raise_error_if_edit_is_not_allowed_in_the_library()

        if self._item_metadata.status != LibraryItemStatus.DRAFT:
            raise VersioningException("The object is not in draft status.")
        self._item_metadata = self._item_metadata.new_draft_version(
            author=author, change_description=change_description
        )

    def soft_delete(self) -> None:
        if self._item_metadata.major_version == 0:
            self._is_deleted = True
        else:
            raise VersioningException("Object has been accepted")

    @abc.abstractmethod
    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise NotImplementedError("You cannot get possible actions for abstract class")

    def __raise_error_if_deleted(self) -> None:
        if self.is_deleted:
            raise ValueError("Cannot use deleted object.")

    # Validator functions
    def __raise_error_if_edit_is_not_allowed_in_the_library(self) -> None:
        # some of the derived classes allow to edit theirs instances even
        # when connected to not editable library
        if self._is_edit_allowed_in_non_editable_library():
            return
        if not self.library.is_editable:
            raise VersioningException(
                "Library is not editable.", error_code=403, code="invalid_status_final"
            )


@dataclass
class LibraryItemAggregateRootBase(VersioningActionMixin, abc.ABC):
    """
    An abstract generic library item aggregate for versioning objects
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    # Properties from VersionRoot
    _uid: Optional[str]

    _library: LibraryVO

    # Properties from relationship
    _item_metadata: LibraryItemMetadataVO

    # used for soft delete
    _is_deleted: bool = field(init=False, default=False)

    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    # Getters
    @property
    def item_metadata(self) -> LibraryItemMetadataVO:
        self.__raise_error_if_deleted()
        return self._item_metadata

    @property
    def library(self) -> LibraryVO:
        self.__raise_error_if_deleted()
        return self._library

    @property
    def uid(self) -> str:
        return self._uid  # type: ignore

    @uid.setter
    def uid(self, uid: str) -> None:
        self.__set_uid(uid)

    @property
    def is_deleted(self) -> bool:
        return self._is_deleted

    # Setter for supporting uid creation
    def __set_uid(self, uid: str) -> None:
        self.__raise_error_if_deleted()
        if self._uid is None:
            self._uid = uid
        else:
            raise TypeError("Cannot modify existing uid.")

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return False

    @classmethod
    def _from_input_values(
        cls,
        *,
        author: str,
        library: LibraryVO,
        uid_supplier: Callable[[], Optional[str]] = lambda: None,
        **kwargs,
    ) -> "LibraryItemAggregateRootBase":
        if not library.is_editable:
            raise ValueError("Creating objects in non-editable library is forbidden.")

        # noinspection PyArgumentList
        return cls(
            _uid=uid_supplier(),
            _library=library,  # type: ignore
            _item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author=author
            ),
            **kwargs,
        )

    @classmethod
    def _from_repository_values(
        cls,
        *,
        library: LibraryVO,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        **kwargs,
    ) -> "LibraryItemAggregateRootBase":
        # noinspection PyArgumentList
        return cls(
            _uid=uid,
            _library=library,  # type: ignore
            _item_metadata=item_metadata,
            **kwargs,
        )

    def __raise_error_if_deleted(self) -> None:
        if self.is_deleted:
            raise ValueError("Cannot use deleted object.")


@dataclass(frozen=True)
class TemplateVO:
    """
    Value Object class representing template values
    """

    # template name value
    name: str
    name_plain: Optional[str] = None
    # Optional, default parameter values
    default_parameter_values: Optional[Sequence[ParameterValueEntryVO]] = None

    # template guidance text
    guidance_text: Optional[str] = None

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
        default_parameter_values: Optional[Sequence[ParameterValueEntryVO]] = None,
        template_guidance_text: Optional[str] = None,
    ) -> "TemplateVO":
        # TODO: rename method after removing from_input_values
        if not is_syntax_of_template_name_correct(template_name):
            raise ValueError(f"Template string syntax incorrect: {template_name}")
        result = cls(
            name=template_name,
            name_plain=strip_html(template_name),
            guidance_text=template_guidance_text,
            default_parameter_values=tuple(default_parameter_values)
            if default_parameter_values
            else None,
        )
        for parameter_name in result.parameter_names:
            if not parameter_name_exists_callback(parameter_name):
                raise ValueError(
                    f"Unknown parameter name in template string: {parameter_name}"
                )
        return result

    @classmethod
    def from_repository_values(
        cls,
        template_name: str,
        template_name_plain: str,
        template_guidance_text: Optional[str] = None,
    ) -> "TemplateVO":
        return cls(
            name=template_name,
            name_plain=template_name_plain,
            guidance_text=template_guidance_text,
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

    _editable_instance: bool

    _template: Optional[TemplateVO] = None

    _counts: Optional[InstantiationCountsVO] = None

    _study_count: Optional[int] = None

    @property
    def editable_instance(self) -> bool:
        return self._editable_instance

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
    def guidance_text(self) -> Optional[str]:
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
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> "TemplateAggregateRootBase":
        return cls.from_repository_values(
            uid=uid,
            editable_instance=editable_instance,
            template=template,
            library=library,
            item_metadata=item_metadata,
        )

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        editable_instance: bool,
        template: TemplateVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
        study_count: Optional[int] = None,
        counts: Optional[InstantiationCountsVO] = None,
    ) -> "TemplateAggregateRootBase":
        ar = cls(
            _uid=uid,
            _editable_instance=editable_instance,
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
        editable_instance: bool,
        author: str,
        template: TemplateVO,
        library: LibraryVO,
        template_value_exists_callback: Callable[
            [TemplateVO], bool
        ],  # = (lambda _: False),
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
    ) -> "TemplateAggregateRootBase":
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(author=author)
        if not library.is_editable:
            raise ValueError(
                f"The library with the name='{library.name}' does not allow to create objects."
            )
        if template_value_exists_callback(template):
            raise ValueError(
                f"Duplicate templates not allowed - template exists: {template.name}"
            )
        ar = cls(
            _uid=generate_uid_callback(),
            _editable_instance=editable_instance,
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
            if self.__class__.__name__ == "TimeframeTemplateAR":
                raise VersioningException(
                    "The template parameters cannot be modified after being a final version, only the plain text can be modified"
                )
            raise VersioningException(
                "You cannot change number or order of template parameters."
            )
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
