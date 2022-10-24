import dataclasses
import datetime
from typing import Optional, Sequence

from aenum import extend_enum
from neomodel import db

from clinical_mdr_api import config as settings
from clinical_mdr_api.config import GLOBAL_ANCHOR_VISIT_NAME, PREVIOUS_VISIT_NAME
from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value import (
    NumericValueAR,
    NumericValueType,
    NumericValueVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.study_day import (
    StudyDayAR,
    StudyDayVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.study_duration_days import (
    StudyDurationDaysAR,
    StudyDurationDaysVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.study_duration_weeks import (
    StudyDurationWeeksAR,
    StudyDurationWeeksVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.study_week import (
    StudyWeekAR,
    StudyWeekVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.time_point import (
    TimePointAR,
    TimePointVO,
)
from clinical_mdr_api.domain.concepts.simple_concepts.visit_name import (
    VisitNameAR,
    VisitNameVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domain.study_selection.study_epoch import (
    StudyEpochEpoch,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
    TimelineAR,
)
from clinical_mdr_api.domain.study_selection.study_visit import (
    NumericValue,
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    TextValue,
    TimePoint,
    TimeUnit,
    VisitClass,
    VisitSubclass,
)
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.models.study_visit import (
    StudyVisit as StudyVisitNeoModel,
)
from clinical_mdr_api.domain_repositories.study_selection.study_visit_repository import (
    get_valid_time_references_for_study,
    get_valid_visit_types_for_epoch_type,
)
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models import StudyVisit
from clinical_mdr_api.models.study_visit import (
    AllowedTimeReferences,
    AllowedVisitTypesForEpochType,
    SimpleStudyVisit,
    StudyVisitCreateInput,
    StudyVisitEditInput,
    StudyVisitVersion,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    calculate_diffs,
    calculate_diffs_history,
    service_level_generic_filtering,
    service_level_generic_header_filtering,
)


class StudyVisitService:
    def __init__(self, author="TODO Initials"):
        self._repos = MetaRepository()
        self.repo = self._repos.study_visit_repository
        self.author = author
        self._create_ctlist_map()
        self._day_unit, self._week_unit = self.repo.get_day_week_units()

    def _create_ctlist_map(self):
        self.study_visit_types = self.repo.create_ctlist(settings.STUDY_VISIT_TYPE_NAME)
        self.study_visit_timeref = self.repo.create_ctlist(
            settings.STUDY_VISIT_TIMEREF_NAME
        )
        self.study_visit_contact_mode = self.repo.create_ctlist(
            settings.STUDY_VISIT_CONTACT_MODE_NAME
        )
        self.study_visit_contact_mode = self.repo.create_ctlist(
            settings.STUDY_VISIT_CONTACT_MODE_NAME
        )
        self.study_visit_epoch_allocation = self.repo.create_ctlist(
            settings.STUDY_VISIT_EPOCH_ALLOCATION_NAME
        )
        for uid, name in self.study_visit_types.items():
            if uid not in StudyVisitType._member_map_:
                extend_enum(StudyVisitType, uid, name)

        for uid, name in self.study_visit_timeref.items():
            if uid not in StudyVisitTimeReference._member_map_:
                extend_enum(StudyVisitTimeReference, uid, name)

        for uid, name in self.study_visit_contact_mode.items():
            if uid not in StudyVisitContactMode._member_map_:
                extend_enum(StudyVisitContactMode, uid, name)

        for uid, name in self.study_visit_epoch_allocation.items():
            if uid not in StudyVisitEpochAllocation._member_map_:
                extend_enum(StudyVisitEpochAllocation, uid, name)

        self.study_epoch_types = self.repo.create_ctlist(settings.STUDY_EPOCH_TYPE_NAME)
        self.study_epoch_subtypes = self.repo.create_ctlist(
            settings.STUDY_EPOCH_SUBTYPE_NAME
        )

        self.study_epoch_epochs = self.repo.create_ctlist(
            settings.STUDY_EPOCH_EPOCH_NAME
        )
        self.study_visit_sublabels = self.repo.create_ctlist(
            settings.STUDY_VISIT_SUBLABEL
        )

        for uid, name in self.study_epoch_types.items():
            if uid not in StudyEpochType._member_map_:
                extend_enum(StudyEpochType, uid, name)

        for uid, name in self.study_epoch_subtypes.items():
            if uid not in StudyEpochSubType._member_map_:
                extend_enum(StudyEpochSubType, uid, name)

        for uid, name in self.study_epoch_epochs.items():
            if uid not in StudyEpochEpoch._member_map_:
                extend_enum(StudyEpochEpoch, uid, name)

    def get_valid_visit_types_for_epoch_type(self, epoch_type_uid: str, study_uid: str):
        resp = []
        for uid, name in get_valid_visit_types_for_epoch_type(
            epoch_type_uid=epoch_type_uid, study_uid=study_uid
        ).items():
            resp.append(
                AllowedVisitTypesForEpochType(visit_type_uid=uid, visit_type_name=name)
            )
        return sorted(resp, key=lambda visit_type: visit_type.visit_type_name)

    def get_allowed_time_references_for_study(self, study_uid: str):
        resp = []
        for uid, name in get_valid_time_references_for_study(
            study_uid=study_uid
        ).items():
            resp.append(
                AllowedTimeReferences(timeReferenceUid=uid, timeReferenceName=name)
            )
        # if we don't have any visits we have to remove 'previous visit' time reference
        if self.repo.count_study_visits(study_uid=study_uid) < 1:
            resp = [
                item for item in resp if item.timeReferenceName != PREVIOUS_VISIT_NAME
            ]
        return sorted(resp, key=lambda time_reference: time_reference.timeReferenceName)

    def _transform_all_to_response_model(
        self, visit: StudyVisitVO, study_activity_count: Optional[int] = None
    ) -> StudyVisit:
        return StudyVisit(
            uid=visit.uid,
            studyUid=visit.study_uid,
            studyEpochUid=visit.epoch_uid,
            studyEpochName=visit.epoch.epoch.value,
            epochUid=visit.epoch.epoch.name,
            order=visit.visit_order,
            visitTypeUid=visit.visit_type.name,
            visitTypeName=visit.visit_type.value,
            timeReferenceUid=visit.timepoint.visit_timereference.name
            if visit.timepoint
            else None,
            timeReferenceName=visit.timepoint.visit_timereference.value
            if visit.timepoint
            else None,
            timeValue=visit.timepoint.visit_value if visit.timepoint else None,
            timeUnitUid=visit.timepoint.time_unit_uid if visit.timepoint else None,
            timeUnitName=visit.time_unit_object.name
            if visit.time_unit_object
            else None,
            durationTime=visit.get_absolute_duration() if visit.timepoint else None,
            durationTimeUnit=visit.timepoint.time_unit_uid if visit.timepoint else None,
            studyDayNumber=visit.study_day_number if visit.study_day else None,
            studyDayLabel=visit.study_day_label if visit.study_day else None,
            studyDurationDaysLabel=visit.study_duration_days_label
            if visit.study_duration_days
            else None,
            studyWeekNumber=visit.study_week_number if visit.study_week else None,
            studyWeekLabel=visit.study_week_label if visit.study_week else None,
            studyDurationWeeksLabel=visit.study_duration_weeks_label
            if visit.study_duration_weeks
            else None,
            visitNumber=visit.visit_number,
            visitSubNumber=visit.visit_sub_number,
            uniqueVisitNumber=visit.unique_visit_number,
            visitSubName=visit.visit_sub_name,
            visitSubLabel=visit.visit_sub_label,
            visitName=visit.derive_visit_name(),
            visitShortName=visit.visit_short_name,
            legacyVisitId=visit.legacy_visit_id,
            legacyVisitTypeAlias=visit.legacy_visit_type_alias,
            legacyName=visit.legacy_name,
            legacySubName=visit.legacy_sub_name,
            consecutiveVisitGroup=visit.consecutive_visit_group,
            showVisit=visit.show_visit,
            minVisitWindowValue=visit.visit_window_min,
            maxVisitWindowValue=visit.visit_window_max,
            visitWindowUnitUid=visit.window_unit_uid,
            visitWindowUnitName=visit.window_unit_object.name
            if visit.window_unit_object
            else None,
            description=visit.description,
            startRule=visit.start_rule,
            endRule=visit.end_rule,
            note=visit.note,
            visitContactModeUid=visit.visit_contact_mode.name,
            visitContactModeName=visit.visit_contact_mode.value,
            epochAllocationUid=visit.epoch_allocation.name
            if visit.epoch_allocation
            else None,
            epochAllocationName=visit.epoch_allocation.value
            if visit.epoch_allocation
            else None,
            visitType=visit.visit_type.name,
            status=visit.status.value,
            startDate=visit.start_date.strftime(settings.TIME_FORMAT),
            userInitials=visit.author,
            possibleActions=visit.possible_actions,
            studyActivityCount=study_activity_count,
            visitClass=visit.visit_class.name,
            visitSubclass=visit.visit_subclass.name if visit.visit_subclass else None,
            isGlobalAnchorVisit=visit.is_global_anchor_visit,
        )

    def _transform_all_to_history_model(self, visit: StudyVisitVO) -> StudyVisit:
        return StudyVisit(
            uid=visit.uid,
            studyUid=visit.study_uid,
            studyEpochUid=visit.epoch_uid,
            studyEpochName=visit.epoch.epoch.value,
            epochUid=visit.epoch.epoch.name,
            order=0,
            visitTypeUid=visit.visit_type.name,
            visitTypeName=visit.visit_type.value,
            timeReferenceUid=visit.timepoint.visit_timereference.name,
            timeReferenceName=visit.timepoint.visit_timereference.value,
            timeValue=visit.timepoint.visit_value,
            timeUnitUid=visit.timepoint.time_unit_uid,
            timeUnitName=visit.time_unit_object.name,
            durationTime=0,
            durationTimeUnit=visit.timepoint.time_unit_uid if visit.timepoint else None,
            studyDayNumber=0,
            studyDayLabel=0,
            studyDurationDaysLabel=0,
            studyWeekNumber=0,
            studyWeekLabel=0,
            studyDurationWeeksLabel=0,
            visitNumber=0,
            visitSubNumber=0,
            uniqueVisitNumber=0,
            visitSubName=visit.visit_sub_name,
            visitSubLabel=visit.visit_sub_label,
            visitSubLabelReference=visit.visit_sub_label_reference,
            visitName=visit.visit_name,
            visitShortName=visit.visit_short_name,
            legacyVisitId=visit.legacy_visit_id,
            legacyVisitTypeAlias=visit.legacy_visit_type_alias,
            legacyName=visit.legacy_name,
            legacySubName=visit.legacy_sub_name,
            consecutiveVisitGroup=visit.consecutive_visit_group,
            showVisit=visit.show_visit,
            minVisitWindowValue=visit.visit_window_min,
            maxVisitWindowValue=visit.visit_window_max,
            visitWindowUnitUid=visit.window_unit_uid,
            visitWindowUnitName=visit.window_unit_object.name,
            description=visit.description,
            startRule=visit.start_rule,
            endRule=visit.end_rule,
            note=visit.note,
            visitContactModeUid=visit.visit_contact_mode.name,
            visitContactModeName=visit.visit_contact_mode.value,
            epochAllocationUid=visit.epoch_allocation.name
            if visit.epoch_allocation
            else None,
            epochAllocationName=visit.epoch_allocation.value
            if visit.epoch_allocation
            else None,
            visitType=visit.visit_type.name,
            status=visit.status.value,
            startDate=visit.start_date.strftime(settings.TIME_FORMAT),
            userInitials=visit.author,
            possibleActions=visit.possible_actions,
            visitClass=visit.visit_class.name,
            visitSubclass=visit.visit_subclass.name if visit.visit_subclass else None,
            isGlobalAnchorVisit=visit.is_global_anchor_visit,
        )

    def _get_all_visits(self, study_uid: str) -> Sequence[StudyVisitVO]:
        repos = self._repos
        try:
            study_visits = self.repo.find_all_visits_by_study_uid(study_uid=study_uid)
            timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
            assert study_visits is not None
            return timeline.ordered_study_visits
        finally:
            repos.close()

    def get_amount_of_visits_in_given_epoch(
        self, study_uid: str, study_epoch_uid: str
    ) -> int:
        visits_in_given_study_epoch = (
            StudyVisitNeoModel.nodes.fetch_relations()
            .filter(
                study_epoch_has_study_visit__uid=study_epoch_uid,
                has_study_visit__study_root__uid=study_uid,
                is_deleted=False,
            )
            .to_relation_trees()
        )
        return len(visits_in_given_study_epoch)

    def get_global_anchor_visit(self, study_uid: str) -> Optional[SimpleStudyVisit]:
        global_anchor_visit = (
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            )
            .filter(
                has_study_visit__study_root__uid=study_uid,
                is_global_anchor_visit=True,
                is_deleted=False,
            )
            .to_relation_trees()
        )
        if len(global_anchor_visit) > 0:
            return SimpleStudyVisit.from_orm(global_anchor_visit[0])
        return None

    def get_anchor_visits_in_a_group_of_subvisits(
        self, study_uid: str
    ) -> Sequence[SimpleStudyVisit]:
        anchor_visits_in_a_group_of_subv = (
            StudyVisitNeoModel.nodes.fetch_relations(
                "has_visit_name__has_latest_value",
                "has_visit_type__has_name_root__has_latest_value",
            )
            .filter(
                has_study_visit__study_root__uid=study_uid,
                visit_subclass=VisitSubclass.ANCHOR_VISIT_IN_GROUP_OF_SUBV.name,
                is_deleted=False,
            )
            .to_relation_trees()
        )
        return [
            SimpleStudyVisit.from_orm(anchor_visit)
            for anchor_visit in anchor_visits_in_a_group_of_subv
        ]

    @db.transaction
    def get_all_visits(
        self,
        study_uid: str,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyVisit]:
        visits = self._get_all_visits(study_uid)
        visits = [
            self._transform_all_to_response_model(
                visit,
                study_activity_count=self.repo.count_activities(visit_uid=visit.uid),
            )
            for visit in visits
        ]

        filtered_visits = service_level_generic_filtering(
            items=visits,
            filter_by=filter_by,
            filter_operator=filter_operator,
            sort_by=sort_by,
            total_count=total_count,
            page_number=page_number,
            page_size=page_size,
        )
        return filtered_visits

    def get_distinct_values_for_header(
        self,
        study_uid: str,
        field_name: str,
        search_string: Optional[str] = "",
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        result_count: int = 10,
    ):

        all_items = self.get_all_visits(study_uid=study_uid)

        # Do filtering, sorting, pagination and count
        header_values = service_level_generic_header_filtering(
            items=all_items.items,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            result_count=result_count,
        )
        # Return values for field_name
        return header_values

    @db.transaction
    def get_all_references(self, study_uid: str) -> Sequence[StudyVisit]:
        def is_reference(visit: StudyVisitVO):
            if visit.visit_type.value in self.study_visit_timeref.values():
                return True
            return False

        visits = self._get_all_visits(study_uid)

        return [
            self._transform_all_to_response_model(visit)
            for visit in visits
            if is_reference(visit)
        ]

    @db.transaction
    def find_by_uid(self, uid: str) -> StudyVisit:
        """
        finds latest version of visit by uid, status ans version
        if user do not give status and version - will be overwritten by DRAFT
        """
        repos = self._repos
        try:
            study_visit = self.repo.find_by_uid(uid)

            study_visits = self.repo.find_all_visits_by_study_uid(study_visit.study_uid)
            timeline = TimelineAR(study_uid=study_visit.study_uid, _visits=study_visits)
            assert study_visits is not None
            for v in timeline.ordered_study_visits:
                if v.uid == study_visit.uid:
                    return self._transform_all_to_response_model(v)
        except ValueError as e:
            raise ValidationException(str(e)) from e
        finally:
            repos.close()

        return None

    def _validate_visit(
        self,
        visit_input: StudyVisitCreateInput,
        visit_vo: StudyVisitVO,
        timeline: TimelineAR,
        create: bool = True,
        preview: bool = False,
    ):
        is_time_reference_visit = False
        if (
            visit_vo.visit_class
            not in (
                VisitClass.NON_VISIT,
                VisitClass.UNSCHEDULED_VISIT,
            )
            and visit_vo.visit_type.value
            == visit_vo.timepoint.visit_timereference.value
        ):
            is_time_reference_visit = True

        if len(timeline._visits) == 0:
            is_first_reference_visit = visit_vo.visit_type.value in [
                v.value for v in StudyVisitTimeReference
            ]
            is_reference_visit = is_first_reference_visit
        else:
            is_first_reference_visit = False
            is_reference_visit = visit_vo.visit_type.value in [
                v.value for v in StudyVisitTimeReference
            ]

        if is_first_reference_visit and visit_vo.visit_class not in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            if (
                visit_vo.timepoint.visit_value != 0
                and visit_vo.timepoint.visit_timereference.value.lower()
                != GLOBAL_ANCHOR_VISIT_NAME.lower()
            ):
                raise ValueError(
                    "The first visit should have time span set to 0 or reference to GLOBAL ANCHOR VISIT"
                )
            for visit in timeline._visits:
                if (
                    visit.visit_type == visit_vo.visit_type
                    and visit.uid != visit_vo.uid
                ):
                    raise ValueError(
                        f"There can be only one visit with the following visit type {visit_vo.visit_type.value}"
                    )

        if is_reference_visit and visit_vo.visit_class not in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            for visit in timeline._visits:
                if (
                    # if we found another visit with the same visit type
                    visit.visit_type == visit_vo.visit_type
                    # if visit with the same visit type had selected the same value for visit type and time reference
                    and visit.visit_type.value
                    == visit.timepoint.visit_timereference.value
                    # if visit we are creating has the same value selected as visit type and time reference
                    and is_time_reference_visit
                    and visit.uid != visit_vo.uid
                ):
                    raise ValueError(
                        f"There can be only one visit with the following visit type {visit_vo.visit_type.value} that works as time reference"
                    )

        reference_found = False
        if (
            not is_first_reference_visit
            and not is_time_reference_visit
            and visit_vo.visit_class
            not in (
                VisitClass.NON_VISIT,
                VisitClass.UNSCHEDULED_VISIT,
            )
        ):
            reference_name = StudyVisitTimeReference[visit_input.timeReferenceUid]
            for visit in timeline._visits:
                if visit.visit_type.value == reference_name.value:
                    reference_found = True
            if not reference_found and reference_name.value.lower() not in [
                PREVIOUS_VISIT_NAME.lower(),
                GLOBAL_ANCHOR_VISIT_NAME.lower(),
            ]:
                raise ValueError(
                    f"Time reference of type: {visit_vo.timepoint.visit_timereference.value} wasn't used by previous visits as visit type"
                )

        if visit_vo.is_global_anchor_visit:
            if visit_vo.timepoint.visit_value != 0:
                raise ValueError("The global anchor visit must take place at day 0.")
            if create:
                for visit in timeline._visits:
                    if visit.is_global_anchor_visit:
                        raise ValueError("There can be only one global anchor visit")

        if visit_vo.visit_class not in (
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ):
            if create:
                timeline.add_visit(visit_vo)
                ordered_visits = timeline.ordered_study_visits

                for index, visit in enumerate(ordered_visits):
                    if (
                        visit.get_absolute_duration()
                        == visit_vo.get_absolute_duration()
                        and visit.uid != visit_vo.uid
                    ):
                        raise ValueError(
                            f"There already exists a visit with timing set to {visit.timepoint.visit_value}"
                        )
                    if index + 2 < len(ordered_visits):
                        # we check whether the created visit is not from the epoch that sits
                        # out of the epoch schedule
                        if visit.epoch.order > ordered_visits[
                            index + 2
                        ].epoch.order and ordered_visits[index + 2].visit_class not in (
                            VisitClass.NON_VISIT,
                            VisitClass.UNSCHEDULED_VISIT,
                        ):
                            raise ValueError(
                                f"Visit with study day {visit.study_day_number} from "
                                f"epoch with order ({visit.epoch.order}) ({visit.epoch.epoch.value}) is out of order with "
                                f"visit with study day {ordered_visits[index+2].study_day_number} from epoch with order "
                                f"({ordered_visits[index+2].epoch.order}) ({ordered_visits[index+2].epoch.epoch.value})"
                            )
            if not preview:
                study_epochs = (
                    self._repos.study_epoch_repository.find_all_epochs_by_study(
                        study_uid=visit_vo.study_uid
                    )
                )
                timeline.collect_visits_to_epochs(study_epochs)

                for epoch in study_epochs:
                    if epoch.uid == visit_input.study_epoch_uid:
                        if epoch.previous_visit:
                            if (
                                visit_vo.get_absolute_duration()
                                < epoch.previous_visit.get_absolute_duration()
                            ):
                                raise ValueError(
                                    f"The following visit can't be created as previous epoch ({epoch.previous_visit.epoch.epoch.value}) "
                                    f"ends at the {epoch.previous_visit.study_day_number} study day"
                                )
                        if epoch.next_visit:
                            if (
                                visit_vo.get_absolute_duration()
                                > epoch.next_visit.get_absolute_duration()
                            ):
                                raise ValueError(
                                    f"The following visit can't be created as the next epoch ({epoch.next_visit.epoch.epoch.value}) "
                                    f"starts at the {epoch.next_visit.study_day_number} study day"
                                )
            if create:
                timeline.remove_visit(visit_vo)

        if visit_input.visitSubLabelCodelistUid:
            if visit_input.visitSubLabelCodelistUid not in self.study_visit_sublabels:
                raise ValueError("Visit Sub Label codelist is not used properly")
        if visit_input.visitContactModeUid not in self.study_visit_contact_mode:
            raise ValueError(
                f"The following CTTerm identified by uid {visit_input.visitContactModeUid} is not a valid"
                f"Visit Contact Mode term."
            )

    def _get_sponsor_library_vo(self):
        lib = self._repos.library_repository.find_by_name(name="Sponsor")
        return LibraryVO.from_input_values_2(
            library_name=lib.library_name,
            is_library_editable_callback=lambda _: lib.is_editable,
        )

    def _create_visit_name_simple_concept(self, visit_name: str):

        visit_name_ar = VisitNameAR.from_input_values(
            author=self.author,
            simple_concept_vo=VisitNameVO.from_repository_values(
                name=visit_name,
                name_sentence_case=visit_name.lower(),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.numeric_value_repository.generate_uid,
            find_uid_by_name_callback=self._repos.numeric_value_repository.find_uid_by_name,
        )
        self._repos.visit_name_repository.save(visit_name_ar)
        visit_name = TextValue(uid=visit_name_ar.uid, name=visit_name_ar.name)
        return visit_name

    def _create_numeric_value_simple_concept(
        self, value: int, numeric_value_type: NumericValueType
    ):
        if numeric_value_type == NumericValueType.NUMERIC_VALUE:
            aggregate_class = NumericValueAR
            value_object_class = NumericValueVO
            repository_class = self._repos.numeric_value_repository
        elif numeric_value_type == NumericValueType.STUDY_DAY:
            aggregate_class = StudyDayAR
            value_object_class = StudyDayVO
            repository_class = self._repos.study_day_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_DAYS:
            aggregate_class = StudyDurationDaysAR
            value_object_class = StudyDurationDaysVO
            repository_class = self._repos.study_duration_days_repository
        elif numeric_value_type == NumericValueType.STUDY_WEEK:
            aggregate_class = StudyWeekAR
            value_object_class = StudyWeekVO
            repository_class = self._repos.study_week_repository
        elif numeric_value_type == NumericValueType.STUDY_DURATION_WEEKS:
            aggregate_class = StudyDurationWeeksAR
            value_object_class = StudyDurationWeeksVO
            repository_class = self._repos.study_duration_weeks_repository
        else:
            raise ValueError(
                f"Unknown numeric value type to create {numeric_value_type.value}"
            )

        numeric_ar = aggregate_class.from_input_values(
            author=self.author,
            simple_concept_vo=value_object_class.from_input_values(
                value=float(value),
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.numeric_value_repository.generate_uid,
            find_uid_by_name_callback=self._repos.numeric_value_repository.find_uid_by_name,
        )
        repository_class.save(numeric_ar)
        numeric_value_object = NumericValue(
            uid=numeric_ar.uid, value=numeric_ar.concept_vo.value
        )
        return numeric_value_object

    def _create_timepoint_simple_concept(
        self, study_visit_input: StudyVisitCreateInput
    ):

        numeric_ar = self._create_numeric_value_simple_concept(
            value=study_visit_input.timeValue,
            numeric_value_type=NumericValueType.NUMERIC_VALUE,
        )
        timepoint_ar = TimePointAR.from_input_values(
            author=self.author,
            simple_concept_vo=TimePointVO.from_input_values(
                name_sentence_case=None,
                definition=None,
                abbreviation=None,
                is_template_parameter=True,
                numeric_value_uid=numeric_ar.uid,
                unit_definition_uid=study_visit_input.timeUnitUid,
                time_reference_uid=study_visit_input.timeReferenceUid,
                find_numeric_value_by_uid=self._repos.numeric_value_repository.find_by_uid_2,
                find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
                find_time_reference_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            ),
            library=self._get_sponsor_library_vo(),
            generate_uid_callback=self._repos.time_point_repository.generate_uid,
            find_uid_by_name_callback=self._repos.time_point_repository.find_uid_by_name,
        )
        self._repos.time_point_repository.save(timepoint_ar)
        timepoint_object = TimePoint(
            uid=timepoint_ar.uid,
            visit_timereference=StudyVisitTimeReference[
                study_visit_input.timeReferenceUid
            ],
            time_unit_uid=study_visit_input.timeUnitUid,
            visit_value=study_visit_input.timeValue,
        )
        return timepoint_object

    def _from_input_values(
        self, create_input: StudyVisitCreateInput, epoch: StudyEpochVO
    ):
        unit_repository = self._repos.unit_definition_repository
        if create_input.timeUnitUid:
            req_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.timeUnitUid
            )
            req_time_unit = req_time_unit_ar.concept_vo
        else:
            req_time_unit = None
        if create_input.visitWindowUnitUid:
            window_time_unit_ar: UnitDefinitionAR = unit_repository.find_by_uid_2(
                create_input.visitWindowUnitUid
            )
            window_time_unit = window_time_unit_ar.concept_vo
            window_unit_object = TimeUnit(
                name=window_time_unit.name,
                conversion_factor_to_master=window_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            window_unit_object = None
        if (
            create_input.visitSubLabelCodelistUid != ""
            and create_input.visitSubLabelCodelistUid is not None
        ):
            visit_sublabel = self.study_visit_sublabels[
                create_input.visitSubLabelCodelistUid
            ]
        else:
            visit_sublabel = None

        if req_time_unit:
            time_unit_object = TimeUnit(
                name=req_time_unit.name,
                conversion_factor_to_master=req_time_unit.conversion_factor_to_master,
                from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
            )
        else:
            time_unit_object = None
        day_unit_object = TimeUnit(
            name="day",
            conversion_factor_to_master=self._day_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

        week_unit_object = TimeUnit(
            name="Week",
            conversion_factor_to_master=self._week_unit.concept_vo.conversion_factor_to_master,
            from_timedelta=lambda u, x: u.conversion_factor_to_master * x,
        )

        study_visit_vo = StudyVisitVO(
            legacy_visit_id=create_input.legacyVisitId,
            legacy_visit_type_alias=create_input.legacyVisitTypeAlias,
            legacy_name=create_input.legacyName,
            legacy_sub_name=create_input.legacySubName,
            visit_sub_label=visit_sublabel,
            visit_sub_label_uid=create_input.visitSubLabelCodelistUid,
            visit_sub_label_reference=create_input.visitSubLabelReference,
            consecutive_visit_group=create_input.consecutiveVisitGroup,
            show_visit=create_input.show_visit,
            visit_window_min=create_input.minVisitWindowValue,
            visit_window_max=create_input.maxVisitWindowValue,
            window_unit_uid=create_input.visitWindowUnitUid,
            window_unit_object=window_unit_object,
            time_unit_object=time_unit_object,
            description=create_input.description,
            start_rule=create_input.startRule,
            end_rule=create_input.endRule,
            note=create_input.note,
            visit_contact_mode=StudyVisitContactMode[create_input.visitContactModeUid],
            epoch_allocation=StudyVisitEpochAllocation[create_input.epochAllocationUid]
            if create_input.epochAllocationUid
            else None,
            visit_type=StudyVisitType[create_input.visitTypeUid],
            start_date=datetime.datetime.now(),
            author=self.author,
            status=StudyStatus.DRAFT,
            day_unit_object=day_unit_object,
            week_unit_object=week_unit_object,
            epoch_connector=epoch,
            visit_class=VisitClass[create_input.visitClass],
            visit_subclass=VisitSubclass[create_input.visitSubclass]
            if create_input.visitSubclass
            else None,
            is_global_anchor_visit=create_input.isGlobalAnchorVisit,
            visit_number=1,
            visit_order=1,
        )
        if study_visit_vo.visit_class not in [
            VisitClass.NON_VISIT,
            VisitClass.UNSCHEDULED_VISIT,
        ]:
            study_visit_vo.timepoint = self._create_timepoint_simple_concept(
                study_visit_input=create_input
            )
            study_visit_vo.study_day = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_day_number(),
                numeric_value_type=NumericValueType.STUDY_DAY,
            )
            study_visit_vo.study_duration_days = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_days_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_DAYS,
                )
            )
            study_visit_vo.study_week = self._create_numeric_value_simple_concept(
                value=study_visit_vo.derive_study_week_number(),
                numeric_value_type=NumericValueType.STUDY_WEEK,
            )
            study_visit_vo.study_duration_weeks = (
                self._create_numeric_value_simple_concept(
                    value=study_visit_vo.derive_study_duration_weeks_number(),
                    numeric_value_type=NumericValueType.STUDY_DURATION_WEEKS,
                )
            )
        return study_visit_vo

    def synchronize_visit_numbers(
        self, ordered_visits: Sequence, start_index_to_synchronize: int
    ):
        """
        Fixes the visit number if some visit was added in between of others or some of the visits were removed, edited.
        :param ordered_visits:
        :param start_index_to_synchronize:
        :return:
        """
        for visit in ordered_visits[start_index_to_synchronize:]:
            self.assign_props_derived_from_visit_number(study_visit=visit)
            self.repo.save(visit)

    def assign_props_derived_from_visit_number(self, study_visit: StudyVisitVO):
        """
        Assigns some properties of StudyVisitVO that are derived from Visit Number.
        Visit Number property is not assigned when we create StudyVisitVO.
        It's done later as we need to derive VisitNumber from the order of given Visit in a sequence of all Study Visits.
        This is why we need to initialize some of the properties later then creation of StudyVisitVO.
        :param study_visit:
        :return:
        """
        study_visit.visit_name_sc = self._create_visit_name_simple_concept(
            visit_name=study_visit.derive_visit_name()
        )

    @db.transaction
    def create(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        try:
            study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

            epoch = self._repos.study_epoch_repository.find_by_uid(
                uid=study_visit_input.study_epoch_uid
            )
            study_visit = self._from_input_values(study_visit_input, epoch)
            timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
            self._validate_visit(study_visit_input, study_visit, timeline, create=True)
            self.assign_props_derived_from_visit_number(study_visit=study_visit)
            added_item = self.repo.save(study_visit)

            timeline.add_visit(added_item)

            ordered_visits = timeline.ordered_study_visits
            # if added item is not last in ordered_study_visits, then we have to synchronize Visit Numbers
            if added_item.uid != ordered_visits[-1].uid:
                self.synchronize_visit_numbers(
                    ordered_visits=ordered_visits,
                    start_index_to_synchronize=added_item.visit_number,
                )
            ordered_visits_without_added = [
                vis for vis in ordered_visits if vis.uid != added_item.uid
            ]
            sorted_study_visits = sorted(study_visits, key=lambda item: item.uid)
            sorted_study_visits_without_added = sorted(
                ordered_visits_without_added, key=lambda item: item.uid
            )
            for visit_bef_add, visit_aft_add in zip(
                sorted_study_visits, sorted_study_visits_without_added
            ):
                if (
                    visit_bef_add.unique_visit_number
                    != visit_aft_add.unique_visit_number
                ):
                    self.repo.save(visit_aft_add)
            return self._transform_all_to_response_model(added_item)
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

    @db.transaction
    def preview(self, study_uid: str, study_visit_input: StudyVisitCreateInput):
        try:
            study_visits = self.repo.find_all_visits_by_study_uid(study_uid)

            epoch = self._repos.study_epoch_repository.find_by_uid(
                uid=study_visit_input.study_epoch_uid
            )
            study_visit = self._from_input_values(study_visit_input, epoch)
            timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
            self._validate_visit(
                study_visit_input, study_visit, timeline, create=True, preview=True
            )

            study_visit.uid = "preview"
            timeline.add_visit(study_visit)

            return self._transform_all_to_response_model(study_visit)
        except ValueError as e:
            raise ValidationException(e.args[0]) from e

    @db.transaction
    def edit(
        self,
        study_uid: str,
        study_visit_uid: str,
        study_visit_input: StudyVisitEditInput,
    ):
        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        study_visit = self.repo.find_by_uid(study_visit_uid)

        epoch = self._repos.study_epoch_repository.find_by_uid(
            uid=study_visit_input.study_epoch_uid
        )
        updated_visit = self._from_input_values(study_visit_input, epoch)
        update_dict = {
            k: v
            for k, v in dataclasses.asdict(updated_visit).items()
            if k not in ["uid"]
        }
        update_dict["time_unit_object"] = updated_visit.time_unit_object
        update_dict["window_unit_object"] = updated_visit.window_unit_object
        update_dict["day_unit_object"] = updated_visit.day_unit_object
        update_dict["week_unit_object"] = updated_visit.week_unit_object
        update_dict["timepoint"] = updated_visit.timepoint
        update_dict["study_day"] = updated_visit.study_day
        update_dict["study_duration_days"] = updated_visit.study_duration_days
        update_dict["study_duration_weeks"] = updated_visit.study_duration_weeks
        update_dict["study_week"] = updated_visit.study_week
        update_dict["visit_name_sc"] = updated_visit.visit_name_sc

        new_study_visit = dataclasses.replace(study_visit, **update_dict)
        new_study_visit.epoch_connector = epoch

        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        timeline.update_visit(new_study_visit)

        self._validate_visit(study_visit_input, study_visit, timeline, create=False)

        ordered_visits = timeline.ordered_study_visits

        # If Visit Number was edited, then we have to synchronize the Visit Numbers in the database
        if study_visit.visit_number != new_study_visit.visit_number:
            if new_study_visit.visit_number < study_visit.visit_number:
                start_index_to_sync = new_study_visit.visit_number - 1
            else:
                start_index_to_sync = study_visit.visit_number - 1
            self.synchronize_visit_numbers(
                ordered_visits=ordered_visits,
                start_index_to_synchronize=start_index_to_sync,
            )
        self.assign_props_derived_from_visit_number(study_visit=new_study_visit)

        self.repo.save(new_study_visit)

        return self._transform_all_to_response_model(new_study_visit)

    @db.transaction
    def delete(self, study_uid: str, study_visit_uid: str):
        study = self._repos.study_definition_repository.find_by_uid(uid=study_uid)
        if study.current_metadata.ver_metadata.study_status != StudyStatus.DRAFT:
            raise ValueError("Cannot delete visits in non DRAFT study")
        study_visit = self.repo.find_by_uid(study_visit_uid)
        if study_visit.status != StudyStatus.DRAFT:
            raise ValueError("Cannot delete visits non DRAFT status")
        study_visit.delete()

        self.repo.save(study_visit)

        study_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        ordered_visits = timeline.ordered_study_visits

        # we want to synchronize numbers if we have more than one visit
        if len(ordered_visits) > 0:
            # After removing specific visit if it was not the last visit,
            # we have to synchronize the Visit Numbers to fill in the gap
            if study_visit.uid != ordered_visits[-1].uid:
                self.synchronize_visit_numbers(
                    ordered_visits=ordered_visits,
                    start_index_to_synchronize=study_visit.visit_number - 1,
                )

    @db.transaction
    def get_consecutive_groups(self, study_uid: str):
        all_visits = self.repo.find_all_visits_by_study_uid(study_uid)
        groups = [
            visit.consecutive_visit_group
            for visit in all_visits
            if visit.consecutive_visit_group is not None
        ]
        groups_set = set(groups)
        return groups_set

    @db.transaction
    def audit_trail(
        self,
        visit_uid: str,
        study_uid: str,
    ) -> Sequence[StudyVisitVersion]:
        all_versions = self.repo.get_all_versions(visit_uid, study_uid=study_uid)
        versions = [
            self._transform_all_to_history_model(_).dict() for _ in all_versions
        ]
        data = calculate_diffs(versions, StudyVisitVersion)
        return data

    @db.transaction
    def audit_trail_all_visits(
        self,
        study_uid: str,
    ) -> Sequence[StudyVisitVersion]:
        data = calculate_diffs_history(
            get_all_object_versions=self.repo.get_all_visit_versions,
            transform_all_to_history_model=self._transform_all_to_history_model,
            study_uid=study_uid,
            version_object_class=StudyVisitVersion,
        )
        return data
