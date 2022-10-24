from typing import Optional

from pydantic import validator

from clinical_mdr_api.domain.configurations import CTConfigAR
from clinical_mdr_api.models.concept import NoLibraryConceptModelNoName
from clinical_mdr_api.models.utils import BaseModel


class CTConfigBaseModel(BaseModel):
    studyFieldName: Optional[str]
    studyFieldDataType: Optional[str]
    studyFieldNullValueCode: Optional[str]

    configuredCodelistUid: Optional[str]
    configuredTermUid: Optional[str]

    studyFieldGrouping: Optional[str]
    studyFieldNameProperty: Optional[str]
    studyFieldNameApi: Optional[str]


class CTConfigModel(CTConfigBaseModel, NoLibraryConceptModelNoName):
    @classmethod
    def from_ct_config_ar(cls, ct_config_definition_ar: CTConfigAR) -> "CTConfigModel":
        return CTConfigModel(
            uid=ct_config_definition_ar.uid,
            studyFieldName=ct_config_definition_ar.value.study_field_name,
            studyFieldDataType=ct_config_definition_ar.value.study_field_data_type,
            studyFieldNullValueCode=ct_config_definition_ar.value.study_field_null_value_code,
            configuredCodelistUid=ct_config_definition_ar.value.configured_codelist_uid,
            configuredTermUid=ct_config_definition_ar.value.configured_term_uid,
            studyFieldGrouping=ct_config_definition_ar.value.study_field_grouping,
            studyFieldNameProperty=ct_config_definition_ar.value.study_field_name_property,
            studyFieldNameApi=ct_config_definition_ar.value.study_field_name_api,
            startDate=ct_config_definition_ar.item_metadata.start_date,
            status=ct_config_definition_ar.item_metadata.status.value,
            version=ct_config_definition_ar.item_metadata.version,
            userInitials=ct_config_definition_ar.item_metadata.user_initials,
            changeDescription=ct_config_definition_ar.item_metadata.change_description,
        )


class CTConfigPostInput(CTConfigBaseModel):
    # field used to create a configuration based on codelist name
    configuredCodelistName: Optional[str]

    @validator("*")
    # pylint:disable=no-self-argument
    def replace_empty_string_with_none(cls, field):
        if field == "":
            return None
        return field


class CTConfigPatchInput(CTConfigBaseModel):
    changeDescription: str
