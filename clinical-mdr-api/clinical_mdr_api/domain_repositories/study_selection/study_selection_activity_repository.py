import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api.domain.study_selection.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.activities import ActivityRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyActivity


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    activity_uid: str
    flowchart_group_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    show_activity_group_in_protocol_flowchart: Optional[bool]
    show_activity_subgroup_in_protocol_flowchart: Optional[bool]
    show_activity_in_protocol_flowchart: Optional[bool]
    note: Optional[str]
    activity_order: Optional[int]
    end_date: Optional[datetime.datetime]
    activity_version: Optional[str]


class StudySelectionActivityRepository:
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
        activity_names: Optional[Sequence[str]] = None,
        activity_sub_group_names: Optional[Sequence[str]] = None,
        activity_group_names: Optional[Sequence[str]] = None,
    ) -> Sequence[StudySelectionActivityVO]:
        query = ""
        query_parameters = {}
        # First, we want to match the StudyRoot and its latest version
        if study_uid:
            query = "MATCH (sr:StudyRoot {uid: $uid})-[l:LATEST]->(sv:StudyValue)"
            query_parameters["uid"] = study_uid
        else:
            query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"
        # Add project related filters if applicable
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

        # Then, match the StudyActivity and Activity
        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[ver:LATEST_FINAL]-(ar:ActivityRoot)
        """

        # Filter on Activity, ActivityGroup or ActivityGroupNames if provided as a specific filter
        # This improves performance vs full service level filter
        if (
            activity_names is not None
            or activity_group_names is not None
            or activity_sub_group_names is not None
        ):
            query += " WHERE "
            filter_list = []
            if activity_names is not None:
                filter_list.append("av.name IN $activity_names")
                query_parameters["activity_names"] = activity_names
            if activity_sub_group_names is not None:
                filter_list.append(
                    "size([(av)-[:IN_SUB_GROUP]->(v:ActivitySubGroupValue) WHERE v.name IN $activity_sub_group_names | v.name]) > 0"
                )
                query_parameters["activity_sub_group_names"] = activity_sub_group_names
            if activity_group_names is not None:
                filter_list.append(
                    """size([(concept_value)-[:IN_SUB_GROUP]->(:ActivitySubGroupValue)
                    -[:IN_GROUP]->(v:ActivityGroupValue) WHERE v.name IN $activity_group_names | v.name]) > 0"""
                )
                query_parameters["activity_group_names"] = activity_group_names

            query += " AND ".join(filter_list)

        # Finally, match the FlowchartGroup and StudyAction
        query += """
            WITH DISTINCT sr, sa, ar, ver
            MATCH (sa)-[:HAS_FLOWCHART_GROUP]->(elr:CTTermRoot)<-[:HAS_TERM]-(:CTCodelistRoot)
            -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(:CTCodelistNameValue {name: "Flowchart Group"})
            WITH DISTINCT sr, sa, ar, ver, elr
            ORDER BY sa.order ASC
            MATCH (sa)<-[:AFTER]-(sac:StudyAction)
            RETURN
                sr.uid AS study_uid,
                sa.order AS activity_order,
                sa.uid AS study_selection_uid,
                sa.show_activity_group_in_protocol_flowchart AS show_activity_group_in_protocol_flowchart,
                sa.show_activity_subgroup_in_protocol_flowchart AS show_activity_subgroup_in_protocol_flowchart,
                sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                sa.note AS note,
                elr.uid AS flowchart_group_uid,
                sa.accepted_version AS accepted_version,
                ar.uid AS activity_uid,
                sac.date AS start_date,
                sac.user_initials AS user_initials,
                ver.version AS activity_version
        """

        all_activity_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in helpers.db_result_to_list(all_activity_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionActivityVO.from_input_values(
                study_selection_uid=selection["study_selection_uid"],
                study_uid=selection["study_uid"],
                activity_uid=selection["activity_uid"],
                activity_version=selection["activity_version"],
                flowchart_group_uid=selection["flowchart_group_uid"],
                activity_order=selection["activity_order"],
                show_activity_group_in_protocol_flowchart=selection[
                    "show_activity_group_in_protocol_flowchart"
                ],
                show_activity_subgroup_in_protocol_flowchart=selection[
                    "show_activity_subgroup_in_protocol_flowchart"
                ],
                show_activity_in_protocol_flowchart=selection[
                    "show_activity_in_protocol_flowchart"
                ],
                note=selection["note"],
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
        activity_names: Optional[Sequence[str]] = None,
        activity_sub_group_names: Optional[Sequence[str]] = None,
        activity_group_names: Optional[Sequence[str]] = None,
    ) -> Optional[Sequence[StudySelectionActivityAR]]:
        """
        Finds all the selected study activities for all studies, and create the aggregate
        :return: List of StudySelectionActivityAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            activity_names=activity_names,
            activity_sub_group_names=activity_sub_group_names,
            activity_group_names=activity_group_names,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of AR from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionActivityAR.from_repository_values(
                    study_uid=study_uid, study_objects_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self, study_uid: str, for_update: bool = False
    ) -> Optional[StudySelectionActivityAR]:
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(study_uid)
        selection_aggregate = StudySelectionActivityAR.from_repository_values(
            study_uid=study_uid, study_objects_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionActivityAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_objects_selection:
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

    def save(self, study_selection: StudySelectionActivityAR, author: str) -> None:
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

        # process new/changed/deleted elements for each activity
        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete has been called
        if len(closure_data) > len(study_selection.study_objects_selection):
            # remove the last item from old list, as there will no longer be any study activity with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_objects_selection, start=1
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

        # loop through and remove selections
        for order, study_activity in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_activity.get(
                uid=study_activity.study_selection_uid
            )
            self._remove_old_selection_if_exists(
                study_selection.study_uid, study_activity
            )
            audit_node = self._get_audit_node(
                study_selection, study_activity.study_selection_uid
            )
            audit_node = self._set_before_audit_info(
                last_study_selection_node, audit_node, study_root_node, author
            )
            audit_trail_nodes[study_activity.study_selection_uid] = audit_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node, order, study_activity, audit_node, True
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
            self._add_new_selection(
                latest_study_value_node, order, selection, audit_node, False
            )

    def _remove_old_selection_if_exists(
        self, study_uid: str, study_selection: StudySelectionActivityVO
    ) -> None:
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_ACTIVITY]->(sa:StudyActivity { uid: $study_selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "study_selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        study_activity_selection_node: StudyActivity,
        audit_node: StudyAction,
        study_root_node: StudyRoot,
        author: str,
    ) -> StudyAction:
        audit_node.user_initials = author
        audit_node.date = datetime.datetime.now()
        audit_node.save()

        study_activity_selection_node.has_before.connect(audit_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        # find the activity value
        activity_root_node: ActivityRoot = ActivityRoot.nodes.get(
            uid=selection.activity_uid
        )
        latest_activity_value_node = activity_root_node.get_value_for_version(
            selection.activity_version
        )
        # Create new activity selection
        study_activity_selection_node = StudyActivity(
            order=order,
            show_activity_group_in_protocol_flowchart=selection.show_activity_group_in_protocol_flowchart,
            show_activity_subgroup_in_protocol_flowchart=selection.show_activity_subgroup_in_protocol_flowchart,
            show_activity_in_protocol_flowchart=selection.show_activity_in_protocol_flowchart,
            note=selection.note,
        )
        study_activity_selection_node.uid = selection.study_selection_uid
        study_activity_selection_node.accepted_version = selection.accepted_version
        study_activity_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity.connect(
                study_activity_selection_node
            )
        # Connect new node with audit trail
        study_activity_selection_node.has_after.connect(audit_node)
        # Connect new node with Activity value
        study_activity_selection_node.has_selected_activity.connect(
            latest_activity_value_node
        )
        # Set flowchart group
        ct_term_root = CTTermRoot.nodes.get(uid=selection.flowchart_group_uid)
        study_activity_selection_node.has_flowchart_group.connect(ct_term_root)

    def study_activity_exists(self, study_activity_uid: str) -> bool:
        study_activity_node = StudyActivity.nodes.get_or_none(uid=study_activity_uid)
        return study_activity_node is not None

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study activity either for a specific selection or for all study activity for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivity { uid: $study_selection_uid})
            WITH sa
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivity)
            WITH distinct(all_sa)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            WITH DISTINCT all_sa
            """
        specific_activity_selections_audit_trail = db.cypher_query(
            cypher
            + """
            MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)

            CALL {
              WITH av
              MATCH (av) <-[ver]-(ar:ActivityRoot)
              WHERE ver.status = "Final"
              RETURN ver as ver, ar as ar
              ORDER BY ver.startDate DESC
              LIMIT 1
            }

            WITH DISTINCT all_sa, ar, ver
            OPTIONAL MATCH (all_sa)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)
            WITH DISTINCT all_sa, ar, ver, fgr
            ORDER BY all_sa.order ASC
            MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sa, ar, asa, bsa, ver, fgr
            ORDER BY all_sa.uid, asa.date DESC
            RETURN
                all_sa.order AS activity_order,
                all_sa.uid AS study_selection_uid,
                all_sa.show_activity_group_in_protocol_flowchart AS show_activity_group_in_protocol_flowchart,
                all_sa.show_activity_subgroup_in_protocol_flowchart AS show_activity_subgroup_in_protocol_flowchart,
                all_sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                all_sa.note AS note,
                ar.uid AS activity_uid,
                fgr.uid AS flowchart_group_uid,
                asa.date AS start_date,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date,
                ver.version AS activity_version
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_activity_selections_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistory(
                    study_selection_uid=res["study_selection_uid"],
                    activity_uid=res["activity_uid"],
                    activity_order=res["activity_order"],
                    activity_version=res["activity_version"],
                    flowchart_group_uid=res["flowchart_group_uid"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    show_activity_group_in_protocol_flowchart=res[
                        "show_activity_group_in_protocol_flowchart"
                    ],
                    show_activity_subgroup_in_protocol_flowchart=res[
                        "show_activity_subgroup_in_protocol_flowchart"
                    ],
                    show_activity_in_protocol_flowchart=res[
                        "show_activity_in_protocol_flowchart"
                    ],
                    note=res["note"],
                    end_date=end_date,
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str = None
    ) -> List[Optional[dict]]:
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        pass
