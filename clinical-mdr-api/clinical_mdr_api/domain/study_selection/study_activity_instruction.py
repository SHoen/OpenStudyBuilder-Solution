import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class StudyActivityInstructionVO:
    study_uid: str
    study_activity_uid: Optional[str]
    activity_instruction_uid: Optional[str]

    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]

    uid: Optional[str] = None
    activity_instruction_name: Optional[str] = None
