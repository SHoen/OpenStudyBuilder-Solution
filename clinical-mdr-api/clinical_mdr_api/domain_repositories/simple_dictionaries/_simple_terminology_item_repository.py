from typing import Collection, Optional

# noinspection PyProtectedMember
from clinical_mdr_api.domain.simple_dictionaries.simple_terminology_item import (
    SimpleTerminologyItem,
)


class SimpleTerminologyItemRepository:
    def find_by_code_and_codelist_code(
        self, code: str, codelist_code: str
    ) -> Optional[SimpleTerminologyItem]:
        raise NotImplementedError

    def find_by_codelist_code(
        self, codelist_code: str
    ) -> Collection[SimpleTerminologyItem]:
        raise NotImplementedError

    def close(self) -> None:
        pass

    def __del__(self):
        self.close()
