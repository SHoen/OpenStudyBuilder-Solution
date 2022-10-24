import datetime

import neo4j
from neomodel import (
    BooleanProperty,
    DateTimeProperty,
    IntegerProperty,
    Property,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredNode,
    StructuredRel,
    db,
)
from neomodel.properties import validator

from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.domain_repositories.models._utils import (
    CustomNodeSet,
    classproperty,
    convert_to_datetime,
    convert_to_tz_aware_datetime,
)
from clinical_mdr_api.exceptions import NotFoundException


class ZonedDateTimeProperty(DateTimeProperty):
    @validator
    def deflate(self, value: datetime.datetime):
        return convert_to_tz_aware_datetime(value)

    @validator
    def inflate(self, value: neo4j.time.DateTime):
        return convert_to_datetime(value)


class ClinicalMdrNode(StructuredNode):
    """
    A `ClinicalMdrNode` is the highest level of abstraction for
    a relationship in the graph.
    It inherits directly from a neomodel `StructuredNode` object.
    All other node models inherit from this class.
    """

    __abstract_node__ = True

    @classproperty
    # pylint:disable=no-self-argument
    def nodes(cls):
        """
        Returns a CustomNodeSet(NodeSet) object representing all nodes of the classes label
        :return: CustomNodeSet
        :rtype: CustomNodeSet
        """

        return CustomNodeSet(cls)

    @classmethod
    def category(cls):
        pass

    @classmethod
    def get_definition(cls):
        defined_props = cls.defined_properties()
        return {
            key: value
            for key, value in defined_props.items()
            if isinstance(value, Property)
        }

    def to_dict(self):

        defined_props = self.get_definition()
        props = vars(self)
        return {key: props[key] for key, value in defined_props.items()}

    @classmethod
    def strip_datadict(cls, datadict: dict):
        internals = cls.get_definition()
        return_dict = {}
        for key, value in datadict.items():
            if key.startswith("_"):
                key = key[1:]
            if key in internals:
                return_dict[key] = value

        return return_dict


class ClinicalMdrNodeWithUID(ClinicalMdrNode):
    """
    An extension of a ClinicalMdrNode that automatically sets a generated UID when it is saved.
    """

    __abstract_node__ = True
    uid = StringProperty(unique_index=True)

    @classmethod
    def get_next_free_uid_and_increment_counter(cls) -> str:
        """
        Finds the next free available UID for a given object.
        If none of the objects have ever been created, sets up a new incremental counter for this object type.
        """
        object_name = (
            cls.__name__[: len(cls.__name__) - 4]
            if cls.__name__.endswith("Root")
            else cls.__name__
        )
        return str(
            db.cypher_query(
                """
        MERGE (m:Counter{{counterId:'{LABEL}Counter'}})
        ON CREATE SET m:{LABEL}Counter, m.count=0
        WITH m
        CALL apoc.atomic.add(m,'count',1,1) yield oldValue, newValue
        WITH apoc.convert.toInteger(newValue) as uidNumber
        RETURN "{LABEL}_"+apoc.text.lpad(""+(uidNumber), 6, "0")
        """.format(
                    LABEL=object_name
                )
            )[0][0][0]
        )

    @classmethod
    def generate_node_uids_if_not_present(cls) -> None:
        """
        Generates UIDs for all nodes of this class that do not yet have a UID.
        Uses the template structure [NODELABEL]_999999 for the generated identifiers.
        """
        node_label = cls.__name__
        object_name = (
            node_label[: len(node_label) - 4]
            if node_label.endswith("Root")
            else node_label
        )
        db.cypher_query(
            """
        // the new UIDs will start at the value from the memory node.
        MERGE (m:Counter{{counterId:'{LABEL}Counter'}})
        ON CREATE SET m:{LABEL}Counter, m.count=1
        WITH m
        CALL apoc.lock.nodes([m])

        // Then, get all newly created nodes of a specific label without assigned UID.
        MATCH (n:{NODE_LABEL})
        USING SCAN n:{NODE_LABEL}
        WHERE n.uid is null
        WITH collect(n) as newNodes, m

        // Increment the counter by the size of the newly created nodes, so we store this for the next transaction.
        SET m.count = m.count + size(newNodes)

        // Then, we need to assign new UIDs to the created nodes.
        // We start at the old counter value (startUidNumber), and increment the values for each new node.
        WITH newNodes, range(0,size(newNodes)-1) as indices, m.count - size(newNodes) as startUidNumber
        UNWIND indices as index
        WITH newNodes[index] as node, index + startUidNumber as uidNumber
        SET node.uid = "{LABEL}_"+apoc.text.lpad(""+(uidNumber), 6, "0")
        """.format(
                LABEL=object_name, NODE_LABEL=node_label
            )
        )

    def save(self):
        """
        Saves the node after create/update of a node.
        This method ensures that there will always be a generated UID assigned.
        """
        if self.uid is None:
            object_name = (
                self.__class__.__name__[: len(self.__class__.__name__) - 4]
                if self.__class__.__name__.endswith("Root")
                else self.__class__.__name__
            )

            new_uid = db.cypher_query(
                """
            MERGE (m:Counter{{counterId:'{LABEL}Counter'}})
            ON CREATE SET m:{LABEL}Counter, m.count=1
            ON MATCH SET m.count = m.count + 1
            WITH m
            RETURN m.count as number
            """.format(
                    LABEL=object_name
                )
            )[0][0][0]
            self.uid = str(object_name) + "_" + str(new_uid).zfill(6)
        return super().save()


class ClinicalMdrRel(StructuredRel):
    __abstract_node__ = True
    """
    A `ClinicalMdrRel` is the highest level of abstraction for a
    relationship in the graph.
    It inherits directly from a neomodel `StructuredRel` object.
    All other relationship models inherit from this class.
    """

    def to_dict(self):
        defined_props = self.defined_properties()
        props = vars(self)
        return {
            key: props[key]
            for key, value in defined_props.items()
            if isinstance(value, Property)
        }

    def strip_datadict(self, datadict: dict):
        internals = self.to_dict()
        return_dict = {}
        for key, value in datadict.items():
            if key in internals:
                return_dict[key] = value
        return return_dict


class TemplateUsesParameterRelation(ClinicalMdrRel):
    position = IntegerProperty()


class ObjectUsesParameterRelation(ClinicalMdrRel):
    position = IntegerProperty()
    index = IntegerProperty()
    set_number = IntegerProperty()


class ConjunctionRelation(ClinicalMdrRel):
    position = IntegerProperty()
    set_number = IntegerProperty()


class Library(ClinicalMdrNode):
    name = StringProperty()
    is_editable = BooleanProperty()


class VersionRelationship(ClinicalMdrRel):
    """
    A `VersionRelationship` represents a relationship between a `VersionRoot`
    and a `VersionValue` node.
    In the graph, these are persisted as `LATEST`, `HAS_VERSION`,
    `LATEST_DRAFT` or `LATEST_FINAL`.
    """

    start_date = ZonedDateTimeProperty(format="%Y-%m-%d %H:%M:%S.%f")
    end_date = ZonedDateTimeProperty(format="%Y-%m-%d %H:%M:%S.%f")
    change_description = StringProperty()
    version = StringProperty()
    status = StringProperty()
    user_initials = StringProperty()


class VersionValue(ClinicalMdrNode):
    __abstract_node__ = True
    """
    A `VersionValue` contains at least a name for the object being versioned.
    domain entities (activities, objectives) inherit from this class and add
    other properties if needed.
    """
    name = StringProperty()
    STUDY_SELECTION_REL_LABEL = ""
    STUDY_VALUE_REL_LABEL = ""

    def get_root_uid_by_latest(self):
        cypher_query = f"""
        MATCH (ot)-[:LATEST_FINAL|LATEST_DRAFT]-> (ov:{self.__label__} {{name: "{self.name}"}})
        return ot.uid
        """

        uids, _ = db.cypher_query(cypher_query)
        if len(uids) > 0:
            return uids[0][0]
        raise NotFoundException(f"Cannot find root for this name {self.name}")

    def get_study_count(self) -> int:
        cypher_query = f"""
        MATCH (n)<-[:{self.STUDY_SELECTION_REL_LABEL}]-(:StudySelection)<-[:{self.STUDY_VALUE_REL_LABEL}]-(:StudyValue)<--(sr:StudyRoot)
        WHERE id(n)={self.id}
        RETURN count(DISTINCT sr)
        """

        count, _ = db.cypher_query(cypher_query)
        return count[0][0]


class VersionRoot(ClinicalMdrNodeWithUID):
    __abstract_node__ = True
    """
    A `VersionRoot` contains the UID of the entity being versioned.
    The object holds references to one or more VersionValues with
    VersionRelationships.
    """
    TEMPLATE_REL_LABEL = ""
    LIBRARY_REL_LABEL = "CONTAINS"
    PARAMETERS_LABEL = "HAS_PARAMETERS"

    has_template = RelationshipTo("VersionRoot", "HAS_TEMPLATE")

    has_version = RelationshipTo(VersionValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(VersionValue, "LATEST")

    latest_draft = RelationshipTo(
        VersionValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        VersionValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        VersionValue, "LATEST_RETIRED", model=VersionRelationship
    )

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_parameters = RelationshipTo(
        ".template_parameter.TemplateParameter",
        PARAMETERS_LABEL,
        model=TemplateUsesParameterRelation,
    )

    def get_final_before(self, date_before: datetime):
        # pylint: disable=no-member
        value = self.latest_final.get_or_none()
        if value is not None:
            rel = self.latest_final.relationship(value)
            if rel.start_date <= date_before:
                return value
        past_final_versions = self.has_version.match(
            start_date__lte=date_before,
            end_date__gte=date_before,
            status=LibraryItemStatus.FINAL.value,
        )
        # I expect only one or zero elements here
        # otherwise it would mean overreaching entries for the same status
        if len(past_final_versions) > 0:
            return past_final_versions[0]
        return None

    def get_retired_before(self, date_before: datetime):
        # pylint: disable=no-member
        value = self.latest_retired.get_or_none()
        if value is not None:
            rel = self.latest_retired.relationship(value)
            if rel.start_date <= date_before:
                return value
            past_retired_versions = self.has_version.match(
                start_date__lte=date_before,
                end_date__gte=date_before,
                status=LibraryItemStatus.RETIRED.value,
            )
            # I expect only one or zero elements here
            # otherwise it would mean overreaching entries for the same status
            if len(past_retired_versions) > 0:
                return past_retired_versions[0]
        return None

    def get_value_for_version(self, version: str):
        # pylint: disable=no-member
        matching_values = self.latest_final.match(version=version)
        if len(matching_values) == 0:
            matching_values = self.latest_draft.match(version=version)
        if len(matching_values) == 0:
            matching_values = self.latest_retired.match(version=version)
        if len(matching_values) == 0:
            matching_values = self.has_version.match(version=version)
        if len(matching_values) > 0:
            return matching_values[0]
        return None

    def get_relation_for_version(self, version: str):
        # pylint: disable=no-member
        value = self.get_value_for_version(version)
        relationships = self.latest_final.all_relationships(value)
        if len(relationships) == 0:
            relationships = self.latest_draft.all_relationships(value)
        if len(relationships) == 0:
            relationships = self.latest_retired.all_relationships(value)
        if len(relationships) == 0:
            relationships = self.has_version.all_relationships(value)

        if len(relationships) > 0:
            return relationships[0]
        return None

    def get_instantiations_count(self):
        cypher_query = """
        MATCH (ot:{template_label} {{uid: "{uid}" }})
        CALL {{WITH ot MATCH (ot)-[:{relation_label}]->(obr)-[:LATEST_FINAL]-> (obv) RETURN count(obv) as finals}}
        CALL {{WITH ot MATCH (ot)-[:{relation_label}]->(obr)-[:LATEST_DRAFT]-> (obv) RETURN count(obv) as drafts}}
        CALL {{WITH ot MATCH (ot)-[:{relation_label}]->(obr)-[:LATEST_RETIRED]-> (obv) RETURN count(obv) as retired}}
        RETURN  finals, drafts, retired
        """.format(
            template_label=self.__label__,
            uid=self.uid,
            relation_label=self.TEMPLATE_REL_LABEL,
        )

        counts, _ = db.cypher_query(cypher_query)
        return counts[0]


class VersionObjectRoot(VersionRoot):
    __abstract_node__ = True
    TEMPLATE_REL_LABEL = "HAS_TIMEFRAME"

    has_template = RelationshipFrom(VersionRoot, TEMPLATE_REL_LABEL)


class Conjunction(ClinicalMdrNode):
    string = StringProperty()
