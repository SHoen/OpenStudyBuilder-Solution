from neomodel import RelationshipFrom, RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.activity_description_template import (
    ActivityDescriptionTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Conjunction,
    ConjunctionRelation,
    Library,
    ObjectUsesParameterRelation,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)


class ActivityInstructionValue(VersionValue):
    ROOT_NODE_LABEL = "ActivityInstructionRoot"
    VALUE_NODE_LABEL = "ActivityInstructionValue"
    PARAMETERS_LABEL = "OV_USES_VALUE"  # FIXME: rename
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_ACTIVITY_INSTRUCTION"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ACTIVITY_INSTRUCTION"

    name = StringProperty()
    name_plain = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )

    activity_instruction_root = RelationshipFrom("ActivityInstructionRoot", "LATEST")


class ActivityInstructionRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ACTIVITY_INSTRUCTION"
    TEMPLATE_REL_LABEL = "HAS_ACTIVITY_DESCRIPTION"  # FIXME: rename

    has_template = RelationshipFrom(ActivityDescriptionTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        ActivityInstructionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityInstructionValue, "LATEST")
    latest_draft = RelationshipTo(
        ActivityInstructionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityInstructionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityInstructionValue, "LATEST_RETIRED", model=VersionRelationship
    )
