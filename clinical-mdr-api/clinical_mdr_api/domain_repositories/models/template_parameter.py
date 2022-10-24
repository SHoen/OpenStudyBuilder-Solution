from neomodel import (
    BooleanProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    db,
)

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    TemplateUsesParameterRelation,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class TemplateParameter(ClinicalMdrNode):
    RELATION_LABEL = "HAS_VALUE"
    has_value = RelationshipTo("TemplateParameterValueRoot", RELATION_LABEL)

    name = StringProperty()


class TemplateParameterValue(VersionValue):
    name = StringProperty()
    is_active_template_parameter = BooleanProperty()


class TemplateParameterValueRoot(VersionRoot):
    RELATION_LABEL = "HAS_VALUE"
    PARAMETERS_LABEL = "USES_DEFAULT_VALUE"

    uid = StringProperty()

    has_value = RelationshipFrom(TemplateParameter, RELATION_LABEL)

    has_version = RelationshipTo(
        TemplateParameterValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(TemplateParameterValue, "LATEST")

    latest_draft = RelationshipTo(
        TemplateParameterValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        TemplateParameterValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        TemplateParameterValue, "LATEST_RETIRED", model=VersionRelationship
    )

    @classmethod
    def check_value_exists(cls, parameter_name: str, parameter_value_uid: str) -> bool:
        cypher_query = """
            MATCH (pt:TemplateParameter {name: $name})<-[:HAS_PARENT_PARAMETER*0..]-(ptParents)-[:HAS_VALUE]->(pr {uid: $uid})
            RETURN
                pt.name AS name, ptParents.name AS type, pr.uid AS uid
            """
        dataset, _ = db.cypher_query(
            cypher_query, {"uid": parameter_value_uid, "name": parameter_name}
        )
        if len(dataset) == 0:
            return False
        return True


class ParameterTemplateValue(TemplateParameterValue):
    template_string = StringProperty()

    def get_all(self):
        cypher_query = """
            MATCH (otv:ParameterTemplateValue)<-[:LATEST_FINAL]-(ot:ParameterTemplateRoot)<-[rel:TPCV_USES_TPV]-(pt)
            where ID(pt) = $id
            RETURN
                pt.name AS name, ot.uid AS uid, rel.position as position, otv.value as value, otv.name as param_value

            """
        dataset, _ = db.cypher_query(cypher_query, {"id": self.id})
        return dataset


class ParameterTemplateRoot(TemplateParameterValueRoot):
    has_version = RelationshipTo(
        ParameterTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ParameterTemplateValue, "LATEST")

    latest_draft = RelationshipTo(
        ParameterTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ParameterTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ParameterTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_value = RelationshipFrom(TemplateParameter, "HAS_VALUE")
    has_definition = RelationshipFrom(TemplateParameter, "HAS_DEFINITION")


class TemplateParameterComplexValue(TemplateParameterValue):
    uses_parameter = RelationshipTo(
        TemplateParameterValueRoot, "TPCV_USES_TPV", model=TemplateUsesParameterRelation
    )

    def get_all(self):
        cypher_query = """
            MATCH (otv:TemplateParameterValue)<-[:LATEST_FINAL]-(ot:TemplateParameterValueRoot)<-[rel:TPCV_USES_TPV]-(pt)
            where ID(pt) = $id
            RETURN
                pt.name AS name, ot.uid AS uid, rel.position as position, otv.value as value, otv.name as param_value
                         
            """
        dataset, _ = db.cypher_query(cypher_query, {"id": self.id})
        return dataset


class TemplateParameterComplexRoot(TemplateParameterValueRoot):
    has_version = RelationshipTo(
        TemplateParameterComplexValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(TemplateParameterComplexValue, "LATEST")

    latest_draft = RelationshipTo(
        TemplateParameterComplexValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        TemplateParameterComplexValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        TemplateParameterComplexValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_complex_value = RelationshipFrom(ParameterTemplateRoot, "HAS_COMPLEX_VALUE")
