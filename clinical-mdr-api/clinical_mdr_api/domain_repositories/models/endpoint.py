from neomodel import RelationshipFrom, RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.endpoint_template import (
    EndpointTemplateRoot,
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


class EndpointValue(VersionValue):
    __optional_labels__ = ["TemplateParameterValue"]
    ROOT_NODE_LABEL = "EndpointRoot"
    VALUE_NODE_LABEL = "EndpointValue"
    PARAMETERS_LABEL = "EV_USES_VALUE"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_ENDPOINT"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ENDPOINT"

    name = StringProperty()
    name_plain = StringProperty()
    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )


class EndpointRoot(VersionRoot):
    __optional_labels__ = ["TemplateParameterValueRoot"]
    LIBRARY_REL_LABEL = "CONTAINS_ENDPOINT"
    TEMPLATE_REL_LABEL = "HAS_ENDPOINT"
    uid_prefix = "Endpoint_"

    has_template = RelationshipFrom(EndpointTemplateRoot, TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)

    has_version = RelationshipTo(
        EndpointValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(EndpointValue, "LATEST")
    latest_draft = RelationshipTo(
        EndpointValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        EndpointValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        EndpointValue, "LATEST_RETIRED", model=VersionRelationship
    )
