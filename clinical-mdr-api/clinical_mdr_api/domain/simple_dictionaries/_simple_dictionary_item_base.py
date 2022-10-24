from abc import ABC
from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleDictionaryItemBase(ABC):
    code: str
    name: str
    definition: str
