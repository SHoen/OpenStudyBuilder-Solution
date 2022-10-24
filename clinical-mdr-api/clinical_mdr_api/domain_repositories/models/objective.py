from neomodel import RelationshipFrom, RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.generic import (
    Conjunction,
    ConjunctionRelation,
    Library,
    ObjectUsesParameterRelation,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.objective_template import (
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)


class ObjectiveValue(VersionValue):
    ROOT_NODE_LABEL = "ObjectiveRoot"
    VALUE_NODE_LABEL = "ObjectiveValue"
    PARAMETERS_LABEL = "OV_USES_VALUE"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_OBJECTIVE"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_OBJECTIVE"

    name = StringProperty()
    name_plain = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class ObjectiveRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_OBJECTIVE"
    TEMPLATE_REL_LABEL = "HAS_OBJECTIVE"
    uid_prefix = "Objective_"

    has_template = RelationshipFrom(ObjectiveTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        ObjectiveValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ObjectiveValue, "LATEST")
    latest_draft = RelationshipTo(
        ObjectiveValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ObjectiveValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ObjectiveValue, "LATEST_RETIRED", model=VersionRelationship
    )
