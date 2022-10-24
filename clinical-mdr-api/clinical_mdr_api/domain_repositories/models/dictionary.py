from neomodel import RelationshipFrom, RelationshipTo, StringProperty

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CodelistTermRelationship,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class DictionaryTermValue(VersionValue):
    __optional_labels__ = ["TemplateParameterValue"]
    name = StringProperty()
    dictionary_id = StringProperty()
    name_sentence_case = StringProperty()
    abbreviation = StringProperty()
    definition = StringProperty()


class DictionaryTermRoot(VersionRoot):
    __optional_labels__ = ["TemplateParameterValueRoot"]
    LIBRARY_REL_LABEL = "CONTAINS_DICTIONARY_TERM"

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_version = RelationshipTo(
        DictionaryTermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(DictionaryTermValue, "LATEST")
    latest_final = RelationshipTo(
        DictionaryTermValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        DictionaryTermValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        DictionaryTermValue, "LATEST_DRAFT", model=VersionRelationship
    )
    has_term = RelationshipFrom(
        "DictionaryCodelistRoot", "HAS_TERM", model=CodelistTermRelationship
    )
    had_term = RelationshipFrom(
        "DictionaryCodelistRoot", "HAD_TERM", model=CodelistTermRelationship
    )


class DictionaryCodelistValue(VersionValue):
    __optional_labels__ = ["TemplateParameter"]
    name = StringProperty()


class DictionaryCodelistRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_DICTIONARY_CODELIST"

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_version = RelationshipTo(
        DictionaryCodelistValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(DictionaryCodelistValue, "LATEST")
    latest_final = RelationshipTo(
        DictionaryCodelistValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        DictionaryCodelistValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        DictionaryCodelistValue, "LATEST_DRAFT", model=VersionRelationship
    )
    has_term = RelationshipTo(
        DictionaryTermRoot, "HAS_TERM", model=CodelistTermRelationship
    )
    had_term = RelationshipTo(
        DictionaryTermRoot, "HAD_TERM", model=CodelistTermRelationship
    )


class SnomedTermValue(DictionaryTermValue):
    pass


class SnomedTermRoot(DictionaryTermRoot):
    has_version = RelationshipTo(
        SnomedTermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(SnomedTermValue, "LATEST")
    latest_final = RelationshipTo(
        SnomedTermValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        SnomedTermValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        SnomedTermValue, "LATEST_DRAFT", model=VersionRelationship
    )


class MEDRTTermValue(DictionaryTermValue):
    pass


class MEDRTTermRoot(DictionaryTermRoot):
    has_version = RelationshipTo(
        MEDRTTermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(MEDRTTermValue, "LATEST")
    latest_final = RelationshipTo(
        MEDRTTermValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        MEDRTTermValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        MEDRTTermValue, "LATEST_DRAFT", model=VersionRelationship
    )


class UNIITermValue(DictionaryTermValue):
    has_pclass = RelationshipTo(MEDRTTermRoot, "HAS_PCLASS")


class UNIITermRoot(DictionaryTermRoot):
    has_version = RelationshipTo(
        UNIITermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(UNIITermValue, "LATEST")
    latest_final = RelationshipTo(
        UNIITermValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        UNIITermValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        UNIITermValue, "LATEST_DRAFT", model=VersionRelationship
    )


class UCUMTermValue(DictionaryTermValue):
    pass


class UCUMTermRoot(DictionaryTermRoot):
    has_version = RelationshipTo(
        UCUMTermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(UCUMTermValue, "LATEST")
    latest_final = RelationshipTo(
        UCUMTermValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        UCUMTermValue, "LATEST_RETIRED", model=VersionRelationship
    )
    latest_draft = RelationshipTo(
        UCUMTermValue, "LATEST_DRAFT", model=VersionRelationship
    )
