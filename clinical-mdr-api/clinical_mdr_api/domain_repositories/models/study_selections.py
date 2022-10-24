from neomodel import (
    BooleanProperty,
    IntegerProperty,
    One,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.activities import ActivityValue
from clinical_mdr_api.domain_repositories.models.activity_instruction import (
    ActivityInstructionValue,
)
from clinical_mdr_api.domain_repositories.models.compounds import CompoundAliasValue
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValueWithUnitRoot,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.criteria import CriteriaValue
from clinical_mdr_api.domain_repositories.models.criteria_template import (
    CriteriaTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.endpoint import EndpointValue
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNodeWithUID,
    ClinicalMdrRel,
    Conjunction,
    ConjunctionRelation,
)
from clinical_mdr_api.domain_repositories.models.objective import ObjectiveValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.timeframe import TimeframeValue


class AuditTrailMixin:
    """Mixin class to provide audit trail required relations."""

    has_before = RelationshipFrom(StudyAction, "BEFORE", model=ConjunctionRelation)
    has_after = RelationshipFrom(StudyAction, "AFTER", model=ConjunctionRelation)


class StudySelection(ClinicalMdrNodeWithUID, AuditTrailMixin):
    order = IntegerProperty()
    accepted_version = BooleanProperty()


class StudyObjective(StudySelection):
    has_selected_objective = RelationshipTo(
        ObjectiveValue, "HAS_SELECTED_OBJECTIVE", model=ClinicalMdrRel
    )
    has_objective_level = RelationshipTo(
        CTTermRoot, "HAS_OBJECTIVE_LEVEL", model=ClinicalMdrRel
    )
    study_endpoint_has_study_objective = RelationshipFrom(
        "StudyEndpoint", "STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE", model=ClinicalMdrRel
    )


class StudyEndpointUnitRel(ClinicalMdrRel):
    index = IntegerProperty()


class StudyEndpoint(StudySelection):
    __optional_labels__ = ["TemplateParameterValueRoot"]
    text = StringProperty()
    study_endpoint_has_study_objective = RelationshipTo(
        StudyObjective, "STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE", model=ClinicalMdrRel
    )
    has_selected_endpoint = RelationshipTo(
        EndpointValue, "HAS_SELECTED_ENDPOINT", model=ClinicalMdrRel
    )
    has_selected_timeframe = RelationshipTo(
        TimeframeValue, "HAS_SELECTED_TIMEFRAME", model=ClinicalMdrRel
    )
    has_endpoint_level = RelationshipTo(
        CTTermRoot, "HAS_ENDPOINT_LEVEL", model=ClinicalMdrRel
    )
    has_endpoint_sub_level = RelationshipTo(
        CTTermRoot, "HAS_ENDPOINT_SUB_LEVEL", model=ClinicalMdrRel
    )
    has_unit = RelationshipTo(
        UnitDefinitionRoot, "HAS_UNIT", model=StudyEndpointUnitRel
    )
    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class StudyCompound(StudySelection):
    other_information = StringProperty()
    has_selected_compound = RelationshipTo(
        CompoundAliasValue, "HAS_SELECTED_COMPOUND", model=ClinicalMdrRel
    )
    has_type_of_treatment = RelationshipTo(
        CTTermRoot, "HAS_TYPE_OF_TREATMENT", model=ClinicalMdrRel
    )
    has_route_of_administration = RelationshipTo(
        CTTermRoot, "HAS_ROUTE_OF_ADMINISTRATION", model=ClinicalMdrRel
    )
    has_strength_value = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_STRENGTH_VALUE", model=ClinicalMdrRel
    )
    has_dosage_form = RelationshipTo(
        CTTermRoot, "HAS_DOSAGE_FORM", model=ClinicalMdrRel
    )
    has_suspended_in = RelationshipTo(
        CTTermRoot, "HAS_DISPENSED_IN", model=ClinicalMdrRel
    )
    has_device = RelationshipTo(CTTermRoot, "HAS_DEVICE", model=ClinicalMdrRel)
    has_formulation = RelationshipTo(
        CTTermRoot, "HAS_FORMULATION", model=ClinicalMdrRel
    )
    has_reason_for_missing = RelationshipTo(
        CTTermRoot, "HAS_REASON_FOR_NULL_VALUE", model=ClinicalMdrRel
    )


class StudyCriteria(StudySelection):
    has_selected_criteria = RelationshipTo(
        CriteriaValue, "HAS_SELECTED_CRITERIA", model=ClinicalMdrRel
    )
    has_selected_criteria_template = RelationshipTo(
        CriteriaTemplateValue, "HAS_SELECTED_CRITERIA_TEMPLATE", model=ClinicalMdrRel
    )
    key_criteria = BooleanProperty(default=False)


class StudyActivity(StudySelection):

    has_study_activity = RelationshipFrom(".study.StudyValue", "HAS_STUDY_ACTIVITY")
    has_selected_activity = RelationshipTo(
        ActivityValue, "HAS_SELECTED_ACTIVITY", model=ClinicalMdrRel
    )
    has_flowchart_group = RelationshipTo(
        CTTermRoot, "HAS_FLOWCHART_GROUP", model=ClinicalMdrRel
    )

    show_activity_group_in_protocol_flowchart = BooleanProperty(default=True)
    show_activity_subgroup_in_protocol_flowchart = BooleanProperty(default=True)
    show_activity_in_protocol_flowchart = BooleanProperty(default=False)
    note = StringProperty()


class StudyActivitySchedule(ClinicalMdrNodeWithUID, AuditTrailMixin):
    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_ACTIVITY_SCHEDULE")
    study_activity = RelationshipFrom(
        StudyActivity, "STUDY_ACTIVITY_HAS_SCHEDULE", model=ClinicalMdrRel
    )
    study_visit = RelationshipFrom(
        ".study_visit.StudyVisit", "STUDY_VISIT_HAS_SCHEDULE", model=ClinicalMdrRel
    )

    note = StringProperty()


class StudyDesignCell(ClinicalMdrNodeWithUID, AuditTrailMixin):
    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_DESIGN_CELL")
    study_arm = RelationshipFrom(
        ".study_selections.StudyArm",
        "STUDY_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    study_branch_arm = RelationshipFrom(
        ".study_selections.StudyBranchArm",
        "STUDY_BRANCH_ARM_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=ZeroOrOne,
    )
    study_epoch = RelationshipFrom(
        ".study_epoch.StudyEpoch",
        "STUDY_EPOCH_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    study_element = RelationshipFrom(
        ".study_selections.StudyElement",
        "STUDY_ELEMENT_HAS_DESIGN_CELL",
        model=ClinicalMdrRel,
        cardinality=One,
    )

    transition_rule = StringProperty()
    order = IntegerProperty()


class StudyArm(StudySelection):

    name = StringProperty()
    short_name = StringProperty()
    arm_code = StringProperty()
    description = StringProperty()
    arm_colour = StringProperty()
    randomization_group = StringProperty()
    number_of_subjects = IntegerProperty()

    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_ARM")

    arm_type = RelationshipTo(CTTermRoot, "HAS_ARM_TYPE", model=ClinicalMdrRel)
    has_design_cell = RelationshipTo(
        StudyDesignCell, "STUDY_ARM_HAS_DESIGN_CELL", model=ClinicalMdrRel
    )
    has_branch_arm = RelationshipTo(
        ".study_selections.StudyBranchArm",
        "STUDY_ARM_HAS_BRANCH_ARM",
        model=ClinicalMdrRel,
    )
    has_cohort = RelationshipTo(
        ".study_selections.StudyCohort", "STUDY_ARM_HAS_COHORT", model=ClinicalMdrRel
    )


class StudyElement(StudySelection):
    name = StringProperty()
    short_name = StringProperty()
    element_code = StringProperty()
    description = StringProperty()
    planned_duration = StringProperty()
    start_rule = StringProperty()
    end_rule = StringProperty()
    element_colour = StringProperty()
    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_ELEMENT")
    element_subtype = RelationshipTo(
        CTTermRoot, "HAS_ELEMENT_SUBTYPE", model=ClinicalMdrRel
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell, "STUDY_ELEMENT_HAS_DESIGN_CELL", model=ClinicalMdrRel
    )


class StudyActivityInstruction(AuditTrailMixin, ClinicalMdrNodeWithUID):
    study_value = RelationshipFrom(
        ".study.StudyValue", "HAS_STUDY_ACTIVITY_INSTRUCTION"
    )
    study_activity = RelationshipFrom(
        StudyActivity, "STUDY_ACTIVITY_HAS_INSTRUCTION", model=ClinicalMdrRel
    )
    activity_instruction_value = RelationshipFrom(
        ActivityInstructionValue,
        "HAS_SELECTED_ACTIVITY_INSTRUCTION",
        model=ClinicalMdrRel,
    )


class StudyBranchArm(StudySelection):

    name = StringProperty()
    short_name = StringProperty()
    branch_arm_code = StringProperty()
    description = StringProperty()
    colour_code = StringProperty()
    randomization_group = StringProperty()
    number_of_subjects = IntegerProperty()
    order = StringProperty()

    study_value = RelationshipFrom(
        ".study.StudyValue", "HAS_STUDY_BRANCH_ARM", model=ClinicalMdrRel
    )
    has_design_cell = RelationshipTo(
        StudyDesignCell, "STUDY_BRANCH_ARM_HAS_DESIGN_CELL", model=ClinicalMdrRel
    )
    has_cohort = RelationshipTo(
        ".study_selections.StudyCohort",
        "STUDY_BRANCH_ARM_HAS_COHORT",
        model=ClinicalMdrRel,
    )
    arm_root = RelationshipFrom(
        StudyArm, "STUDY_ARM_HAS_BRANCH_ARM", model=ClinicalMdrRel
    )


class StudyCohort(StudySelection):

    name = StringProperty()
    short_name = StringProperty()
    cohort_code = StringProperty()
    description = StringProperty()
    colour_code = StringProperty()
    number_of_subjects = IntegerProperty()

    study_value = RelationshipFrom(
        ".study.StudyValue", "HAS_STUDY_COHORT", model=ClinicalMdrRel
    )
    arm_root = RelationshipFrom(StudyArm, "STUDY_ARM_HAS_COHORT", model=ClinicalMdrRel)
    branch_arm_root = RelationshipFrom(
        StudyBranchArm, "STUDY_BRANCH_ARM_HAS_COHORT", model=ClinicalMdrRel
    )


class StudyCompoundDosing(StudySelection):

    study_value = RelationshipFrom(".study.StudyValue", "HAS_STUDY_COMPOUND_DOSING")

    has_dose_frequency = RelationshipTo(
        CTTermRoot, "HAS_DOSE_FREQUENCY", cardinality=ZeroOrOne
    )
    has_dose_value = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_DOSE_VALUE", cardinality=ZeroOrOne
    )
    study_compound = RelationshipFrom(
        StudyCompound, "STUDY_COMPOUND_HAS_COMPOUND_DOSING", model=ClinicalMdrRel
    )
    study_element = RelationshipFrom(
        StudyElement, "STUDY_ELEMENT_HAS_COMPOUND_DOSING", model=ClinicalMdrRel
    )
