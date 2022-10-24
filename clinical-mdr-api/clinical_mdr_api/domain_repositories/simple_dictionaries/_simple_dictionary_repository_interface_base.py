import abc
from typing import Generic, Iterable, Optional, TypeVar

SimpleDictionaryEntity = TypeVar("SimpleDictionaryEntity")


class SimpleDictionaryRepositoryInterfaceBase(Generic[SimpleDictionaryEntity], abc.ABC):
    @abc.abstractmethod
    def find_by_code(self, code: str) -> Optional[SimpleDictionaryEntity]:
        """
        Return dictionary item by code.
        :param code:
        :return: item or None if there's no such code in the dictionary
        """
        raise NotImplementedError

    @abc.abstractmethod
    def find_all(self) -> Iterable[SimpleDictionaryEntity]:
        """
        Returns iterable of all dictionary items.
        :return:
        """
        raise NotImplementedError

    def code_exists(self, code: str) -> bool:
        return self.find_by_code(code) is not None
