from clinical_mdr_api.models.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceVersion,
)


class Reminder(ActivityInstance):
    pass


class ReminderCreateInput(ActivityInstanceCreateInput):
    pass


class ReminderEditInput(ActivityInstanceEditInput):
    pass


class ReminderVersion(ActivityInstanceVersion):
    pass
