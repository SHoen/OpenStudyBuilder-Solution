from clinical_mdr_api.domain.library.timeframes import TimeframeAR
from clinical_mdr_api.domain.library.timepoints import TimepointAR
from clinical_mdr_api.models.timepoint import Timepoint, TimepointVersion
from clinical_mdr_api.services.generic_object_service import (
    GenericObjectService,  # type: ignore
)


class TimepointService(GenericObjectService[TimeframeAR]):
    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: TimeframeAR
    ) -> Timepoint:
        # return Timeframe(**self._get_datamap(item_ar))
        return Timepoint.from_timepoint_ar(item_ar)

    aggregate_class = TimepointAR
    version_class = TimepointVersion
    templateUidProperty = "timepointTemplateUid"
    templateNameProperty = "timepointTemplate"
