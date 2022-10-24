from clinical_mdr_api.domain.concepts.activities.reminder import ReminderAR, ReminderVO
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ReminderRoot,
    ReminderValue,
)
from clinical_mdr_api.models.activities.reminder import Reminder


class ReminderRepository(ActivityInstanceRepository):

    root_class = ReminderRoot
    value_class = ReminderValue
    aggregate_class = ReminderAR
    value_object_class = ReminderVO
    return_model = Reminder
