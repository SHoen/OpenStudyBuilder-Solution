from typing import List, Optional

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class SimpleMappingTarget(BaseModel):
    uid: Optional[str] = Field(
        None,
        title="uid of mapping target",
    )
    name: Optional[str] = Field(
        None,
        title="name of mapping target",
    )


class SimpleImplementsVariable(BaseModel):
    uid: str = Field(
        ...,
        title="uid of implemented variable",
    )
    name: str = Field(
        ...,
        title="name of implemented variable",
    )


class SimpleDataset(BaseModel):
    ordinal: Optional[str] = Field(
        None,
        title="ordinal of variable in dataset",
    )
    name: str = Field(
        ...,
        title="name of the variable dataset",
    )


class SimpleReferencedCodelist(BaseModel):
    class Config:
        orm_mode = True

    uid: Optional[str] = Field(
        None,
        title="uid",
        description="The uid of the referenced codelist",
    )
    name: Optional[str] = Field(
        None,
        title="uid",
        description="The name of the referenced codelist",
    )


class DatasetVariable(BaseModel):
    class Config:
        orm_mode = True

    uid: str = Field(
        ...,
        title="uid",
        description="The uid of the dataset",
    )
    label: Optional[str] = Field(
        None,
        title="label",
        description="The label of the dataset",
    )
    title: Optional[str] = Field(
        None,
        title="title",
        description="The title of the dataset",
    )
    description: Optional[str] = Field(
        None, title="description", description="description", nullable=True
    )
    simple_datatype: Optional[str] = Field(
        None, title="simple_datatype", description="simple_datatype", nullable=True
    )
    question_text: Optional[str] = Field(
        None, title="question_text", description="question_text", nullable=True
    )
    prompt: Optional[str] = Field(
        None, title="prompt", description="prompt", nullable=True
    )
    completion_instructions: Optional[str] = Field(
        None,
        title="completion_instructions",
        description="completion_instructions",
        nullable=True,
    )
    implementation_notes: Optional[str] = Field(
        None,
        title="implementation_notes",
        description="implementation_notes",
        nullable=True,
    )
    mapping_instructions: Optional[str] = Field(
        None,
        title="mapping_instructions",
        description="mapping_instructions",
        nullable=True,
    )
    role: Optional[str] = Field(None, title="role", description="role", nullable=True)
    core: Optional[str] = Field(None, title="core", description="core", nullable=True)
    dataset: SimpleDataset = Field(
        ...,
        title="dataset",
        description="dataset",
    )
    data_model_ig_names: List[str] = Field(
        ...,
        title="Versions of associated data model implementation guides",
        description="Versions of associated data model implementation guides",
    )
    implements_variable: Optional[SimpleImplementsVariable] = Field(None)
    has_mapping_target: Optional[SimpleMappingTarget] = Field(None)
    catalogue_name: str = Field(
        ...,
        title="catalogue",
        description="catalogue",
    )
    referenced_codelist: Optional[SimpleReferencedCodelist] = Field(None)

    @classmethod
    def from_repository_output(cls, input_dict: dict):
        return cls(
            uid=input_dict.get("uid"),
            label=input_dict.get("standard_value").get("label"),
            title=input_dict.get("standard_value").get("title"),
            description=input_dict.get("standard_value").get("description"),
            simple_datatype=input_dict.get("standard_value").get("simple_datatype"),
            role=input_dict.get("standard_value").get("role"),
            core=input_dict.get("standard_value").get("core"),
            question_text=input_dict.get("question_text"),
            prompt=input_dict.get("prompt"),
            completion_instructions=input_dict.get("completion_instructions"),
            implementation_notes=input_dict.get("implementation_notes"),
            mapping_instructions=input_dict.get("mapping_instructions"),
            catalogue_name=input_dict.get("catalogue_name"),
            data_model_ig_names=input_dict.get("data_model_ig_names"),
            dataset=SimpleDataset(
                name=input_dict.get("dataset").get("name"),
                ordinal=input_dict.get("dataset").get("ordinal"),
            ),
            implements_variable=SimpleImplementsVariable(
                uid=input_dict.get("implements_variable").get("uid"),
                name=input_dict.get("implements_variable").get("name"),
            )
            if input_dict.get("implements_variable")
            else None,
            has_mapping_target=SimpleMappingTarget(
                uid=input_dict.get("has_mapping_target").get("uid"),
                name=input_dict.get("has_mapping_target").get("name"),
            )
            if input_dict.get("has_mapping_target")
            else None,
            referenced_codelist=SimpleReferencedCodelist(
                uid=input_dict.get("referenced_codelist").get("uid"),
                name=input_dict.get("referenced_codelist").get("name"),
            )
            if input_dict.get("referenced_codelist")
            else None,
        )
