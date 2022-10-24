import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api.domain.study_selection.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.objective import ObjectiveRoot
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyEndpoint,
    StudyObjective,
)


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    objective_uid: Optional[str]
    objective_level_uid: Optional[str]
    start_date: datetime.datetime
    status: Optional[str]
    user_initials: str
    change_type: str
    end_date: Optional[datetime.datetime]
    order: int
    objective_version: Optional[str]


class StudySelectionObjectiveRepository:
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
    ) -> Sequence[StudySelectionObjectiveVO]:
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
            MATCH (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)-[:HAS_SELECTED_OBJECTIVE]->(ov:ObjectiveValue)
            CALL {
              WITH ov
              MATCH (ov) <-[ver]-(or:ObjectiveRoot) 
              WHERE ver.status = "Final"
              RETURN ver as ver, or as or
              ORDER BY ver.startDate DESC
              LIMIT 1
            }
            WITH DISTINCT sr, so, or, ver
            OPTIONAL MATCH (so)-[:HAS_OBJECTIVE_LEVEL]->(olr:CTTermRoot)<-[has_term:HAS_TERM]-(:CTCodelistRoot)
            -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(:CTCodelistNameValue {name: "Objective Level"})
            WITH sr, so, or, ver, olr, has_term
            ORDER BY has_term.order, so.order ASC
            MATCH (so)<-[:AFTER]-(sa:StudyAction)
            RETURN
                sr.uid AS study_uid,
                so.uid AS study_selection_uid,
                so.accepted_version AS accepted_version,
                or.uid AS objective_uid,
                olr.uid AS objective_level_uid,
                has_term.order as objective_level_order,
                sa.date AS start_date,
                sa.user_initials AS user_initials,
                ver.version AS objective_version
            """

        all_objective_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in helpers.db_result_to_list(all_objective_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionObjectiveVO.from_input_values(
                study_uid=selection["study_uid"],
                study_selection_uid=selection["study_selection_uid"],
                objective_uid=selection["objective_uid"],
                objective_version=selection["objective_version"],
                objective_level_uid=selection["objective_level_uid"],
                objective_level_order=selection["objective_level_order"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                user_initials=selection["user_initials"],
                accepted_version=acv,
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
    ) -> Optional[Sequence[StudySelectionObjectivesAR]]:
        """
        Finds all the selected study objectives for all studies, and create the aggregate
        :return: List of StudySelectionObjectivesAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionObjectivesAR.from_repository_values(
                    study_uid=study_uid, study_objectives_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self, study_uid: str, for_update: bool = False
    ) -> Optional[StudySelectionObjectivesAR]:
        """
        Finds all the selected study objectives for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(study_uid)
        selection_aggregate = StudySelectionObjectivesAR.from_repository_values(
            study_uid=study_uid, study_objectives_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionObjectivesAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_objectives_selection:
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

    def save(self, study_selection: StudySelectionObjectivesAR, author: str) -> None:
        """
        Persist the set of selected study objectives from the aggregate to the database
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
        if len(closure_data) > len(study_selection.study_objectives_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_objectives_selection, start=1
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

        # earlier connnected study endpoints
        study_endpoints_nodes = {}

        # loop through and remove selections
        for order, study_objective in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_objective.get(
                uid=study_objective.study_selection_uid
            )
            study_endpoints_nodes[
                study_objective.study_selection_uid
            ] = self._get_connected_study_endpoints(last_study_selection_node)
            self._remove_old_selection_if_exists(
                study_selection.study_uid, study_objective
            )
            audit_node = self._get_audit_node(
                study_selection, study_objective.study_selection_uid
            )
            audit_node = self._set_before_audit_info(
                audit_node=audit_node,
                study_objective_selection_node=last_study_selection_node,
                study_root_node=study_root_node,
                author=author,
            )
            audit_trail_nodes[study_objective.study_selection_uid] = audit_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node,
                    order,
                    study_objective,
                    audit_node,
                    [],
                    True,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            if selection.study_selection_uid in audit_trail_nodes:
                audit_node = audit_trail_nodes[selection.study_selection_uid]
            else:
                audit_node = Create()
                audit_node.user_initials = selection.user_initials
                audit_node.date = selection.start_date
                audit_node.save()
                study_root_node.audit_trail.connect(audit_node)
            if selection.study_selection_uid in study_endpoints_nodes:
                endpoints = study_endpoints_nodes[selection.study_selection_uid]
            else:
                endpoints = []
            self._add_new_selection(
                latest_study_value_node, order, selection, audit_node, endpoints, False
            )

    def _get_connected_study_endpoints(
        self, last_study_selection_node: StudyObjective
    ) -> List[StudyEndpoint]:
        all_connected_endpoints = (
            last_study_selection_node.study_endpoint_has_study_objective.all()
        )
        # Remove the relationship to the study endpoint, to move them to the new version
        for endpoint in all_connected_endpoints:
            endpoint.study_endpoint_has_study_objective.disconnect(
                last_study_selection_node
            )
        return all_connected_endpoints

    def _remove_old_selection_if_exists(
        self, study_uid: str, study_selection: StudySelectionObjectiveVO
    ) -> None:
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_OBJECTIVE]->(so:StudyObjective { uid: $study_selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "study_selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_objective_selection_node: StudyObjective,
        study_root_node: StudyRoot,
        author: str,
    ) -> StudyAction:
        audit_node.user_initials = author
        audit_node.date = datetime.datetime.now()
        audit_node.save()

        study_objective_selection_node.has_before.connect(audit_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionObjectiveVO,
        audit_node: StudyAction,
        study_endpoint_nodes: List[StudyEndpoint],
        for_deletion: bool = False,
    ):
        # find the objective value
        objective_root_node: ObjectiveRoot = ObjectiveRoot.nodes.get(
            uid=selection.objective_uid
        )
        latest_objective_value_node = objective_root_node.get_value_for_version(
            selection.objective_version
        )
        # Create new objective selection
        study_objective_selection_node = StudyObjective(order=order)
        study_objective_selection_node.uid = selection.study_selection_uid
        study_objective_selection_node.accepted_version = selection.accepted_version
        study_objective_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_objective.connect(
                study_objective_selection_node
            )
        # Connect new node with audit trail
        study_objective_selection_node.has_after.connect(audit_node)
        # reconnect the study endpoint which was connected to the prvius version
        for study_endpoint in study_endpoint_nodes:
            study_objective_selection_node.study_endpoint_has_study_objective.connect(
                study_endpoint
            )
        # Connect new node with Objective value
        study_objective_selection_node.has_selected_objective.connect(
            latest_objective_value_node
        )
        # Set objective level if exists
        if selection.objective_level_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.objective_level_uid)
            study_objective_selection_node.has_objective_level.connect(ct_term_root)

    def study_objective_exists(self, study_objective_uid: str) -> bool:
        """
        Simple function checking whether a study objective exist for a uid
        :return: boolean value
        """
        study_objective_node = StudyObjective.nodes.first_or_none(
            uid=study_objective_uid
        )
        if study_objective_node is None:
            return False
        return True

    def generate_uid(self) -> str:
        return StudyObjective.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study objectives either for a specific selection or for all study objectives for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(so:StudyObjective { uid: $study_selection_uid})
            WITH so
            MATCH (so)-[:AFTER|BEFORE*0..]-(all_so:StudyObjective)
            WITH distinct(all_so)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_so:StudyObjective)
            WITH DISTINCT all_so
            """
        specific_objective_selections_audit_trail = db.cypher_query(
            cypher
            + """
            MATCH (all_so)-[:HAS_SELECTED_OBJECTIVE]->(ov:ObjectiveValue)

            CALL {
              WITH ov
              MATCH (ov) <-[ver]-(or:ObjectiveRoot) 
              WHERE ver.status = "Final"
              RETURN ver as ver, or as or
              ORDER BY ver.startDate DESC
              LIMIT 1
            }

            WITH DISTINCT all_so, or, ver
            OPTIONAL MATCH (all_so)-[:HAS_OBJECTIVE_LEVEL]->(olr:CTTermRoot)
            WITH DISTINCT all_so, or, olr, ver
            MATCH (all_so)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_so)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_so, or, olr, asa, bsa, ver
            ORDER BY all_so.uid, asa.date DESC
            RETURN
                all_so.uid AS study_selection_uid,
                or.uid AS objective_uid,
                olr.uid AS objective_level_uid,
                asa.date AS start_date,
                asa.status AS status,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date,
                all_so.order AS order,
                ver.version AS objective_version""",
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_objective_selections_audit_trail):
            for action in res["change_type"]:
                if not "StudyAction" in action:
                    change_type = action
            if res["end_date"]:
                end_date = convert_to_datetime(value=res["end_date"])
            else:
                end_date = None
            result.append(
                SelectionHistory(
                    study_selection_uid=res["study_selection_uid"],
                    objective_uid=res["objective_uid"],
                    objective_level_uid=res["objective_level_uid"],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    status=res["status"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    end_date=end_date,
                    order=res["order"],
                    objective_version=res["objective_version"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str = None
    ) -> List[Optional[dict]]:
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
