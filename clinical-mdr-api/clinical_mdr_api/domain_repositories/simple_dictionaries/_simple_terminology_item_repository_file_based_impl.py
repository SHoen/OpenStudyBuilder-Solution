import os
from dataclasses import dataclass
from typing import (
    AbstractSet,
    Collection,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    Set,
)

from clinical_mdr_api.domain_repositories._utils.json_file_based_static_repo import (
    JsonFileBasedStaticRepo,  # type: ignore
)
from clinical_mdr_api.domain_repositories.simple_dictionaries._simple_terminology_item_repository import (  # type: ignore
    SimpleTerminologyItem,
    SimpleTerminologyItemRepository,
)

_DEFAULT_SIMPLE_TERMINOLOGY_ITEMS_JSON_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "simple_terminology_items.json"
)


@dataclass(frozen=True)
class _TerminologyItemKey:
    codelist_code: str
    code: str


class SimpleTerminologyItemRepositoryFileBasedImpl(
    JsonFileBasedStaticRepo[_TerminologyItemKey, SimpleTerminologyItem],
    SimpleTerminologyItemRepository,
):
    def _json_object_hook(self, dct: dict) -> SimpleTerminologyItem:
        # we put codelist_name into the json file only for convenience of editing (to see what is what there)
        dct.pop(
            "codelist_name"
        )  # so we remove it before invoking constructor to avoid error
        return SimpleTerminologyItem(**dct)

    @staticmethod
    def _get_key_for_entity_instance(
        instance: SimpleTerminologyItem,
    ) -> _TerminologyItemKey:
        return _TerminologyItemKey(
            codelist_code=instance.codelist_code, code=instance.code
        )

    # we need that to be able to quickly search by part of our key (i.e. codelist_uid)
    _by_code_list: Mapping[str, Collection[SimpleTerminologyItem]]

    @classmethod
    def _store_by_code_list_dictionary(cls, all_items: Iterable[SimpleTerminologyItem]):
        # the method stores a class wide dictionary mapping from codelist_uid to Collection of Terminology items
        new_by_code_list: MutableMapping[str, Set[SimpleTerminologyItem]] = {}
        for item in all_items:
            # we check whether we have that codelist in dict
            if new_by_code_list.get(item.codelist_code) is None:
                # if not we initialize it with this single item
                new_by_code_list[item.codelist_code] = {item}
            else:
                # if there is we just add ne item to the collection associated with this code
                new_by_code_list[item.codelist_code].add(item)

        # now we freeze it (so we can safely return it later)
        frozen_new_code_list: MutableMapping[
            str, AbstractSet[SimpleTerminologyItem]
        ] = {}
        for (codelist_code, terminology_items) in new_by_code_list.items():
            frozen_new_code_list[codelist_code] = frozenset(terminology_items)
        cls._by_code_list = frozen_new_code_list

    def _get_fresh_dictionary_content(self) -> Iterable[SimpleTerminologyItem]:
        # we override this to hook into refresh process to store our _by_code_list dictionary
        result = (
            super()._get_fresh_dictionary_content()
        )  # first we allow super class to its work
        self._store_by_code_list_dictionary(result)  # then store what we need later
        return result  # and return as if nothing unusual happen

    def find_by_codelist_code(
        self, codelist_code: str
    ) -> Iterable[SimpleTerminologyItem]:
        # first we do that to ensure we have content
        self._refresh_if_needed()
        # now we know we have our _by_code_list refreshed as well
        result = self._by_code_list.get(codelist_code)
        return frozenset() if result is None else result

    def find_by_code_and_codelist_code(
        self, code: str, codelist_code: str
    ) -> Optional[SimpleTerminologyItem]:
        return self._find_by_key(
            key=_TerminologyItemKey(codelist_code=codelist_code, code=code)
        )

    def __init__(
        self,
        simple_terminology_items_json_file_path: str = _DEFAULT_SIMPLE_TERMINOLOGY_ITEMS_JSON_FILE_PATH,
    ):
        super().__init__(json_file_path=simple_terminology_items_json_file_path)
