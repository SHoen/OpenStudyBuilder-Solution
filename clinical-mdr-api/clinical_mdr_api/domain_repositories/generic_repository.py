from dataclasses import dataclass
from typing import Any, Mapping, Optional

from cachetools import TTLCache
from neomodel import NeomodelException, RelationshipManager

from clinical_mdr_api import config
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.repositories._utils import sb_clear_cache


class EntityNotFoundError(LookupError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


@dataclass(frozen=True)
class RepositoryClosureData:
    not_for_update: bool
    repository: Any
    additional_closure: Any


class RepositoryImpl:
    """
    A repository is responsible for reading/writing data to/from the database.
    Results from a repository should be used to build aggregate root (AR) objects.
    """

    cache_store_item_by_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )

    value_class: type
    root_class: type

    @property
    def user_initials(self) -> Optional[str]:
        return self._user_initials

    def __init__(self, user: str = None):
        self._user_initials = user

    def _get_neomodel_objects(self, uid: str):
        """
        This function calls the DB (several times) to retrieve the data layer Neomodel objects.
        The aggregate state can then be changed by the service, after which
        this repository writes the state back to the DB.
        """
        try:
            root: VersionRoot = self.root_class.nodes.get(uid=uid)
            value: VersionValue = root.has_latest_value.single()
            latest_value: VersionRelationship = root.has_latest_value.relationship(
                value
            )
            latest_draft: VersionRelationship = root.latest_draft.relationship(value)
            latest_final: VersionRelationship = root.latest_final.relationship(value)
        except NeomodelException as exc:
            raise EntityNotFoundError(
                "Entity with " + uid + " is not found in the database."
            ) from exc

        return root, value, latest_value, latest_draft, latest_final

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_and_link_nodes(
        self,
        root: ClinicalMdrNode,
        value: ClinicalMdrNode,
        rel_properties: Mapping[str, Any],
    ):
        """
        Creates versioned root and versioned object nodes.
        # TODO - GEneration of uids should be removed (additional service?)
        """
        self._db_save_node(root)
        self._db_save_node(value)
        latest_value = self._db_create_relationship(root.has_latest_value, value)

        if rel_properties["status"] != "Final":
            latest_draft = self._db_create_relationship(
                root.latest_draft, value, rel_properties
            )
            latest_final = None
        else:
            # if we create an object that is immediately in a final state, we create a LATEST_FINAL relationship.
            latest_draft = None
            latest_final = self._db_create_relationship(
                root.latest_final, value, rel_properties
            )

        # self._db_create_relationship(root.has_version, value, rel_properties)
        return root, value, latest_value, latest_draft, latest_final

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_save_node(self, node: ClinicalMdrNode) -> ClinicalMdrNode:
        """
        Saves a Neomodel node object in the graph.
        TODO: optionalty accept multiple nodes and handle in same DB transaction.
        """
        if node is not None:
            node.save()
        return node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_delete_node(self, node: ClinicalMdrNode) -> ClinicalMdrNode:
        """
        Deletes a Neomodel node object in the graph.
        TODO: optionally accept multiple nodes and handle in same DB transaction.
        """
        if node is not None:
            node.delete()
        return node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_relationship(
        self,
        origin: RelationshipManager,
        destination: ClinicalMdrNode,
        parameters: Optional[Mapping[str, Any]] = None,
    ) -> VersionRelationship:
        """
        Creates a relationship of an origin type (e.g.VersionRoot.has_latest) to a destination (VersionValue).
        Parameters of a VersionRelationship must be included.
        """
        if parameters is None:
            parameters = {}

        if parameters:
            return origin.connect(destination, parameters)
        return origin.connect(destination)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_remove_relationship(
        self, relationship: RelationshipManager, value: Optional[ClinicalMdrNode] = None
    ):
        """
        Removes a relationship.
        Example input: {relationship: compound_root.latest_draft,
                        value: compound_value}
        """
        if value is None:
            relationship.disconnect_all()
        else:
            relationship.disconnect(value)

    def generate_uid_callback(self):
        return self.root_class.get_next_free_uid_and_increment_counter()
