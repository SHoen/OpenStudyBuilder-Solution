from datetime import datetime
from typing import Callable, Optional, Sequence, cast

from fastapi import Depends
from neomodel import db
from pydantic.main import BaseModel

from clinical_mdr_api.domain.configurations import CTConfigAR, CTConfigValueVO
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from clinical_mdr_api.models.configuration import (
    CTConfigModel,
    CTConfigPatchInput,
    CTConfigPostInput,
)
from clinical_mdr_api.oauth import get_current_user_id
from clinical_mdr_api.services._meta_repository import MetaRepository


def _get_current_user_id(current_user_id: str = Depends(get_current_user_id)) -> str:
    return current_user_id


def _get_meta_repository(
    user_id: str = Depends(_get_current_user_id),
) -> MetaRepository:
    return MetaRepository(user=user_id)


class CTConfigService:
    _repos: MetaRepository
    _user_id: str

    def __init__(
        self,
        *,
        user_id: str = Depends(_get_current_user_id),
        meta_repository: MetaRepository = Depends(_get_meta_repository)
    ):
        self._repos = meta_repository
        self._user_id = user_id

    @db.transaction
    def get_all(self) -> Sequence[CTConfigModel]:
        configs = [
            CTConfigModel.from_ct_config_ar(_)
            for _ in self._repos.ct_config_repository.find_all()
        ]
        return configs

    @db.transaction
    def get_by_uid(
        self,
        uid: str,
        *,
        at_specified_datetime: Optional[datetime],
        status: Optional[str],
        version: Optional[str]
    ) -> CTConfigModel:

        status_as_enum = LibraryItemStatus(status) if status is not None else None

        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid,
            status=status_as_enum,
            version=version,
            for_update=False,
            at_specific_date=at_specified_datetime,
        )
        if ct_config_ar is None:
            raise NotFoundException(
                "Not Found - The concept with the specified 'uid' could not be found"
            )
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def get_versions(self, uid: str) -> Sequence[CTConfigModel]:
        versions = self._repos.ct_config_repository.get_all_versions_2(uid)
        if not versions:
            raise NotFoundException("Resource not found.")
        return [CTConfigModel.from_ct_config_ar(_) for _ in versions]

    @db.transaction
    def post(self, post_input: CTConfigPostInput) -> CTConfigModel:
        try:
            ct_config_ar = CTConfigAR.from_input_values(
                author=self._user_id,
                generate_uid_callback=self._repos.ct_config_repository.generate_uid_callback,
                ct_config_value=self._post_input_to_codelist_config_value_vo(
                    post_input
                ),
                ct_configuration_exists_by_name_callback=self._repos.ct_config_repository.check_exists_by_name,
            )
        except ValueError as value_error:
            raise ValidationException(value_error.args[0]) from value_error
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def patch(self, uid: str, patch_input: CTConfigPatchInput) -> CTConfigModel:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )
        if ct_config_ar is None:
            raise NotFoundException(
                "Not Found - The configuration with the specified 'uid' could not be found."
            )
        try:
            new_value = self._patch_input_to_new_codelist_config_value_vo(
                patch_input=patch_input, current=ct_config_ar
            )
            ct_config_ar.edit_draft(
                author=self._user_id,
                change_description=patch_input.changeDescription,
                new_ct_config_value=new_value,
                ct_configuration_exists_by_name_callback=self._repos.ct_config_repository.check_exists_by_name,
            )
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    @db.transaction
    def delete(self, uid: str) -> None:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )
        if ct_config_ar is None:
            raise NotFoundException("Resource not found.")
        try:
            ct_config_ar.soft_delete()
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.ct_config_repository.save(ct_config_ar)

    @db.transaction
    def approve(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).approve(self._user_id)
        )

    @db.transaction
    def inactivate(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).inactivate(self._user_id)
        )

    @db.transaction
    def reactivate(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).reactivate(self._user_id)
        )

    @db.transaction
    def new_version(self, uid: str) -> CTConfigModel:
        return self._workflow_action(
            uid, lambda ar: cast(CTConfigAR, ar).create_new_version(self._user_id)
        )

    def _workflow_action(
        self, uid: str, workflow_ar_method: Callable[[CTConfigAR], None]
    ) -> CTConfigModel:
        ct_config_ar = self._repos.ct_config_repository.find_by_uid_2(
            uid, for_update=True
        )
        if ct_config_ar is None:
            raise NotFoundException("Resource not found.")
        try:
            workflow_ar_method(ct_config_ar)
        except ValueError as err:
            raise ValidationException(err.args[0]) from err
        except VersioningException as err:
            raise BusinessLogicException(err.msg) from err
        self._repos.ct_config_repository.save(ct_config_ar)
        return CTConfigModel.from_ct_config_ar(ct_config_ar)

    def _is_library_editable(self, library_name: str) -> Optional[bool]:
        library_ar = self._repos.library_repository.find_by_name(library_name)
        return library_ar.is_editable if library_ar is not None else None

    def _post_input_to_codelist_config_value_vo(
        self, post_input: CTConfigPostInput
    ) -> CTConfigValueVO:
        if post_input.configuredCodelistName is not None:
            all_codelists: Sequence[
                CTCodelistNameAR
            ] = self._repos.ct_codelist_name_repository.find_all(
                library="Sponsor"
            ).items
            for codelist in all_codelists:
                if codelist.ct_codelist_vo.name == post_input.configuredCodelistName:
                    post_input.configuredCodelistUid = codelist.uid

        return CTConfigValueVO.from_input_values(
            study_field_name=post_input.studyFieldName,
            study_field_data_type=post_input.studyFieldDataType,
            study_field_null_value_code=post_input.studyFieldNullValueCode,
            configured_codelist_uid=post_input.configuredCodelistUid,
            configured_term_uid=post_input.configuredTermUid,
            study_field_grouping=post_input.studyFieldGrouping,
            study_field_name_property=post_input.studyFieldNameProperty,
            study_field_name_api=post_input.studyFieldNameApi,
        )

    @staticmethod
    def _fill_missing_values_in_base_model_from_reference_base_model(
        *, base_model_with_missing_values: BaseModel, reference_base_model: BaseModel
    ) -> None:

        for field_name in base_model_with_missing_values.__fields_set__:
            if isinstance(
                getattr(base_model_with_missing_values, field_name), BaseModel
            ) and isinstance(getattr(reference_base_model, field_name), BaseModel):
                CTConfigService._fill_missing_values_in_base_model_from_reference_base_model(
                    base_model_with_missing_values=getattr(
                        base_model_with_missing_values, field_name
                    ),
                    reference_base_model=getattr(reference_base_model, field_name),
                )

        for field_name in (
            reference_base_model.__fields_set__
            - base_model_with_missing_values.__fields_set__
        ).intersection(base_model_with_missing_values.__fields__):
            setattr(
                base_model_with_missing_values,
                field_name,
                getattr(reference_base_model, field_name),
            )

    def _patch_input_to_new_codelist_config_value_vo(
        self, *, patch_input: CTConfigPatchInput, current: CTConfigAR
    ) -> CTConfigValueVO:
        codelist_config_model = CTConfigModel.from_ct_config_ar(current)
        self._fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=patch_input,
            reference_base_model=codelist_config_model,
        )
        return CTConfigValueVO.from_input_values(
            study_field_name=patch_input.studyFieldName,
            study_field_data_type=patch_input.studyFieldDataType,
            study_field_null_value_code=patch_input.studyFieldNullValueCode,
            configured_codelist_uid=patch_input.configuredCodelistUid,
            configured_term_uid=patch_input.configuredTermUid,
            study_field_grouping=patch_input.studyFieldGrouping,
            study_field_name_property=patch_input.studyFieldNameProperty,
            study_field_name_api=patch_input.studyFieldNameApi,
        )
