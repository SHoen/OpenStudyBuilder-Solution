from typing import Generic, Iterable, Optional, TypeVar

from clinical_mdr_api.domain_repositories.simple_dictionaries._simple_terminology_item_repository import (  # type: ignore
    SimpleTerminologyItemRepository,
)

DictionaryItemType = TypeVar("DictionaryItemType")


class SimpleTerminologyBasedDictionaryItemRepository(Generic[DictionaryItemType]):
    _simple_terminology_item_repository: SimpleTerminologyItemRepository

    _dictionary_item_type: Optional[type] = None
    _codelist_code: Optional[str] = None

    def __init__(
        self, simple_terminology_item_repository: SimpleTerminologyItemRepository
    ):
        self._simple_terminology_item_repository = simple_terminology_item_repository

    def find_all(self) -> Iterable[DictionaryItemType]:
        assert (
            self._dictionary_item_type is not None
        ), "-dictionary_item_type class var mus be assigned by subclass"
        codelist_code = self._codelist_code  # type: ignore
        assert codelist_code is not None
        return {
            # pylint:disable=not-callable
            self._dictionary_item_type(
                code=item.code,
                name=item.nci_preferred_term,
                definition=item.cdisc_definition,
            )
            for item in self._simple_terminology_item_repository.find_by_codelist_code(
                codelist_code
            )
        }

    def find_by_code(self, code: str) -> Optional[DictionaryItemType]:
        assert (
            self._dictionary_item_type is not None
        ), "-dictionary_item_type class var mus be assigned by subclass"
        codelist_code = self._codelist_code  # type: ignore
        assert codelist_code is not None
        terminology_item = (
            self._simple_terminology_item_repository.find_by_code_and_codelist_code(
                code, codelist_code
            )
        )
        return (
            # pylint:disable=not-callable
            self._dictionary_item_type(
                code=terminology_item.code,
                name=terminology_item.nci_preferred_term,
                definition=terminology_item.cdisc_definition,
            )
            if terminology_item is not None
            else None
        )

    def close(self) -> None:
        # we do not close injected simple_terminology_item_repository since we have not created it
        # as a rule we should cleanup only those resources we have initialized
        pass

    def __del__(self):
        self.close()
