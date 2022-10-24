from typing import List, Optional

from pydantic import Field

from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
)
from clinical_mdr_api.models.utils import BaseModel


class TemplateParameterMultiSelectInput(BaseModel):
    values: Optional[List[IndexedTemplateParameterValue]] = Field(
        ...,
        title="values",
        description="A list of indexed template parameter values that are used at this position in the template.",
    )
    value: Optional[float] = Field(
        None,
        title="value",
        description="A numeric value used at this position in the template.",
    )
    conjunction: Optional[str] = Field(
        None,
        title="conjunction",
        description="If the selected template parameter value has multiple values, "
        "the conjunction string to connect them. Available values are ['and', 'or', ','].",
    )
