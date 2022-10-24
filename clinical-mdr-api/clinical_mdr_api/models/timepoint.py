from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain._utils import extract_parameters
from clinical_mdr_api.domain.library.parameter_value import ComplexParameterValue
from clinical_mdr_api.domain.library.timepoints import TimepointAR
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
    MultiTemplateParameterValue,
    TemplateParameterComplexValue,
)
from clinical_mdr_api.models.utils import BaseModel


class Timepoint(BaseModel):
    uid: Optional[str] = None
    name: Optional[str] = None

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None

    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the timeframe. "
            "Actions are: 'approve', 'edit', 'inactivate', 'reactivate' and 'delete'."
        ),
    )

    parameterValues: Optional[List[TemplateParameterComplexValue]] = Field(
        None,
        description="Holds the parameter values that are used within the timeframe. The values are ordered as they occur in the timeframe name.",
    )
    library: Optional[Library] = None

    @classmethod
    def from_timepoint_ar(cls, timepoint_ar: TimepointAR) -> "Timepoint":

        parameter_values: List[MultiTemplateParameterValue] = []
        for position, parameter in enumerate(timepoint_ar.get_parameters()):
            values: List[IndexedTemplateParameterValue] = []
            if isinstance(parameter, ComplexParameterValue):
                param_names = extract_parameters(parameter.parameter_template)
                param_list = []
                for i, param_name in enumerate(param_names):
                    param_value = parameter.parameters[i]
                    pp = IndexedTemplateParameterValue(
                        name=param_value.value,
                        uid=param_value.uid,
                        index=1,
                        type=param_name,
                    )
                    param_list.append(pp)
                pv = TemplateParameterComplexValue(
                    position=position + 1,
                    conjunction="",
                    values=param_list,
                    format_string=parameter.parameter_template,
                )
                parameter_values.append(pv)
            else:
                for index, parameter_value in enumerate(parameter.parameters):
                    pv = IndexedTemplateParameterValue(
                        index=index + 1,
                        uid=parameter_value.uid,
                        name=parameter_value.value,
                        type=parameter.parameter_name,
                    )
                    values.append(pv)
                conjunction = parameter.conjunction

                parameter_values.append(
                    MultiTemplateParameterValue(
                        conjunction=conjunction, position=position + 1, values=values
                    )
                )
        return cls(
            uid=timepoint_ar.uid,
            name=timepoint_ar.name,
            startDate=timepoint_ar.item_metadata.start_date,
            endDate=timepoint_ar.item_metadata.end_date,
            status=timepoint_ar.item_metadata.status.value,
            version=timepoint_ar.item_metadata.version,
            changeDescription=timepoint_ar.item_metadata.change_description,
            userInitials=timepoint_ar.item_metadata.user_initials,
            possibleActions=sorted(
                {_.value for _ in timepoint_ar.get_possible_actions()}
            ),
            library=Library.from_library_vo(timepoint_ar.library),
            parameterValues=parameter_values,
        )


class TimepointVersion(Timepoint):
    """
    Class for storing Timepoints and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the timeframe (e.g. name, startDate, ..)."
        ),
    )


class TimepointParameterInput(BaseModel):
    parameterValues: List[TemplateParameterMultiSelectInput] = Field(
        None,
        title="parameterValues",
        description="An ordered list of selected parameter values that are used to replace the parameters of the timeframe template.",
    )


class TimepointEditInput(TimepointParameterInput):
    changeDescription: str = Field(
        ...,
        description="A short description about what has changed compared to the previous version.",
    )


class TimepointCreateInput(TimepointParameterInput):
    timeframeTemplateUid: str = Field(
        ...,
        title="timeframeTemplateUid",
        description="The unique id of the timeframe template that is used as the basis for the new timeframe.",
    )
    libraryName: str = Field(
        None,
        title="libraryName",
        description="If specified: The name of the library to which the timeframe will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* endpoint can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true. \n\n"
        "If not specified: The library of the timeframe template will be used.",
    )
