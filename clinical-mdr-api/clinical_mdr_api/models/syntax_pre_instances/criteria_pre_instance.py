from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domains.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceAR,
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


class CriteriaPreInstance(BaseModel):
    uid: str
    sequence_id: Optional[str] = Field(None, nullable=True)
    template_uid: str
    template_name: str
    template_type_uid: Optional[str] = Field(None, nullable=True)
    name: Optional[str] = Field(None, nullable=True)
    name_plain: Optional[str] = Field(None, nullable=True)
    start_date: Optional[datetime] = Field(None, nullable=True)
    end_date: Optional[datetime] = Field(None, nullable=True)
    status: Optional[str] = Field(None, nullable=True)
    version: Optional[str] = Field(None, nullable=True)
    change_description: Optional[str] = Field(None, nullable=True)
    user_initials: Optional[str] = Field(None, nullable=True)
    parameter_terms: List[MultiTemplateParameterTerm] = Field(
        [],
        description="Holds the parameter terms that are used within the criteria. The terms are ordered as they occur in the criteria name.",
    )
    indications: List[DictionaryTerm] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the pre-instance.",
    )
    categories: List[CTTermNameAndAttributes] = Field(
        [], description="A list of categories the pre-instance belongs to."
    )
    sub_categories: List[CTTermNameAndAttributes] = Field(
        [], description="A list of sub-categories the pre-instance belongs to."
    )
    library: Optional[Library] = Field(None, nullable=True)
    possible_actions: List[str] = Field([])

    @classmethod
    def from_criteria_pre_instance_ar(
        cls, criteria_pre_instance_ar: CriteriaPreInstanceAR
    ) -> "CriteriaPreInstance":
        parameter_terms: List[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(criteria_pre_instance_ar.get_parameters()):
            terms: List[IndexedTemplateParameterTerm] = []
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
            uid=criteria_pre_instance_ar.uid,
            sequence_id=criteria_pre_instance_ar.sequence_id,
            template_uid=criteria_pre_instance_ar.template_uid,
            template_name=criteria_pre_instance_ar.template_name,
            template_type_uid=None,
            name=criteria_pre_instance_ar.name,
            name_plain=criteria_pre_instance_ar.name_plain,
            start_date=criteria_pre_instance_ar.item_metadata.start_date,
            end_date=criteria_pre_instance_ar.item_metadata.end_date,
            status=criteria_pre_instance_ar.item_metadata.status.value,
            version=criteria_pre_instance_ar.item_metadata.version,
            change_description=criteria_pre_instance_ar.item_metadata.change_description,
            user_initials=criteria_pre_instance_ar.item_metadata.user_initials,
            library=Library.from_library_vo(criteria_pre_instance_ar.library),
            parameter_terms=parameter_terms,
            indications=sorted(
                [
                    DictionaryTerm.from_dictionary_term_ar(indication)
                    for indication in criteria_pre_instance_ar.indications
                ],
                key=lambda item: item.term_uid,
            )
            if criteria_pre_instance_ar.indications
            else [],
            categories=sorted(
                [
                    CTTermNameAndAttributes.from_ct_term_ars(*category)
                    for category in criteria_pre_instance_ar.categories
                ],
                key=lambda item: item.term_uid,
            )
            if criteria_pre_instance_ar.categories
            else [],
            sub_categories=sorted(
                [
                    CTTermNameAndAttributes.from_ct_term_ars(*category)
                    for category in criteria_pre_instance_ar.sub_categories
                ],
                key=lambda item: item.term_uid,
            )
            if criteria_pre_instance_ar.sub_categories
            else [],
            possible_actions=sorted(
                {_.value for _ in criteria_pre_instance_ar.get_possible_actions()}
            ),
        )


class CriteriaPreInstanceIndexingsInput(BaseModel):
    indication_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the pre-instance to.",
    )
    category_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the categories to attach the pre-instance to.",
    )
    sub_category_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the sub_categories to attach the pre-instance to.",
    )


class CriteriaPreInstanceCreateInput(PreInstanceInput):
    indication_uids: List[str]
    category_uids: List[str]
    sub_category_uids: List[str]


class CriteriaPreInstanceEditInput(PreInstanceInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaPreInstanceVersion(CriteriaPreInstance):
    """
    Class for storing Criteria Pre-Instances and calculation of differences
    """

    changes: Optional[Dict[str, bool]] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )
