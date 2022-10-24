from abc import ABC
from typing import TypeVar

from clinical_mdr_api.domain.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryItemMetadataVO
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    VersionRoot,
    VersionValue,
)

_AggregateRootType = TypeVar("_AggregateRootType")


class SimpleConceptGenericRepository(ConceptGenericRepository[_AggregateRootType], ABC):
    def _create(self, item: _AggregateRootType) -> _AggregateRootType:

        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class.nodes.get_or_none(uid=item.uid)

        # try to find an existing simple concept root node with given uid
        if root is None:
            root = self.root_class(uid=item.uid)
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

    def _get_or_create_value(
        self, root: VersionRoot, ar: ConceptARBase
    ) -> VersionValue:
        # try to find an existing simple concept value with given name
        value_node = self.value_class.nodes.get_or_none(name=ar.name)
        if value_node is not None:
            return value_node
        new_value = self._create_new_value_node(ar=ar)
        self._db_save_node(new_value)
        return new_value
