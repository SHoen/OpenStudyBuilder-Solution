from typing import Optional

from clinical_mdr_api.models.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceVersion,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel


class Finding(ActivityInstance):
    valueSasDisplayFormat: Optional[str]
    specimen: Optional[SimpleTermModel]
    testCode: Optional[SimpleTermModel]


class FindingCreateInput(ActivityInstanceCreateInput):
    valueSasDisplayFormat: Optional[str] = None
    specimen: Optional[str] = None
    testCode: Optional[str] = None


class FindingEditInput(ActivityInstanceEditInput):
    valueSasDisplayFormat: Optional[str]
    specimen: Optional[str]
    testCode: Optional[str]


class FindingVersion(ActivityInstanceVersion, Finding):
    pass
