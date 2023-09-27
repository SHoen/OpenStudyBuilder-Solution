from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TemplateParameterTerm(BaseModel):
    uid: str = Field(
        ...,
        title="uid",
        description="The unique id of the template parameter term.",
    )

    name: str | None = Field(
        ...,
        title="name",
        description="The name or the actual value. E.g. 'Lipids', 'Haematology', 'Body Temperature', ...",
    )

    type: str | None = Field(
        ...,
        title="type",
        description="the type of template parameter, E.g. 'NumericFinding', 'CategoricFinding'",
    )


class IndexedTemplateParameterTerm(TemplateParameterTerm):
    index: int | None = Field(
        ...,
        title="index",
        description="The index of the template parameter term in the given template position.",
    )


class MultiTemplateParameterTerm(BaseModel):
    """
    A MultiTemplateParameterTerm provides a way to select a list of template parameter terms for a
    given position in a template.

    Given the template "To evaluate [Activity]", and the value "To evaluate [Activity X and Activity Y]",
    an example value for a MultiTemplateParameterTerm is:
    {
        position: 1,
        conjunction: 'and',
        terms: [
             {index: 1, name: "Activity_0001", uid: "39040243"},
             {index: 2, name: "Activity_0002", uid: "32210211"}
        ]
    }
    """

    position: int | None = Field(
        ...,
        title="position",
        description="The position in the template that the template parameter is in.",
    )
    conjunction: str | None = Field(
        ...,
        title="conjunction",
        description="If the selected template parameter term has multiple terms, "
        "the conjunction string to connect them. Available terms are ['and', 'or', ','].",
    )
    terms: list[IndexedTemplateParameterTerm] = Field(
        [],
        title="terms",
        description="A list of indexed template parameter terms that are used at this position in the template.",
    )


class TemplateParameterComplexValue(MultiTemplateParameterTerm):
    """
    TemplateParameterComplexValue is a value for a complex type that can be implemented using
    Numeric terms. Below you can find the example of it.
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

    format_string: str | None
