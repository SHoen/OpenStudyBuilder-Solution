import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from neomodel import db

from clinical_mdr_api import config as settings
from clinical_mdr_api.domain.study_selection.study_selection_element import (
    StudySelectionElementAR,
    StudySelectionElementVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
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
from clinical_mdr_api.domain_repositories.models.study_selections import StudyElement


@dataclass
class SelectionHistoryElement:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: Optional[str]
    element_name: Optional[str]
    element_short_name: Optional[str]
    element_code: Optional[str]
    element_description: Optional[str]
    element_planned_duration: Optional[str]
    element_start_rule: Optional[str]
    element_end_rule: Optional[str]
    element_colour: Optional[str]
    element_subtype: Optional[str]
    # Study selection Versioning
    start_date: datetime.datetime
    user_initials: Optional[str]
    change_type: str
    end_date: Optional[datetime.datetime]
    order: int
    status: Optional[str]
    accepted_version: Optional[bool]


class StudySelectionElementRepository:
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

    def get_allowed_configs(self):
        cypher_query = """
        MATCH (:CTCodelistNameValue {name: $code_list_name})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]
        -(:CTCodelistRoot)-[:HAS_TERM]->(term_subtype_root:CTTermRoot)-[:HAS_NAME_ROOT]->
        (term_subtype_name_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_subtype_name_value:CTTermNameValue)
        MATCH (term_subtype_root)-[:HAS_PARENT_TYPE]->(term_type_root:CTTermRoot)-
        [:HAS_NAME_ROOT]->(term_type_name_root)-[:LATEST_FINAL]->(term_type_name_value:CTTermNameValue)
        return term_subtype_root.uid, term_subtype_name_value.name, term_type_root.uid, term_type_name_value.name
        """
        items, _ = db.cypher_query(
            cypher_query, {"code_list_name": settings.STUDY_ELEMENT_SUBTYPE_NAME}
        )
        return items

    def _retrieves_all_data(
        self,
        study_uid: Optional[str] = None,
        project_name: Optional[str] = None,
        project_number: Optional[str] = None,
    ) -> Sequence[StudySelectionElementVO]:
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
            MATCH (sv)-[:HAS_STUDY_ELEMENT]->(sar:StudyElement)
            WITH DISTINCT sr, sar 
            
            OPTIONAL MATCH (sar)-[:HAS_ELEMENT_SUBTYPE]->(elr:CTTermRoot)
            OPTIONAL MATCH (sar)-[:STUDY_ELEMENT_HAS_COMPOUND_DOSING]->(scd)<-[:HAS_STUDY_COMPOUND_DOSING]-(StudyValue)

            MATCH (sar)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT 
                sr.uid AS study_uid,
                sar.uid AS study_selection_uid,
                sar.name AS element_name,
                sar.short_name AS element_short_name,
                sar.element_code AS element_code,
                sar.description AS element_description,
                sar.planned_duration AS element_planned_duration,
                sar.start_rule AS element_start_rule,
                sar.end_rule AS element_end_rule,
                sar.element_colour AS element_colour,
                sar.order AS order,
                sar.accepted_version AS accepted_version,
                elr.uid AS element_subtype_uid,
                sar.text AS text,
                count(scd) AS study_compound_dosing_count,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_element_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in helpers.db_result_to_list(all_element_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionElementVO.from_input_values(
                user_initials=selection["user_initials"],
                study_uid=selection["study_uid"],
                name=selection["element_name"],
                short_name=selection["element_short_name"],
                code=selection["element_code"],
                description=selection["element_description"],
                planned_duration=selection["element_planned_duration"],
                start_rule=selection["element_start_rule"],
                end_rule=selection["element_end_rule"],
                element_colour=selection["element_colour"],
                study_selection_uid=selection["study_selection_uid"],
                element_subtype_uid=selection["element_subtype_uid"],
                study_compound_dosing_count=selection["study_compound_dosing_count"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                accepted_version=selection["accepted_version"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_by_study(
        self, study_uid: str, for_update: bool = False
    ) -> Optional[StudySelectionElementAR]:
        """
        Finds all the selected study endpoints for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        # take the selections from the db
        all_selections = self._retrieves_all_data(study_uid)
        # map to element object
        selection_aggregate = StudySelectionElementAR.from_repository_values(
            study_uid=study_uid, study_elements_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_uid(
        self, study_uid: str, study_element_uid: str
    ) -> Tuple[StudySelectionElementVO, int]:
        """Find a study element by its UID."""
        query_parameters = {
            "study_uid": study_uid,
            "study_element_uid": study_element_uid,
        }
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_ELEMENT]->(se:StudyElement {uid: $study_element_uid})
        WITH sr, sv, se
        OPTIONAL MATCH (se)-[:HAS_ELEMENT_SUBTYPE]->(elr:CTTermRoot)
        OPTIONAL MATCH (sar)-[:STUDY_ELEMENT_HAS_COMPOUND_DOSING]->(scd)<-[:HAS_STUDY_COMPOUND_DOSING]-(StudyValue)
        MATCH (se)<-[:AFTER]-(sa:StudyAction)
        RETURN DISTINCT
            sr.uid AS study_uid,
            se.uid AS study_selection_uid,
            se.name AS element_name,
            se.short_name AS element_short_name,
            se.element_code AS element_code,
            se.description AS element_description,
            se.planned_duration AS element_planned_duration,
            se.start_rule AS element_start_rule,
            se.end_rule AS element_end_rule,
            se.element_colour AS element_colour,
            se.order AS order,
            se.accepted_version AS accepted_version,
            elr.uid AS element_subtype_uid,
            se.text AS text,
            count(scd) AS study_compound_dosing_count,
            sa.date AS start_date,
            sa.user_initials AS user_initials
            ORDER BY order
        """

        result = db.cypher_query(query, query_parameters)
        result = helpers.db_result_to_list(result)
        assert (
            len(result) == 1
        ), f"Found more than 1 study element with uid {study_element_uid}"
        selection = result[0]
        selection_vo = StudySelectionElementVO.from_input_values(
            study_uid=selection["study_uid"],
            name=selection["element_name"],
            short_name=selection["element_short_name"],
            code=selection["element_code"],
            description=selection["element_description"],
            planned_duration=selection["element_planned_duration"],
            start_rule=selection["element_start_rule"],
            end_rule=selection["element_end_rule"],
            element_colour=selection["element_colour"],
            element_subtype_uid=selection["element_subtype_uid"],
            study_compound_dosing_count=selection["study_compound_dosing_count"],
            study_selection_uid=selection["study_selection_uid"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            user_initials=selection["user_initials"],
        )
        return selection_vo, selection["order"]

    def _get_audit_node(
        self, study_selection: StudySelectionElementAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_elements_selection:
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

    def element_specific_has_connected_cell(
        self, study_uid: str, element_uid: str
    ) -> bool:
        """
        Returns True if StudyElement with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = (
            StudyElement.nodes.fetch_relations("has_design_cell", "has_after")
            .filter(
                study_value__study_root__uid=study_uid,
                uid=element_uid,
                has_design_cell__study_value__study_root__uid=study_uid,
            )
            .to_relation_trees()
        )
        return len(sdc_node) > 0

    def validate_delete_init(
        self, study_uid: str, closure: StudySelectionElementAR
    ) -> None:

        # make validations
        assert closure is not None

        # getting the latest study value node
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

    def save(self, study_selection: StudySelectionElementAR, author: str) -> None:
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
        if len(closure_data) > len(study_selection.study_elements_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_elements_selection, start=1
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
            last_study_selection_node = latest_study_value_node.has_study_element.get(
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
                    latest_study_value_node,
                    order,
                    selection,
                    audit_node,
                    for_deletion=True,
                    before_node=last_study_selection_node,
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
                latest_study_value_node,
                order,
                selection,
                audit_node,
                for_deletion=False,
                before_node=last_study_selection_node,
            )

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionElementVO
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
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_ELEMENT]->(se:StudyElement { uid: $selection_uid})
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
        study_selection_node: StudyElement,
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
        selection: StudySelectionElementVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyElement = None,
    ):
        # Create new element selection
        study_element_selection_node = StudyElement(order=order).save()
        study_element_selection_node.uid = selection.study_selection_uid
        study_element_selection_node.accepted_version = selection.accepted_version
        study_element_selection_node.name = selection.name
        study_element_selection_node.short_name = selection.short_name
        study_element_selection_node.element_code = selection.code
        study_element_selection_node.description = selection.description
        study_element_selection_node.planned_duration = selection.planned_duration
        study_element_selection_node.start_rule = selection.start_rule
        study_element_selection_node.end_rule = selection.end_rule
        study_element_selection_node.element_colour = selection.element_colour
        study_element_selection_node.save()

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_element.connect(
                study_element_selection_node
            )
        # Connect new node with audit trail
        study_element_selection_node.has_after.connect(audit_node)

        if before_node is not None:
            design_cells = before_node.has_design_cell.all()
            for i_design_cell in design_cells:
                # if the i_design_cell is an actual one then carry it to the new node
                if i_design_cell.study_value.get_or_none() is not None:
                    i_design_cell.study_element.reconnect(
                        old_node=i_design_cell.study_element.single(),
                        new_node=study_element_selection_node,
                    )

        # check if element subtype is set
        if selection.element_subtype_uid:
            # find the objective
            study_element_subtype = CTTermRoot.nodes.get(
                uid=selection.element_subtype_uid
            )
            # connect to node
            # pylint: disable=no-member
            study_element_selection_node.element_subtype.connect(study_element_subtype)

    def generate_uid(self) -> str:
        return StudyElement.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study element either for a specific selection or for all study element for the study
        """
        if study_selection_uid:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyElement { uid: $study_selection_uid})
                    WITH sa
                    MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyElement)
                    WITH distinct(all_sa)
                    """
        else:
            cypher = """
                    MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyElement)
                    WITH DISTINCT all_sa
                    """
        specific_element_selections_audit_trail = db.cypher_query(
            cypher
            + """
            WITH DISTINCT all_sa
            OPTIONAL MATCH (all_sa)-[:HAS_ELEMENT_SUBTYPE]->(at:CTTermRoot)
            WITH DISTINCT all_sa, at
            ORDER BY all_sa.order ASC
            MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sa, asa, bsa, at
            ORDER BY all_sa.uid, asa.date DESC
            RETURN
                all_sa.uid AS study_selection_uid,
                all_sa.name AS element_name,
                all_sa.short_name AS element_short_name,
                all_sa.element_code AS element_code,
                all_sa.description AS element_description,
                all_sa.planned_duration AS element_planned_duration,
                all_sa.start_rule AS element_start_rule,
                all_sa.end_rule AS element_end_rule,
                all_sa.element_colour AS element_colour,
                all_sa.order AS order,
                all_sa.accepted_version AS accepted_version,
                //all_sa.number_of_subjects AS number_of_subjects,
                //all_sa.randomization_group AS randomization_group,
                at.uid AS element_subtype_uid,
                all_sa.text AS text,
                asa.date AS start_date,
                asa.user_initials AS user_initials,
                labels(asa) AS change_type,
                bsa.date AS end_date
            """,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_element_selections_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                SelectionHistoryElement(
                    study_selection_uid=res["study_selection_uid"],
                    study_uid=study_uid,
                    element_name=res["element_name"],
                    element_short_name=res["element_short_name"],
                    element_code=res["element_code"],
                    element_description=res["element_description"],
                    element_planned_duration=res["element_planned_duration"],
                    element_start_rule=res["element_start_rule"],
                    element_end_rule=res["element_end_rule"],
                    element_colour=res["element_colour"],
                    element_subtype=res["element_subtype_uid"],
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
    ) -> List[SelectionHistoryElement]:
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
