from typing import List, Optional

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TemplateParameterValue(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the template parameter value.",
    )

    name: Optional[str] = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Lipids', 'Haematology', 'Body Temperature', ...",
    )

    type: Optional[str] = Field(
        ...,
        title="type",
        description="the type of template parameter, E.g. 'NumericFinding', 'CategoricFinding'",
    )


class IndexedTemplateParameterValue(TemplateParameterValue):
    index: Optional[int] = Field(
        ...,
        title="index",
        description="The index of the template parameter value in the given template position.",
    )


class MultiTemplateParameterValue(BaseModel):
    """
    A MultiTemplateParameterValue provides a way to select a list of template parameter values for a
    given position in a template.

    Given the template "To evaluate [Activity]", and the value "To evaluate [Activity X and Activity Y]",
    an example value for a MultiTemplateParameterValue is:
    {
        position: 1,
        conjunction: 'and',
        values: [
             {index: 1, name: "Activity_0001", uid: "39040243"},
             {index: 2, name: "Activity_0002", uid: "32210211"}
        ]
    }
    """

    position: Optional[int] = Field(
        ...,
        title="position",
        description="The position in the template that the template parameter is in.",
    )
    conjunction: Optional[str] = Field(
        ...,
        title="conjunction",
        description="If the selected template parameter value has multiple values, "
        "the conjunction string to connect them. Available values are ['and', 'or', ','].",
    )
    values: Optional[List[IndexedTemplateParameterValue]] = Field(
        ...,
        title="values",
        description="A list of indexed template parameter values that are used at this position in the template.",
    )


class TemplateParameterComplexValue(MultiTemplateParameterValue):
    """
    TemplataParameterComplexValue is a value for a complex type that can be implmented using
    Numeric values. Below you can find the example of it.
    {
        position: 1,
        conjunction: '',
        format_string: "[TimeUnit] [NumericValue]"
        parameters: [
            {name: "TimeUnit_0001", uid: "39040243"},
            {name: "NumericValue_0002", uid: null, value: 123 }
        ]
    }
    """

    format_string: Optional[str]
