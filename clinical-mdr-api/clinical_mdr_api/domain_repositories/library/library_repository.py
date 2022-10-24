from typing import MutableMapping, Optional

from clinical_mdr_api.domain.library.library_ar import LibraryAR
from clinical_mdr_api.domain_repositories.models.generic import Library


class LibraryRepository:
    _cache: MutableMapping[str, Optional[LibraryAR]]

    def __init__(self):
        self._cache = {}

    def library_exists(self, library_name: str) -> bool:
        library_node = Library.nodes.get_or_none(name=library_name)
        return bool(library_node)

    def find_by_name(self, name: str) -> Optional[LibraryAR]:
        if name not in self._cache:
            library_node: Optional[Library] = Library.nodes.get_or_none(name=name)
            self._cache[name] = (
                LibraryAR.from_repository_values(
                    library_name=library_node.name, is_editable=library_node.is_editable
                )
                if library_node is not None
                else None
            )
        return self._cache[name]
