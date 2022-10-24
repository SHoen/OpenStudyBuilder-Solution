import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api.domain.study_selection.study_selection_criteria import (
    StudySelectionCriteriaAR,
    StudySelectionCriteriaVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.criteria import CriteriaRoot
from clinical_mdr_api.domain_repositories.models.criteria_template import (
    CriteriaTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyCriteria


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    syntax_object_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    criteria_type_uid: Optional[str]
    criteria_type_order: Optional[int]
    status: Optional[str]
    end_date: Optional[datetime.datetime]
    syntax_object_version: Optional[str]
    is_instance: bool = True
    key_criteria: bool = False


class StudySelectionCriteriaRepository:
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
    ) -> Sequence[StudySelectionCriteriaVO]:
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
            MATCH (sv)-[:HAS_STUDY_CRITERIA]->(sc:StudyCriteria)
            CALL {
                WITH sc
                MATCH (sc)-[:HAS_SELECTED_CRITERIA]->(:CriteriaValue)<-[ver]-(cr:CriteriaRoot)<-[:HAS_CRITERIA]-(:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, cr as obj, term.uid as termUid, true as isInstance
                ORDER BY ver.startDate DESC
                LIMIT 1
            UNION
                WITH sc
                MATCH (sc)-[:HAS_SELECTED_CRITERIA_TEMPLATE]->(:CriteriaTemplateValue)<-[ver]-(ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, ctr as obj, term.uid as termUid, false as isInstance
                ORDER BY ver.startDate DESC
                LIMIT 1
            }
            WITH DISTINCT sr, termUid, sc, obj, ver, isInstance
            ORDER BY termUid, sc.order ASC
            MATCH (sc)<-[:AFTER]-(sa:StudyAction)
            RETURN
                sr.uid AS study_uid,
                termUid AS criteria_type_uid,
                sc.order AS criteria_type_order,
                sc.uid AS study_selection_uid,
                sc.accepted_version AS accepted_version,
                obj.uid AS syntax_object_uid,
                sa.date AS start_date,
                sa.user_initials AS user_initials,
                ver.version AS syntax_object_version,
                isInstance AS is_instance,
                sc.key_criteria as key_criteria
            """

        all_criteria_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in helpers.db_result_to_list(all_criteria_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionCriteriaVO.from_input_values(
                study_uid=selection["study_uid"],
                criteria_type_uid=selection["criteria_type_uid"],
                criteria_type_order=selection["criteria_type_order"],
                study_selection_uid=selection["study_selection_uid"],
                syntax_object_uid=selection["syntax_object_uid"],
                syntax_object_version=selection["syntax_object_version"],
                is_instance=selection["is_instance"],
                key_criteria=selection["key_criteria"],
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
    ) -> Optional[Sequence[StudySelectionCriteriaAR]]:
        """
        Finds all the selected study criteria for all studies, and create the aggregate
        :return: List of StudySelectionCriteriaAR, potentially empty
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
                StudySelectionCriteriaAR.from_repository_values(
                    study_uid=study_uid, study_criteria_selection=selections
                )
            )

        return selection_aggregates

    def find_by_study(
        self, study_uid: str, for_update: bool = False
    ) -> Optional[StudySelectionCriteriaAR]:
        """
        Finds all the selected study criteria for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """

        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(study_uid)
        selection_aggregate = StudySelectionCriteriaAR.from_repository_values(
            study_uid=study_uid, study_criteria_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionCriteriaAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_criteria_selection:
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

    def update_selection_to_instance(
        self,
        study_uid: str,
        study_criteria_uid: str,
        criteria_uid: str,
        criteria_version: str,
    ) -> None:
        """Update the selection to instance

        Args:
            study_uid (str): The uid of the study
            study_criteria_uid (str): The uid of the study criteria node
            criteria_uid (str): The uid of the instance to select
            criteria_version (str): The version of the instance to select

        Returns:
            None
        """

        # Get criteria value node
        criteria_root_node: CriteriaRoot = CriteriaRoot.nodes.get(uid=criteria_uid)
        latest_criteria_value_node = criteria_root_node.get_value_for_version(
            criteria_version
        )

        # Get the latest version of the study criteria node
        study_root_node: StudyRoot = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value_node: StudyValue = study_root_node.latest_value.single()
        study_criteria_selection_node: StudyCriteria = (
            latest_study_value_node.has_study_criteria.get_or_none(
                uid=study_criteria_uid
            )
        )
        # Connect study criteria node with criteria value node
        study_criteria_selection_node.has_selected_criteria.connect(
            latest_criteria_value_node
        )
        # Detach criteria selection node from criteria template node
        study_criteria_selection_node.has_selected_criteria_template.disconnect_all()

    def _get_latest_study_value(self, study_uid: str) -> Tuple[StudyRoot, StudyValue]:
        """Returns the study root and latest study value nodes for the given study, if re-ordering is allowed

        Args:
            study_uid (str): UID of the study

        Raises:
            VersioningException: Returns an error if the study cannot be reordered or get new items

        Returns:
            Tuple[StudyRoot, StudyValue]: Returned node objects
        """
        study_root_node = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        if study_root_node.latest_released.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a released state."
            )

        if study_root_node.latest_locked.get_or_none() == latest_study_value_node:
            raise VersioningException(
                "You cannot add or reorder a study selection when the study is in a locked state."
            )

        return study_root_node, latest_study_value_node

    def _list_selections_to_add_or_remove(
        self, closure: dict, criteria: dict
    ) -> Tuple[dict, dict]:
        """Compares the current and target state of the selection and returns the lists of objects to add/remove to/from the selection

        Args:
            closure (dict): The closure object containing the current selection
            criteria (dict): The object containing the new target state of the selection

        Returns:
            Tuple[dict, dict]: Returns two lists of selections to add and to remove
        """
        selections_to_remove = {}
        selections_to_add = {}

        # First, check for any removed items
        for criteria_type, criteria_list in closure.items():
            # check if object is removed from the selection list - delete has been called
            # two options to detect object is removed : list for given criteria type is empty or smaller than the list in the closure
            if (criteria_type not in criteria) or len(criteria_list) > len(
                criteria[criteria_type]
            ):
                # remove the last item from old list, as there will no longer be any study criteria with that high order
                selections_to_remove[criteria_type] = [
                    (len(criteria_list), criteria_list[-1])
                ]

        # Then, check for any added items
        # This has to be done by criteria type
        for criteria_type, criteria_list in criteria.items():
            # For each criteria in the current type, check if it is new
            for order, selected_object in enumerate(criteria_list, start=1):
                if criteria_type in closure:
                    _closure_data = closure[criteria_type]
                    # Nothing has been added, but an object might have been replaced
                    if len(_closure_data) > order - 1:
                        # check if anything has changed
                        if selected_object is not _closure_data[order - 1]:
                            # update the selection by removing the old if the old exists, and adding new selection
                            selections_to_remove.setdefault(criteria_type, []).append(
                                (order, _closure_data[order - 1])
                            )
                            selections_to_add.setdefault(criteria_type, []).append(
                                (order, selected_object)
                            )
                    else:
                        # else something new has been added
                        selections_to_add.setdefault(criteria_type, []).append(
                            (order, selected_object)
                        )
                else:
                    selections_to_add[criteria_type] = [(1, criteria_list[0])]

        return selections_to_remove, selections_to_add

    def save(self, study_selection: StudySelectionCriteriaAR, author: str) -> None:
        """
        Persist the set of selected study criteria from the aggregate to the database
        :param study_selection:
        :param author:
        """
        assert study_selection.repository_closure_data is not None

        # getting the latest study value node
        study_root_node, latest_study_value_node = self._get_latest_study_value(
            study_uid=study_selection.study_uid
        )
        # group closure by criteria type
        closure_group_by_type = {}
        for selected_object in study_selection.repository_closure_data:
            closure_group_by_type.setdefault(
                selected_object.criteria_type_uid, []
            ).append(selected_object)
        # group criteria by type
        criteria_group_by_type = {}
        for selected_object in study_selection.study_criteria_selection:
            criteria_group_by_type.setdefault(
                selected_object.criteria_type_uid, []
            ).append(selected_object)

        # process new/changed/deleted elements for each criteria type
        (
            selections_to_remove,
            selections_to_add,
        ) = self._list_selections_to_add_or_remove(
            closure=closure_group_by_type, criteria=criteria_group_by_type
        )

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}

        # loop through and remove selections
        for criteria_list in selections_to_remove.values():
            for selection in criteria_list:
                order = selection[0]
                selected_object = selection[1]
                last_study_selection_node = (
                    latest_study_value_node.has_study_criteria.get(
                        uid=selected_object.study_selection_uid
                    )
                )
                self._remove_old_selection_if_exists(
                    study_selection.study_uid, selected_object
                )
                audit_node = self._get_audit_node(
                    study_selection, selected_object.study_selection_uid
                )
                audit_node = self._set_before_audit_info(
                    audit_node, last_study_selection_node, study_root_node, author
                )
                audit_trail_nodes[selected_object.study_selection_uid] = audit_node
                if isinstance(audit_node, Delete):
                    self._add_new_selection(
                        latest_study_value_node,
                        order,
                        selected_object,
                        audit_node,
                        True,
                    )

        # loop through and add selections
        for criteria_list in selections_to_add.values():
            for selection in criteria_list:
                order = selection[0]
                selected_object = selection[1]
                if selected_object.study_selection_uid in audit_trail_nodes:
                    audit_node = audit_trail_nodes[selected_object.study_selection_uid]
                else:
                    audit_node = Create()
                    audit_node.user_initials = selected_object.user_initials
                    audit_node.date = selected_object.start_date
                    audit_node.save()
                    study_root_node.audit_trail.connect(audit_node)
                self._add_new_selection(
                    latest_study_value_node, order, selected_object, audit_node, False
                )

    def _remove_old_selection_if_exists(
        self, study_uid: str, study_selection: StudySelectionCriteriaVO
    ) -> None:
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_CRITERIA]->(so:StudyCriteria { uid: $study_selection_uid})
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
        study_criteria_selection_node: StudyCriteria,
        study_root_node: StudyRoot,
        author: str,
    ) -> StudyAction:
        audit_node.user_initials = author
        audit_node.date = datetime.datetime.now()
        audit_node.save()

        study_criteria_selection_node.has_before.connect(audit_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionCriteriaVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        if selection.is_instance:
            # Get the criteria value
            criteria_root_node: CriteriaRoot = CriteriaRoot.nodes.get(
                uid=selection.syntax_object_uid
            )
            latest_criteria_value_node = criteria_root_node.get_value_for_version(
                selection.syntax_object_version
            )
        else:
            # Get the criteria template value
            criteria_template_root_node: CriteriaTemplateRoot = (
                CriteriaTemplateRoot.nodes.get(uid=selection.syntax_object_uid)
            )
            latest_criteria_template_value_node = (
                criteria_template_root_node.get_value_for_version(
                    selection.syntax_object_version
                )
            )

        # Create new criteria selection
        study_criteria_selection_node = StudyCriteria(
            order=order, key_criteria=selection.key_criteria
        )
        study_criteria_selection_node.uid = selection.study_selection_uid
        study_criteria_selection_node.accepted_version = selection.accepted_version
        study_criteria_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_criteria.connect(
                study_criteria_selection_node
            )
        # Connect new node with audit trail
        study_criteria_selection_node.has_after.connect(audit_node)

        # Connect new node with object value node
        if selection.is_instance:
            study_criteria_selection_node.has_selected_criteria.connect(
                latest_criteria_value_node
            )
        else:
            study_criteria_selection_node.has_selected_criteria_template.connect(
                latest_criteria_template_value_node
            )

    def study_criteria_exists(self, study_criteria_uid: str) -> bool:
        """
        Simple function checking whether a study criteria exist for a uid
        :return: boolean value
        """
        study_criteria_node = StudyCriteria.nodes.get_or_none(uid=study_criteria_uid)
        if study_criteria_node is None:
            return False
        return True

    def generate_uid(self) -> str:
        return StudyCriteria.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study criteria either for a specific selection or for all study criteria for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sc:StudyCriteria { uid: $study_selection_uid})
            WITH sc
            MATCH (sc)-[:AFTER|BEFORE*0..]-(all_sc:StudyCriteria)
            WITH DISTINCT(all_sc)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sc:StudyCriteria)
            WITH DISTINCT all_sc
            """

        specific_criteria_selections_audit_trail_query = """
            CALL {
                WITH all_sc
                MATCH (all_sc)-[:HAS_SELECTED_CRITERIA]->(:CriteriaValue)<-[ver]-(cr:CriteriaRoot)<-[:HAS_CRITERIA]-(:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, cr as obj, term.uid as termUid, true as isInstance
                ORDER BY ver.startDate DESC
                LIMIT 1
            UNION
                WITH all_sc
                MATCH (all_sc)-[:HAS_SELECTED_CRITERIA_TEMPLATE]->(:CriteriaTemplateValue)<-[ver]-(ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(term:CTTermRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, ctr as obj, term.uid as termUid, false as isInstance
                ORDER BY ver.startDate DESC
                LIMIT 1
            }

            WITH DISTINCT termUid, all_sc, obj, ver, isInstance
            ORDER BY termUid, all_sc.order ASC
            MATCH (all_sc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sc)<-[:BEFORE]-(bsa:StudyAction)
            WITH termUid, all_sc, obj, asa, bsa, ver, isInstance
            ORDER BY all_sc.uid, asa.date DESC
            RETURN
                termUid AS criteria_type_uid,
                all_sc.order AS criteria_type_order,
                all_sc.uid AS study_selection_uid,
                obj.uid AS syntax_object_uid,
                asa.date AS start_date,
                asa.status AS status,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date,
                ver.version AS syntax_object_version,
                isInstance AS is_instance,
                all_sc.key_criteria as key_criteria
            """

        specific_criteria_selections_audit_trail = db.cypher_query(
            cypher + specific_criteria_selections_audit_trail_query,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_criteria_selections_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            if res["end_date"]:
                end_date = convert_to_datetime(value=res["end_date"])
            else:
                end_date = None
            result.append(
                SelectionHistory(
                    study_selection_uid=res["study_selection_uid"],
                    syntax_object_uid=res["syntax_object_uid"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    criteria_type_uid=res["criteria_type_uid"],
                    criteria_type_order=res["criteria_type_order"],
                    status=res["status"],
                    end_date=end_date,
                    syntax_object_version=res["syntax_object_version"],
                    is_instance=res["is_instance"],
                    key_criteria=res["key_criteria"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str = None
    ) -> List[Optional[dict]]:
        """
        Simple method to return all versions of a study criteria for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid is not None:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def _is_selected_object_instance(
        self, study_uid: str, study_selection_uid: str
    ) -> bool:
        """Method to return if the selected object is an instance or a template

        Args:
            study_uid (str) : UID of the study
            study_selection_uid (str): UID of the study selection

        Returns:
            bool: True if the selected object is an instance, False if it is a template
        """
        query = """
        MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[HAS_STUDY_CRITERIA]->(sc:StudyCriteria{uid:$study_selection_uid})
        WITH CASE WHEN EXISTS((sc)-[:HAS_SELECTED_CRITERIA_TEMPLATE]->()) THEN false ELSE true END AS is_instance
        RETURN is_instance
        """
        query_parameters = {
            "study_uid": study_uid,
            "study_selection_uid": study_selection_uid,
        }

        result_array, _ = db.cypher_query(query, query_parameters)
        return result_array[0][0]

    def close(self) -> None:
        pass
