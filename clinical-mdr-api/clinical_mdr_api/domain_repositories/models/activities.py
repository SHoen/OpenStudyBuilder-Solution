from neomodel import (
    BooleanProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import VersionRelationship


class ActivityGroupValue(ConceptValue):
    has_latest_value = RelationshipFrom("ActivityGroupRoot", "LATEST")


class ActivityGroupRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityGroupValue, "LATEST")

    latest_draft = RelationshipTo(
        ActivityGroupValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityGroupValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityGroupValue, "LATEST_RETIRED", model=VersionRelationship
    )


class ActivitySubGroupValue(ConceptValue):
    has_latest_value = RelationshipFrom("ActivitySubGroupRoot", "LATEST")
    in_group = RelationshipTo(ActivityGroupValue, "IN_GROUP")


class ActivitySubGroupRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivitySubGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivitySubGroupValue, "LATEST")

    latest_draft = RelationshipTo(
        ActivitySubGroupValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivitySubGroupValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivitySubGroupValue, "LATEST_RETIRED", model=VersionRelationship
    )


class ActivityValue(ConceptValue):
    in_sub_group = RelationshipTo(ActivitySubGroupValue, "IN_SUB_GROUP")
    has_latest_value = RelationshipFrom("ActivityRoot", "LATEST")


class ActivityRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityValue, "LATEST")

    latest_draft = RelationshipTo(
        ActivityValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityValue, "LATEST_RETIRED", model=VersionRelationship
    )


class ActivityItem(ConceptRoot):
    has_sdtm_variable = RelationshipTo(
        CTTermRoot, "TABULATED_IN", cardinality=ZeroOrOne
    )
    has_cdash_variable = RelationshipTo(CTTermRoot, "HAS_CDASH", cardinality=ZeroOrOne)


class ActivityDefinition(ActivityItem):
    has_sdtm_domain = RelationshipTo(
        CTTermRoot, "HAS_SDTM_DOMAIN", cardinality=ZeroOrOne
    )
    has_sdtm_cat = RelationshipTo(CTTermRoot, "HAS_SDTM_CAT", cardinality=ZeroOrOne)
    has_sdtm_subcat = RelationshipTo(
        CTTermRoot, "HAS_SDTM_SUBCAT", cardinality=ZeroOrOne
    )

    # Findings specific
    has_findings_test_code = RelationshipTo(
        CTTermRoot, "HAS_TEST_CODE", cardinality=ZeroOrOne
    )
    has_findings_specimen = RelationshipTo(
        CTTermRoot, "HAS_SPECIMEN", cardinality=ZeroOrOne
    )

    # Numeric Finding specific
    has_numeric_finding_unit_dimension = RelationshipTo(
        CTTermRoot, "HAS_UNIT_DIMENSION", cardinality=ZeroOrOne
    )
    has_numeric_finding_unit_definition = RelationshipTo(
        UnitDefinitionRoot, "HAS_UNIT_DEFINITION", cardinality=ZeroOrOne
    )

    # Categoric Finding specific
    has_categoric_response_value = RelationshipTo(
        CTTermRoot, "HAS_CATEGORIC_RESPONSE_VALUE", cardinality=ZeroOrOne
    )
    has_categoric_response_list = RelationshipTo(
        CTTermRoot, "HAS_CATEGORIC_RESPONSE_LIST", cardinality=ZeroOrOne
    )


class ActivityCollection(ActivityItem):
    has_odm_item = RelationshipTo("OdmItemRoot", "HAS_ODM_ITEM", cardinality=ZeroOrOne)


class ActivityInstanceValue(ConceptValue):
    topic_code = StringProperty()
    adam_param_code = StringProperty()
    legacy_description = StringProperty()

    def activity_type(self) -> str:
        """
        Method maps the ActivityInstanceValue subtype node label into specific activity type.
        The most specific types are placed on the top of the if clause section as we are interested
        in the most specific label.
        :return str:
        """
        labels = self.labels()
        if "ReminderValue" in labels:
            label = "reminders"
        elif "CompoundValue" in labels:
            label = "compounds"
        elif "CompoundDosingValue" in labels:
            label = "compound-dosings"
        elif "SpecialPurposeValue" in labels:
            label = "special-purposes"
        elif "RatingScaleValue" in labels:
            label = "rating-scales"
        elif "LaboratoryActivityValue" in labels:
            label = "laboratory-activities"
        elif "CategoricFindingValue" in labels:
            label = "categoric-findings"
        elif "NumericFindingValue" in labels:
            label = "numeric-findings"
        elif "TextualFindingValue" in labels:
            label = "textual-findings"
        elif "EventValue" in labels:
            label = "events"
        else:
            raise ValueError(
                f"Given labels {labels} don't match with any of activity-instance subtype."
            )
        return label

    in_hierarchy = RelationshipTo(ActivityValue, "IN_HIERARCHY")
    defined_by = RelationshipTo(ActivityDefinition, "DEFINED_BY")
    collected_in = RelationshipTo(ActivityCollection, "COLLECTED_IN")


class ActivityInstanceRoot(ConceptRoot):
    has_version = RelationshipTo(
        ActivityInstanceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(ActivityInstanceValue, "LATEST")

    latest_draft = RelationshipTo(
        ActivityInstanceValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        ActivityInstanceValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        ActivityInstanceValue, "LATEST_RETIRED", model=VersionRelationship
    )


class ReminderValue(ActivityInstanceValue):
    pass


class ReminderRoot(ActivityInstanceRoot):
    pass


class InterventionValue(ActivityInstanceValue):
    pass


class InterventionRoot(ActivityInstanceRoot):
    pass


class CompoundDosingValue(InterventionValue):
    pass


class CompoundDosingRoot(InterventionRoot):
    pass


class SpecialPurposeValue(ActivityInstanceValue):
    pass


class SpecialPurposeRoot(ActivityInstanceRoot):
    pass


class FindingValue(ActivityInstanceValue):
    value_sas_display_format = StringProperty()


class FindingRoot(ActivityInstanceRoot):
    pass


class CategoricFindingValue(FindingValue):
    pass


class CategoricFindingRoot(FindingRoot):
    pass


class RatingScaleValue(CategoricFindingValue):
    pass


class RatingScaleRoot(CategoricFindingRoot):
    pass


class LaboratoryActivityValue(CategoricFindingValue):
    pass


class LaboratoryActivityRoot(CategoricFindingRoot):
    pass


class NumericFindingValue(FindingValue):
    molecular_weight = IntegerProperty()
    convert_to_si_unit = BooleanProperty()
    convert_to_us_conventional_unit = BooleanProperty()


class NumericFindingRoot(FindingRoot):
    pass


class TextualFindingValue(FindingValue):
    max_text_length = IntegerProperty()
    split_text_in_supp_qual = BooleanProperty()


class TextualFindingRoot(FindingRoot):
    pass


class EventValue(ActivityInstanceValue):
    pass


class EventRoot(ActivityInstanceRoot):
    pass
