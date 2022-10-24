import datetime
from typing import Optional, Sequence

from neomodel import db

from clinical_mdr_api import config as settings
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domain.study_selection import study_epoch
from clinical_mdr_api.domain.study_selection.study_epoch import StudyEpochVO
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_epoch import StudyEpochOGM, StudyEpochOGMVer


def get_ctlist_terms_by_name(code_list_name: str):
    cypher_query = """
        MATCH (:CTCodelistNameValue {name: $code_list_name})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
        (:CTCodelistRoot)-[:HAS_TERM]->
        (tr:CTTermRoot)-[:HAS_NAME_ROOT]->
        (:CTTermNameRoot)-[:LATEST_FINAL]->
        (ctnv:CTTermNameValue)
        return tr.uid, ctnv.name
        """
    items, _ = db.cypher_query(cypher_query, {"code_list_name": code_list_name})
    return {a[0]: a[1] for a in items}


class StudyEpochRepository:
    def __init__(self, author: str):
        self.author = author

    def create_ctlist(self, code_list_name: str):
        return get_ctlist_terms_by_name(code_list_name)

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
            cypher_query, {"code_list_name": settings.STUDY_EPOCH_SUBTYPE_NAME}
        )
        return items

    def get_basic_epoch(self, study_uid: str) -> Optional[str]:
        cypher_query = """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)-[:HAS_EPOCH_SUB_TYPE]->(:CTTermRoot)-
        [:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(:CTTermNameValue {name:$basic_epoch_name})
        return study_epoch.uid
        """
        basic_visit, _ = db.cypher_query(
            cypher_query,
            {"basic_epoch_name": settings.BASIC_EPOCH_NAME, "study_uid": study_uid},
        )
        return basic_visit[0][0] if len(basic_visit) > 0 else None

    def find_all_epochs_by_study(self, study_uid: str) -> Sequence[StudyEpochVO]:
        all_epochs = [
            self._from_neomodel_to_vo(
                study_epoch_ogm_input=StudyEpochOGM.from_orm(sas_node)
            )
            for sas_node in StudyEpoch.nodes.fetch_relations(
                "has_epoch", "has_epoch_subtype", "has_epoch_type", "has_after"
            )
            .fetch_optional_relations("has_duration_unit")
            .filter(has_study_epoch__study_root__uid=study_uid, is_deleted=False)
            .order_by("order")
            .to_relation_trees()
        ]
        return all_epochs

    def epoch_specific_has_connected_design_cell(
        self, study_uid: str, epoch_uid: str
    ) -> bool:
        """
        Returns True if StudyEpoch with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = (
            StudyEpoch.nodes.fetch_relations("has_design_cell", "has_after")
            .filter(study_value__study_root__uid=study_uid, uid=epoch_uid)
            .to_relation_trees()
        )
        return len(sdc_node) > 0

    def find_by_uid(self, uid: str) -> StudyEpochVO:
        epoch_node = (
            StudyEpoch.nodes.fetch_relations(
                "has_study_epoch__study_root",
                "has_epoch",
                "has_epoch_subtype",
                "has_epoch_type",
                "has_after",
            )
            .fetch_optional_relations("has_duration_unit")
            .filter(uid=uid)  # ADD study_uid filtering
            .to_relation_trees()
        )

        if len(epoch_node) > 1:
            raise ValueError(f"Found more than one StudyEpoch node with uid='{uid}'.")
        if len(epoch_node) == 0:
            raise ValueError(f"The StudyEpoch with uid='{uid}' could not be found.")
        return self._from_neomodel_to_vo(
            study_epoch_ogm_input=StudyEpochOGM.from_orm(epoch_node[0])
        )

    def get_all_versions(self, uid: str, study_uid):
        version_nodes = [
            self._from_neomodel_to_vo(
                study_epoch_ogm_input=StudyEpochOGMVer.from_orm(se_node)
            )
            for se_node in StudyEpoch.nodes.fetch_relations(
                "has_after__audit_trail",
                "has_epoch",
                "has_epoch_subtype",
                "has_epoch_type",
            )
            .fetch_optional_relations("has_duration_unit")
            .filter(uid=uid, has_after__audit_trail__uid=study_uid)
            .to_relation_trees()
        ]
        return sorted(version_nodes, key=lambda item: item.start_date, reverse=True)

    def get_all_epoch_versions(self, study_uid: str):
        version_nodes = [
            self._from_neomodel_to_vo(
                study_epoch_ogm_input=StudyEpochOGMVer.from_orm(se_node)
            )
            for se_node in StudyEpoch.nodes.fetch_relations(
                "has_after__audit_trail",
                "has_epoch",
                "has_epoch_subtype",
                "has_epoch_type",
            )
            .fetch_optional_relations("has_duration_unit")
            .filter(has_after__audit_trail__uid=study_uid)
            .order_by("order")
            .to_relation_trees()
        ]
        return sorted(version_nodes, key=lambda item: item.start_date, reverse=True)

    def _from_neomodel_to_vo(self, study_epoch_ogm_input: StudyEpochOGM):
        return StudyEpochVO(
            uid=study_epoch_ogm_input.uid,
            study_uid=study_epoch_ogm_input.studyUid,
            start_rule=study_epoch_ogm_input.startRule,
            end_rule=study_epoch_ogm_input.endRule,
            description=study_epoch_ogm_input.description,
            epoch=study_epoch.StudyEpochEpoch[study_epoch_ogm_input.epoch],
            subtype=study_epoch.StudyEpochSubType[study_epoch_ogm_input.epochSubType],
            epoch_type=study_epoch.StudyEpochType[study_epoch_ogm_input.epochType],
            order=study_epoch_ogm_input.order,
            status=StudyStatus(study_epoch_ogm_input.status),
            start_date=study_epoch_ogm_input.startDate,
            author=self.author,
            color_hash=study_epoch_ogm_input.colorHash,
        )

    def save(self, epoch: StudyEpochVO):
        # if exists
        if epoch.uid is not None:
            # if has to be deleted
            if epoch.is_deleted:
                self._soft_delete(epoch)
            # if has to be modified
            else:
                return self._update(epoch, create=False)
        # if has to be created
        else:
            return self._update(epoch, create=True)
        return None

    def handle_update(self, item: StudyEpochVO, create: bool = False):
        if item._is_deleted:
            self._soft_delete(item)
        else:
            self._update(item, create=create)

    def _soft_delete(self, item: StudyEpochVO) -> None:
        previous_item = StudyEpoch.nodes.filter(uid=item.uid).has(has_before=False)[0]
        previous_item.is_deleted = True
        previous_item.save()
        study_root = StudyRoot.nodes.get(uid=item.study_uid)
        self.manage_versioning_delete(
            study_root=study_root, item=item, previous_item=previous_item
        )

    def _update(self, item: StudyEpochVO, create: bool = False):
        study_root = StudyRoot.nodes.get(uid=item.study_uid)
        study_value = study_root.latest_draft.get_or_none()
        if study_value is None:
            raise ValueError("Study does not have draft version")
        new_study_epoch = StudyEpoch(
            uid=item.uid,
            accepted_version=item.accepted_version,
            order=item.order,
            name=item.name,
            short_name=item.short_name,
            description=item.description,
            start_rule=item.start_rule,
            end_rule=item.end_rule,
            color_hash=item.color_hash,
            status=item.status.value,
            is_deleted=False,
        )
        if item.uid is not None:
            new_study_epoch.uid = item.uid
        new_study_epoch.save()
        if item.uid is None:
            item.uid = new_study_epoch.uid
        ct_epoch_subtype = CTTermRoot.nodes.get(uid=item.subtype.name)
        new_study_epoch.has_epoch_subtype.connect(ct_epoch_subtype)
        ct_epoch_type = CTTermRoot.nodes.get(uid=item.epoch_type.name)
        new_study_epoch.has_epoch_type.connect(ct_epoch_type)
        ct_epoch = CTTermRoot.nodes.get(uid=item.epoch.name)
        new_study_epoch.has_epoch.connect(ct_epoch)

        if create:
            self.manage_versioning_create(
                study_root=study_root, item=item, new_item=new_study_epoch
            )
        else:
            previous_item = StudyEpoch.nodes.filter(uid=item.uid).has(
                has_study_epoch=True
            )[0]
            self.manage_versioning_update(
                study_root=study_root,
                item=item,
                previous_item=previous_item,
                new_item=new_study_epoch,
            )
            previous_item.has_study_epoch.disconnect(study_value)

            self._maintain_relationship_on_save(
                relation_name="has_design_cell",
                expected_latest_value=new_study_epoch,
                previous_value=previous_item,
            )
            self._maintain_relationship_on_save(
                relation_name="has_study_visit",
                expected_latest_value=new_study_epoch,
                previous_value=previous_item,
            )

        new_study_epoch.has_study_epoch.connect(study_value)
        return item

    def _maintain_relationship_on_save(
        self,
        relation_name: str,
        expected_latest_value: StudyEpoch,
        previous_value: StudyEpoch,
    ):
        # check if new value node is created
        if expected_latest_value is not previous_value:
            # remove the relation from the old value node
            study_selection_nodes = getattr(previous_value, relation_name).all()
            # only the has_design_cell is deleted because
            # the cardinality and the function of the studyDesign cell is to have just one StudyEpoch at the time
            if "has_design_cell" in relation_name:
                getattr(previous_value, relation_name).disconnect_all()

            # add the relation to the new node
            for study_selection_node in study_selection_nodes:
                getattr(expected_latest_value, relation_name).connect(
                    study_selection_node
                )

    def manage_versioning_create(
        self, study_root: StudyRoot, item: StudyEpochVO, new_item: StudyEpoch
    ):
        action = Create(
            date=datetime.datetime.now(),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        new_item.has_after.connect(action)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
        new_item: StudyEpoch,
    ):
        action = Edit(
            date=datetime.datetime.now(),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        previous_item.has_before.connect(action)
        new_item.has_after.connect(action)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
    ):
        action = Delete(
            date=datetime.datetime.now(),
            status=item.status.value,
            user_initials=item.author,
        )
        action.save()
        previous_item.has_before.connect(action)
        study_root.audit_trail.connect(action)
