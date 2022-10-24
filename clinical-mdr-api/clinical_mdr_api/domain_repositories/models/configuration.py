from neomodel import RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class CTConfigValue(VersionValue):
    study_field_name = StringProperty()
    study_field_data_type = StringProperty()
    study_field_null_value_code = StringProperty()

    study_field_grouping = StringProperty()
    study_field_name_property = StringProperty()
    study_field_name_api = StringProperty()

    has_configured_codelist = RelationshipTo(CTCodelistRoot, "HAS_CONFIGURED_CODELIST")
    has_configured_term = RelationshipTo(CTTermRoot, "HAS_CONFIGURED_TERM")


class CTConfigRoot(VersionRoot):

    has_version = RelationshipTo(
        CTConfigValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CTConfigValue, "LATEST")
    latest_draft = RelationshipTo(
        CTConfigValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        CTConfigValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        CTConfigValue, "LATEST_RETIRED", model=VersionRelationship
    )


class FieldNameConfigRoot(CTConfigRoot):
    study_field_name = StringProperty()


class SelectionRelTypeConfigRoot(CTConfigRoot):
    study_selection_rel_type = StringProperty()
