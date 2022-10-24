from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.models.ct_term import CTTermNameAndAttributes
from clinical_mdr_api.models.dictionary_term import DictionaryTerm
from clinical_mdr_api.models.library import ItemCounts, Library
from clinical_mdr_api.models.template_parameter import TemplateParameter
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
)
from clinical_mdr_api.models.utils import BaseModel


class ObjectiveTemplateName(BaseModel):
    name: Optional[str] = Field(
        None,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    namePlain: Optional[str] = Field(
        None,
        description="The plain text version of the name property, stripped of HTML tags",
    )


class ObjectiveTemplateNameUid(ObjectiveTemplateName):
    uid: str = Field(..., description="The unique id of the objective template.")


class ObjectiveTemplate(ObjectiveTemplateNameUid):
    editableInstance: bool = Field(
        ...,
        description="Indicates if the name of this template's instances can be edited.",
    )
    startDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the (version of the) objective template was created. "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    endDate: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Part of the metadata: The point in time when the version of the objective template was closed (and a new one was created). "
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )
    status: Optional[str] = Field(
        None,
        description="The status in which the (version of the) objective template is in. "
        "Possible values are: 'Final', 'Draft' or 'Retired'.",
    )
    version: Optional[str] = Field(
        None,
        description="The version number of the (version of the) objective template. "
        "The format is: <major>.<minor> where <major> and <minor> are digits. E.g. '0.1', '0.2', '1.0', ...",
    )
    changeDescription: Optional[str] = Field(
        None,
        description="A short description about what has changed compared to the previous version.",
    )
    userInitials: Optional[str] = Field(
        None,
        description="The initials of the user that triggered the change of the objective template.",
    )

    # TODO use the standard _link/name approach
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the objective template. "
            "Actions are: 'approve', 'edit', 'newVersion', 'inactivate', 'reactivate' and 'delete'."
        ),
    )
    parameters: Optional[List[TemplateParameter]] = Field(
        None, description="Those parameters that are used by the objective template."
    )
    defaultParameterValues: Optional[
        Dict[int, List[MultiTemplateParameterValue]]
    ] = Field(
        None,
        description="""Holds the default values for the parameters that are used
        within the template. The values are ordered as they occur in the template's name.""",
    )
    library: Optional[Library] = Field(
        None, description=("The library to which the objective template belongs.")
    )

    # Template groupings
    indications: Optional[List[DictionaryTerm]] = Field(
        None,
        description="The study indications, conditions, diseases or disorders in scope for the template.",
    )
    confirmatoryTesting: Optional[bool] = Field(
        None, description="Indicates if template is related to confirmatory testing."
    )
    categories: Optional[List[CTTermNameAndAttributes]] = Field(
        None, description="A list of categories the template belongs to."
    )

    studyCount: Optional[int] = Field(
        None, description="Count of studies referencing template"
    )

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> "ObjectiveTemplate":
        default_parameter_values: Dict[int, List[MultiTemplateParameterValue]] = {}
        if objective_template_ar.template_value.default_parameter_values is not None:
            for (
                set_number,
                value_set,
            ) in objective_template_ar.template_value.default_parameter_values.items():
                value_list = []
                for position, parameter in enumerate(value_set):
                    values: List[IndexedTemplateParameterValue] = [
                        IndexedTemplateParameterValue(
                            index=index + 1,
                            uid=parameter_value.uid,
                            name=parameter_value.value,
                            type=parameter.parameter_name,
                        )
                        for index, parameter_value in enumerate(parameter.parameters)
                    ]

                    value_list.append(
                        MultiTemplateParameterValue(
                            conjunction=parameter.conjunction,
                            position=position + 1,
                            values=values,
                        )
                    )
                default_parameter_values[set_number] = value_list

        return cls(
            uid=objective_template_ar.uid,
            editableInstance=objective_template_ar.editable_instance,
            name=objective_template_ar.name,
            namePlain=objective_template_ar.name_plain,
            startDate=objective_template_ar.item_metadata.start_date,
            endDate=objective_template_ar.item_metadata.end_date,
            status=objective_template_ar.item_metadata.status.value,
            version=objective_template_ar.item_metadata.version,
            changeDescription=objective_template_ar.item_metadata.change_description,
            userInitials=objective_template_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in objective_template_ar.get_possible_actions()]
            ),
            library=Library.from_library_vo(objective_template_ar.library),
            confirmatoryTesting=objective_template_ar.confirmatory_testing,
            indications=[
                DictionaryTerm.from_dictionary_term_ar(indication)
                for indication in objective_template_ar.indications
            ]
            if objective_template_ar.indications
            else None,
            categories=[
                CTTermNameAndAttributes.from_ct_term_ars(*category)
                for category in objective_template_ar.categories
            ]
            if objective_template_ar.categories
            else None,
            studyCount=objective_template_ar.study_count,
            parameters=[
                TemplateParameter(name=_)
                for _ in objective_template_ar.template_value.parameter_names
            ],
            defaultParameterValues=default_parameter_values,
        )


class ObjectiveTemplateWithCount(ObjectiveTemplate):
    counts: Optional[ItemCounts] = Field(
        None, description="Optional counts of objective instatiations"
    )

    @classmethod
    def from_objective_template_ar(
        cls, objective_template_ar: ObjectiveTemplateAR
    ) -> "ObjectiveTemplate":
        ot = super().from_objective_template_ar(objective_template_ar)
        if objective_template_ar.counts is not None:
            ot.counts = ItemCounts(
                draft=objective_template_ar.counts.count_draft,
                final=objective_template_ar.counts.count_final,
                retired=objective_template_ar.counts.count_retired,
                total=objective_template_ar.counts.count_total,
            )
        return ot


class ObjectiveTemplateVersion(ObjectiveTemplate):
    """
    Class for storing Objective Templates and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective template (e.g. name, startDate, ..)."
        ),
    )


class ObjectiveTemplateNameInput(BaseModel):
    name: str = Field(
        ...,
        description="The actual value/content. It may include parameters referenced by simple strings in square brackets [].",
    )
    guidanceText: Optional[str] = Field(
        None, description="Optional guidance text for using the template."
    )


class ObjectiveTemplateCreateInput(ObjectiveTemplateNameInput):
    studyUid: Optional[str] = Field(
        None,
        description="The UID of the Study in scope of which given template is being created.",
    )
    libraryName: Optional[str] = Field(
        "Sponsor",
        description="If specified: The name of the library to which the objective template will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true.",
    )
    defaultParameterValues: Optional[List[MultiTemplateParameterValue]] = Field(
        None,
        description="""Holds the parameter values to be used as default for this
        template. The values are ordered as they occur in the template name. \n"""
        "These default parameter values will be created as set#0.",
    )

    editableInstance: Optional[bool] = Field(
        False,
        description="Indicates if the name of this template's instances can be edited. Defaults to False.",
    )

    indicationUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    confirmatoryTesting: Optional[bool] = Field(
        None, description="Indicates if template is related to confirmatory testing."
    )
    categoryUids: Optional[List[str]] = Field(
        None, description="A list of UID of the categories to attach the template to."
    )


class ObjectiveTemplateEditInput(ObjectiveTemplateNameInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class ObjectiveTemplateEditGroupingsInput(BaseModel):
    indicationUids: Optional[List[str]] = Field(
        None,
        description="A list of UID of the study indications, conditions, diseases or disorders to attach the template to.",
    )
    categoryUids: Optional[List[str]] = Field(
        None, description="A list of UID of the categories to attach the template to."
    )
    confirmatoryTesting: Optional[bool] = Field(
        None, description="Indicates if template is related to confirmatory testing."
    )
