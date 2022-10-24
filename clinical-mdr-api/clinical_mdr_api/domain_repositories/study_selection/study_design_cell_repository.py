import datetime
from dataclasses import dataclass
from typing import List, Optional, Sequence

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.study_selection.study_design_cell import StudyDesignCellVO
from clinical_mdr_api.domain_repositories._utils import helpers
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyDesignCell


@dataclass
class StudyDesignCellHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str
    study_arm_uid: str
    study_branch_arm_uid: str
    study_epoch_uid: str
    study_element_uid: str
    user_initials: str
    change_type: str
    start_date: datetime.datetime
    end_date: Optional[datetime.datetime]
    transition_rule: str
    order: int


class StudyDesignCellRepository:
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

    def find_by_uid(self, study_uid: str, uid: str) -> StudyDesignCellVO:
        design_cell_node = (
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after",
                "study_epoch",
                "study_element",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(study_value__study_root__uid=study_uid, uid=uid)
            .order_by("order")
            .to_relation_trees()
        )

        if len(design_cell_node) > 1:
            raise ValueError(
                f"Found more than one StudyDesignCell node with uid='{uid}' in the study='{study_uid}'."
            )
        if len(design_cell_node) == 0:
            raise ValueError(
                f"The StudyDesignCell with uid='{uid}' could not be found in the study='{study_uid}'."
            )
        return self._from_repository_values(
            study_uid=study_uid, design_cell=design_cell_node[0]
        )

    def find_all_design_cells_by_study(
        self, study_uid: str
    ) -> Sequence[StudyDesignCellVO]:
        all_design_cells = [
            self._from_repository_values(study_uid=study_uid, design_cell=sas_node)
            for sas_node in StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after",
                "study_epoch",
                "study_element",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(study_value__study_root__uid=study_uid)
            .order_by("order")
            .to_relation_trees()
        ]
        return all_design_cells

    def _from_repository_values(
        self, study_uid: str, design_cell: StudyDesignCell
    ) -> StudyDesignCellVO:
        study_action = design_cell.has_after.all()[0]
        study_arm = design_cell.study_arm.single()
        study_branch_arm = design_cell.study_branch_arm.single()
        study_epoch = design_cell.study_epoch.single()
        study_epoch_name = (
            study_epoch.has_epoch.single()
            .has_name_root.single()
            .has_latest_value.single()
            .name
        )
        study_element = design_cell.study_element.single()
        return StudyDesignCellVO(
            uid=design_cell.uid,
            study_uid=study_uid,
            order=design_cell.order,
            study_arm_uid=study_arm.uid if study_arm is not None else None,
            study_arm_name=study_arm.name if study_arm is not None else None,
            study_branch_arm_uid=study_branch_arm.uid
            if study_branch_arm is not None
            else None,
            study_branch_arm_name=study_branch_arm.name
            if study_branch_arm is not None
            else None,
            study_epoch_uid=study_epoch.uid,
            study_epoch_name=study_epoch_name,
            study_element_uid=study_element.uid,
            study_element_name=study_element.name,
            transition_rule=design_cell.transition_rule,
            start_date=study_action.date,
            user_initials=study_action.user_initials,
        )

    # pylint: disable=unused-argument
    # TODO: Use author in audit trail!
    def save(
        self, design_cell_vo: StudyDesignCellVO, author: str, create: bool = False
    ) -> StudyDesignCellVO:

        # Get nodes and check if they can play together
        study_root_node = StudyRoot.nodes.get_or_none(uid=design_cell_vo.study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {design_cell_vo.study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()

        # check if the studyArm has StudyBranchArms assigned to it
        # get StudyArm only if it's necessary
        if design_cell_vo.study_arm_uid:
            study_arm_node = latest_study_value_node.has_study_arm.get_or_none(
                uid=design_cell_vo.study_arm_uid
            )
            # if any StudyBranchArms connectect to StudyArm has a study_value
            if (
                sum(
                    i_branch_arm.study_value.all() != []
                    for i_branch_arm in study_arm_node.has_branch_arm.all()
                )
                > 0
            ):
                raise exceptions.BusinessLogicException(
                    f"The Study Arm with uid {study_arm_node.uid} cannot be "
                    "assigned to a Study Design Cell because it has Study Branch Arms assigned to it"
                )
        else:
            study_arm_node = None

        # get StudyBranchArm only if it's necessary
        if design_cell_vo.study_branch_arm_uid:
            study_branch_arm_node = (
                latest_study_value_node.has_study_branch_arm.get_or_none(
                    uid=design_cell_vo.study_branch_arm_uid
                )
            )
        else:
            study_branch_arm_node = None

        # at least one of the two has to be defined
        if study_arm_node is None and study_branch_arm_node is None:
            raise exceptions.NotFoundException(
                f"The study arm {design_cell_vo.study_arm_uid} or the Study Branch Arm {design_cell_vo.study_branch_arm_uid} must exist"
            )

        # get StudyEpoch
        study_epoch_node = latest_study_value_node.has_study_epoch.get_or_none(
            uid=design_cell_vo.study_epoch_uid
        )
        if study_epoch_node is None:
            raise exceptions.NotFoundException(
                f"The study epoch with uid {design_cell_vo.study_epoch_uid} was not found"
            )

        # get StudyElement
        if design_cell_vo.study_element_uid is not None:
            study_element_node = latest_study_value_node.has_study_element.get_or_none(
                uid=design_cell_vo.study_element_uid
            )
            if study_element_node is None:
                raise exceptions.NotFoundException(
                    f"The study element with uid {design_cell_vo.study_element_uid} was not found"
                )

        # Create new node
        design_cell = StudyDesignCell(
            uid=design_cell_vo.uid,
            transitionRule=design_cell_vo.transition_rule,
            order=design_cell_vo.order,
        )
        design_cell.save()

        # Create relations
        # ensure switching
        #       study_branch_arm was defined even if the arm was specified will be connected to study branch arm
        if study_branch_arm_node is not None:
            design_cell.study_branch_arm.connect(study_branch_arm_node)
        #       just arm was defined
        else:
            design_cell.study_arm.connect(study_arm_node)
        design_cell.study_epoch.connect(study_epoch_node)
        design_cell.study_element.connect(study_element_node)

        if create:
            self.manage_versioning_create(
                study_root=study_root_node,
                study_design_cell=design_cell_vo,
                new_item=design_cell,
            )
        else:
            # get the previous item
            previous_item = StudyDesignCell.nodes.filter(uid=design_cell_vo.uid).has(
                study_value=True
            )[0]
            self.manage_versioning_update(
                study_root=study_root_node,
                study_design_cell=design_cell_vo,
                previous_item=previous_item,
                new_item=design_cell,
            )
            previous_item.study_value.disconnect(latest_study_value_node)

        design_cell.study_value.connect(latest_study_value_node)
        # return the json response model
        return self._from_repository_values(design_cell_vo.study_uid, design_cell)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_design_cell: StudyDesignCellVO,
        previous_item: StudyDesignCell,
        new_item: StudyDesignCell,
    ):
        action = Edit(
            date=datetime.datetime.now(),
            user_initials=study_design_cell.user_initials,
        )
        action.save()
        previous_item.has_before.connect(action)
        new_item.has_after.connect(action)
        study_root.audit_trail.connect(action)

    def manage_versioning_create(
        self,
        study_root: StudyRoot,
        study_design_cell: StudyDesignCellVO,
        new_item: StudyDesignCell,
    ):
        # create StudyAction node
        action = Create(
            date=datetime.datetime.now(),
            user_initials=study_design_cell.user_initials,
        )
        action.save()
        # connect the new item to the newly StudyAction
        new_item.has_after.connect(action)
        # connect the audit trail to the studyRoot node
        study_root.audit_trail.connect(action)

    def _remove_old_selection_if_exists(self, design_cell: StudyDesignCell):
        return db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_DESIGN_CELL]->(:StudyDesignCell {uid: $design_cell_uid})
            DELETE rel
            """,
            {
                "study_uid": design_cell.study_uid,
                "design_cell_uid": design_cell.uid,
            },
        )

    def patch_study_element(
        self, study_uid: str, design_cell_uid: str, study_element_uid: str
    ):
        # Get Study Root node
        study_root_node = StudyRoot.nodes.get_or_none(uid=study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()
        design_cell = latest_study_value_node.has_study_design_cell.get_or_none(
            uid=design_cell_uid
        )
        if design_cell is None:
            raise exceptions.NotFoundException(
                f"The study design cell with uid {design_cell_uid} was not found"
            )

        # Get study element node
        study_element_node = latest_study_value_node.has_study_element.get_or_none(
            uid=study_element_uid
        )

        # Change the study element the cell is connected to
        design_cell.study_element.reconnect(
            old_node=design_cell.study_element.single(), new_node=study_element_node
        )

    def patch_study_arm(
        self, study_uid: str, design_cell_uid: str, study_arm_uid: str, author: str
    ):

        study_design_cell = self.find_by_uid(study_uid=study_uid, uid=design_cell_uid)
        study_design_cell.study_arm_uid = study_arm_uid
        study_design_cell.study_branch_arm_uid = None

        self.save(study_design_cell, author, create=False)

    def get_design_cells_connected_to_branch_arm(
        self, study_uid: str, study_branch_arm_uid: str
    ):
        sdc_node = (
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after",
                "study_epoch",
                "study_element",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(
                study_value__study_root__uid=study_uid,
                study_branch_arm__uid=study_branch_arm_uid,
                study_branch_arm__study_value__study_root__uid=study_uid,
            )
            .order_by("order")
            .to_relation_trees()
        )
        return sdc_node

    def get_design_cells_connected_to_epoch(self, study_uid: str, study_epoch_uid: str):
        sdc_node = (
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "has_after",
                "study_epoch",
                "study_element",
            )
            .fetch_optional_relations("study_arm", "study_branch_arm")
            .filter(
                study_value__study_root__uid=study_uid,
                study_epoch__uid=study_epoch_uid,
                study_epoch__study_value__study_root__uid=study_uid,
            )
            .order_by("order")
            .to_relation_trees()
        )

        return sdc_node

    def get_design_cells_connected_to_arm(self, study_uid: str, study_arm_uid: str):
        sdc_node = (
            StudyDesignCell.nodes.fetch_relations(
                "study_epoch__has_epoch__has_name_root__has_latest_value",
                "study_arm",
                "has_after",
                "study_epoch",
                "study_element",
            )
            .filter(
                study_value__study_root__uid=study_uid,
                study_arm__uid=study_arm_uid,
                study_arm__study_value__study_root__uid=study_uid,
            )
            .order_by("order")
            .to_relation_trees()
        )

        return sdc_node

    def get_design_cells_connected_to_element(
        self, study_uid: str, study_element_uid: str
    ):
        sdc_node = (
            StudyDesignCell.nodes.fetch_relations(
                "study_element",
                "has_after",
            )
            .filter(
                study_value__study_root__uid=study_uid,
                study_element__uid=study_element_uid,
                study_element__study_value__study_root__uid=study_uid,
            )
            .order_by("order")
            .to_relation_trees()
        )
        return sdc_node

    def patch_study_branch_arm(
        self, study_uid: str, design_cell_uid: str, study_branch_arm_uid: str
    ):
        # Get Study Root node
        study_root_node = StudyRoot.nodes.get_or_none(uid=study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()
        design_cell = latest_study_value_node.has_study_design_cell.get_or_none(
            uid=design_cell_uid
        )
        if design_cell is None:
            raise exceptions.NotFoundException(
                f"The study design cell with uid {design_cell_uid} was not found"
            )

        # Get study branch arm node
        study_branch_arm_node = (
            latest_study_value_node.has_study_branch_arm.get_or_none(
                uid=study_branch_arm_uid
            )
        )
        if study_branch_arm_node is None:
            raise exceptions.NotFoundException(
                f"The study branch arm with uid {study_branch_arm_uid} was not found"
            )

        # Detect to if the StudyDesignCell it's connected to StudyArm or StudyBranchArm so it can be disconnected, then connect it to a StudyArm
        if design_cell.study_branch_arm.single() is not None:
            # Change the study branch arm the cell is connected to
            design_cell.study_branch_arm.reconnect(
                old_node=design_cell.study_branch_arm.single(),
                new_node=study_branch_arm_node,
            )
        elif design_cell.study_arm is not None:
            # previously has a StudyBranchArm connection, we have to delete it, then chage it to a StudyArm
            design_cell.study_arm.disconnect(design_cell.study_arm.single())
            design_cell.study_branch_arm.connect(study_branch_arm_node)

    def delete(self, study_uid: str, design_cell_uid: str, author: str):
        study_root_node = StudyRoot.nodes.get_or_none(uid=study_uid)
        if study_root_node is None:
            raise exceptions.NotFoundException(
                f"The study with uid {study_uid} was not found"
            )
        latest_study_value_node = study_root_node.latest_value.single()
        design_cell = latest_study_value_node.has_study_design_cell.get_or_none(
            uid=design_cell_uid
        )
        if design_cell is None:
            raise exceptions.NotFoundException(
                f"The study design cell with uid {design_cell_uid} was not found"
            )

        # create delete version
        new_design_cell = StudyDesignCell(
            uid=design_cell.uid,
            transition_rule=design_cell.transition_rule,
            order=design_cell.order,
        )
        new_design_cell.save()

        study_arm_node = design_cell.study_arm.single()
        study_branch_arm_node = design_cell.study_branch_arm.single()
        # at least one of the two has to be defined
        if study_arm_node:
            new_design_cell.study_arm.connect(study_arm_node)
        elif study_branch_arm_node:
            new_design_cell.study_branch_arm.connect(study_branch_arm_node)
        else:
            raise exceptions.NotFoundException(
                "Study arm or Study Branch Arm must exist"
            )

        # get StudyEpoch
        study_epoch_node = design_cell.study_epoch.single()
        if study_epoch_node:
            new_design_cell.study_epoch.connect(study_epoch_node)
        else:
            raise exceptions.NotFoundException("Study epoch must exists")

        # gest StudyElement
        study_element_node = design_cell.study_element.single()
        if study_element_node:
            new_design_cell.study_element.connect(study_element_node)
        else:
            raise exceptions.NotFoundException("Study element must exists")

        # Audit trail
        audit_node = Delete(user_initials=author, date=datetime.datetime.now())
        audit_node.save()
        study_root_node.audit_trail.connect(audit_node)
        design_cell.has_before.connect(audit_node)
        new_design_cell.has_after.connect(audit_node)
        # Delete relation
        design_cell.study_value.disconnect(latest_study_value_node)

    def generate_uid(self) -> str:
        return StudyDesignCell.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(self, study_uid: str, design_cell_uid: str = None):
        """
        returns the audit trail for study design cell either for a
        specific selection or for all study design cells for the study.
        """
        # if some DesignCell is specified
        if design_cell_uid:
            # then query just that specific design cell
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sdc:StudyDesignCell {uid: $design_cell_uid})
            WITH sdc
            MATCH (sdc)-[:AFTER|BEFORE*0..]-(all_sdc:StudyDesignCell)
            WITH distinct(all_sdc)
            """
        # if get all study design cells history is called
        else:
            # then query all the design cells
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sdc:StudyDesignCell)
            WITH DISTINCT all_sdc
            """
        specific_design_cells_audit_trail = db.cypher_query(
            cypher
            + """
            OPTIONAL MATCH (all_sdc)<-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL]-(sba:StudyBranchArm)
            OPTIONAL MATCH (all_sdc)<-[:STUDY_ARM_HAS_DESIGN_CELL]-(sa:StudyArm)
            MATCH (all_sdc)<-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(se:StudyEpoch)
            OPTIONAL MATCH (all_sdc)<-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sel:StudyElement)
            MATCH (all_sdc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sdc)<-[:BEFORE]-(bsa:StudyAction)
            WITH all_sdc, sa, se, sel, asa, bsa, sba
            ORDER BY all_sdc.uid, asa.date DESC
            RETURN
                all_sdc.uid AS uid,
                all_sdc.transition_rule AS transition_rule,
                all_sdc.order AS order,
                sa.uid AS study_arm_uid, 
                sba.uid AS study_branch_arm_uid,
                se.uid AS study_epoch_uid,
                sel.uid AS study_element_uid,
                labels(asa) AS change_type,
                asa.date AS start_date,
                bsa.date AS end_date,
                asa.user_initials AS user_initials
            """,
            {"study_uid": study_uid, "design_cell_uid": design_cell_uid},
        )
        result = []
        for res in helpers.db_result_to_list(specific_design_cells_audit_trail):
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                StudyDesignCellHistory(
                    study_uid=study_uid,
                    study_selection_uid=res["uid"],
                    study_arm_uid=res["study_arm_uid"],
                    study_branch_arm_uid=res["study_branch_arm_uid"],
                    study_epoch_uid=res["study_epoch_uid"],
                    study_element_uid=res["study_element_uid"],
                    user_initials=res["user_initials"],
                    change_type=change_type,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    transition_rule=res["transition_rule"],
                    order=res["order"],
                    end_date=end_date,
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, design_cell_uid: str = None
    ) -> List[Optional[dict]]:
        if design_cell_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, design_cell_uid=design_cell_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        pass
