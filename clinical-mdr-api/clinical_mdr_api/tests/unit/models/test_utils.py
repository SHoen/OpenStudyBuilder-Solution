import unittest

from parameterized import parameterized
from pydantic import BaseModel

from clinical_mdr_api.models import utils


class TestModelUtils(unittest.TestCase):
    @parameterized.expand(
        [
            (True, "yes", "yes"),
            (False, "yes", "no"),
            (1, "yes", "yes"),
            (0, "yes", "no"),
            (1, "y", "y"),
            (0, "y", "n"),
            (1, "t", "t"),
            (0, "t", "f"),
            (1, "true", "true"),
            (0, "true", "false"),
            (1, "on", "on"),
            (0, "on", "off"),
            (1, "1", "1"),
            (0, "1", "0"),
        ]
    )
    def test_booltostr(self, boolean, true_format, expected):
        assert utils.booltostr(boolean, true_format) == expected

    def test_booltostr_raises_exception(self):
        self.assertRaises(ValueError, utils.booltostr, 1, "NonExistingTrueFormat")

    @parameterized.expand(
        [
            ("snake_case_input", "snakeCaseInput"),
            ("snake_32_case_input_", "snake32CaseInput"),
            ("..._snake_____case_input____", "...SnakeCaseInput"),
            ("zzz_snake_____case_input____", "zzzSnakeCaseInput"),
        ]
    )
    def test_snake_to_camel(self, input_data, expected):
        assert utils.snake_to_camel(input_data) == expected

    @parameterized.expand(
        [
            ("camelCaseInput", "camel_case_input"),
            ("camel32CaseInput_", "camel32_case_input_"),
            ("...Camel____CaseInput____", "..._camel_____case_input____"),
            ("zzzCamel____CaseInput____", "zzz_camel_____case_input____"),
        ]
    )
    def test_camel_to_snake(self, input_data, expected):
        assert utils.camel_to_snake(input_data) == expected

    @parameterized.expand(
        [
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                False,
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                },
            ),
            (
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput_": "y",
                },
                True,
                {
                    "_camel_case_input": "x",
                    "_camel32_case_input_": "y",
                },
            ),
        ]
    )
    def test_snake_case_data(self, input_data, privates, expected):
        assert utils.snake_case_data(input_data, privates) == expected

    @parameterized.expand(
        [
            (
                {
                    "camel_case_input": "x",
                    "camel32_case_input_": "y",
                    "_camel32_case_input_": "y",
                },
                # pylint:disable=duplicate-key
                {
                    "camelCaseInput": "x",
                    "camel32CaseInput": "y",
                    "camel32CaseInput": "y",
                },
            )
        ]
    )
    def test_camel_case_data(self, input_data, expected):
        assert utils.camel_case_data(input_data) == expected

    def test_is_attribute_in_model(self):
        model = type("model", (BaseModel,), {"z": "somehing", "x": 123})

        assert utils.isAttributeInModel("x", model)
        assert not utils.isAttributeInModel("y", model)
