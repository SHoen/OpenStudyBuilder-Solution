from datetime import datetime
from typing import Self

from pydantic import Field

from clinical_mdr_api.domains.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.syntax_pre_instances.generic_pre_instance import (
    PreInstanceInput,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel

IS_CONFIRMATORY_TESTING_DESC = (
    "Indicates if pre-instance is related to confirmatory testing."
)


class ObjectivePreInstance(BaseModel):
    uid: str
    sequence_id: str | None = Field(None, nullable=True)
    template_uid: str
    template_name: str
    name: str | None = Field(None, nullable=True)
    name_plain: str | None = Field(None, nullable=True)
    start_date: datetime | None = Field(None, nullable=True)
    end_date: datetime | None = Field(None, nullable=True)
    status: str | None = Field(None, nullable=True)
    version: str | None = Field(None, nullable=True)
    change_description: str | None = Field(None, nullable=True)
    user_initials: str | None = Field(None, nullable=True)
    is_confirmatory_testing: bool = Field(
        False, description=IS_CONFIRMATORY_TESTING_DESC
    )
    parameter_terms: list[MultiTemplateParameterTerm] = Field(
        [],
        description="Holds the parameter terms that are used within the objective. The terms are ordered as they occur in the objective name.",
    )
    indications: list[DictionaryTerm] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the pre-instance.",
    )
    categories: list[CTTermNameAndAttributes] = Field(
        [], description="A list of categories the pre-instance belongs to."
    )
    library: Library | None = Field(None, nullable=True)
    possible_actions: list[str] = []

    @classmethod
    def from_objective_pre_instance_ar(
        cls, objective_pre_instance_ar: ObjectivePreInstanceAR
    ) -> Self:
        parameter_terms: list[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(
            objective_pre_instance_ar.get_parameters()
        ):
            terms: list[IndexedTemplateParameterTerm] = []
            for index, parameter_term in enumerate(parameter.parameters):
                pv = IndexedTemplateParameterTerm(
                    index=index + 1,
                    uid=parameter_term.uid,
                    name=parameter_term.value,
                    type=parameter.parameter_name,
                )
                terms.append(pv)
            conjunction = parameter.conjunction

            parameter_terms.append(
                MultiTemplateParameterTerm(
                    conjunction=conjunction, position=position + 1, terms=terms
                )
            )
        return cls(
            uid=objective_pre_instance_ar.uid,
            sequence_id=objective_pre_instance_ar.sequence_id,
            template_uid=objective_pre_instance_ar.template_uid,
            template_name=objective_pre_instance_ar.template_name,
            name=objective_pre_instance_ar.name,
            name_plain=objective_pre_instance_ar.name_plain,
            start_date=objective_pre_instance_ar.item_metadata.start_date,
            end_date=objective_pre_instance_ar.item_metadata.end_date,
            status=objective_pre_instance_ar.item_metadata.status.value,
            version=objective_pre_instance_ar.item_metadata.version,
            change_description=objective_pre_instance_ar.item_metadata.change_description,
            user_initials=objective_pre_instance_ar.item_metadata.user_initials,
            library=Library.from_library_vo(objective_pre_instance_ar.library),
            is_confirmatory_testing=False
            if objective_pre_instance_ar.is_confirmatory_testing is None
            else objective_pre_instance_ar.is_confirmatory_testing,
            parameter_terms=parameter_terms,
            indications=sorted(
                [
                    DictionaryTerm.from_dictionary_term_ar(indication)
                    for indication in objective_pre_instance_ar.indications
                ],
                key=lambda item: item.term_uid,
            )
            if objective_pre_instance_ar.indications
            else [],
            categories=sorted(
                [
                    CTTermNameAndAttributes.from_ct_term_ars(*category)
                    for category in objective_pre_instance_ar.categories
                ],
                key=lambda item: item.term_uid,
            )
            if objective_pre_instance_ar.categories
            else [],
            possible_actions=sorted(
                {_.value for _ in objective_pre_instance_ar.get_possible_actions()}
            ),
        )


class ObjectivePreInstanceCreateInput(PreInstanceInput):
    is_confirmatory_testing: bool | None = Field(
        None, description=IS_CONFIRMATORY_TESTING_DESC
    )
    indication_uids: list[str]
    category_uids: list[str]


class ObjectivePreInstanceEditInput(PreInstanceInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ObjectivePreInstanceIndexingsInput(BaseModel):
    is_confirmatory_testing: bool | None = Field(
        None, description=IS_CONFIRMATORY_TESTING_DESC
    )
    indication_uids: list[str] | None = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the pre-instance to.",
    )
    category_uids: list[str] | None = Field(
        None,
        description="A list of UID of the categories to attach the pre-instance to.",
    )


class ObjectivePreInstanceVersion(ObjectivePreInstance):
    """
    Class for storing Objective Pre-Instances and calculation of differences
    """

    changes: dict[str, bool] | None = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
