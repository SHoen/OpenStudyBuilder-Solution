from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.syntax_pre_instances.endpoint_pre_instance import (
    EndpointPreInstanceAR,
)
from clinical_mdr_api.models.ct_term import CTTermNameAndAttributes
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.syntax_pre_instances.generic_pre_instance import (
    PreInstanceCreateInput,
)
from clinical_mdr_api.models.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel


class EndpointPreInstance(BaseModel):
    uid: Optional[str] = None
    template_uid: str
    name: Optional[str] = None
    name_plain: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    change_description: Optional[str] = None
    user_initials: Optional[str] = None
    parameter_terms: Optional[List[MultiTemplateParameterTerm]] = Field(
        None,
        description="Holds the parameter terms that are used within the endpoint. The terms are ordered as they occur in the endpoint name.",
    )
    indications: Optional[List[DictionaryTerm]] = Field(
        None,
        description="The study indications, conditions, diseases or disorders in scope for the pre instance.",
    )
    categories: Optional[List[CTTermNameAndAttributes]] = Field(
        None, description="A list of categories the pre instance belongs to."
    )
    sub_categories: Optional[List[CTTermNameAndAttributes]] = Field(
        None, description="A list of sub-categories the pre instance belongs to."
    )
    library: Optional[Library] = None
    possible_actions: Optional[List[str]] = None

    @classmethod
    def from_endpoint_pre_instance_ar(
        cls, endpoint_pre_instance_ar: EndpointPreInstanceAR
    ) -> "EndpointPreInstance":
        parameter_terms: List[MultiTemplateParameterTerm] = []
        for position, parameter in enumerate(endpoint_pre_instance_ar.get_parameters()):
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
            uid=endpoint_pre_instance_ar.uid,
            template_uid=endpoint_pre_instance_ar.template_uid,
            name=endpoint_pre_instance_ar.name,
            name_plain=endpoint_pre_instance_ar.name_plain,
            start_date=endpoint_pre_instance_ar.item_metadata.start_date,
            end_date=endpoint_pre_instance_ar.item_metadata.end_date,
            status=endpoint_pre_instance_ar.item_metadata.status.value,
            version=endpoint_pre_instance_ar.item_metadata.version,
            change_description=endpoint_pre_instance_ar.item_metadata.change_description,
            user_initials=endpoint_pre_instance_ar.item_metadata.user_initials,
            library=Library.from_library_vo(endpoint_pre_instance_ar.library),
            parameter_terms=parameter_terms,
            indications=[
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in endpoint_pre_instance_ar.indications
            ]
            if endpoint_pre_instance_ar.indications
            else None,
            categories=[
                CTTermNameAndAttributes.from_ct_term_ars(*category)
                for category in endpoint_pre_instance_ar.categories
            ]
            if endpoint_pre_instance_ar.categories
            else None,
            sub_categories=[
                CTTermNameAndAttributes.from_ct_term_ars(*category)
                for category in endpoint_pre_instance_ar.sub_categories
            ]
            if endpoint_pre_instance_ar.sub_categories
            else None,
            possible_actions=sorted(
                {_.value for _ in endpoint_pre_instance_ar.get_possible_actions()}
            ),
        )


class EndpointPreInstanceVersion(EndpointPreInstance):
    """
    Class for storing Endpoint Pre Instances and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the endpoint (e.g. name, start_date, ..)."
        ),
    )


class EndpointPreInstanceCreateInput(PreInstanceCreateInput):
    indication_uids: List[str]
    category_uids: List[str]
    sub_category_uids: List[str]