from typing import Optional

import pytest
from pydantic import BaseModel

from clinical_mdr_api.services._utils import (
    FieldsDirective,
    filter_base_model_using_fields_directive,
)


@pytest.mark.parametrize(
    "query_param, field_path, expected_should_include",
    [
        ("", "whateverField", True),
        ("", "whatever.nested.field", True),
        (None, "whateverField", True),
        (None, "whatever.nested.field", True),
        ("f1, +f2", "f1", True),
        ("f1, +f2", "f2", True),
        ("f1, +f2", "f3", False),
        ("f1, +f2", "f1.any.nested.field", True),
        ("f1, +f2", "f2.any.nested.field", True),
        ("f1, +f2", "f3.any.nested.field", False),
        ("f1, +f2, -f2.excluded_nested", "f2.any.nested.field", True),
        ("f1, +f2, -f2.excluded_nested", "f2.excluded_nested", False),
        ("f1, +f2, -f2.nested.excluded", "f2.nested.nonExcluded", True),
        ("f1, +f2, -f2.nested.excluded", "f2.nested.excluded", False),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "something.else",
            False,
        ),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "very.specific.deeply.nested.field",
            True,
        ),
        (
            "very.specific.deeply.nested.field, another.very.specific.deeply.nested.field",
            "another.very.specific.deeply.nested.field",
            True,
        ),
    ],
)
def test__field_directive__is_field_included__results(
    query_param: Optional[str], field_path: str, expected_should_include: bool
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_param
    )

    # when
    should_include = field_directive.is_field_included(field_path)

    # then
    assert should_include == expected_should_include


@pytest.mark.parametrize("query_param", ["f1, f2", "f1, -f1.nested", "f3.nested", None])
@pytest.mark.parametrize("before_dot_part", ["f1", "f2", "f3", "f5678"])
@pytest.mark.parametrize("after_dot_part", ["f1", "f2", "f3", "f5678", "nested"])
def test__field_directive__is_field_included_and_get_fields_directive_for_children_of_field__consistent_results(
    query_param: Optional[str], before_dot_part: str, after_dot_part: str
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_param
    )
    nested_field_path = f"{before_dot_part}.{after_dot_part}"

    # when
    should_include_result = field_directive.is_field_included(nested_field_path)
    should_include_by_nesting_result = field_directive.is_field_included(
        before_dot_part
    ) and (
        field_directive.get_fields_directive_for_children_of_field(
            before_dot_part
        ).is_field_included(after_dot_part)
    )

    # then
    assert should_include_by_nesting_result == should_include_result


class ChildBaseModel(BaseModel):
    childField: Optional[str] = None


class ParentBaseModel(BaseModel):
    parentField: Optional[str] = None
    child: Optional[ChildBaseModel] = None


@pytest.mark.parametrize(
    "given_parent_field, given_child_field, query_fields_param",
    [
        ("parent Field Value", "child Field Value", None),
        ("parent Field Value", "child Field Value", "parentField"),
        ("parent Field Value", "child Field Value", "child"),
        ("parent Field Value", "child Field Value", "child, -child.childField"),
        ("parent Field Value", "child Field Value", "-child"),
    ],
)
def test__filter_base_model_using_fields_directive__consistency_with_directive(
    given_parent_field: Optional[str],
    given_child_field: Optional[str],
    query_fields_param: Optional[str],
):
    # given
    field_directive: FieldsDirective = FieldsDirective.from_fields_query_parameter(
        query_fields_param
    )
    given_base_model = ParentBaseModel(
        parentField=given_parent_field,
        child=ChildBaseModel(childField=given_child_field),
    )

    # when
    resulting_base_model = filter_base_model_using_fields_directive(
        given_base_model, field_directive
    )

    # then
    if field_directive.is_field_included("parentField"):
        assert resulting_base_model.__dict__.get("parentField") is not None
    else:
        assert resulting_base_model.__dict__.get("parentField") is None

    if field_directive.is_field_included("child"):
        assert resulting_base_model.__dict__.get("child") is not None
        assert field_directive.is_field_included("child.childField") == (
            "childField" in resulting_base_model.child.__fields_set__
        )
    else:
        assert resulting_base_model.__dict__.get("child") is None
