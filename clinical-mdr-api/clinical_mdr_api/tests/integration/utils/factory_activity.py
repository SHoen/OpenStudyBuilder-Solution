from clinical_mdr_api.models import StudySelectionActivityCreateInput
from clinical_mdr_api.services.study_activity_selection import (
    StudyActivitySelectionService,
)


def create_study_activity(study_uid: str, activity_uid="activity_root1"):
    return StudyActivitySelectionService(author="test").make_selection(
        study_uid,
        StudySelectionActivityCreateInput(
            flowchartGroupUid="term_root_final", activityUid=activity_uid
        ),
    )
