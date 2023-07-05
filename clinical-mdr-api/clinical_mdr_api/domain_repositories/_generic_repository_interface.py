import abc
from datetime import datetime
from typing import Generic, Iterable, Optional, TypeVar

from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericRepository(Generic[_AggregateRootType], abc.ABC):

    """
    Generic repository class with definition of necessary actions that
    library versioned objects repository have to support
    """

    @abc.abstractmethod
    def find_all(
        self,
        *,
        status: Optional[LibraryItemStatus] = None,
        library_name: Optional[str] = None,
    ) -> Iterable[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_by_uid_2(
        self,
        uid: str,
        *,
        version: Optional[str] = None,
        status: Optional[LibraryItemStatus] = None,
        at_specific_date: Optional[datetime] = None,
        for_update: bool = False,
    ) -> Optional[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def save(self, item: _AggregateRootType) -> None:
        raise NotImplementedError()

    @property
    @abc.abstractmethod
    def user_initials(self) -> Optional[str]:
        raise NotImplementedError()

    @user_initials.setter
    @abc.abstractmethod
    def user_initials(self, user_initials: str) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all_versions_2(
        self, uid: str, return_study_count: bool = False
    ) -> Iterable[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def find_releases(
        self, uid: str, return_study_count: bool = True
    ) -> Iterable[_AggregateRootType]:
        raise NotImplementedError()

    @abc.abstractmethod
    def check_exists_by_name(self, name: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def check_exists_final_version(self, uid: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def generate_uid_callback(self):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        pass
