from dataclasses import dataclass, field
from typing import AbstractSet, Any, Callable, Optional

from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    ObjectAction,
    VersioningActionMixin,
)


@dataclass(frozen=True)
class CTConfigValueVO:
    study_field_name: str
    study_field_data_type: Optional[str]
    study_field_null_value_code: Optional[str]

    configured_codelist_uid: Optional[str]
    configured_term_uid: Optional[str]

    study_field_grouping: Optional[str]
    study_field_name_property: Optional[str]
    study_field_name_api: Optional[str]

    @classmethod
    def from_input_values(
        cls,
        *,
        study_field_name: str,
        study_field_data_type: Optional[str],
        study_field_null_value_code: Optional[str],
        configured_codelist_uid: Optional[str],
        configured_term_uid: Optional[str],
        study_field_grouping: Optional[str],
        study_field_name_property: Optional[str],
        study_field_name_api: Optional[str],
    ) -> "CTConfigValueVO":
        return cls.from_repository_values(
            study_field_name=normalize_string(study_field_name),
            study_field_data_type=study_field_data_type,
            study_field_null_value_code=study_field_null_value_code,
            configured_codelist_uid=configured_codelist_uid,
            configured_term_uid=configured_term_uid,
            study_field_grouping=study_field_grouping,
            study_field_name_property=study_field_name_property,
            study_field_name_api=study_field_name_api,
        )

    @classmethod
    def from_repository_values(
        cls,
        *,
        study_field_name: str,
        study_field_data_type: Optional[str],
        study_field_null_value_code: Optional[str],
        configured_codelist_uid: Optional[str],
        configured_term_uid: Optional[str],
        study_field_grouping: Optional[str],
        study_field_name_property: Optional[str],
        study_field_name_api: Optional[str],
    ) -> "CTConfigValueVO":
        return cls(
            study_field_name=normalize_string(study_field_name),
            study_field_data_type=study_field_data_type,
            study_field_null_value_code=study_field_null_value_code,
            configured_codelist_uid=configured_codelist_uid,
            configured_term_uid=configured_term_uid,
            study_field_grouping=study_field_grouping,
            study_field_name_property=study_field_name_property,
            study_field_name_api=study_field_name_api,
        )

    def validate(
        self,
        ct_configuration_exists_by_name_callback: Callable[[str], bool],
        previous_name: str = None,
    ):
        if (
            ct_configuration_exists_by_name_callback(self.study_field_name)
            and self.study_field_name != previous_name
        ):
            raise ValueError(
                f"{self.__class__.__name__} for field identified by name ({self.study_field_name}) already exists"
            )


@dataclass
class CTConfigAR(VersioningActionMixin):
    _value: CTConfigValueVO

    # Properties from relationship
    _item_metadata: LibraryItemMetadataVO
    _uid: Optional[str] = None

    # used for soft delete
    _is_deleted: bool = field(init=False, default=False)

    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    study_field_name: Optional[str] = None
    study_selection_rel_type: Optional[str] = None

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        raise NotImplementedError("Possible actions retrieval not implemented.")

    @property
    def item_metadata(self):
        return self._item_metadata

    @property
    def value(self):
        return self._value

    @property
    def name(self) -> str:
        return self.value.study_field_name

    def create_new_version(self, author: str):
        super()._create_new_version(author)

    @property
    def uid(self):
        return self._uid

    @property
    def is_deleted(self):
        return self._is_deleted

    def set_uid(self, uid: str):
        self._uid = uid

    def edit_draft(
        self,
        *,
        author: str,
        change_description: str,
        new_ct_config_value: CTConfigValueVO,
        ct_configuration_exists_by_name_callback: Callable[[str], bool],
    ) -> None:
        """
        Edits a draft version of the object, creating a new draft version.
        """
        new_ct_config_value.validate(
            ct_configuration_exists_by_name_callback=ct_configuration_exists_by_name_callback,
            previous_name=self.name,
        )

        if self._value != new_ct_config_value:
            super()._edit_draft(
                author=author, change_description=normalize_string(change_description)
            )

            self._value = new_ct_config_value

    @classmethod
    def from_input_values(
        cls,
        *,
        author: str,
        generate_uid_callback: Callable[[], Optional[str]] = (lambda: None),
        ct_config_value: CTConfigValueVO,
        ct_configuration_exists_by_name_callback: Callable[[str], bool],
    ) -> "CTConfigAR":
        ct_config_value.validate(
            ct_configuration_exists_by_name_callback=ct_configuration_exists_by_name_callback
        )

        result: CTConfigAR = cls(
            _uid=generate_uid_callback(),
            _value=ct_config_value,
            _item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author=author
            ),
        )
        return result

    @classmethod
    def from_repository_values(
        cls,
        *,
        uid: str,
        item_metadata: LibraryItemMetadataVO,
        ct_config_value: CTConfigValueVO,
    ) -> "CTConfigAR":
        result: CTConfigAR = cls(
            _uid=uid, _item_metadata=item_metadata, _value=ct_config_value
        )
        return result

    def _is_edit_allowed_in_non_editable_library(self):
        return True
