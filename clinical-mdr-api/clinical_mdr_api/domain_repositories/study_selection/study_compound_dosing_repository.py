import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.study_selection.study_compound_dosing import (
    StudyCompoundDosingVO,
    StudySelectionCompoundDosingsAR,
)
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueWithUnitRoot,
)
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
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyCompoundDosing,
)


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    order: int
    study_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime]

    study_compound_uid: str
    study_element_uid: str
    compound_uid: str
    compound_alias_uid: str
    dose_value_uid: Optional[str]
    dose_frequency_uid: Optional[str]


class StudyCompoundDosingRepository:
    def generate_uid(self) -> str:
        return StudyCompoundDosing.get_next_free_uid_and_increment_counter()

    def _from_repository_values(
        self, study_uid: str, compound_dosing: StudyCompoundDosing
    ) -> StudyCompoundDosingVO:
        study_action = compound_dosing.has_after.all()[0]
        study_compound = compound_dosing.study_compound.single()
        compound_alias = study_compound.has_selected_compound.single()

        study_element = compound_dosing.study_element.single()
        dose_value = compound_dosing.has_dose_value.single()
        dose_frequency = compound_dosing.has_dose_frequency.single()
        return StudyCompoundDosingVO(
            study_selection_uid=compound_dosing.uid,
            study_uid=study_uid,
            study_compound_uid=study_compound.uid,
            study_element_uid=study_element.uid,
            compound_uid=compound_alias.is_compound.single().uid,
            compound_alias_uid=compound_alias.compound_alias_root.single().uid,
            dose_frequency_uid=dose_frequency.uid if dose_frequency else None,
            dose_value_uid=dose_value.uid if dose_value else None,
            start_date=study_action.date,
            user_initials=study_action.user_initials,
        )

    def _remove_old_selection_if_exists(
        self, study_uid: str, compound_dosing: StudyCompoundDosingVO
    ):
        return db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
            -[rel:HAS_STUDY_COMPOUND_DOSING]->(:StudyCompoundDosing {uid: $compound_dosing_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "compound_dosing_uid": compound_dosing.study_selection_uid,
            },
        )

    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_selection_node: StudyCompoundDosing,
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
        selection: StudyCompoundDosingVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        study_compound_node = latest_study_value_node.has_study_compound.get_or_none(
            uid=selection.study_compound_uid
        )
        if study_compound_node is None:
            raise exceptions.NotFoundException(
                f"The study compound with uid {selection.study_compound_uid} was not found"
            )
        study_element_node = latest_study_value_node.has_study_element.get_or_none(
            uid=selection.study_element_uid
        )
        if study_element_node is None:
            raise exceptions.NotFoundException(
                f"The study element with uid {selection.study_element_uid} was not found"
            )

        # Create new compound selection
        selection_node = StudyCompoundDosing(order=order)
        selection_node.uid = selection.study_selection_uid
        selection_node.save()
        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_compound_dosing.connect(selection_node)
        # Connect new node with audit trail
        selection_node.has_after.connect(audit_node)

        # Create relations
        selection_node.study_compound.connect(study_compound_node)
        selection_node.study_element.connect(study_element_node)

        # Create optional relations
        if selection.dose_value_uid:
            node = NumericValueWithUnitRoot.nodes.get_or_none(
                uid=selection.dose_value_uid
            )
            if node is None:
                raise exceptions.NotFoundException(
                    f"The selected CT Term for 'dose' with UID '{selection.dose_value_uid}' cannot be found."
                )
            selection_node.has_dose_value.connect(node)
        if selection.dose_frequency_uid:
            node = CTTermRoot.nodes.get_or_none(uid=selection.dose_frequency_uid)
            if node is None:
                raise exceptions.NotFoundException(
                    f"The selected CT Term for 'dose form' with UID '{selection.dose_frequency_uid}' cannot be found."
                )
            selection_node.has_dose_frequency.connect(node)

    def _get_audit_node(
        self, study_selection: StudySelectionCompoundDosingsAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_compound_dosings_selection:
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

    def save(
        self, study_selection: StudySelectionCompoundDosingsAR, author: str
    ) -> None:
        """
        Persist the set of selected study compounds from the aggregate to the database
        :param study_selection:
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
        if len(closure_data) > len(study_selection.study_compound_dosings_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_compound_dosings_selection, start=1
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
            last_study_selection_node = (
                latest_study_value_node.has_study_compound_dosing.get(
                    uid=selection.study_selection_uid
                )
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            audit_node = self._set_before_audit_info(
                audit_node,
                last_study_selection_node,
                study_root_node,
                author,
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

    def get_study_selection(
        self, study_value_node: StudyValue, selection_uid: str
    ) -> StudyCompoundDosing:
        compound_dosing = study_value_node.has_study_compound_dosing.get_or_none(
            uid=selection_uid
        )
        if compound_dosing is None:
            raise exceptions.NotFoundException(
                f"The study compound dosing with uid {selection_uid} was not found"
            )
        return compound_dosing

    def _get_selection_with_history(self, study_uid: str, selection_uid: str = None):
        """
        returns the audit trail for study compound dosing either for a
        specific selection or for all study compound dosings of the study.
        """
        if selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(scd:StudyCompoundDosing {uid: $selection_uid})
            WITH scd
            MATCH (scd)-[:AFTER|BEFORE*0..]-(all_scd:StudyCompoundDosing)
            WITH distinct(all_scd)
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_scd:StudyCompoundDosing)
            WITH DISTINCT all_scd
            """
        specific_audit_trail = db.cypher_query(
            cypher
            + """
            MATCH (all_scd)<-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]-(sc:StudyCompound)
            MATCH (all_scd)<-[:STUDY_ELEMENT_HAS_COMPOUND_DOSING]-(se:StudyElement)
            MATCH (all_scd)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_scd)<-[:BEFORE]-(bsa:StudyAction)
            OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)<-[:LATEST_FINAL]-(car:CompoundAliasRoot)
            OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)
            OPTIONAL MATCH (all_scd)-[:HAS_DOSE_VALUE]->(dvr:NumericValueWithUnitRoot)
            OPTIONAL MATCH (all_scd)-[:HAS_DOSE_FREQUENCY]->(df:CTTermRoot)
            WITH all_scd, sc, se, asa, bsa, car, cr, dvr, df
            ORDER BY all_scd.uid, asa.date DESC
            RETURN
                all_scd.uid AS uid,
                all_scd.order AS order,
                se.uid AS study_element_uid,
                sc.uid AS study_compound_uid,
                cr.uid AS compound_uid,
                car.uid AS compound_alias_uid,
                dvr.uid AS dose_value_uid,
                df.uid AS dose_frequency_uid,
                labels(asa) AS change_type,
                asa.date AS start_date,
                bsa.date AS end_date,
                asa.user_initials AS user_initials
            """,
            {"study_uid": study_uid, "selection_uid": selection_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_audit_trail):
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
                    order=res["order"],
                    study_element_uid=res["study_element_uid"],
                    study_compound_uid=res["study_compound_uid"],
                    compound_uid=res["compound_uid"],
                    compound_alias_uid=res["compound_alias_uid"],
                    dose_value_uid=res["dose_value_uid"],
                    dose_frequency_uid=res["dose_frequency_uid"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    end_date=end_date,
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, selection_uid: str = None
    ) -> List[Optional[dict]]:
        kwargs = {}
        if selection_uid:
            kwargs["selection_uid"] = selection_uid
        return self._get_selection_with_history(study_uid=study_uid, **kwargs)

    def _retrieves_all_data(
        self, study_uid: Optional[str] = None
    ) -> Sequence[StudyCompoundDosingVO]:
        query = ""
        query_parameters = {}
        if study_uid:
            query = "MATCH (sr:StudyRoot {uid: $uid})-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_COMPOUND_DOSING]->(scd:StudyCompoundDosing)"
            query_parameters["uid"] = study_uid
        else:
            query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_COMPOUND_DOSING]->(scd:StudyCompoundDosing)"

        query += """
        OPTIONAL MATCH (scd)<-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]-(sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot)
        OPTIONAL MATCH (scd)<-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]-(sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)
        OPTIONAL MATCH (scd)<-[:STUDY_ELEMENT_HAS_COMPOUND_DOSING]-(se)
        WITH DISTINCT sr, sv, scd, sc, se, car, cr
        """

        query += """
            OPTIONAL MATCH (scd)-[:HAS_DOSE_VALUE]->(dvr:NumericValueWithUnitRoot)
            OPTIONAL MATCH (scd)-[:HAS_DOSE_FREQUENCY]->(df:CTTermRoot)

            MATCH (sc)<-[:AFTER]-(sa:StudyAction)

            WITH sr, scd, sc, se, car, cr, dvr, df, sa
            RETURN
                sr.uid AS study_uid,
                scd.uid AS study_compound_dosing_uid,
                sc.uid AS study_compound_uid,
                se.uid AS study_element_uid,
                scd.order AS order,
                cr.uid AS compound_uid,
                car.uid AS compound_alias_uid,
                dvr.uid AS dose_value_uid,
                df.uid AS dose_frequency_uid,
                sa.date AS start_date,
                sa.user_initials AS user_initials
                ORDER BY order
            """

        all_selections = db.cypher_query(query, query_parameters)
        result = []
        for selection in helpers.db_result_to_list(all_selections):
            selection_vo = StudyCompoundDosingVO.from_input_values(
                study_uid=selection["study_uid"],
                study_selection_uid=selection["study_compound_dosing_uid"],
                study_compound_uid=selection["study_compound_uid"],
                compound_uid=selection["compound_uid"],
                compound_alias_uid=selection["compound_alias_uid"],
                study_element_uid=selection["study_element_uid"],
                dose_value_uid=selection.get("dose_value_uid"),
                dose_frequency_uid=selection.get("dose_frequency_uid"),
                start_date=convert_to_datetime(value=selection["start_date"]),
                user_initials=selection["user_initials"],
            )
            result.append(selection_vo)
        return tuple(result)

    def find_by_study(
        self, study_uid: str, for_update: bool = False, **filters
    ) -> Optional[StudySelectionCompoundDosingsAR]:
        """
        Finds all the selected study compounds for a given study
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            helpers.acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(study_uid, **filters)
        selection_aggregate = StudySelectionCompoundDosingsAR.from_repository_values(
            study_uid=study_uid, selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_all(self) -> Sequence[StudySelectionCompoundDosingsAR]:
        """Find all the selected study compound dosings for all studies."""
        all_selections = self._retrieves_all_data()
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
                StudySelectionCompoundDosingsAR.from_repository_values(
                    study_uid=study_uid, selection=selections
                )
            )
        return selection_aggregates

    def get_selection_uid_by_compound_dose_and_frequency(
        self, study_compound_dosing: StudyCompoundDosingVO
    ) -> Optional[str]:
        query = """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_COMPOUND_DOSING]->
                    (scd:StudyCompoundDosing)-[HAS_DOSE_FREQUENCY]->(dfr:CTTermRoot {uid: $dose_frequency_uid})
            WITH *
            MATCH (scd)-[:HAS_DOSE_VALUE]->(dvr:NumericValueWithUnitRoot {uid: $dose_value_uid})
            WITH *
            MATCH (scd)<-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]-(sc:StudyCompound {uid: $study_compound_uid})               
            RETURN scd
            """
        result, _ = db.cypher_query(
            query,
            {
                "study_uid": study_compound_dosing.study_uid,
                "study_compound_uid": study_compound_dosing.study_compound_uid,
                "dose_value_uid": study_compound_dosing.dose_value_uid,
                "dose_frequency_uid": study_compound_dosing.dose_frequency_uid,
            },
        )
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0].get("uid")
        return None
