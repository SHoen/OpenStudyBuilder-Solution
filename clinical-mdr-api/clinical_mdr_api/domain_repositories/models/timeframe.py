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
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)
from clinical_mdr_api.domain_repositories.models.timeframe_template import (
    TimeframeTemplateRoot,
)


class TimeframeValue(VersionValue):
    PARAMETERS_LABEL = "TV_USES_VALUE"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_TIMEFRAME"
    STUDY_VALUE_REL_LABEL = "HAS_SELECTED_TIMEFRAME"

    name = StringProperty()
    name_plain = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class TimeframeRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_TIMEFRAME"
    TEMPLATE_REL_LABEL = "HAS_TIMEFRAME"
    uid_prefix = "Timeframe_"

    has_template = RelationshipFrom(TimeframeTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        TimeframeValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(TimeframeValue, "LATEST")
    latest_draft = RelationshipTo(
        TimeframeValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        TimeframeValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        TimeframeValue, "LATEST_RETIRED", model=VersionRelationship
    )
