from neomodel import RelationshipFrom, RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.criteria_template import (
    CriteriaTemplateRoot,
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


class CriteriaValue(VersionValue):
    ROOT_NODE_LABEL = "CriteriaRoot"
    VALUE_NODE_LABEL = "CriteriaValue"
    PARAMETERS_LABEL = "OV_USES_VALUE"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_CRITERIA"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_CRITERIA"

    name = StringProperty()
    name_plain = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class CriteriaRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_CRITERIA"
    TEMPLATE_REL_LABEL = "HAS_CRITERIA"

    has_template = RelationshipFrom(CriteriaTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        CriteriaValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CriteriaValue, "LATEST")
    latest_draft = RelationshipTo(
        CriteriaValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        CriteriaValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        CriteriaValue, "LATEST_RETIRED", model=VersionRelationship
    )
