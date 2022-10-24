import datetime
from typing import Sequence

from neomodel import db

from clinical_mdr_api.config import (
    GLOBAL_ANCHOR_VISIT_NAME,
    PREVIOUS_VISIT_NAME,
    STUDY_VISIT_TIMEREF_NAME,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domain.study_selection.study_visit import (
    NumericValue,
    StudyVisitVO,
    TextValue,
    TimeUnit,
)
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.domain_repositories.concepts.unit_definition.unit_definition_repository import (
    UnitDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    StudyDayRoot,
    StudyDurationDaysRoot,
    StudyDurationWeeksRoot,
    StudyWeekRoot,
    TimePointRoot,
    UnitDefinitionRoot,
    VisitNameRoot,
)
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
from clinical_mdr_api.domain_repositories.models.study_visit import StudyVisit
from clinical_mdr_api.domain_repositories.study_selection.study_epoch_repository import (
    StudyEpochRepository,
    get_ctlist_terms_by_name,
)
from clinical_mdr_api.models.study_visit import StudyVisitOGM, StudyVisitOGMVer


def get_valid_visit_types_for_epoch_type(epoch_type_uid: str, study_uid: str):
    cypher_query = """
        MATCH (visit_type_value:CTTermNameValue)<-[:LATEST]-(:CTTermNameRoot)<-[:HAS_NAME_ROOT]-
        (visit_type_root:CTTermRoot)-[:VALID_FOR_EPOCH_TYPE]->(:CTTermRoot {uid:$epoch_type_uid})

        RETURN visit_type_root.uid, visit_type_value.name
        """
    items, _ = db.cypher_query(
        cypher_query, {"epoch_type_uid": epoch_type_uid, "study_uid": study_uid}
    )
    return {a[0]: a[1] for a in items}


def get_valid_time_references_for_study(study_uid: str):
    cypher_query = """
        MATCH (time_reference_value:CTTermNameValue)<-[:LATEST]-(:CTTermNameRoot)<-[HAS_NAME_ROOT]-
        (time_reference_root:CTTermRoot)<-[HAS_TERM]-(codelist_root:CTCodelistRoot)-[:HAS_NAME_ROOT]->
        (:CTCodelistNameRoot)-[:LATEST]->(:CTCodelistNameValue {name:$time_reference_codelist_name})
        
        WHERE time_reference_value.name IN [
            (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_VISIT]->
            (study_visit:StudyVisit)-[:HAS_VISIT_TYPE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->
            (visit_type_value:CTTermNameValue) WHERE study_visit.is_deleted=false | visit_type_value.name 
        ] OR time_reference_value.name IN [$global_anchor_visit_name, $previous_visit_name]

        RETURN time_reference_root.uid, time_reference_value.name
        """
    items, _ = db.cypher_query(
        cypher_query,
        {
            "time_reference_codelist_name": STUDY_VISIT_TIMEREF_NAME,
            "study_uid": study_uid,
            "global_anchor_visit_name": GLOBAL_ANCHOR_VISIT_NAME,
            "previous_visit_name": PREVIOUS_VISIT_NAME,
        },
    )

    return {time_reference[0]: time_reference[1] for time_reference in items}


class StudyVisitRepository:
    def __init__(self, author: str):
        self.author = author
        unit_repository = UnitDefinitionRepository(self.author)
        units, _ = unit_repository.find_all()
        unit: UnitDefinitionAR
        self._day_unit = None
        self._week_unit = None
        for unit in units:
            if unit.concept_vo.name == "day":
                self._day_unit = unit
            if unit.concept_vo.name == "week":
                self._week_unit = unit

    def create_ctlist(self, code_list_name: str):
        return get_ctlist_terms_by_name(code_list_name)

    def get_day_week_units(self):
        return (self._day_unit, self._week_unit)

    def handle_update(self, item: StudyVisitVO, create: bool = False):
        if item.is_deleted:
            self._soft_delete(item)
        else:
            self._update(item, create=create)

    def save(self, visit: StudyVisitVO):
        if visit.uid is not None:
            if visit.is_deleted:
                self._soft_delete(visit)
            else:
                return self._update(visit, create=False)
        else:
            return self._update(visit, create=True)
        return None

    def _soft_delete(self, item: StudyVisitVO) -> None:
        previous_item: StudyVisit = StudyVisit.nodes.filter(uid=item.uid).has(
            has_before=False
        )[0]
        previous_item.is_deleted = True
        previous_item.save()
        study_root = StudyRoot.nodes.get(uid=item.study_uid)
        self.manage_versioning_delete(
            study_root=study_root, study_visit=item, previous_item=previous_item
        )

    def count_activities(self, visit_uid: str) -> int:
        """
        Returns the amount of activities assigned to given study visit

        :return: int
        """
        query = """
            MATCH (:StudyVisit {uid:$uid})-[:STUDY_VISIT_HAS_SCHEDULE]->(activity_schedule:StudyActivitySchedule)
            RETURN count(activity_schedule)
            """
        result, _ = db.cypher_query(query=query, params={"uid": visit_uid})
        return result[0][0] if len(result) > 0 else 0

    def count_study_visits(self, study_uid: str) -> int:
        nodes = StudyVisit.nodes.filter(
            has_study_visit__study_root__uid=study_uid, is_deleted=False
        ).to_relation_trees()
        return len(nodes)

    def from_neomodel_to_vo(self, study_visit_ogm_input: StudyVisitOGM):

        epoch_repository = StudyEpochRepository(author=self.author)
        study_epoch_object = epoch_repository.find_by_uid(
            study_visit_ogm_input.epoch_uid
        )

        unit_repository = UnitDefinitionRepository(self.author)
        if study_visit_ogm_input.timepoint:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                study_visit_ogm_input.timepoint.time_unit_uid
            )
            req_time_unit = req_time_unit_ar.concept_vo
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None

        if study_visit_ogm_input.window_unit_uid is not None:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                study_visit_ogm_input.window_unit_uid
            )
            window_time_unit = window_time_unit_ar.concept_vo
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None

        if study_visit_ogm_input.study_day:
            study_day = StudyDayRoot.nodes.get(
                uid=study_visit_ogm_input.study_day.uid
            ).has_latest_value.get()
        else:
            study_day = None
        if study_visit_ogm_input.study_duration_days:
            study_duration_days = StudyDurationDaysRoot.nodes.get(
                uid=study_visit_ogm_input.study_duration_days.uid
            ).has_latest_value.get()
        else:
            study_duration_days = None
        if study_visit_ogm_input.study_week:
            study_week = StudyWeekRoot.nodes.get(
                uid=study_visit_ogm_input.study_week.uid
            ).has_latest_value.get()
        else:
            study_week = None
        if study_visit_ogm_input.study_duration_weeks:
            study_duration_weeks = StudyDurationWeeksRoot.nodes.get(
                uid=study_visit_ogm_input.study_duration_weeks.uid
            ).has_latest_value.get()
        else:
            study_duration_weeks = None
        visit_name = VisitNameRoot.nodes.get(
            uid=study_visit_ogm_input.visit_name_sc.uid
        ).has_latest_value.get()
        return StudyVisitVO(
            uid=study_visit_ogm_input.uid,
            visit_number=study_visit_ogm_input.visit_number,
            visit_sub_label=study_visit_ogm_input.visit_sub_label,
            visit_sub_label_reference=study_visit_ogm_input.visit_sub_label_reference,
            visit_sub_label_uid=study_visit_ogm_input.visit_sub_label_uid,
            consecutive_visit_group=study_visit_ogm_input.consecutive_visit_group,
            show_visit=study_visit_ogm_input.show_visit,
            timepoint=study_visit_ogm_input.timepoint,
            study_day=NumericValue(
                uid=study_visit_ogm_input.study_day.uid, value=int(study_day.value)
            )
            if study_visit_ogm_input.study_day
            else None,
            study_duration_days=NumericValue(
                uid=study_visit_ogm_input.study_duration_days.uid,
                value=int(study_duration_days.value),
            )
            if study_visit_ogm_input.study_duration_days
            else None,
            study_week=NumericValue(
                uid=study_visit_ogm_input.study_week.uid, value=int(study_week.value)
            )
            if study_visit_ogm_input.study_week
            else None,
            study_duration_weeks=NumericValue(
                uid=study_visit_ogm_input.study_duration_weeks.uid,
                value=int(study_duration_weeks.value),
            )
            if study_visit_ogm_input.study_duration_weeks
            else None,
            visit_name_sc=TextValue(
                uid=study_visit_ogm_input.visit_name_sc.uid, name=visit_name.name
            ),
            time_unit_object=time_unit_object,
            window_unit_object=window_unit_object,
            visit_window_min=study_visit_ogm_input.visit_window_min,
            visit_window_max=study_visit_ogm_input.visit_window_max,
            window_unit_uid=study_visit_ogm_input.window_unit_uid,
            description=study_visit_ogm_input.description,
            start_rule=study_visit_ogm_input.start_rule,
            end_rule=study_visit_ogm_input.end_rule,
            note=study_visit_ogm_input.note,
            visit_contact_mode=study_visit_ogm_input.visit_contact_mode,
            epoch_allocation=study_visit_ogm_input.epoch_allocation,
            visit_type=study_visit_ogm_input.visit_type,
            status=StudyStatus(study_visit_ogm_input.status),
            start_date=study_visit_ogm_input.start_date,
            author=study_visit_ogm_input.author,
            day_unit_object=study_visit_ogm_input.day_unit_object,
            week_unit_object=study_visit_ogm_input.week_unit_object,
            epoch_connector=study_epoch_object,
            visit_class=study_visit_ogm_input.visit_class,
            visit_subclass=study_visit_ogm_input.visit_subclass
            if study_visit_ogm_input.visit_subclass
            else None,
            is_global_anchor_visit=study_visit_ogm_input.is_global_anchor_visit,
            visit_order=study_visit_ogm_input.visit_number,
        )

    def find_all_visits_by_study_uid(self, study_uid: str) -> Sequence[StudyVisitOGM]:
        all_visits = [
            StudyVisitOGM.from_orm(sas_node)
            for sas_node in StudyVisit.nodes.fetch_relations(
                "study_epoch_has_study_visit__has_epoch",
                "has_visit_type",
                "has_visit_contact_mode",
                "has_visit_name__has_latest_value",
                "has_after",
                "has_after__audit_trail",
            )
            .fetch_optional_relations(
                "has_window_unit__has_latest_value",
                "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                "has_timepoint__has_latest_value__has_time_reference",
                "has_timepoint__has_latest_value__has_value__has_latest_value",
                "has_study_day__has_latest_value",
                "has_study_duration_days__has_latest_value",
                "has_study_week__has_latest_value",
                "has_study_duration_weeks__has_latest_value",
                "has_epoch_allocation",
            )
            .filter(has_study_visit__study_root__uid=study_uid, is_deleted=False)
            .order_by("unique_visit_number")
            .to_relation_trees()
        ]
        return all_visits

    def find_by_uid(self, uid: str) -> StudyVisitVO:
        visit_node = (
            StudyVisit.nodes.fetch_relations(
                "has_study_visit__study_root",
                "study_epoch_has_study_visit__has_epoch",
                "study_epoch_has_study_visit__has_study_epoch",
                "has_visit_type",
                "has_visit_contact_mode",
                "has_visit_name__has_latest_value",
                "has_after",
                "has_after__audit_trail",
            )
            .fetch_optional_relations(
                "has_window_unit__has_latest_value",
                "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                "has_timepoint__has_latest_value__has_time_reference",
                "has_timepoint__has_latest_value__has_value__has_latest_value",
                "has_study_day__has_latest_value",
                "has_study_duration_days__has_latest_value",
                "has_study_week__has_latest_value",
                "has_study_duration_weeks__has_latest_value",
                "has_epoch_allocation",
            )
            .filter(uid=uid, is_deleted=False)
            .to_relation_trees()
        )
        unique_visits = []
        for ith_visit_node in visit_node:
            if ith_visit_node not in unique_visits:
                unique_visits.extend([ith_visit_node])
        if len(unique_visits) > 1:
            raise ValueError(f"Found more than one StudyVisit node with uid='{uid}'.")
        if len(unique_visits) == 0:
            raise ValueError(f"The study visit with uid='{uid}' could not be found.")
        return self.from_neomodel_to_vo(
            study_visit_ogm_input=StudyVisitOGM.from_orm(unique_visits[0])
        )

    def get_all_versions(self, uid: str, study_uid: str):
        version_nodes = [
            self.from_neomodel_to_vo(
                study_visit_ogm_input=StudyVisitOGMVer.from_orm(se_node)
            )
            for se_node in StudyVisit.nodes.fetch_relations(
                "study_epoch_has_study_visit__has_epoch",
                "has_visit_type",
                "has_visit_contact_mode",
                "has_visit_name__has_latest_value",
                "has_after",
                "has_after__audit_trail",
            )
            .fetch_optional_relations(
                "has_window_unit__has_latest_value",
                "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                "has_timepoint__has_latest_value__has_time_reference",
                "has_timepoint__has_latest_value__has_value__has_latest_value",
                "has_study_day__has_latest_value",
                "has_study_duration_days__has_latest_value",
                "has_study_week__has_latest_value",
                "has_study_duration_weeks__has_latest_value",
                "has_epoch_allocation",
            )
            .filter(uid=uid, has_after__audit_trail__uid=study_uid)
            .to_relation_trees()
        ]
        return sorted(version_nodes, key=lambda item: item.start_date, reverse=True)

    def get_all_visit_versions(self, study_uid: str):
        version_nodes = [
            StudyVisitOGMVer.from_orm(se_node)
            for se_node in StudyVisit.nodes.fetch_relations(
                "study_epoch_has_study_visit__has_epoch",
                "has_visit_type",
                "has_visit_contact_mode",
                "has_visit_name__has_latest_value",
                "has_after",
                "has_after__audit_trail",
            )
            .fetch_optional_relations(
                "has_window_unit__has_latest_value",
                "has_timepoint__has_latest_value__has_unit_definition__has_latest_value",
                "has_timepoint__has_latest_value__has_time_reference",
                "has_timepoint__has_latest_value__has_value__has_latest_value",
                "has_study_day__has_latest_value",
                "has_study_duration_days__has_latest_value",
                "has_study_week__has_latest_value",
                "has_study_duration_weeks__has_latest_value",
                "has_epoch_allocation",
            )
            .filter(has_after__audit_trail__uid=study_uid)
            .to_relation_trees()
        ]
        return version_nodes

    def manage_versioning_create(
        self, study_root: StudyRoot, study_visit: StudyVisitVO, new_item: StudyVisit
    ):
        action = Create(
            date=datetime.datetime.now(),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        new_item.has_after.connect(action)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
        new_item: StudyVisit,
    ):
        action = Edit(
            date=datetime.datetime.now(),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        previous_item.has_before.connect(action)
        # previous_item.study_epoch_has_study_visit.disconnect_all()
        previous_item.has_study_visit.disconnect_all()
        new_item.has_after.connect(action)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        study_visit: StudyVisitVO,
        previous_item: StudyVisit,
    ):
        action = Delete(
            date=datetime.datetime.now(),
            status=study_visit.status.value,
            user_initials=study_visit.author,
        )
        action.save()
        previous_item.has_before.connect(action)
        study_root.audit_trail.connect(action)

    def _update(self, study_visit: StudyVisitVO, create: bool = False):
        study_root = StudyRoot.nodes.get(uid=study_visit.study_uid)
        study_value = study_root.latest_draft.get_or_none()
        if study_value is None:
            raise ValueError("Study does not have draft version")

        new_visit = StudyVisit(
            uid=study_visit.uid,
            legacy_visit_id=study_visit.legacy_visit_id,
            legacy_visit_type_alias=study_visit.legacy_visit_type_alias,
            legacy_name=study_visit.legacy_name,
            legacy_sub_name=study_visit.legacy_sub_name,
            visit_number=study_visit.visit_number,
            visit_sub_label=study_visit.visit_sub_label,
            visit_sub_label_uid=study_visit.visit_sub_label_uid,
            visit_sub_label_reference=study_visit.visit_sub_label_reference,
            visit_name_label=study_visit.visit_name_label,
            short_visit_label=study_visit.visit_short_name,
            unique_visit_number=study_visit.unique_visit_number,
            consecutive_visit_group=study_visit.consecutive_visit_group,
            show_visit=study_visit.show_visit,
            visit_window_min=study_visit.visit_window_min,
            visit_window_max=study_visit.visit_window_max,
            description=study_visit.description,
            start_rule=study_visit.start_rule,
            end_rule=study_visit.end_rule,
            note=study_visit.note,
            is_deleted=False,
            status=study_visit.status.name,
            visit_class=study_visit.visit_class.name,
            visit_subclass=study_visit.visit_subclass.name
            if study_visit.visit_subclass
            else None,
            is_global_anchor_visit=study_visit.is_global_anchor_visit,
        )
        if study_visit.uid:
            new_visit.uid = study_visit.uid
        new_visit.save()
        if study_visit.uid is None:
            study_visit.uid = new_visit.uid
        new_visit.has_study_visit.connect(study_value)

        visit_type = CTTermRoot.nodes.get(uid=study_visit.visit_type.name)
        new_visit.has_visit_type.connect(visit_type)

        if study_visit.timepoint:
            visit_timepoint = TimePointRoot.nodes.get(uid=study_visit.timepoint.uid)
            new_visit.has_timepoint.connect(visit_timepoint)
        if study_visit.study_day:
            study_day_numeric_value = StudyDayRoot.nodes.get(
                uid=study_visit.study_day.uid
            )
            new_visit.has_study_day.connect(study_day_numeric_value)
        if study_visit.study_duration_days:
            study_duration_days = StudyDurationDaysRoot.nodes.get(
                uid=study_visit.study_duration_days.uid
            )
            new_visit.has_study_duration_days.connect(study_duration_days)
        if study_visit.study_week:
            study_week_numeric_value = StudyWeekRoot.nodes.get(
                uid=study_visit.study_week.uid
            )
            new_visit.has_study_week.connect(study_week_numeric_value)
        if study_visit.study_duration_weeks:
            study_duration_weeks = StudyDurationWeeksRoot.nodes.get(
                uid=study_visit.study_duration_weeks.uid
            )
            new_visit.has_study_duration_weeks.connect(study_duration_weeks)

        visit_name_text_value = VisitNameRoot.nodes.get(
            uid=study_visit.visit_name_sc.uid
        )
        new_visit.has_visit_name.connect(visit_name_text_value)

        if study_visit.window_unit_uid is not None:
            window_unit = UnitDefinitionRoot.nodes.get(uid=study_visit.window_unit_uid)
            new_visit.has_window_unit.connect(window_unit)
        else:
            window_unit = None
        visit_contact_mode = CTTermRoot.nodes.get(
            uid=study_visit.visit_contact_mode.name
        )
        new_visit.has_visit_contact_mode.connect(visit_contact_mode)
        if study_visit.epoch_allocation:
            epoch_allocation = CTTermRoot.nodes.get(
                uid=study_visit.epoch_allocation.name
            )
            new_visit.has_epoch_allocation.connect(epoch_allocation)

        if not create:
            previous_item = StudyVisit.nodes.filter(uid=study_visit.uid).has(
                study_epoch_has_study_visit=True
            )[0]

        study_epoch = (
            StudyEpoch.nodes.has(has_after=True)
            .has(has_before=False)
            .get(uid=study_visit.epoch_uid)
        )
        new_visit.study_epoch_has_study_visit.connect(study_epoch)
        if not create:
            self.manage_versioning_update(
                study_root=study_root,
                study_visit=study_visit,
                previous_item=previous_item,
                new_item=new_visit,
            )
        else:
            self.manage_versioning_create(
                study_root=study_root, study_visit=study_visit, new_item=new_visit
            )

        return study_visit
