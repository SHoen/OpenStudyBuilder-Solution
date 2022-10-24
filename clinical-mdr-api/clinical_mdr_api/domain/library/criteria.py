from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from clinical_mdr_api.domain._utils import extract_parameters
from clinical_mdr_api.domain.library.object import (
    ParametrizedTemplateARBase,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domain.library.parameter_value import ParameterValueEntryVO
from clinical_mdr_api.domain.versioned_object_aggregate import TemplateVO


@dataclass(frozen=True)
class CriteriaTemplateVO(ParametrizedTemplateVO):

    guidance_text: str

    @classmethod
    def from_repository_values(
        cls,
        *,
        template_name: str,
        template_uid: str,
        guidance_text: str,
        parameter_values: Sequence[ParameterValueEntryVO]
    ) -> "CriteriaTemplateVO":
        """
        Create object based on repository values.

        Overriden version to include guidance text.
        """
        return cls(
            template_uid=template_uid,
            template_name=template_name,
            guidance_text=guidance_text,
            parameter_values=tuple(parameter_values),
        )

    @classmethod
    def from_input_values_2(
        cls,
        *,
        template_uid: str,
        parameter_values: Sequence[ParameterValueEntryVO],
        name_override: Optional[str] = None,
        is_instance_editable_callback: Optional[Callable[[str], bool]] = None,
        get_final_template_vo_by_template_uid_callback: Callable[
            [str], Optional[TemplateVO]
        ]
    ) -> "CriteriaTemplateVO":
        """
        Creates object based on external input.

        Overriden version to include guidance text.
        """
        template = get_final_template_vo_by_template_uid_callback(template_uid)

        if template is None:
            raise ValueError(
                "The template was not found. Make sure that there is a latest 'Final' version."
            )

        # TODO: is there replacement?
        # if [_.parameter_name for _ in parameter_values] != list(template.parameter_names):
        #    raise ValueError("Parameter value list does not match template defined parameter list")

        if name_override is not None:
            if extract_parameters(name_override) != extract_parameters(template.name):
                raise ValueError(
                    "Name override does not match template defined parameter list"
                )
            if not is_instance_editable_callback(template_uid):
                raise ValueError(
                    "Editing the name of an instance of this template is not allowed"
                )

        return cls(
            template_name=name_override if name_override is not None else template.name,
            template_uid=template_uid,
            parameter_values=tuple(parameter_values),
            guidance_text=template.guidance_text,
        )


@dataclass
class CriteriaAR(ParametrizedTemplateARBase):
    """
    Implementation of Criteria AR. Solely based on Parametrized Template.
    If there will be a need to customize behavior of Criteria comparing to
    other template derived objects - this code should go here.
    """

    _template: CriteriaTemplateVO

    @property
    def template_guidance_text(self) -> str:
        """Shortcut to access template's guidance text."""
        return self._template.guidance_text
