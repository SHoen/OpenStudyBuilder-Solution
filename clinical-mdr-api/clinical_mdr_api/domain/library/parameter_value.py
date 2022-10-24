from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain._utils import extract_parameters


@dataclass(frozen=True)
class ParameterValueVO:
    uid: str


@dataclass(frozen=True)
class SimpleParameterValueVO(ParameterValueVO):
    """
    Value object representing single parameter value - a pair of (name, uid)
    """

    value: str

    @classmethod
    def from_repository_values(cls, *, uid: str, value: str) -> "ParameterValueVO":
        return cls(uid=uid, value=value)

    @classmethod
    def from_input_values(
        cls,
        *,
        uid: str,
        value_by_uid_lookup_callback: Optional[Callable[[str], Optional[str]]] = None,
        value: Optional[str] = None,
    ) -> "ParameterValueVO":
        if value is None:
            if value_by_uid_lookup_callback is None:
                raise ValueError(
                    "value_by_uid_lookup_callback is required when value is None"
                )
            value = value_by_uid_lookup_callback(uid)
            if value is None:
                raise ValueError(
                    # f"Unknown template parameter uid ({uid})."
                    "One or more of the specified template parameters can not be found."
                )
        return cls(uid=uid, value=value)


@dataclass(frozen=True)
class NumericParameterValueVO(SimpleParameterValueVO):
    value: float

    @classmethod
    def from_input_values(cls, *, uid: str, value: float) -> "NumericParameterValueVO":
        return cls(uid=uid, value=value)


@dataclass(frozen=True)
class ComplexParameterValue(ParameterValueVO):
    parameters: Sequence[SimpleParameterValueVO]
    parameter_template: str
    conjunction: str = ""

    @property
    def value(self):
        val = self.parameter_template
        for i, param in enumerate(extract_parameters(self.parameter_template)):
            val = val.replace(f"[{param}]", str(self.parameters[i].value))
        return val


@dataclass(frozen=True)
class ParameterValueEntryVO:
    """
    Value Object representing a set of single parameter values entered into template
    placeholder. Contains parameter name, a conjunction  and list of parameter
    values to be combined into resulting name.
    """

    parameters: Sequence[ParameterValueVO]
    conjunction: str
    parameter_name: str

    @classmethod
    def from_repository_values(
        cls,
        *,
        parameter_name: str,
        parameters: Sequence[ParameterValueVO],
        conjunction: str,
    ) -> "ParameterValueEntryVO":
        return cls(
            parameter_name=parameter_name,
            parameters=tuple(parameters),
            conjunction=conjunction,
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        parameter_name: str,
        parameters: Sequence[ParameterValueVO],
        conjunction: str,
        parameter_exists_callback: Callable[[str], bool],
        parameter_value_uid_exists_for_parameter_callback: Callable[[str, str], bool],
        conjunction_exists_callback: Callable[[str], bool],
    ) -> "ParameterValueEntryVO":

        if not parameter_exists_callback(parameter_name):
            raise ValueError(f"Unknown parameter name: {parameter_name}")

        for parameter_value in parameters:
            if not parameter_value_uid_exists_for_parameter_callback(
                parameter_name, parameter_value.uid, parameter_value.value
            ):
                raise ValueError(
                    f"Parameter value {parameter_value.uid} ('{parameter_value.value}') not valid for"
                    f" parameter '{parameter_name}'"
                )

        if not conjunction_exists_callback(conjunction):
            raise ValueError(f"Unknown conjunction: {conjunction}")

        return cls(
            parameter_name=parameter_name,
            conjunction=conjunction,
            parameters=tuple(parameters),
        )
