from typing import List, Optional

from pydantic import Field

from clinical_mdr_api.models.template_parameter_value import TemplateParameterValue
from clinical_mdr_api.models.utils import BaseModel


class TemplateParameter(BaseModel):
    name: Optional[str] = Field(
        ...,
        title="name",
        description="The name of the template parameter. E.g. 'Intervention', 'Indication', 'Activity', ...",
    )

    values: Optional[List[TemplateParameterValue]] = Field(
        None,
        title="values",
        description="The possible values of the template parameter.",
    )


class ComplexTemplateParameter(BaseModel):
    name: Optional[str]
    format: Optional[str]
    parameters: Optional[List[TemplateParameter]]
    values: Optional[List[TemplateParameterValue]] = Field(
        None,
        title="values",
        description="The possible values of the template parameter.",
    )
