import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api.config import STUDY_ENDPOINT_TP_NAME
from clinical_mdr_api.domain.study_selection.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.endpoint import EndpointRoot
from clinical_mdr_api.domain_repositories.models.generic import Conjunction
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyEndpoint
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.domain_repositories.models.timeframe import TimeframeRoot


@dataclass
class SelectionHistoryObject:
    """Class for selection history items"""

    study_selection_uid: str
    endpoint_uid: Optional[str]
    endpoint_version: Optional[str]
    endpoint_level: Optional[str]
    endpoint_sub_level: Optional[str]
    study_objective_uid: Optional[str]
    timeframe_uid: Optional[str]
    timeframe_version: Optional[str]
    endpoint_units: Sequence[str]
    unit_separator: Optional[str]
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]
    change_type: str
    end_date: Optional[datetime.datetime]
    order: int
    status: Optional[str]


class StudySelectionEndpointRepository:
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
    ) -> Sequence[StudySelectionEndpointVO]:
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
            MATCH (sv)-[:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint)
            OPTIONAL MATCH (se)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
            CALL {
              WITH ev
              OPTIONAL MATCH (ev) <-[ver]-(er:EndpointRoot) 
              WHERE ver.status = "Final"
              RETURN ver as endpoint_ver, er as er
              ORDER BY ver.startDate DESC
              LIMIT 1
            }
            OPTIONAL MATCH (se)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL {
              WITH tv
              OPTIONAL MATCH (tv) <-[ver]-(tr:TimeframeRoot) 
              WHERE ver.status = "Final"
              RETURN ver as timeframe_ver, tr as tr
              ORDER BY ver.startDate DESC
              LIMIT 1
            }
            WITH DISTINCT sr, se, er, tr, timeframe_ver, endpoint_ver

            OPTIONAL MATCH (se)-[:HAS_ENDPOINT_LEVEL]->(elr:CTTermRoot)<-[has_term:HAS_TERM]-(:CTCodelistRoot)
            -[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)-[:LATEST_FINAL]->(:CTCodelistNameValue {name: "Endpoint Level"})
            OPTIONAL MATCH (se)-[:HAS_ENDPOINT_SUB_LEVEL]->(endpoint_sub_level_root:CTTermRoot)
    
            OPTIONAL MATCH (se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)

            WITH sr, se, er, tr, elr, so, timeframe_ver, endpoint_ver, has_term, endpoint_sub_level_root
            CALL {
                WITH se
                OPTIONAL MATCH (se)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)
                WITH rel, un, se ORDER BY rel.index
                WITH collect(un.uid) as units, se
                OPTIONAL MATCH (se)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                WITH  units, co
                RETURN {units :units, separator : co.string} as values 
            }

            MATCH (se)<-[:AFTER]-(sa:StudyAction)

            RETURN
                sr.uid AS study_uid,
                se.uid AS study_endpoint_uid,
                se.order AS order,
                se.accepted_version AS accepted_version,
                er.uid AS endpoint_uid,
                has_term.order AS endpoint_order,
                tr.uid AS timeframe_uid,
                endpoint_ver.version AS endpoint_version,
                timeframe_ver.version AS timeframe_version,
                elr.uid AS endpoint_level_uid,
                endpoint_sub_level_root.uid AS endpoint_sub_level_uid,
                so.uid AS study_objective_uid,
                se.text AS text,
                sa.date AS start_date,
                sa.user_initials AS user_initials,
                values
                ORDER BY order
            """

        all_endpoint_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_endpoint_selections):
            if selection["values"] is not None:
                if "units" in selection["values"]:
                    units = selection["values"]["units"]
                else:
                    units = None
                if "separator" in selection["values"]:
                    separator = selection["values"]["separator"]
                else:
                    separator = None
            else:
                units = None
                separator = None
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionEndpointVO.from_input_values(
                study_uid=selection["study_uid"],
                endpoint_uid=selection["endpoint_uid"],
                endpoint_version=selection["endpoint_version"],
                endpoint_level_uid=selection["endpoint_level_uid"],
                endpoint_sub_level_uid=selection["endpoint_sub_level_uid"],
                endpoint_level_order=selection["endpoint_order"],
                endpoint_units=units,
                timeframe_uid=selection["timeframe_uid"],
                timeframe_version=selection["timeframe_version"],
                unit_separator=separator,
                study_objective_uid=selection["study_objective_uid"],
                study_selection_uid=selection["study_endpoint_uid"],
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
    ) -> Optional[Sequence[StudySelectionEndpointsAR]]:
        """
        Finds all the selected study endpoints for all studies, and create the aggregate
        :return: List of StudySelectionEndpointsAR, potentially empty
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
                StudySelectionEndpointsAR.from_repository_values(
                    study_uid=study_uid, study_endpoints_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self, study_uid: str, for_update: bool = False
    ) -> Optional[StudySelectionEndpointsAR]:
        """
        Finds all the selected study endpoints for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(study_uid)
        selection_aggregate = StudySelectionEndpointsAR.from_repository_values(
            study_uid=study_uid, study_endpoints_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionEndpointsAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_endpoints_selection:
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

    def save(self, study_selection: StudySelectionEndpointsAR, author: str) -> None:
        """
        Persist the set of selected study endpoints from the aggregate to the database
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
        if len(closure_data) > len(study_selection.study_endpoints_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_endpoints_selection, start=1
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
        for order, selection in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_endpoint.get(
                uid=selection.study_selection_uid
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            audit_node = self._set_before_audit_info(
                audit_node=audit_node,
                study_selection_node=last_study_selection_node,
                study_root_node=study_root_node,
                author=author,
            )
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node, order, selection, audit_node, True
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

            # If some objectives already used this study endpoint
            # Update the parameter relationship
            self._maintain_parameters(selection.study_selection_uid)

    def _maintain_parameters(self, study_endpoint_uid: str):
        query = """
            MATCH (old:StudyEndpoint {uid: $uid})<-[rel:OV_USES_VALUE]-()
            WHERE NOT (old)<--(:StudyValue)
            MATCH (new:StudyEndpoint {uid: $uid})<--(:StudyValue)
            CALL apoc.refactor.to(rel, new)
            YIELD input, output
            RETURN input, output
        """

        db.cypher_query(query, {"uid": study_endpoint_uid})

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionEndpointVO
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
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint { uid: $selection_uid})
            REMOVE se:TemplateParameterValueRoot
            DELETE rel
            WITH se
            MATCH (se)<-[tp_rel:HAS_VALUE]-(:TemplateParameter)
            DELETE tp_rel
            """,
            {
                "study_uid": study_uid,
                "selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_selection_node: StudyEndpoint,
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
        selection: StudySelectionEndpointVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        # Create new endpoint selection
        study_endpoint_selection_node = StudyEndpoint(order=order).save()
        study_endpoint_selection_node.uid = selection.study_selection_uid
        study_endpoint_selection_node.accepted_version = selection.accepted_version
        study_endpoint_selection_node.save()

        # Connect new node with StudyEndpoint template parameter
        _ = TemplateParameter.nodes.get(name=STUDY_ENDPOINT_TP_NAME)
        db.cypher_query(
            """
            MATCH (se:StudyEndpoint) WHERE id(se)=$id SET se:TemplateParameterValueRoot
            WITH se
            MATCH (tp:TemplateParameter {name: $tp_name})
            MERGE (tp)-[:HAS_VALUE]->(se)
        """,
            {"id": study_endpoint_selection_node.id, "tp_name": STUDY_ENDPOINT_TP_NAME},
        )

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_endpoint.connect(
                study_endpoint_selection_node
            )
        # Connect new node with audit trail
        study_endpoint_selection_node.has_after.connect(audit_node)

        # check if endpoint is set
        if selection.endpoint_uid:
            # find the endpoint value
            endpoint_root_node = EndpointRoot.nodes.get(uid=selection.endpoint_uid)
            latest_endpoint_value_node = endpoint_root_node.get_value_for_version(
                version=selection.endpoint_version
            )
            # Connect new node with endpoint value
            study_endpoint_selection_node.has_selected_endpoint.connect(
                latest_endpoint_value_node
            )
        # check if timeframe is set
        if selection.timeframe_uid:
            # find the timeframe value
            timeframe_root_node = TimeframeRoot.nodes.get(uid=selection.timeframe_uid)
            latest_timeframe_value_node = timeframe_root_node.get_value_for_version(
                version=selection.timeframe_version
            )
            # Connect new node with timeframe value
            study_endpoint_selection_node.has_selected_timeframe.connect(
                latest_timeframe_value_node
            )
        # check if study objective is set
        if selection.study_objective_uid:
            # find the objective
            study_objective = latest_study_value_node.has_study_objective.get(
                uid=selection.study_objective_uid
            )
            # connect to node
            study_endpoint_selection_node.study_endpoint_has_study_objective.connect(
                study_objective
            )
        # Set endpoint level if exists
        if selection.endpoint_level_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.endpoint_level_uid)
            study_endpoint_selection_node.has_endpoint_level.connect(ct_term_root)
        # Set endpoint sub level if exists
        if selection.endpoint_sub_level_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.endpoint_sub_level_uid)
            study_endpoint_selection_node.has_endpoint_sub_level.connect(ct_term_root)
        # for all units which was set
        for index, unit in enumerate(selection.endpoint_units, start=1):
            # get unit definition node
            endpoint_unit_node = UnitDefinitionRoot.nodes.get_or_none(uid=unit)

            # connect to the unit node
            rel = study_endpoint_selection_node.has_unit.connect(endpoint_unit_node)
            rel.index = index
            rel.save()
        # check if any separator is selected
        if selection.unit_separator:
            # create new conjunction if it does not all ready exists
            conjunction_node = Conjunction.nodes.first_or_none(
                string=selection.unit_separator
            )
            if conjunction_node is None:
                conjunction_node = Conjunction(string=selection.unit_separator).save()
            # connect to conjunction which is used as a separator for the units
            rel = study_endpoint_selection_node.has_conjunction.connect(
                conjunction_node
            )
            # We add a meaningless position value, as there can always only be 1. However we do this to follow the
            #  data model
            rel.position = 1
            rel.save()

    def is_used_as_parameter(self, study_selection_uid: str) -> bool:
        result = db.cypher_query(
            """
                MATCH (:StudyValue)--(se:StudyEndpoint {uid:$uid})<-[OV_USES_VALUE]-(v:ObjectiveValue)--(:StudyObjective)--(:StudyValue)
                RETURN count(v) > 0
            """,
            {"uid": study_selection_uid},
        )

        return result[0][0][0]

    def generate_uid(self) -> str:
        return StudyEndpoint.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study endpoints either for a specific selection or for all study endpoints for the study
        """
        if study_selection_uid:

            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(se:StudyEndpoint { uid: $study_selection_uid})
            WITH se
            MATCH (se)-[:AFTER|BEFORE*0..]-(all_se:StudyEndpoint)
            WITH distinct all_se
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_se:StudyEndpoint)
            WITH DISTINCT all_se
            """
        specific_objective_selections_audit_trail = db.cypher_query(
            cypher
            + """
            MATCH (all_se)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)

            CALL {
              WITH ev
              OPTIONAL MATCH (ev) <-[ver]-(er:EndpointRoot) 
              WHERE ver.status = "Final"
              RETURN ver as endpoint_ver, er as er
              ORDER BY ver.startDate DESC
              LIMIT 1
            }
            OPTIONAL MATCH (all_se)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL {
              WITH tv
              OPTIONAL MATCH (tv) <-[ver]-(tr:TimeframeRoot) 
              WHERE ver.status = "Final"
              RETURN ver as timeframe_ver, tr as tr
              ORDER BY ver.startDate DESC
              LIMIT 1
            }
            WITH DISTINCT all_se, er, tr, timeframe_ver, endpoint_ver

            OPTIONAL MATCH (all_se)-[:HAS_ENDPOINT_LEVEL]->(elr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(:CTTermNameValue)
            OPTIONAL MATCH (all_se)-[:HAS_ENDPOINT_SUB_LEVEL]->(endpoint_sub_level:CTTermRoot)
            OPTIONAL MATCH (all_se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)

            WITH all_se, er, tr, elr, so, timeframe_ver, endpoint_ver, endpoint_sub_level
            CALL {
                WITH all_se
                OPTIONAL MATCH (all_se)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)
                WITH rel, un, all_se ORDER BY rel.index
                WITH collect(un.uid) as units, all_se
                OPTIONAL MATCH (all_se)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                WITH  units, co
                RETURN {units :units, separator : co.string} as values 
            }

            MATCH (all_se)<-[:AFTER]-(sa:StudyAction)
            OPTIONAL MATCH (all_se)<-[:BEFORE]-(bsa:StudyAction)

            WITH all_se, er, elr, sa, bsa , endpoint_ver, timeframe_ver, tr, so, values, endpoint_sub_level
            ORDER BY all_se.uid, sa.date DESC
            RETURN
                all_se.uid AS study_endpoint_uid,
                all_se.order AS order,
                er.uid AS endpoint_uid,
                tr.uid AS timeframe_uid,
                endpoint_ver.version AS endpoint_version,
                timeframe_ver.version AS timeframe_version,
                elr.uid AS endpoint_level,
                endpoint_sub_level.uid AS endpoint_sub_level,
                so.uid AS study_objective_uid,
                all_se.text AS text,
                values,
                sa.date AS start_date,
                sa.status AS status,
                sa.user_initials AS user_initials,
                labels(sa) AS change_type,
                bsa.date AS end_date""",
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
            if res["values"] is not None:
                if "units" in res["values"]:
                    units = res["values"]["units"]
                else:
                    units = None
                if "separator" in res["values"]:
                    separator = res["values"]["separator"]
                else:
                    separator = None
            else:
                units = None
                separator = None
            result.append(
                SelectionHistoryObject(
                    study_selection_uid=res["study_endpoint_uid"],
                    endpoint_uid=res["endpoint_uid"],
                    endpoint_version=res["endpoint_version"],
                    endpoint_level=res["endpoint_level"],
                    endpoint_sub_level=res["endpoint_sub_level"],
                    study_objective_uid=res["study_objective_uid"],
                    timeframe_uid=res["timeframe_uid"],
                    timeframe_version=res["timeframe_version"],
                    endpoint_units=units,
                    unit_separator=separator,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    end_date=end_date,
                    order=res["order"],
                    status=res["status"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str = None
    ) -> List[SelectionHistoryObject]:
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
