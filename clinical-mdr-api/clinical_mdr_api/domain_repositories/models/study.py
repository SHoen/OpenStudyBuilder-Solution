from neomodel import (  # pylint: disable=E0401 # type: ignore
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
)

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,  # type: ignore
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrNodeWithUID,
    ConjunctionRelation,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_field import (
    StudyArrayField,
    StudyBooleanField,
    StudyIntField,
    StudyProjectField,
    StudyTextField,
    StudyTimeField,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivityInstruction,
    StudyActivitySchedule,
    StudyArm,
    StudyBranchArm,
    StudyCohort,
    StudyCompound,
    StudyCompoundDosing,
    StudyCriteria,
    StudyDesignCell,
    StudyElement,
    StudyEndpoint,
    StudyObjective,
)


class StudyValue(ClinicalMdrNode):
    """
    Represents the data for a given version of the compound in the graph.
    Version information is stored on the relationship between the
    Compound Root and this node.
    """

    study_number = StringProperty()
    study_acronym = StringProperty()
    study_id_prefix = StringProperty()

    study_root = RelationshipFrom("StudyRoot", "LATEST")

    has_project = RelationshipTo(StudyProjectField, "HAS_PROJECT", model=ClinicalMdrRel)
    has_time_field = RelationshipTo(
        StudyTimeField, "HAS_TIME_FIELD", model=ClinicalMdrRel
    )
    has_text_field = RelationshipTo(
        StudyTextField, "HAS_TEXT_FIELD", model=ClinicalMdrRel
    )
    has_int_field = RelationshipTo(StudyIntField, "HAS_INT_FIELD", model=ClinicalMdrRel)
    has_array_field = RelationshipTo(
        StudyArrayField, "HAS_ARRAY_FIELD", model=ClinicalMdrRel
    )
    has_boolean_field = RelationshipTo(
        StudyBooleanField, "HAS_BOOLEAN_FIELD", model=ClinicalMdrRel
    )

    has_study_objective = RelationshipTo(
        StudyObjective, "HAS_STUDY_OBJECTIVE", model=ClinicalMdrRel
    )
    has_study_endpoint = RelationshipTo(
        StudyEndpoint, "HAS_STUDY_ENDPOINT", model=ClinicalMdrRel
    )
    has_study_compound = RelationshipTo(
        StudyCompound, "HAS_STUDY_COMPOUND", model=ClinicalMdrRel
    )
    has_study_compound_dosing = RelationshipTo(
        StudyCompoundDosing, "HAS_STUDY_COMPOUND_DOSING", model=ClinicalMdrRel
    )
    has_study_criteria = RelationshipTo(
        StudyCriteria, "HAS_STUDY_CRITERIA", model=ClinicalMdrRel
    )
    has_study_epoch = RelationshipTo(
        ".study_epoch.StudyEpoch", "HAS_STUDY_EPOCH", model=ClinicalMdrRel
    )
    has_study_visit = RelationshipTo(
        ".study_visit.StudyVisit", "HAS_STUDY_VISIT", model=ClinicalMdrRel
    )
    has_study_activity = RelationshipTo(
        StudyActivity, "HAS_STUDY_ACTIVITY", model=ClinicalMdrRel
    )
    has_study_activity_schedule = RelationshipTo(
        StudyActivitySchedule, "HAS_STUDY_ACTIVITY_SCHEDULE", model=ClinicalMdrRel
    )
    has_study_activity_instruction = RelationshipTo(
        StudyActivityInstruction, "HAS_STUDY_ACTIVITY_INSTRUCTION", model=ClinicalMdrRel
    )
    has_study_design_cell = RelationshipTo(
        StudyDesignCell, "HAS_STUDY_DESIGN_CELL", model=ClinicalMdrRel
    )

    has_latest = RelationshipFrom(ClinicalMdrNode, "LATEST", model=ClinicalMdrRel)

    has_study_arm = RelationshipTo(StudyArm, "HAS_STUDY_ARM", model=ClinicalMdrRel)

    has_study_element = RelationshipTo(
        StudyElement, "HAS_STUDY_ELEMENT", model=ClinicalMdrRel
    )

    has_study_branch_arm = RelationshipTo(
        StudyBranchArm, "HAS_STUDY_BRANCH_ARM", model=ClinicalMdrRel
    )

    has_study_cohort = RelationshipTo(
        StudyCohort, "HAS_STUDY_COHORT", model=ClinicalMdrRel
    )

    has_before = RelationshipFrom(StudyAction, "BEFORE", model=ConjunctionRelation)
    has_after = RelationshipFrom(StudyAction, "AFTER", model=ConjunctionRelation)
    latest_value = RelationshipFrom("StudyRoot", "LATEST", model=ClinicalMdrRel)


class StudyRoot(ClinicalMdrNodeWithUID):
    """
    Represents the root object for a given compound in the graph.
    May have several compound values (versions) connected to it.
    """

    has_version = RelationshipTo(StudyValue, "HAS_VERSION", model=VersionRelationship)
    latest_value = RelationshipTo(StudyValue, "LATEST", model=ClinicalMdrRel)
    latest_locked = RelationshipTo(
        StudyValue, "LATEST_LOCKED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(StudyValue, "LATEST_DRAFT", model=VersionRelationship)
    latest_released = RelationshipTo(
        StudyValue, "LATEST_RELEASED", model=VersionRelationship
    )
    audit_trail = RelationshipTo(StudyAction, "AUDIT_TRAIL", model=ClinicalMdrRel)
