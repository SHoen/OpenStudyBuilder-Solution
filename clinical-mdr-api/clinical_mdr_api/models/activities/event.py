from clinical_mdr_api.models.activities.activity_instance import (
    ActivityInstance,
    ActivityInstanceCreateInput,
    ActivityInstanceEditInput,
    ActivityInstanceVersion,
)


class Event(ActivityInstance):
    pass


class EventCreateInput(ActivityInstanceCreateInput):
    pass


class EventEditInput(ActivityInstanceEditInput):
    pass


class EventVersion(ActivityInstanceVersion):
    pass
