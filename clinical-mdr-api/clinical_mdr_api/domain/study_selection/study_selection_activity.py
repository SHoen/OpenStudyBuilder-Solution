import datetime
from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.study_selection import study_selection_base


@dataclass(frozen=True)
class StudySelectionActivityVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivityVO acts as the value object for a
    single selection between a study and an activity
    """

    study_selection_uid: str
    study_uid: str
    activity_uid: str
    activity_version: Optional[str]
    flowchart_group_uid: str
    activity_order: Optional[int]
    show_activity_group_in_protocol_flowchart: bool
    show_activity_subgroup_in_protocol_flowchart: bool
    show_activity_in_protocol_flowchart: bool
    note: Optional[str]
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]
    accepted_version: bool = False

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        activity_uid: str,
        activity_version: str,
        flowchart_group_uid: str,
        user_initials: str,
        show_activity_group_in_protocol_flowchart: Optional[bool] = True,
        show_activity_subgroup_in_protocol_flowchart: Optional[bool] = True,
        show_activity_in_protocol_flowchart: Optional[bool] = False,
        note: Optional[str] = None,
        activity_order: Optional[int] = 0,
        study_selection_uid: Optional[str] = None,
        start_date: Optional[datetime.datetime] = None,
        accepted_version: bool = False,
        generate_uid_callback: Callable[[], str] = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now()

        return cls(
            study_uid=normalize_string(study_uid),
            activity_uid=normalize_string(activity_uid),
            activity_version=activity_version,
            flowchart_group_uid=normalize_string(flowchart_group_uid),
            show_activity_group_in_protocol_flowchart=show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=show_activity_in_protocol_flowchart,
            note=note,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            activity_order=activity_order,
            user_initials=normalize_string(user_initials),
            accepted_version=accepted_version,
        )

    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        # Checks if there exists an activity which is approved with activity_uid
        if not object_exist_callback(normalize_string(self.activity_uid)):
            raise ValueError(
                f"There is no approved activity identified by provided uid ({self.activity_uid})"
            )
        if not ct_term_level_exist_callback(self.flowchart_group_uid):
            raise ValueError(
                f"There is no approved flowchart group identified by provided term uid ({self.flowchart_group_uid})"
            )


@dataclass
class StudySelectionActivityAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityAR holds all the study activity
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection

    """

    _object_type = "activity"
    _object_uid_field = "activity_uid"
    _order_field_name = "activity_order"
