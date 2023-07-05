from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domains.syntax_templates.criteria_template import (
    CriteriaTemplateAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.dictionaries.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.libraries.library import ItemCounts, Library
from clinical_mdr_api.models.syntax_templates.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.utils import BaseModel


class CriteriaTemplateName(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    name_plain: str = Field(
        ...,
        description="The plain text version of the name property, stripped of HTML tags",
    )
    guidance_text: Optional[str] = Field(
        None,
        description="Optional guidance text for using the template.",
        nullable=True,
    )


class CriteriaTemplateNameUid(CriteriaTemplateName):
    uid: str = Field(..., description="The unique id of the criteria template.")
    sequence_id: Optional[str] = Field(None, nullable=True)


class CriteriaTemplate(CriteriaTemplateNameUid):
    start_date: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) criteria template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    end_date: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the criteria template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        nullable=True,
    )
    status: Optional[str] = Field(
        None,
        description="The status in which the (version of the) criteria template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
        nullable=True,
    )
    version: Optional[str] = Field(
        None,
        description="The version number of the (version of the) criteria template. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
        nullable=True,
    )
    change_description: Optional[str] = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
        nullable=True,
    )
    user_initials: Optional[str] = Field(
        None,
        description="The initials of the user that triggered the change of the criteria template.",
        nullable=True,
    )

    # TODO use the standard _link/name approach
    possible_actions: List[str] = Field(
        [],
        description=(
            "Holds those actions that can be performed on the criteria template. "
            "Actions are: 'approve', 'edit', 'new_version', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: List[TemplateParameter] = Field(
        [], description="Those parameters that are used by the criteria template."
    )
    default_parameter_terms: Optional[
        Dict[int, List[MultiTemplateParameterTerm]]
    ] = Field(
        None,
        description="""Holds the default terms for the parameters that are used
        within the template. The terms are ordered as they occur in the template's name.""",
    )
    library: Optional[Library] = Field(
        None,
        description="The library to which the criteria template belongs.",
        nullable=True,
    )

    # Template indexings
    type: Optional[CTTermNameAndAttributes] = Field(
        None, description="The criteria type.", nullable=True
    )
    indications: List[DictionaryTerm] = Field(
        [],
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    categories: List[CTTermNameAndAttributes] = Field(
        [], description="A list of categories the template belongs to."
    )
    sub_categories: List[CTTermNameAndAttributes] = Field(
        [], description="A list of sub-categories the template belongs to."
    )

    study_count: int = Field(0, description="Count of studies referencing template")

    @classmethod
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> "CriteriaTemplate":
        default_parameter_terms: Dict[int, List[MultiTemplateParameterTerm]] = {}
        if criteria_template_ar.template_value.default_parameter_terms is not None:
            for (
                set_number,
                term_set,
            ) in criteria_template_ar.template_value.default_parameter_terms.items():
                term_list = []
                for position, parameter in enumerate(term_set):
                    terms: List[IndexedTemplateParameterTerm] = [
                        IndexedTemplateParameterTerm(
                            index=index + 1,
                            uid=parameter_term.uid,
                            name=parameter_term.value,
                            type=parameter.parameter_name,
                        )
                        for index, parameter_term in enumerate(parameter.parameters)
                    ]

                    term_list.append(
                        MultiTemplateParameterTerm(
                            conjunction=parameter.conjunction,
                            position=position + 1,
                            terms=terms,
                        )
                    )

                default_parameter_terms[set_number] = term_list

        return cls(
            uid=criteria_template_ar.uid,
            sequence_id=criteria_template_ar.sequence_id,
            name=criteria_template_ar.name,
            name_plain=criteria_template_ar.name_plain,
            guidance_text=criteria_template_ar.guidance_text,
            start_date=criteria_template_ar.item_metadata.start_date,
            end_date=criteria_template_ar.item_metadata.end_date,
            status=criteria_template_ar.item_metadata.status.value,
            version=criteria_template_ar.item_metadata.version,
            change_description=criteria_template_ar.item_metadata.change_description,
            user_initials=criteria_template_ar.item_metadata.user_initials,
            possible_actions=sorted(
                [_.value for _ in criteria_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(criteria_template_ar.library),
            type=CTTermNameAndAttributes.from_ct_term_ars(*criteria_template_ar.type)
            if criteria_template_ar.type
            else None,
            indications=[
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in criteria_template_ar.indications
            ]
            if criteria_template_ar.indications
            else [],
            categories=[
                CTTermNameAndAttributes.from_ct_term_ars(*category)
                for category in criteria_template_ar.categories
            ]
            if criteria_template_ar.categories
            else [],
            sub_categories=[
                CTTermNameAndAttributes.from_ct_term_ars(*category)
                for category in criteria_template_ar.sub_categories
            ]
            if criteria_template_ar.sub_categories
            else [],
            study_count=criteria_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in criteria_template_ar.template_value.parameter_names
            ],
            default_parameter_terms=default_parameter_terms,
        )


class CriteriaTemplateWithCount(CriteriaTemplate):
    counts: Optional[ItemCounts] = Field(
        None, description="Optional counts of criteria instantiations"
    )

    @classmethod
    def from_criteria_template_ar(
        cls, criteria_template_ar: CriteriaTemplateAR
    ) -> "CriteriaTemplate":
        ot = super().from_criteria_template_ar(criteria_template_ar)
        if criteria_template_ar.counts is not None:
            ot.counts = ItemCounts(
                draft=criteria_template_ar.counts.count_draft,
                final=criteria_template_ar.counts.count_final,
                retired=criteria_template_ar.counts.count_retired,
                total=criteria_template_ar.counts.count_total,
            )
        return ot


class CriteriaTemplateVersion(CriteriaTemplate):
    """
    Class for storing Criteria Templates and calculation of differences
    """

    changes: Optional[Dict[str, bool]] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the criteria template (e.g. name, start_date, ..)."
        ),
        nullable=True,
    )


class CriteriaTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
        min_length=1,
    )
    guidance_text: Optional[str] = Field(
        None, description="Optional guidance text for using the template."
    )


class CriteriaTemplateCreateInput(CriteriaTemplateNameInput):
    study_uid: Optional[str] = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    library_name: Optional[str] = Field(
        "Sponsor",
        description="If specified: The name of the library to which the criteria template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'is_editable' property of the library needs to be true.",
    )
    default_parameter_terms: Optional[List[MultiTemplateParameterTerm]] = Field(
        None,
        description="""Holds the parameter terms to be used as default for this
        template. The terms are ordered as they occur in the template name. \n"""
        "These default parameter terms will be created as set#0.",
    )
    type_uid: str = Field(
        ...,
        description="The UID of the criteria type to attach the template to.",
        min_length=1,
    )
    indication_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    category_uids: Optional[List[str]] = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    sub_category_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the sub_categories to attach the template to.",
    )


class CriteriaTemplateEditInput(CriteriaTemplateNameInput):
    change_description: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class CriteriaTemplateEditIndexingsInput(BaseModel):
    indication_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    category_uids: Optional[List[str]] = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    sub_category_uids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the sub_categories to attach the template to.",
    )
