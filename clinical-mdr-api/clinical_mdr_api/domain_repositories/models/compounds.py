from neomodel import (
    BooleanProperty,
    One,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.brand import Brand
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    LagTimeRoot,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import VersionRelationship
from clinical_mdr_api.domain_repositories.models.project import Project


class CompoundValue(ConceptValue):
    analyte_number = StringProperty()
    nnc_short_number = StringProperty()
    nnc_long_number = StringProperty()
    is_sponsor_compound = BooleanProperty()
    is_name_inn = BooleanProperty()

    has_unii_value = RelationshipTo(
        DictionaryTermRoot, "HAS_UNII_VALUE", cardinality=ZeroOrMore
    )

    has_dose_frequency = RelationshipTo(
        CTTermRoot, "HAS_DOSE_FREQUENCY", cardinality=ZeroOrMore
    )
    has_dosage_form = RelationshipTo(
        CTTermRoot, "HAS_DOSAGE_FORM", cardinality=ZeroOrMore
    )
    has_route_of_administration = RelationshipTo(
        CTTermRoot, "HAS_ROUTE_OF_ADMINISTRATION", cardinality=ZeroOrMore
    )
    has_delivery_device = RelationshipTo(
        CTTermRoot, "HAS_DELIVERY_DEVICE", cardinality=ZeroOrMore
    )
    has_dispenser = RelationshipTo(CTTermRoot, "HAS_DISPENSER", cardinality=ZeroOrMore)
    has_dose_value = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_DOSE_VALUE", cardinality=ZeroOrMore
    )
    has_strength_value = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_STRENGTH_VALUE", cardinality=ZeroOrMore
    )
    has_half_life = RelationshipTo(
        NumericValueWithUnitRoot, "HAS_HALF_LIFE", cardinality=ZeroOrOne
    )
    has_lag_time = RelationshipTo(LagTimeRoot, "HAS_LAG_TIME", cardinality=ZeroOrMore)
    has_project = RelationshipTo(Project, "HAS_PROJECT", cardinality=ZeroOrMore)
    has_brand = RelationshipTo(Brand, "HAS_BRAND", cardinality=ZeroOrMore)


class CompoundRoot(ConceptRoot):
    has_version = RelationshipTo(
        CompoundValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CompoundValue, "LATEST")

    latest_draft = RelationshipTo(
        CompoundValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        CompoundValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        CompoundValue, "LATEST_RETIRED", model=VersionRelationship
    )


class CompoundAliasValue(ConceptValue):
    is_preferred_synonym = BooleanProperty()

    is_compound = RelationshipTo(CompoundRoot, "IS_COMPOUND", cardinality=One)

    compound_alias_root = RelationshipFrom(
        "CompoundAliasRoot", "HAS_VERSION", model=VersionRelationship
    )


class CompoundAliasRoot(ConceptRoot):
    has_version = RelationshipTo(
        CompoundAliasValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(CompoundAliasValue, "LATEST")

    latest_draft = RelationshipTo(
        CompoundAliasValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        CompoundAliasValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        CompoundAliasValue, "LATEST_RETIRED", model=VersionRelationship
    )
