from neomodel import RelationshipFrom, RelationshipTo, cardinality, db  # type: ignore
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


class CriteriaTemplateValue(SyntaxTemplateValue):
    PARAMETERS_LABEL = "USES_DEFAULT_VALUE"

    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )

    def get_study_count(self) -> int:
        cypher_query = f"""
        MATCH (n)<--(:CriteriaTemplateRoot)-[:HAS_CRITERIA]->(:CriteriaRoot)-->(:CriteriaValue)<-[:HAS_SELECTED_CRITERIA]-(:StudySelection)<-[:HAS_STUDY_CRITERIA]-(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
        WHERE id(n)={self.id}
        RETURN count(DISTINCT sr)
        """

        count, _ = db.cypher_query(cypher_query)
        return count[0][0]


class CriteriaTemplateRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_CRITERIA_TEMPLATE"
    PARAMETERS_LABEL = "OT_USES_PARAMETER"
    TEMPLATE_REL_LABEL = "HAS_CRITERIA"

    editable_instance = BooleanProperty()

    has_template = RelationshipTo(".criteria.CriteriaRoot", TEMPLATE_REL_LABEL)
    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_parameters = RelationshipTo(
        TemplateParameter, PARAMETERS_LABEL, model=TemplateUsesParameterRelation
    )

    has_version = RelationshipTo(
        CriteriaTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CriteriaTemplateValue, "LATEST")
    latest_draft = RelationshipTo(
        CriteriaTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        CriteriaTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        CriteriaTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_type = RelationshipTo(CTTermRoot, "HAS_TYPE", cardinality=cardinality.One)
    has_indication = RelationshipTo(DictionaryTermRoot, "HAS_DISEASE_DISORDER_TERM")
    has_category = RelationshipTo(CTTermRoot, "HAS_CATEGORY")
    has_sub_category = RelationshipTo(CTTermRoot, "HAS_SUB_CATEGORY")
