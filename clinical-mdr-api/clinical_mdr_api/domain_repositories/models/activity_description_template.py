from neomodel import RelationshipFrom, RelationshipTo, db  # type: ignore
from neomodel.properties import BooleanProperty

from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
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


class ActivityDescriptionTemplateValue(SyntaxTemplateValue):
    PARAMETERS_LABEL = "USES_DEFAULT_VALUE"

    has_parameters = RelationshipTo(
        TemplateParameterValueRoot, PARAMETERS_LABEL, model=ObjectUsesParameterRelation
    )

    has_conjunction = RelationshipTo(
        Conjunction, "HAS_CONJUNCTION", model=ConjunctionRelation
    )

    def get_study_count(self) -> int:
        cypher_query = f"""
        MATCH (n)<--(:ActivityDescriptionTemplateRoot)-[:HAS_ACTIVITY_INSTRUCTION]->(:ActivityInstructionRoot)-->(:ActivityInstructionValue)<-[:HAS_SELECTED_ACTIVITY_INSTRUCTION]-(:StudySelection)<-[:HAS_STUDY_ACTIVITY_INSTRUCTION]-(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
        WHERE id(n)={self.id}
        RETURN count(DISTINCT sr)
        """

        count, _ = db.cypher_query(cypher_query)
        return count[0][0]


class ActivityDescriptionTemplateRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_ACTIVITY_DESCRIPTION_TEMPLATE"
    PARAMETERS_LABEL = "OT_USES_PARAMETER"
    TEMPLATE_REL_LABEL = "HAS_ACTIVITY_DESCRIPTION"

    editable_instance = BooleanProperty()

    has_template = RelationshipTo(
        ".activity_instruction.ActivityInstructionRoot", TEMPLATE_REL_LABEL
    )
    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_parameters = RelationshipTo(
        TemplateParameter, PARAMETERS_LABEL, model=TemplateUsesParameterRelation
    )

    has_version = RelationshipTo(
        ActivityDescriptionTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityDescriptionTemplateValue, "LATEST")
    latest_draft = RelationshipTo(
        ActivityDescriptionTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityDescriptionTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityDescriptionTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_indication = RelationshipTo(DictionaryTermRoot, "HAS_DISEASE_DISORDER_TERM")
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    has_activity_sub_group = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUB_GROUP"
    )
