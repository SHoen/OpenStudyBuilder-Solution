from neomodel import RelationshipFrom, StringProperty

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    ZonedDateTimeProperty,
)


class StudyAction(ClinicalMdrNode):
    audit_trail = RelationshipFrom(
        ".study.StudyRoot", "AUDIT_TRAIL", model=ClinicalMdrRel
    )
    date = ZonedDateTimeProperty(format="%Y-%m-%d %H:%M:%S.%f")
    status = StringProperty()
    user_initials = StringProperty()


class Delete(StudyAction):
    pass


class Create(StudyAction):
    pass


class Edit(StudyAction):
    pass
