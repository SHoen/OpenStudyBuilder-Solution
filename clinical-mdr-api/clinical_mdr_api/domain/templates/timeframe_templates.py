from dataclasses import dataclass

from clinical_mdr_api.domain.versioned_object_aggregate import TemplateAggregateRootBase


@dataclass
class TimeframeTemplateAR(TemplateAggregateRootBase):
    """
    A specific Timeframe Template AR. It can be used to customize Timeframe Template
    behavior. Inherits strictly generic template versioning behaviors
    """
