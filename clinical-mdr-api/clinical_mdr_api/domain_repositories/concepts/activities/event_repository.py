from clinical_mdr_api.domain.concepts.activities.event import EventAR, EventVO
from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import EventRoot, EventValue
from clinical_mdr_api.models.activities.event import Event


class EventRepository(ActivityInstanceRepository):
    root_class = EventRoot
    value_class = EventValue
    aggregate_class = EventAR
    value_object_class = EventVO
    return_model = Event
