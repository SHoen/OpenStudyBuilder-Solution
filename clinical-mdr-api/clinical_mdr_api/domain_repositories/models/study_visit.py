from neomodel import (
    BooleanProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
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
from clinical_mdr_api.domain_repositories.models.generic import ConjunctionRelation
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection


class StudyVisit(StudySelection):
    has_study_visit = RelationshipFrom(StudyValue, "HAS_STUDY_VISIT")
    study_epoch_has_study_visit = RelationshipFrom(
        StudyEpoch, "STUDY_EPOCH_HAS_STUDY_VISIT"
    )

    legacy_visit_id = StringProperty()
    legacy_visit_type_alias = StringProperty()
    legacy_name = StringProperty()
    legacy_sub_name = StringProperty()

    visit_number = IntegerProperty()

    has_visit_type = RelationshipTo(CTTermRoot, "HAS_VISIT_TYPE")

    visit_sub_label = StringProperty()
    visit_sub_label_uid = StringProperty()
    visit_sub_label_reference = StringProperty()

    visit_name_label = StringProperty()
    short_visit_label = StringProperty()
    unique_visit_number = StringProperty()
    consecutive_visit_group = StringProperty()
    show_visit = BooleanProperty()

    visit_window_min = IntegerProperty()
    visit_window_max = IntegerProperty()

    has_window_unit = RelationshipTo(UnitDefinitionRoot, "HAS_WINDOW_UNIT")

    description = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    note = StringProperty()
    has_visit_contact_mode = RelationshipTo(CTTermRoot, "HAS_VISIT_CONTACT_MODE")
    has_epoch_allocation = RelationshipTo(CTTermRoot, "HAS_EPOCH_ALLOCATION")
    is_deleted = BooleanProperty()
    is_global_anchor_visit = BooleanProperty()
    status = StringProperty()
    visit_class = StringProperty()
    visit_subclass = StringProperty()

    has_timepoint = RelationshipTo(TimePointRoot, "HAS_TIMEPOINT")
    has_study_day = RelationshipTo(StudyDayRoot, "HAS_STUDY_DAY")
    has_study_duration_days = RelationshipTo(
        StudyDurationDaysRoot, "HAS_STUDY_DURATION_DAYS"
    )
    has_study_week = RelationshipTo(StudyWeekRoot, "HAS_STUDY_WEEK")
    has_study_duration_weeks = RelationshipTo(
        StudyDurationWeeksRoot, "HAS_STUDY_DURATION_WEEKS"
    )
    has_visit_name = RelationshipTo(VisitNameRoot, "HAS_VISIT_NAME")

    has_before = RelationshipFrom(StudyAction, "BEFORE", model=ConjunctionRelation)
    has_after = RelationshipFrom(StudyAction, "AFTER", model=ConjunctionRelation)
