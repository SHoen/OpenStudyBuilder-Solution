from neomodel import (
    BooleanProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
)

from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    ConjunctionRelation,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignCell,
    StudySelection,
)


class OrderedStudySelection(StudySelection):
    accepted_version = BooleanProperty()
    order = IntegerProperty()


class StudyEpoch(OrderedStudySelection):
    has_study_epoch = RelationshipFrom(StudyValue, "HAS_STUDY_EPOCH")
    has_epoch = RelationshipTo(CTTermRoot, "HAS_EPOCH")
    has_epoch_subtype = RelationshipTo(CTTermRoot, "HAS_EPOCH_SUB_TYPE")
    has_epoch_type = RelationshipTo(CTTermRoot, "HAS_EPOCH_TYPE")
    has_duration_unit = RelationshipTo(UnitDefinitionRoot, "HAS_DURATION_UNIT")
    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_EPOCH")

    name = StringProperty()
    short_name = StringProperty()
    description = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    order = IntegerProperty()
    color_hash = StringProperty()
    status = StringProperty()
    is_deleted = BooleanProperty()
    has_design_cell = RelationshipTo(
        StudyDesignCell, "STUDY_EPOCH_HAS_DESIGN_CELL", model=ClinicalMdrRel
    )
    has_study_visit = RelationshipTo(
        ".study_visit.StudyVisit", "STUDY_EPOCH_HAS_STUDY_VISIT", model=ClinicalMdrRel
    )
    has_before = RelationshipFrom(StudyAction, "BEFORE", model=ConjunctionRelation)
    has_after = RelationshipFrom(StudyAction, "AFTER", model=ConjunctionRelation)
