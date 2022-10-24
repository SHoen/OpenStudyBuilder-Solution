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


class ActivityDescriptionValue(VersionValue):
    PARAMETERS_LABEL = "OV_USES_VALUE"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_ACTIVITY_DESCRIPTION"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ACTIVITY_DESCRIPTION"

    name = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class ActivityDescriptionRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ACTIVITY_DESCRIPTION"
    TEMPLATE_REL_LABEL = "HAS_ACTIVITY_DESCRIPTION"

    has_template = RelationshipFrom(ActivityDescriptionTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        ActivityDescriptionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityDescriptionValue, "LATEST")
    latest_draft = RelationshipTo(
        ActivityDescriptionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityDescriptionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityDescriptionValue, "LATEST_RETIRED", model=VersionRelationship
    )
