from neomodel import RelationshipFrom, RelationshipTo, db  # type: ignore
from neomodel.properties import BooleanProperty

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (  # type: ignore
    Conjunction,
    ConjunctionRelation,
    Library,
    ObjectUsesParameterRelation,
    TemplateUsesParameterRelation,
    VersionRelationship,
    VersionRoot,
)
from clinical_mdr_api.domain_repositories.models.syntax_template import (
    SyntaxTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterValueRoot,
)


class EndpointTemplateValue(SyntaxTemplateValue):
    PARAMETERS_LABEL = "USES_DEFAULT_VALUE"

    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )

    def get_study_count(self) -> int:
        cypher_query = f"""
        MATCH (n)<--(:EndpointTemplateRoot)-[:HAS_ENDPOINT]->(:EndpointRoot)-->(:EndpointValue)<-[:HAS_SELECTED_ENDPOINT]-(:StudySelection)<-[:HAS_STUDY_ENDPOINT]-(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
        WHERE id(n)={self.id}
        RETURN count(DISTINCT sr)
        """

        count, _ = db.cypher_query(cypher_query)
        return count[0][0]


class EndpointTemplateRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ENDPOINT_TEMPLATE"
    PARAMETERS_LABEL = "ET_USES_PARAMETER"
    TEMPLATE_REL_LABEL = "HAS_ENDPOINT"

    editable_instance = BooleanProperty()

    has_template = RelationshipTo(".endpoint.EndpointRoot", TEMPLATE_REL_LABEL)

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_parameters = RelationshipTo(
        TemplateParameter, PARAMETERS_LABEL, model=TemplateUsesParameterRelation
    )
    has_version = RelationshipTo(
        EndpointTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(EndpointTemplateValue, "LATEST")
    latest_draft = RelationshipTo(
        EndpointTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        EndpointTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        EndpointTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_indication = RelationshipTo(DictionaryTermRoot, "HAS_DISEASE_DISORDER_TERM")
    has_category = RelationshipTo(CTTermRoot, "HAS_CATEGORY")
    has_sub_category = RelationshipTo(CTTermRoot, "HAS_SUB_CATEGORY")
