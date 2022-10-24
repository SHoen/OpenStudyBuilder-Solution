import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api.domain.study_selection.study_selection_cohort import (
    StudySelectionCohortAR,
    StudySelectionCohortVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyArm,
    StudyBranchArm,
    StudyCohort,
)


@dataclass
class SelectionHistoryCohort:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: Optional[str]
    cohort_name: Optional[str]
    cohort_short_name: Optional[str]
    cohort_code: Optional[str]
    cohort_description: Optional[str]
    cohort_colour_code: Optional[str]
    cohort_number_of_subjects: Optional[int]
    branch_arm_roots: Optional[Sequence[str]]
    arm_roots: Optional[Sequence[str]]
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]
    change_type: str
    end_date: Optional[datetime.datetime]
    order: int
    status: Optional[str]
    accepted_version: Optional[bool]


class StudySelectionCohortRepository:
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

    def _retrieves_all_data(
        self,
        study_uid: Optional[str] = None,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
        arm_uid: Optional[str] = None,
    ) -> Sequence[StudySelectionCohortVO]:
        query = ""
        query_parameters = {}
        if study_uid:
            query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
            query_parameters["uid"] = study_uid
        else:
            query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        if project_name is not None or project_number is not None:
            query += (
                "-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)"
            )
            filter_list = []
            if project_name is not None:
                filter_list.append("proj.name=$project_name")
                query_parameters["project_name"] = project_name
            if project_number is not None:
                filter_list.append("proj.project_number=$project_number")
                query_parameters["project_number"] = project_number
            query += " WHERE "
            query += " AND ".join(filter_list)

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_COHORT]->(sar:StudyCohort)
            WITH DISTINCT sr, sar, sv
            OPTIONAL MATCH (sv)-[:HAS_STUDY_ARM]->(ars:StudyArm)-[:STUDY_ARM_HAS_COHORT]->(sar)
            WITH ars, sr, sv, sar ORDER BY ars.order
            OPTIONAL MATCH (sv)-[:HAS_STUDY_BRANCH_ARM]-(bars:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_COHORT]->(sar)
            WITH bars, ars, sr, sar ORDER BY bars.order
            MATCH (sar)<-[:AFTER]-(sa:StudyAction)"""
        if arm_uid:
            filter_by_arm_uid = """
            WHERE head([(study_arm:StudyArm)-[:STUDY_ARM_HAS_COHORT]->(sar) | study_arm.uid])=$arm_uid"""
            query += filter_by_arm_uid
            query_parameters["arm_uid"] = arm_uid
        query += """
            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS study_selection_uid,
                sar.name AS cohort_name,
                sar.short_name AS cohort_short_name,
                sar.cohort_code AS cohort_code,
                sar.description AS cohort_description,
                sar.order AS order,
                sar.accepted_version AS accepted_version,
                sar.number_of_subjects AS number_of_subjects,
                sar.colour_code AS colour_code,
                COLLECT (bars.uid) AS branch_arm_root_uids,
                COLLECT (ars.uid) AS arm_root_uids,
                sar.text AS text,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_cohort_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_cohort_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionCohortVO.from_input_values(
                user_initials=selection["user_initials"],
                study_uid=selection["study_uid"],
                name=selection["cohort_name"],
                short_name=selection["cohort_short_name"],
                code=selection["cohort_code"],
                description=selection["cohort_description"],
                study_selection_uid=selection["study_selection_uid"],
                branch_arm_root_uids=selection["branch_arm_root_uids"],
                arm_root_uids=selection["arm_root_uids"],
                number_of_subjects=selection["number_of_subjects"],
                colour_code=selection["colour_code"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        arm_uid: Optional[str] = None,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
    ) -> Optional[StudySelectionCohortAR]:
        """
        Finds all the selected study cohorts for a given study
        :param project_name:
        :param project_number:
        :param arm_uid:
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid,
            arm_uid=arm_uid,
            project_name=project_name,
            project_number=project_number,
        )
        selection_aggregate = StudySelectionCohortAR.from_repository_values(
            study_uid=study_uid, study_cohorts_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionCohortAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_cohorts_selection:
            all_current_ids.append(item.study_selection_uid)
        all_closure_ids = []
        for item in study_selection.repository_closure_data:
            all_closure_ids.append(item.study_selection_uid)
        # if uid is in current data
        if study_selection_uid in all_current_ids:
            # if uid is in closure data
            if study_selection_uid in all_closure_ids:
                return Edit()
            return Create()
        return Delete()

    @staticmethod
    def cohort_exists_by(
        db_property: str, value: str, cohort_vo: StudySelectionCohortVO
    ) -> StudyArm:
        kwarg_value = getattr(cohort_vo, value)
        cohort_node = (
            StudyCohort.nodes.has(study_value=True)
            .filter(
                uid__ne=cohort_vo.study_selection_uid,
                study_value__study_root__uid=cohort_vo.study_uid,
            )
            .get_or_none(**{db_property: kwarg_value})
        )
        return cohort_node

    def save(self, study_selection: StudySelectionCohortAR, author: str) -> None:
        """
        Persist the set of selected study amrs from the aggregate to the database
        :param study_selection:
        :param author:
        """
        assert study_selection.repository_closure_data is not None

        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        if study_root_node.latest_released.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a released state."
            )

        if study_root_node.latest_locked.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a locked state."
            )

        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete have been called
        if len(closure_data) > len(study_selection.study_cohorts_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_cohorts_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # update the selection by removing the old if the old exists, and adding new selection
                    selections_to_remove.append((order, closure_data[order - 1]))
                    selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        # dictonary of last nodes to traverse to their old connections
        last_nodes = {}

        # loop through and remove selections
        for order, selection in selections_to_remove:
            # traverse --> study_value__study_branch__uid
            last_study_selection_node = latest_study_value_node.has_study_cohort.get(
                uid=selection.study_selection_uid
            )
            # detect if the action should be create, delete or edit, then create audit node of the that StudyAction type
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            # create the before node to the last_study_selection_node and audit trial to study_root
            audit_node = self._set_before_audit_info(
                audit_node=audit_node,
                study_selection_node=last_study_selection_node,
                study_root_node=study_root_node,
                author=author,
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            # storage of the removed node audit trail to after put the "after" relationship to the new one
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            # storage of the removed node to after get its connections
            last_nodes[selection.study_selection_uid] = last_study_selection_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node=latest_study_value_node,
                    order=order,
                    selection=selection,
                    audit_node=audit_node,
                    for_deletion=True,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            # create last_study_selection_node None as the new studySelection could not have an audit trial node
            last_study_selection_node = None
            # if the study selection already has an audit trail node
            if selection.study_selection_uid in audit_trail_nodes:
                # extract the audit_trail_node
                audit_node = audit_trail_nodes[selection.study_selection_uid]
                # extract the last "AFTER" selection that now is "BEFORE"
                last_study_selection_node = last_nodes[selection.study_selection_uid]
            else:
                audit_node = Create()
                audit_node.user_initials = selection.user_initials
                audit_node.date = selection.start_date
                audit_node.save()
                study_root_node.audit_trail.connect(audit_node)
            self._add_new_selection(
                latest_study_value_node=latest_study_value_node,
                order=order,
                selection=selection,
                audit_node=audit_node,
                for_deletion=False,
            )

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionCohortVO
    ) -> None:
        """
        Removal is taking both new and old uid. When a study selection is deleted, we do no longer need to use the uid
        on that study selection node anymore, however do to database constraint the node needs to have a uid. So we are
        overwriting a deleted node uid, with a new never used dummy uid.

        We are doing this to be able to maintain the selection instead of removing it, instead a removal will only
        detach the selection from the study value node. So we keep the old selection to have full audit trail available
        in the database.
        :param study_uid:
        :param old_uid:
        :param new_uid:
        :return:
        """
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_COHORT]->(se:StudyCohort { uid: $selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_selection_node: StudyCohort,
        study_root_node: StudyRoot,
        author: str,
    ) -> StudyAction:
        audit_node.user_initials = author
        audit_node.date = datetime.datetime.now()
        audit_node.save()

        study_selection_node.has_before.connect(audit_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    @staticmethod
    def _add_new_selection(
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionCohortVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        # Create new cohort selection
        study_cohort_selection_node = StudyCohort(
            order=order,
            uid=selection.study_selection_uid,
            accepted_version=selection.accepted_version,
            name=selection.name,
            short_name=selection.short_name,
            cohort_code=selection.code,
            description=selection.description,
            colour_code=selection.colour_code,
            number_of_subjects=selection.number_of_subjects,
        ).save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_cohort.connect(
                study_cohort_selection_node
            )
        # Connect new node with audit trail
        study_cohort_selection_node.has_after.connect(audit_node)

        # check if arm root is set
        if selection.arm_root_uids:
            for arm_root_uid in selection.arm_root_uids:
                # find the objective
                study_arm_root = StudyArm.nodes.filter(
                    study_value__study_root__uid=selection.study_uid
                ).get_or_none(uid=arm_root_uid)[0]
                # connect to node
                # pylint: disable=no-member
                study_cohort_selection_node.arm_root.connect(study_arm_root)

        # check if branch arm root is set
        if selection.branch_arm_root_uids:
            for branch_arm_root_uid in selection.branch_arm_root_uids:
                # find the objective
                study_branch_arm_root = StudyBranchArm.nodes.filter(
                    study_value__study_root__uid=selection.study_uid
                ).get_or_none(uid=branch_arm_root_uid)[0]
                # connect to node]
                # pylint: disable=no-member
                study_cohort_selection_node.branch_arm_root.connect(
                    study_branch_arm_root
                )

    def generate_uid(self) -> str:
        return StudyCohort.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study cohort either for a specific selection or for all study cohort for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyCohort { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sc:StudyCohort)
                    WITH distinct(all_sc)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sc:StudyCohort)
                    WITH DISTINCT all_sc
                    """
        specific_cohort_selections_audit_trail = db.cypher_query(
            cypher
            + """
            WITH DISTINCT all_sc
            OPTIONAL MATCH (ats:StudyArm)-[:STUDY_ARM_HAS_COHORT]->(all_sc)
            WITH all_sc, ats  ORDER BY ats.order
            OPTIONAL MATCH (bats:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_COHORT]->(all_sc)
            WITH all_sc, ats, bats  ORDER BY bats.order
            WITH DISTINCT all_sc, ats, bats
            ORDER BY all_sc.order ASC
            MATCH (all_sc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sc)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sc, asa, bsa, ats, bats
            ORDER BY all_sc.uid, asa.date DESC
            RETURN
                all_sc.uid AS study_selection_uid,
                all_sc.name AS cohort_name,
                all_sc.short_name AS cohort_short_name,
                all_sc.cohort_code AS cohort_code,
                all_sc.description AS cohort_description,
                all_sc.order AS order,
                all_sc.accepted_version AS accepted_version,
                all_sc.number_of_subjects AS number_of_subjects,
                all_sc.colour_code AS colour_code,
                COLLECT (bats.uid) AS branch_arm_root_uids,
                COLLECT (ats.uid) AS arm_root_uids,
                all_sc.text AS text,
                asa.date AS start_date,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_cohort_selections_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryCohort(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    cohort_name=res["cohort_name"],
                    cohort_short_name=res["cohort_short_name"],
                    cohort_code=res["cohort_code"],
                    cohort_description=res["cohort_description"],
                    cohort_colour_code=res["colour_code"],
                    cohort_number_of_subjects=res["number_of_subjects"],
                    branch_arm_roots=res["branch_arm_root_uids"],
                    arm_roots=res["arm_root_uids"],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    end_date=end_date,
                    accepted_version=res["accepted_version"],
                    status=None,
                    order=res["order"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str = None
    ) -> List[SelectionHistoryCohort]:
        """
        Simple method to return all versions of a study objectives for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        pass
