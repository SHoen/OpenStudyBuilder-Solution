import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class StudyActivityScheduleVO:
    study_uid: str
    study_activity_uid: Optional[str]
    study_activity_name: Optional[str]
    study_visit_uid: Optional[str]
    study_visit_name: Optional[str]
    note: Optional[str]

    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]

    uid: Optional[str] = None
