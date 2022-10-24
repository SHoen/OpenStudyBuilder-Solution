from dataclasses import dataclass, field
from typing import Any, Callable

from clinical_mdr_api.domain._utils import normalize_string


@dataclass
class BrandAR:
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    _uid: str
    name: str

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_input_values(name: str, generate_uid_callback: Callable[[], str]):

        uid = generate_uid_callback()

        return BrandAR(
            _uid=uid,
            name=normalize_string(name),
        )
