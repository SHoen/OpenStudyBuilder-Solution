from dataclasses import dataclass
from typing import Optional

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.study_selection.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivitySchedule,
)
from clinical_mdr_api.domain_repositories.study_selection import base


@dataclass
class SelectionHistory(base.SelectionHistory):
    """Class for selection history items."""

    study_activity_uid: str
    study_visit_uid: str
    note: Optional[str]


class StudyActivityScheduleRepository(base.StudySelectionRepository):
    @staticmethod
    def _acquire_write_lock_study_value(uid: str) -> None:
        db.cypher_query(
            """
             MATCH (sr:StudyRoot {uid: $uid})
             REMOVE sr.__WRITE_LOCK__
             RETURN true
            """,
            {"uid": uid},
        )

    def _from_repository_values(
        self, study_uid: str, selection: StudyActivitySchedule
    ) -> StudyActivityScheduleVO:
        study_action = selection.has_after.all()[0]
        study_activity = selection.study_activity.single()
        study_visit = selection.study_visit.single()
        study_activity_name = study_activity.has_selected_activity.single().name
        study_visit_name = (
            study_visit.has_visit_name.single().has_latest_value.single().name
        )
        return StudyActivityScheduleVO(
            uid=selection.uid,
            study_uid=study_uid,
            study_activity_uid=study_activity.uid,
            study_activity_name=study_activity_name,
            study_visit_uid=study_visit.uid,
            study_visit_name=study_visit_name,
            note=selection.note,
            start_date=study_action.date,
            user_initials=study_action.user_initials,
        )

    def perform_save(
        self,
        study_value_node: StudyValue,
        selection_vo: StudyActivityScheduleVO,
        author: str,
    ) -> StudyActivityScheduleVO:
        study_activity_node = study_value_node.has_study_activity.get_or_none(
            uid=selection_vo.study_activity_uid
        )
        if study_activity_node is None:
            raise exceptions.NotFoundException(
                f"The study activity with uid {selection_vo.study_activity_uid} was not found"
            )
        study_visit_node = study_value_node.has_study_visit.get_or_none(
            uid=selection_vo.study_visit_uid
        )
        if study_visit_node is None:
            raise exceptions.NotFoundException(
                f"The study visit with uid {selection_vo.study_visit_uid} was not found"
            )

        # Detach previous node from study
        if selection_vo.uid is not None:
            self._remove_old_selection_if_exists(selection_vo.study_uid, selection_vo)

        # Create new node
        schedule = StudyActivitySchedule(uid=selection_vo.uid, note=selection_vo.note)
        schedule.save()

        # Create relations
        schedule.study_activity.connect(study_activity_node)
        schedule.study_visit.connect(study_visit_node)
        study_value_node.has_study_activity_schedule.connect(schedule)

        return schedule

    def _remove_old_selection_if_exists(
        self, study_uid: str, schedule: StudyActivityScheduleVO
    ):
        return db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[rel:HAS_STUDY_ACTIVITY_SCHEDULE]->(:StudyActivitySchedule {uid: $schedule_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "schedule_uid": schedule.uid,
            },
        )

    def get_study_selection(
        self, study_value_node: StudyValue, selection_uid: str
    ) -> StudyActivitySchedule:
        schedule = study_value_node.has_study_activity_schedule.get_or_none(
            uid=selection_uid
        )
        if schedule is None:
            raise exceptions.NotFoundException(
                f"The study activity schedule with uid {selection_uid} was not found"
            )
        return schedule

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(self, study_uid: str, selection_uid: str = None):
        """
        returns the audit trail for study activity schedule either for a
        specific selection or for all study activity schedules for the study.
        """
        if selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sas:StudyActivitySchedule {uid: $selection_uid})
            WITH sas
            MATCH (sas)-[:AFTER|BEFORE*0..]-(all_sas:StudyActivitySchedule)
            WITH distinct(all_sas)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sas:StudyActivitySchedule)
            WITH DISTINCT all_sas
            """
        specific_schedules_audit_trail = db.cypher_query(
            cypher
            + """
            MATCH (all_sas)<-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(sa:StudyActivity)
            MATCH (all_sas)<-[:STUDY_VISIT_HAS_SCHEDULE]-(svi:StudyVisit)w
            MATCH (all_sas)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sas)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sas, sa, svi, asa, bsa
            ORDER BY all_sas.uid, asa.date DESC
            RETURN
                all_sas.uid AS uid,
                all_sas.note AS note,
                svi.uid AS study_visit_uid,
                sa.uid AS study_activity_uid,
                labels(asa) AS change_type,
                asa.date AS start_date,
                bsa.date AS end_date,
                asa.user_initials AS user_initials
            """,
            {"study_uid": study_uid, "selection_uid": selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_schedules_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistory(
                    study_uid=study_uid,
                    study_selection_uid=res["uid"],
                    study_activity_uid=res["study_activity_uid"],
                    study_visit_uid=res["study_visit_uid"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    note=res["note"],
                    end_date=end_date,
                )
            )
        return result

    def close(self) -> None:
        pass
