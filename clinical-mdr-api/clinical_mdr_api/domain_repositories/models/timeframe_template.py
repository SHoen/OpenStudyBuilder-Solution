from neomodel import RelationshipFrom, RelationshipTo
from neomodel.properties import BooleanProperty

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    TemplateUsesParameterRelation,
    VersionRelationship,
    VersionRoot,
)
from clinical_mdr_api.domain_repositories.models.syntax_template import (
    SyntaxTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
)


class TimeframeTemplateValue(SyntaxTemplateValue):
    pass


class TimeframeTemplateRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_TIMEFRAME_TEMPLATE"
    PARAMETERS_LABEL = "TT_USES_PARAMETER"
    uid_prefix = "TimeframeTemplate_"
    TEMPLATE_REL_LABEL = "HAS_TIMEFRAME"

    editable_instance = BooleanProperty()

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_template = RelationshipTo(".timeframe.TimeframeRoot", TEMPLATE_REL_LABEL)

    has_parameters = RelationshipTo(
        TemplateParameter, PARAMETERS_LABEL, model=TemplateUsesParameterRelation
    )
    has_version = RelationshipTo(
        TimeframeTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(TimeframeTemplateValue, "LATEST")
    latest_draft = RelationshipTo(
        TimeframeTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        TimeframeTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        TimeframeTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )
