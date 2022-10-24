from typing import Optional

from neomodel import (
    ArrayProperty,
    BooleanProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    db,
)

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    ConjunctionRelation,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction


class StudyField(ClinicalMdrNode):
    has_type = RelationshipTo(CTTermRoot, "HAS_TYPE", model=ClinicalMdrRel)
    has_reason_for_null_value = RelationshipTo(
        CTTermRoot, "HAS_REASON_FOR_NULL_VALUE", model=ClinicalMdrRel
    )

    has_before = RelationshipFrom(StudyAction, "BEFORE", model=ConjunctionRelation)
    has_after = RelationshipFrom(StudyAction, "AFTER", model=ConjunctionRelation)

    @classmethod
    def get_specific_field_currently_used_in_study(
        cls, field_name: str, value: Optional[str], study_uid: str
    ):
        """
        Checks whether the StudyField with a given value has historically already been used in this study.
        """
        if value is None:
            all_similar_study_fields = cls.nodes.filter(
                field_name=field_name, value__isnull=True
            )
        else:
            all_similar_study_fields = cls.nodes.filter(
                field_name=field_name, value=value
            )
        all_fields = all_similar_study_fields.all()
        for field_node in all_fields:
            query = (
                "MATCH (f:StudyField)<--(:StudyValue)<-[:HAS_VERSION]-(s:StudyRoot{uid: $study_uid}) "
                "WHERE id(f) = $self RETURN id(f)"
            )
            result, _ = field_node.cypher(query, params={"study_uid": study_uid})
            if len(result) > 0:
                return field_node
        return None


class StudyProjectField(StudyField):
    has_field = RelationshipFrom(Project, "HAS_FIELD", model=ClinicalMdrRel)


class StudyTextField(StudyField):
    value = StringProperty()
    field_name = StringProperty()

    def is_used(self, study_number: str) -> bool:
        cypher_query = """
        MATCH (stf:StudyField:StudyTextField{field_name: $field_name, value: $value})<-[HAS_TEXT_FIELD]-(sv:StudyValue)<-[:LATEST]-(s:StudyRoot)
        where sv.study_number <> $study_number
        return id(s)
        """
        result, _ = db.cypher_query(
            cypher_query,
            params={
                "field_name": self.field_name,
                "value": self.value,
                "study_number": study_number,
            },
        )
        return len(result) > 0


class StudyIntField(StudyField):
    value = IntegerProperty()
    field_name = StringProperty()


class StudyArrayField(StudyField):
    value = ArrayProperty()
    field_name = StringProperty()


class StudyBooleanField(StudyField):
    value = BooleanProperty()
    field_name = StringProperty()


class StudyTimeField(StudyField):
    value = StringProperty()
    field_name = StringProperty()
