import abc
import copy
from datetime import datetime
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
)

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import OUTGOING, NodeClassNotDefined, RelationshipManager, Traversal, db
from neomodel.exceptions import DoesNotExist

from clinical_mdr_api import config, exceptions
from clinical_mdr_api.domain._utils import convert_to_plain
from clinical_mdr_api.domain.library.parameter_value import (
    ComplexParameterValue,
    NumericParameterValueVO,
    ParameterValueEntryVO,
    SimpleParameterValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    VersioningException,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    GenericRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import RepositoryImpl
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    ControlledTerminology,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    ParameterTemplateRoot,
    TemplateParameterComplexRoot,
    TemplateParameterComplexValue,
)
from clinical_mdr_api.exceptions import BusinessLogicException, NotFoundException
from clinical_mdr_api.repositories._utils import sb_clear_cache

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)
RETRIEVED_READ_ONLY_MARK = object()


class LibraryItemRepositoryImplBase(
    RepositoryImpl, GenericRepository[_AggregateRootType], abc.ABC
):
    cache_store_item_by_uid = TTLCache(
        maxsize=config.CACHE_MAX_SIZE, ttl=config.CACHE_TTL
    )
    has_library = True

    @abc.abstractmethod
    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        study_count: Optional[int] = None,
        counts: Optional[InstantiationCountsVO] = None,
    ) -> _AggregateRootType:
        raise NotImplementedError

    @abc.abstractmethod
    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        raise NotImplementedError

    value_class: type
    root_class: type

    def check_usage_count(self, uid: str) -> int:
        itm: VersionRoot = self.root_class.nodes.get(uid=uid)
        return len(itm.has_template.all())

    def exists_by(self, property_name: str, value: str, on_root: bool = False) -> bool:
        if not on_root:
            query = f"""
                MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{{property_name}: ${property_name}}})
                RETURN or
                """
        else:
            query = f"""
                MATCH (or:{self.root_class.__label__} {{{property_name}: ${property_name}}})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__})
                RETURN or
                """

        result, _ = db.cypher_query(query, {property_name: value})
        return len(result) > 0 and len(result[0]) > 0

    def get_uid_by_property_value(
        self, property_name: str, value: str
    ) -> Optional[str]:
        query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{{property_name}: ${property_name}}})
            RETURN or
            """
        result, _ = db.cypher_query(query, {property_name: value})
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0].get("uid")
        return None

    def check_exists_by_name(self, name: str) -> bool:
        return self.exists_by("name", name)

    def check_exists_by_name_in_library(self, name: str, library: str) -> bool:
        query = f"""
            MATCH (:Library {{name: $library}})-[:{self.root_class.LIBRARY_REL_LABEL}]->(or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{name: $name}})
            RETURN or
            """
        result, _ = db.cypher_query(query, {"name": name, "library": library})
        return len(result) > 0 and len(result[0]) > 0

    def find_uid_by_name(self, name: str) -> Optional[str]:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED]->(ov:{self.value_class.__label__} {{name: $name }})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})
        if len(items) > 0:
            return items[0][0]
        return None

    def _is_repository_related_to_ct(self) -> bool:
        return False

    def _lock_object(self, uid: str) -> None:
        if not self._is_repository_related_to_ct():
            itm = self.root_class.nodes.get_or_none(uid=uid)
        else:
            result, _ = db.cypher_query(
                "MATCH (node) WHERE ID(node)=$id RETURN node",
                {"id": int(uid)},
                resolve_objects=True,
            )
            itm = result[0][0]
        if itm is not None:
            itm.__WRITE_LOCK__ = None
            itm.save()

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _get_or_create_value(
        self, root: VersionRoot, ar: _AggregateRootType
    ) -> VersionValue:
        for itm in root.has_version.filter(name=ar.name):
            return itm

        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired

        if hasattr(ar, "name_plain"):
            new_value = self.value_class(
                name=ar.name, name_plain=convert_to_plain(ar.name)
            )
        else:
            new_value = self.value_class(name=ar.name)
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: _AggregateRootType, value: VersionValue) -> bool:
        base_comparison = ar.name != value.name
        return base_comparison

    def _is_new_version_necessary(
        self, ar: _AggregateRootType, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _update(self, versioned_object: _AggregateRootType):
        """
        Updates the state of the versioned object in the graph.

        First, the properties on the root/value nodes must be updated
        and new value object created if necessary.

        Then, that the version information has changed, new HAS_VERSION
        relationships must be created.
        Additionally, the pointer relationships
        (LATEST_DRAFT, LATEST_FINAL, LATEST) must be removed and added again.
        """
        (
            root,
            value,
            library,
            previous_versioned_object,
        ) = versioned_object.repository_closure_data
        # versioning_data = versioned_object.item_metadata.as_datadict()
        versioning_data = self._library_item_metadata_vo_to_datadict(
            versioned_object.item_metadata
        )

        # condition added because ControlledTerminology items are versioned slightly different than other library items:
        # we have two root nodes - the 'main' root called for instance CTCodelistRoot that contains uid
        # and also contains relationships to nodes called CTCodelistAttributesRoot or CTCodelistNameRoot
        # these two nodes don't contain uids but serves as a roots for versioned relationships
        # Connection to the Library node is attached to the 'main' root not the root that owns versioned relationships
        # this is why we need the following condition
        if self._is_repository_related_to_ct():
            root = root.has_root.single()

        if (
            self.has_library
            and versioned_object.library.name != root.has_library.get().name
        ):
            self._db_remove_relationship(root.has_library)
            try:
                new_library = self._get_library(versioned_object.library.name)
                if not library.is_editable:
                    raise BusinessLogicException(
                        f"The library with the name='{new_library.name}' does not allow to create objects."
                    )  # noqa: E501
            except DoesNotExist as exc:
                raise NotFoundException(
                    f"The library with the name='{versioned_object.library.name}' could not be found."
                ) from exc
            self._db_create_relationship(root.has_library, library)

        # going back from different treatment of ControlledTerminology items
        if self._is_repository_related_to_ct():
            root, _, _, _ = versioned_object.repository_closure_data

        # self._db_save_node(root)
        is_data_changed = False
        if self._is_new_version_necessary(versioned_object, value):
            # Creating nev value object if necessary
            new_value = self._get_or_create_value(root, versioned_object)

            # recreating latest_value relationship
            self._db_remove_relationship(root.has_latest_value, value)
            self._db_create_relationship(root.has_latest_value, new_value)
            is_data_changed = True
        else:
            new_value = value

        # we update relationships when the data is changed or the versioning data is changed
        if (
            is_data_changed
            or previous_versioned_object.item_metadata != versioned_object.item_metadata
        ):
            # Updating latest_draft nad latest_final relationship if necessary
            if versioned_object.item_metadata.status == LibraryItemStatus.DRAFT:
                self._recreate_relationship(
                    root, root.latest_draft, new_value, versioning_data
                )
                # self._close_relationship(root, root.latest_final, versioning_data)

            elif versioned_object.item_metadata.status == LibraryItemStatus.FINAL:
                self._recreate_relationship(
                    root, root.latest_final, new_value, versioning_data
                )
                self._close_relationship(root, root.latest_draft, versioning_data)
                self._close_relationship(root, root.latest_retired, versioning_data)

            elif (
                versioned_object.item_metadata.status == LibraryItemStatus.RETIRED
            ):  # noqa: E501
                self._recreate_relationship(
                    root, root.latest_retired, new_value, versioning_data
                )
                self._close_relationship(root, root.latest_final, versioning_data)

        # recreating parameters connections
        self._maintain_parameters(versioned_object, root, new_value)

        return versioned_object

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _recreate_relationship(
        self,
        root: VersionRoot,
        relation: VersionRelationship,
        value: VersionValue,
        parameters: Mapping[str, Any],
    ):
        old_value = relation.get_or_none()

        if old_value is not None:
            old_rel = relation.relationship(old_value)
            old_parameters = old_rel.to_dict()
            self._db_remove_relationship(relation)
            old_parameters["end_date"] = parameters["start_date"]
            root.has_version.connect(old_value, old_parameters)
        self._db_create_relationship(relation, value, parameters)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _close_relationship(
        self,
        root: VersionRoot,
        relation: VersionRelationship,
        parameters: Mapping[str, Any],
    ):
        old_value = relation.get_or_none()

        if old_value is not None:
            old_rel = relation.relationship(old_value)
            if old_rel.end_date is None:
                old_parameters = old_rel.to_dict()
                self._db_remove_relationship(relation)
                old_parameters["end_date"] = parameters["start_date"]
                root.has_version.connect(old_value, old_parameters)

    def _get_library(self, library_name: str) -> Library:
        # Finds library in database based on library name
        return Library.nodes.get(name=library_name)

    def _get_indication(self, uid: str) -> DictionaryTermRoot:
        # Finds indication in database based on root node uid
        return DictionaryTermRoot.nodes.get(uid=uid)

    def _get_category(self, uid: str) -> CTTermRoot:
        # Finds category in database based on root node uid
        return CTTermRoot.nodes.get(uid=uid)

    def find_all(
        self,
        *,
        status: Optional[LibraryItemStatus] = None,
        library_name: Optional[str] = None,
        return_study_count: Optional[bool] = False,
    ) -> Iterable[_AggregateRootType]:
        """
        GetAll implementation - gets all objects. Ignores versions.
        """
        aggregates = []
        items = []
        if status is None:
            items = self.root_class.nodes.order_by("-uid")
        elif status == LibraryItemStatus.FINAL:
            items = self.root_class.nodes.has(latest_final=True)
        elif status == LibraryItemStatus.DRAFT:
            items = self.root_class.nodes.has(latest_draft=True)
        elif status == LibraryItemStatus.RETIRED:
            items = self.root_class.nodes.has(latest_retired=True)

        for item in items:
            root: VersionRoot = item
            library: Library = root.has_library.get_or_none()

            if library and library_name is not None and library_name != library.name:
                continue

            if status is None:
                value: VersionValue = root.has_latest_value.single()
            elif status == LibraryItemStatus.FINAL:
                value: VersionValue = root.latest_final.single()
            elif status == LibraryItemStatus.DRAFT:
                value: VersionValue = root.latest_draft.single()
            elif status == LibraryItemStatus.RETIRED:
                value: VersionValue = root.latest_retired.single()

            relationship: VersionRelationship = self._get_latest_version(root, value)
            if return_study_count:
                study_count: int = self._get_study_count(value)
                ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root,
                    library=library,
                    relationship=relationship,
                    value=value,
                    study_count=study_count,
                )
            else:
                ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root, library=library, relationship=relationship, value=value
                )
            ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            aggregates.append(ar)
        return aggregates

    def _get_study_count(self, item: VersionValue) -> int:
        return item.get_study_count()

    def _get_latest_version(
        self, root: VersionRoot, value: VersionValue, status: LibraryItemStatus = None
    ) -> VersionRelationship:

        if status is not None:
            if status == LibraryItemStatus.DRAFT:
                rel_data = root.latest_draft.relationship(value)
            elif status == LibraryItemStatus.FINAL:
                rel_data = root.latest_final.relationship(value)
            elif status == LibraryItemStatus.RETIRED:
                rel_data = root.latest_retired.relationship(value)
            return rel_data

        latest_draft = root.latest_draft.get_or_none()
        latest_final = root.latest_final.get_or_none()
        latest_retired = root.latest_retired.get_or_none()
        if latest_draft:
            rel_data = root.latest_draft.relationship(value)
            if rel_data and not rel_data.end_date:
                return rel_data

        if latest_final:
            rel_data = root.latest_final.relationship(value)
            if not rel_data.end_date:
                return rel_data
        assert latest_retired  # this must be true at this stage if not something is very wrong
        rel_data = root.latest_retired.relationship(value)
        assert not rel_data.end_date  # this must be true as well
        return rel_data

    def _get_item_versions(
        self,
        root: VersionRoot,
    ) -> Tuple[
        Sequence[Tuple[Mapping, VersionValue, VersionRelationship]],
        Optional[VersionRelationship],
        Optional[VersionRelationship],
    ]:
        """
        Following code recreates full versioning information based on
        HAS_VERSION relation. First finds all VersionValue-s related to
        specific root, then recreates data dictionaries based on
        relationships between particular nodes (there is more then one
        relation HAS_VERSION) possible between
        single root and value objects)
        """
        latest_final: Optional[VersionRelationship] = None
        latest_draft: Optional[VersionRelationship] = None
        latest_retired: Optional[VersionRelationship] = None
        latest_draft_object: Optional[VersionValue] = root.latest_draft.single()
        if latest_draft_object is not None:
            latest_draft = root.latest_draft.relationship(latest_draft_object)

        latest_final_object: Optional[VersionValue] = root.latest_final.single()
        if latest_final_object is not None:
            latest_final = root.latest_final.relationship(latest_final_object)

        latest_retired_object: Optional[VersionValue] = root.latest_retired.single()
        if latest_retired_object is not None:
            latest_retired = root.latest_retired.relationship(latest_retired_object)

        managed: List[VersionValue] = []
        versions: List[Tuple[Mapping, VersionValue, VersionRelationship]] = []
        traversal = Traversal(
            root,
            root.__label__,
            dict(
                node_class=self.value_class,
                direction=OUTGOING,
                model=VersionRelationship,
            ),
        )
        itm: VersionValue
        for itm in traversal.all():
            assert isinstance(
                itm, (VersionValue, ControlledTerminology)
            )  # PIWQ: juts to check whether I understand what's going here
            if itm in managed:
                continue

            managed.append(itm)
            rels: Iterable[VersionRelationship] = root.has_version.all_relationships(
                itm
            )

            for rel in rels:
                assert isinstance(
                    rel, VersionRelationship
                )  # PIWQ: again to check whether I understand
                versions.append(self._get_version_data_from_db(root, itm, rel))

        if latest_draft is not None:
            d = self._get_version_data_from_db(root, latest_draft_object, latest_draft)
            versions.append(d)
        if latest_final is not None:
            d = self._get_version_data_from_db(root, latest_final_object, latest_final)
            versions.append(d)
        if latest_retired:
            d = self._get_version_data_from_db(
                root, latest_retired_object, latest_retired
            )
            versions.append(d)
        versions = sorted(versions, key=lambda x: x[2].start_date, reverse=True)
        return versions, latest_draft, latest_final

    def get_all_versions_2(
        self, uid: str, return_study_count: Optional[bool] = False
    ) -> Iterable[_AggregateRootType]:
        library: Library = None
        # condition added because ControlledTerminology items are versioned slightly different than other library items:
        # we have two root nodes - the 'main' root called for instance CTCodelistRoot that contains uid
        # and also contains relationships to nodes called CTCodelistAttributesRoot or CTCodelistNameRoot
        # these two nodes don't contain uids but serves as a roots for versioned relationships
        # Connection to the Library node is attached to the 'main' root not the root that owns versioned relationships
        # this is why we need the following condition
        if not self._is_repository_related_to_ct():
            root: Optional[VersionRoot] = self.root_class.nodes.get_or_none(uid=uid)
            if root is not None:
                if self.has_library:
                    library: Library = root.has_library.get()
                else:
                    library = None
        else:
            # ControlledTerminology version root items don't contain uid - then we have to get object by it's id
            result, _ = db.cypher_query(
                "MATCH (node) WHERE ID(node)=$id RETURN node",
                {"id": int(uid)},
                resolve_objects=True,
            )
            root = result[0][0]
            if root is not None:
                if self.has_library:
                    library: Library = root.has_root.single().has_library.get()
                else:
                    library = None

        result: Sequence[_AggregateRootType] = []
        if root is not None:
            if self.has_library:
                assert library is not None
            else:
                assert library is None
            all_version_nodes_and_relationships: Sequence[
                Tuple[VersionValue, VersionRelationship]
            ]
            all_version_nodes_and_relationships = [
                (_[1], _[2]) for _ in self._get_item_versions(root)[0]
            ]
            if return_study_count:
                result = [
                    self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root,
                        value=_[0],
                        relationship=_[1],
                        library=library,
                        study_count=self._get_study_count(_[0]),
                    )
                    for _ in all_version_nodes_and_relationships
                ]
            else:
                result = [
                    self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root, value=_[0], relationship=_[1], library=library
                    )
                    for _ in all_version_nodes_and_relationships
                ]
            for _ in result:
                _.repository_closure_data = RETRIEVED_READ_ONLY_MARK
        return result

    def find_releases_referenced_by_any_study(self) -> Iterable[_AggregateRootType]:
        aggregates = []
        items = self.root_class.nodes.order_by("-uid")

        for item in items:
            # Find releases for given root node
            aggregates += self._find_releases(item, True)

        # Filter out aggregates that don't have studies referencing them
        aggregates_with_study = [agg for agg in aggregates if agg.study_count > 0]

        return aggregates_with_study

    def find_releases(
        self, uid: str, return_study_count: Optional[bool] = True
    ) -> Iterable[_AggregateRootType]:
        """
        Get releases implementation - gets all releases for library object identified by 'uid'
        """
        root: Optional[VersionRoot] = self.root_class.nodes.get_or_none(uid=uid)

        if not root:
            raise exceptions.NotFoundException(
                f"Not Found - The template with the specified 'uid' wasn't found: {uid}"
            )
        return self._find_releases(root, return_study_count)

    def _find_releases(
        self, root: VersionRoot, return_study_count: Optional[bool] = True
    ) -> Iterable[_AggregateRootType]:
        """
        Get all releases for provided version root node
        """
        library: Library = root.has_library.get()
        releases: Sequence[VersionValue] = []

        final_versions = root.has_version.match(
            status=LibraryItemStatus.FINAL.value
        ).all()
        releases += final_versions
        latest_final = root.latest_final.get_or_none()
        if latest_final is not None:
            releases.append(latest_final)

        deduped_releases = []
        for release in releases:
            id_list = [_v.id for _v in deduped_releases]
            if release.id not in id_list:
                deduped_releases.append(release)

        aggregates = []
        for release in deduped_releases:
            latest_final = root.latest_final.relationship(release)
            latest_version = next(
                filter(
                    lambda v: v.status == LibraryItemStatus.FINAL.value,
                    root.has_version.all_relationships(release),
                ),
                None,
            )
            relationship: VersionRelationship = (
                latest_final if latest_final else latest_version
            )

            if return_study_count:
                study_count: int = self._get_study_count(release)
                ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root,
                    library=library,
                    relationship=relationship,
                    value=release,
                    study_count=study_count,
                )
            else:
                ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root, library=library, relationship=relationship, value=release
                )
            ar.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            aggregates.append(ar)

        return aggregates

    def _query_uid_by_id(self, node_id: int) -> Optional[str]:
        result, _ = db.cypher_query(
            "MATCH (node) WHERE ID(node) = $id RETURN node.uid as uid", {"id": node_id}
        )
        return result[0][0] if len(result) > 0 else None

    def find_related_objects_by_uid(self, uid) -> Sequence[_AggregateRootType]:
        root: VersionRoot = self.root_class.nodes.get(uid=uid)
        items = root.has_template.all()
        return [self.find_by_uid_2(it.uid) for it in items]

    def hashkey_library_item(
        self,
        uid: str,
        *,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
        return_study_count: Optional[bool] = False,
        return_instantiation_counts: bool = False,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.

        We need to define this custom hashing function with the same signature as the method we wish to cache (find_by_uid_2),
        since the target method contains optional/default parameters.
        If this custom hashkey function is not defined, most invocations of find_by_uid_2 method will be misses.
        """
        return hashkey(
            str(self.__class__),
            uid,
            version,
            status,
            at_specific_date,
            for_update,
            return_study_count,
            return_instantiation_counts,
        )

    @cached(cache=cache_store_item_by_uid, key=hashkey_library_item)
    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
        return_study_count: Optional[bool] = False,
        return_instantiation_counts: bool = False,
    ) -> Optional[_AggregateRootType]:
        if for_update and (
            version is not None or status is not None or at_specific_date is not None
        ):
            raise NotImplementedError(
                "Retrieval for update supported only for latest version."
            )

        if for_update:
            self._lock_object(uid)

        if not self._is_repository_related_to_ct():
            try:
                root: Optional[VersionRoot] = self.root_class.nodes.get_or_none(uid=uid)
            except NodeClassNotDefined as exc:
                raise VersioningException(
                    "Object labels were changed - likely the object was deleted in a concurrent transaction."
                ) from exc
            if root is None:
                return None
            if self.has_library:
                library: Library = root.has_library.get()
            else:
                library = None
        else:
            result, _ = db.cypher_query(
                "MATCH (node) WHERE ID(node)=$id RETURN node",
                {"id": int(uid)},
                resolve_objects=True,
            )
            root = result[0][0]
            if root is None:
                return None
            ct_root = root.has_root.single()
            if self.has_library:
                library: Library = ct_root.has_library.get()
            else:
                library = None

        value: Optional[VersionValue]
        if version is None:
            if status is None:
                if at_specific_date is None:
                    value = root.has_latest_value.single()
                    if return_instantiation_counts:
                        final, draft, retired = self._get_counts(root)
                        counts = InstantiationCountsVO.from_counts(
                            final=final, draft=draft, retired=retired
                        )
                        if return_study_count:
                            study_count = self._get_study_count(value)
                            result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                                root=root,
                                library=library,
                                relationship=self._get_latest_version(root, value),
                                value=value,
                                counts=counts,
                                study_count=study_count,
                            )
                        else:
                            result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                                root=root,
                                library=library,
                                relationship=self._get_latest_version(root, value),
                                value=value,
                                counts=counts,
                            )
                    else:
                        counts = None
                        if return_study_count:
                            study_count = self._get_study_count(value)
                            result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                                root=root,
                                library=library,
                                relationship=self._get_latest_version(root, value),
                                value=value,
                                study_count=study_count,
                            )
                        else:
                            result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                                root=root,
                                library=library,
                                relationship=self._get_latest_version(root, value),
                                value=value,
                            )
                    if for_update:
                        result.repository_closure_data = (
                            root,
                            value,
                            library,
                            copy.deepcopy(result),
                        )
                    return result
                matching_values: Sequence[VersionValue] = root.has_version.match(
                    start_date__lte=at_specific_date
                )
                latest_matching_relationship: Optional[VersionRelationship] = None
                latest_matching_value: Optional[VersionValue] = None
                for matching_value in matching_values:
                    relationships: Sequence[
                        VersionRelationship
                    ] = root.has_version.all_relationships(matching_value)
                    for relationship in relationships:
                        if (
                            latest_matching_relationship is None
                            or latest_matching_relationship.start_date
                            < relationship.start_date
                        ):
                            latest_matching_relationship = relationship
                            latest_matching_value = matching_value

            else:
                relationship_for_retrieve: Optional[VersionRelationship] = None
                value_for_retrieve: Optional[VersionValue] = None
                relationship_manager_to_use: RelationshipManager = root.latest_retired
                if status == LibraryItemStatus.FINAL:
                    relationship_manager_to_use = root.latest_final
                elif status == LibraryItemStatus.DRAFT:
                    relationship_manager_to_use = root.latest_draft
                value_for_retrieve = relationship_manager_to_use.get_or_none()
                if value_for_retrieve is None:
                    value_for_retrieve = root.has_version.match(status=status.value)
                    return None
                relationship_for_retrieve = relationship_manager_to_use.relationship(
                    value_for_retrieve
                )
                if return_study_count:
                    study_count = self._get_study_count(value_for_retrieve)
                    result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root,
                        value=value_for_retrieve,
                        library=library,
                        relationship=relationship_for_retrieve,
                        study_count=study_count,
                    )
                else:
                    result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                        root=root,
                        value=value_for_retrieve,
                        library=library,
                        relationship=relationship_for_retrieve,
                    )
                result.repository_closure_data = RETRIEVED_READ_ONLY_MARK
                return result
        else:
            matching_value = root.get_value_for_version(version)
            latest_matching_relationship: Optional[VersionRelationship] = None
            latest_matching_value: Optional[VersionValue] = None
            if matching_value is not None:
                latest_matching_relationship = root.get_relation_for_version(version)
                latest_matching_value = matching_value

            if latest_matching_relationship is None:
                return None

            if (
                status is not None
                and latest_matching_relationship.status != status.value
            ):
                return None

            if return_study_count:
                study_count = self._get_study_count(latest_matching_value)
                result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root,
                    library=library,
                    relationship=latest_matching_relationship,
                    value=latest_matching_value,
                    study_count=study_count,
                )
            else:
                result = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
                    root=root,
                    library=library,
                    relationship=latest_matching_relationship,
                    value=latest_matching_value,
                )
            result.repository_closure_data = RETRIEVED_READ_ONLY_MARK
            return result
        return None

    def _get_counts(self, item: VersionRoot) -> Tuple[int, int, int]:
        finals: int
        drafts: int
        retired: int
        finals, drafts, retired = item.get_instantiations_count()
        return (finals, drafts, retired)

    def _get_version_data_from_db(
        self,
        item: Union[VersionRoot, ControlledTerminology],
        value: Union[VersionValue, ControlledTerminology],
        relation: VersionRelationship,
    ) -> Tuple[Mapping, VersionValue, VersionRelationship]:
        if not self.has_library:
            library = None
        elif not self._is_repository_related_to_ct():
            library: Library = item.has_library.get()
        else:
            library: Library = item.has_root.single().has_library.get()
        data = value.to_dict()
        rdata = data.copy()
        rdata.update(relation.to_dict())
        if library is not None:
            rdata["library_name"] = library.name
            rdata["library_is_editable"] = library.is_editable

        return rdata, value, relation

    # noinspection PyMethodMayBeStatic
    def _get_current_user_initials(self) -> Optional[str]:
        # return None  # means this base implementation does not know current user
        # in which case it's going ot be taken from domain layer object (see below)
        return self.user_initials

    def _library_item_metadata_vo_to_datadict(
        self, item_metadata: LibraryItemMetadataVO
    ) -> Mapping[str, Any]:
        # if the repository knows who is logged in, domain information will be ignored
        user_initials = item_metadata.user_initials
        # assert user_initials == item_metadata.user_initials  # however we assume it should not differ
        return {
            "user_initials": user_initials,
            "change_description": item_metadata.change_description,
            "version": item_metadata.version,
            "status": item_metadata.status.value,
            "start_date": item_metadata.start_date,
            "end_date": item_metadata.end_date,
        }

    def _create(self, item: _AggregateRootType) -> _AggregateRootType:
        """
        Creates new VersionedObject AR, checks possibility based on
        library setting, then creates database representation,
        creates TemplateParameters database objects, recreates AR based
        on created database model and returns created AR.
        Saving into database is necessary due to uid creation process that
        require saving object to database.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class(uid=item.uid)
        # If the item is a template, it might have an "editable_instance" property
        # Instances don't have this property, so we need to check for it
        if hasattr(item, "editable_instance"):
            root.editable_instance = item.editable_instance
        self._db_save_node(root)

        value = self._get_or_create_value(root=root, ar=item)

        library = self._get_library(item.library.name)

        (root, value, _, _, _,) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        # Connect root node to library node
        root.has_library.connect(library)

        self._maintain_parameters(item, root, value)

        return item

    @staticmethod
    def _library_item_metadata_vo_from_relation(
        relationship: VersionRelationship,
    ) -> LibraryItemMetadataVO:
        major, minor = relationship.version.split(".")
        return LibraryItemMetadataVO.from_repository_values(
            change_description=relationship.change_description,
            status=LibraryItemStatus(relationship.status),
            author=relationship.user_initials,
            start_date=relationship.start_date,
            end_date=relationship.end_date,
            major_version=int(major),
            minor_version=int(minor),
        )

    def _create_from_neomodel_objects(
        self, root: VersionRoot, value: VersionValue, library: Library
    ) -> _AggregateRootType:
        """
        Creates a VOAR representation from a set of neomodel objects
        (c.q. the nodes in the graph).
        """
        # template_vo = self._get_template(root, value)
        # try:
        #    library = root.has_library.get()
        #    library_vo = LibraryVO.from_input_values_2(library_name=library.name,
        #                                               is_library_editable_callback=(lambda _: library.is_editable))
        # except DoesNotExist:
        #    raise NotFoundException(
        #        "The library for object could not be found.")

        relationship: VersionRelationship = self._get_latest_version(root, value)

        versioned_object_ar = self._create_aggregate_root_instance_from_version_root_relationship_and_value(
            root=root, library=library, relationship=relationship, value=value
        )

        # injecting database objects into versioned_object_ar
        versioned_object_ar.repository_closure_data = (
            root,
            value,
            library,
            copy.deepcopy(versioned_object_ar),
        )
        return versioned_object_ar

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, item: _AggregateRootType) -> None:
        if item.repository_closure_data is RETRIEVED_READ_ONLY_MARK:
            raise NotImplementedError(
                "Only instances which were retrieved for update can be saved by the repository."
            )
        if item.repository_closure_data is not None and not item.is_deleted:
            self._update(item)
        elif item.is_deleted:
            assert item.uid is not None
            self._soft_delete(item.uid)
        else:
            self._create(item)

    def _soft_delete(self, uid: str) -> None:
        label = self.root_class.__label__
        db.cypher_query(
            f"""
            MATCH (otr:{label} {{uid: $uid}})-[latest_draft:LATEST_DRAFT]->(otv)
            WHERE NOT (otr)-[:LATEST_FINAL|HAS_VERSION {{version:'Final'}}]->()
            CREATE (otr)-[v:HAS_VERSION]->(otv)
            SET v = latest_draft,
                v.end_date = datetime(apoc.date.toISO8601(datetime().epochSeconds, 's'))
            SET otr:Deleted{label}
            REMOVE otr:{label}
            """,
            {"uid": uid},
        )

    def check_exists_final_version(self, uid: str) -> bool:
        root_node = self.root_class.nodes.get_or_none(uid=uid)
        if root_node is not None:
            return root_node.latest_final.get_or_none() is not None
        return False

    def _parse_parameter_values(
        self, instance_parameters
    ) -> Dict[int, Sequence[ParameterValueEntryVO]]:
        # Note that this method is used both by templates for default values and instances for values
        # Hence the checks we have to make on the existence of the set_number property
        parameter_strings = []
        # First, parse results from the database
        for position_parameters in instance_parameters:
            position, param_name, param_values, _ = position_parameters
            if len(param_values) == 0:
                # If we find an empty (NA) parameter value, temporary save a none object that will be replaced later
                parameter_strings.append(
                    {
                        "set_number": 0,
                        "position": position,
                        "index": None,
                        "definition": None,
                        "template": None,
                        "parameter_uid": None,
                        "parameter_value": None,
                        "parameter_name": param_name,
                    }
                )

            for parameter in param_values:
                parameter_strings.append(
                    {
                        "set_number": parameter["set_number"]
                        if "set_number" in parameter
                        else 0,
                        "position": parameter["position"],
                        "index": parameter["index"],
                        "parameter_name": parameter["parameter_name"],
                        "parameter_value": parameter["parameter_value"],
                        "parameter_uid": parameter["parameter_uid"],
                        "definition": parameter["definition"],
                        "template": parameter["template"],
                    }
                )

        # Then, start building the nested dictionary to group parameter values in a list
        data_dict = {}
        # Create the first two levels, like
        # set_number
        # --> position
        for param in parameter_strings:
            if not param["set_number"] in data_dict:
                data_dict[param["set_number"]] = {}
            data_dict[param["set_number"]][param["position"]] = {
                "parameter_name": param["parameter_name"],
                "definition": param["definition"],
                "template": param["template"],
                "parameter_uids": [],
                "conjunction": next(
                    filter(
                        lambda x, param=param: x[0] == param["position"]
                        and (
                            len(x[2]) == 0
                            or (
                                "set_number" in x[2][0]
                                and x[2][0]["set_number"] == param["set_number"]
                            )
                        ),
                        instance_parameters,
                    )
                )[3],
            }

        # Then, unwind to create the third level, like:
        # set_number
        # --> position
        # -----> [parameter_uids]
        for param in parameter_strings:
            data_dict[param["set_number"]][param["position"]]["parameter_uids"].append(
                {
                    "index": param["index"],
                    "parameter_uid": param["parameter_uid"],
                    "parameter_name": param["parameter_name"],
                    "parameter_value": param["parameter_value"],
                }
            )

        # Finally, convert the nested dictionary to a list of ParameterValueEntryVO objects, grouped by value set
        return_dict = {}
        for set_number, value_set in data_dict.items():
            value_set = [x[1] for x in sorted(value_set.items(), key=lambda x: x[0])]
            parameter_list = []
            for item in value_set:
                value_list = []
                if item.get("definition"):
                    tpcr = TemplateParameterComplexRoot.nodes.get(
                        uid=item["parameter_uids"][0]["parameter_uid"]
                    )
                    defr: ParameterTemplateRoot = tpcr.has_complex_value.get()
                    tpcv: TemplateParameterComplexValue = tpcr.latest_final.get()
                    items = tpcv.get_all()
                    cpx_params = []
                    param_values = []
                    for itemp in items:
                        param_values.append(
                            {
                                "position": itemp[2],
                                "value": itemp[3],
                                "vv": itemp[4],
                                "item": itemp[1],
                            }
                        )
                    param_values = sorted(param_values, key=lambda x: x["position"])
                    for param in param_values:
                        if param["value"] is not None:
                            tp = NumericParameterValueVO(
                                uid=param["item"], value=param["value"]
                            )
                        else:
                            tp = SimpleParameterValueVO(
                                uid=param["item"], value=param["vv"]
                            )
                        cpx_params.append(tp)
                    parameter_list.append(
                        ComplexParameterValue(
                            uid=defr.uid,
                            parameter_template=item["template"],
                            parameters=cpx_params,
                        )
                    )
                else:
                    for value in sorted(
                        item["parameter_uids"],
                        key=lambda x: x["index"] if not x["index"] is None else 0,
                    ):
                        if value["parameter_uid"]:
                            pv = self._parameter_from_repository_values(value)
                            value_list.append(pv)
                    pve = ParameterValueEntryVO.from_repository_values(
                        parameters=value_list,
                        parameter_name=item["parameter_name"],
                        conjunction=item.get("conjunction", ""),
                    )
                    parameter_list.append(pve)
            return_dict[set_number] = parameter_list
        return return_dict

    def _parameter_from_repository_values(self, value):
        pv = SimpleParameterValueVO.from_repository_values(
            uid=value["parameter_uid"], value=value["parameter_value"]
        )
        return pv

    def close(self) -> None:
        pass

    def _get_uid_or_none(self, node):
        return node.uid if node is not None else None
