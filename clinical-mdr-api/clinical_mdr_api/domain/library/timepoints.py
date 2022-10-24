from dataclasses import dataclass

from clinical_mdr_api.domain.library.object import ParametrizedTemplateARBase


@dataclass
class TimepointAR(ParametrizedTemplateARBase):
    """
    Implementation of Timepoint AR. Solely based on Parametrized Template.
    If there will be a need to customize behavior of Timepoints comparing to
    other template derived objects - this code should go here.
    """