import csv
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Optional

from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    HighLevelStudyDesignVO,
    RegistryIdentifiersVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.domain_repositories.configuration.configuration_repository import (
    CTConfigRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_codelist_name_repository import (
    CTCodelistNameRepository,
)


class StudyFieldType(Enum):
    INT = "int"
    TEXT = "text"
    CODELIST_SELECT = "codelist_select"
    CODELIST_MULTISELECT = "multiselect"
    TIME = "time"
    DATE = "date"
    BOOL = "bool"
    REGISTRY = "registry"
    PROJECT = "project"


@dataclass
class StudyFieldConfigurationEntry:
    study_field_data_type: StudyFieldType  # maps to name property from config_value
    study_field_name: str
    study_field_null_value_code: Optional[str]
    configured_codelist_uid: Optional[str]
    configured_term_uid: Optional[str]
    study_field_grouping: str  # stores name of value object in study AR
    study_value_object_class: type
    study_field_name_property: str  # stores name of value in neomodel
    study_field_name_api: str


fieldnames = [
    "study_field_data_type",
    "study_field_name",
    "configured_codelist_uid",
    "study_field_null_value_code",
    "configured_term_uid",
    "study_field_grouping",
    "study_field_name_property",
    "study_field_name_api",
]


def sanitize_value(val: str):
    if isinstance(val, str):
        val = val.strip()
    if val == "False":
        return False
    if val == "None":
        return None
    if val == "":
        return None
    if val == "True":
        return True
    return val


def from_file(filename):
    dataset = []
    codelist_repo = CTCodelistNameRepository()
    all_codelists = codelist_repo.find_all().items
    with open(filename, encoding="UTF-8") as f:
        r = csv.DictReader(f)
        for line in r:
            line["study_field_data_type"] = StudyFieldType(
                line["study_field_data_type"]
            )
            data = {}
            for k, v in line.items():
                # creating a mapping based on codelist name
                if line.get("configured_codelist_name") is not None:
                    for codelist in all_codelists:
                        if (
                            codelist.ct_codelist_vo.name
                            == line["configured_codelist_name"]
                        ):
                            line["configured_codelist_uid"] = codelist.uid
                if k in fieldnames:
                    data[k] = sanitize_value(v)
                    if k == "study_field_grouping":
                        if v == "id_metadata":
                            data[
                                "study_value_object_class"
                            ] = StudyIdentificationMetadataVO
                        elif v == "ver_metadata":
                            data["study_value_object_class"] = StudyVersionMetadataVO
                        elif v == "high_level_study_design":
                            data["study_value_object_class"] = HighLevelStudyDesignVO
                        elif v == "study_population":
                            data["study_value_object_class"] = StudyPopulationVO
                        elif v == "study_intervention":
                            data["study_value_object_class"] = StudyInterventionVO
                        elif v == "study_description":
                            data["study_value_object_class"] = StudyDescriptionVO
                        elif v == "id_metadata.registry_identifiers":
                            data["study_value_object_class"] = RegistryIdentifiersVO
                        else:
                            raise ValueError(f"Unknow field {v}")
            item = StudyFieldConfigurationEntry(**data)
            dataset.append(item)
    return dataset


def from_database():
    dataset = []
    repo = CTConfigRepository()
    items = repo.find_all()
    all_codelists = []
    if items:
        codelist_repo = CTCodelistNameRepository()
        all_codelists = codelist_repo.find_all().items
    for item in items:
        line = item.value
        linedata = asdict(line)
        data = {}
        for k, v in linedata.items():
            # creating a mapping based on codelist name
            if linedata.get("configured_codelist_name") is not None:
                for codelist in all_codelists:
                    if (
                        codelist.ct_codelist_vo.name
                        == linedata["configured_codelist_name"]
                    ):
                        linedata["configured_codelist_uid"] = codelist.uid
            if k in fieldnames:
                if k == "study_field_data_type":
                    data[k] = StudyFieldType(v)
                else:
                    data[k] = sanitize_value(v)
                if k == "study_field_grouping":
                    if v == "id_metadata":
                        data["study_value_object_class"] = StudyIdentificationMetadataVO
                    elif v == "ver_metadata":
                        data["study_value_object_class"] = StudyVersionMetadataVO
                    elif v == "high_level_study_design":
                        data["study_value_object_class"] = HighLevelStudyDesignVO
                    elif v == "study_population":
                        data["study_value_object_class"] = StudyPopulationVO
                    elif v == "study_intervention":
                        data["study_value_object_class"] = StudyInterventionVO
                    elif v == "study_description":
                        data["study_value_object_class"] = StudyDescriptionVO
                    elif v == "id_metadata.registry_identifiers":
                        data["study_value_object_class"] = RegistryIdentifiersVO
                    else:
                        raise ValueError(f"Unknow field {v}")
        item = StudyFieldConfigurationEntry(**data)
        dataset.append(item)
    return dataset


def to_file(filename, data):
    with open(filename, "w", encoding="UTF-8") as f:
        wr = csv.DictWriter(f, fieldnames)
        wr.writeheader()
        item: StudyFieldConfigurationEntry
        for item in data:
            datadict = asdict(item)
            datadict["study_field_name"] = item.study_field_data_type.name
            wr.writerow(datadict)


class FieldConfiguration:
    field_config = []

    @classmethod
    def default_field_config(cls):
        if not cls.field_config:
            cls.field_config = from_database()
        return cls.field_config
