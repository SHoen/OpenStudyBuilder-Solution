import collections.abc
from abc import ABC, abstractmethod
from datetime import datetime
from threading import Lock
from typing import (
    Collection,
    Dict,
    Generic,
    Iterable,
    Mapping,
    MutableMapping,
    Optional,
    TypeVar,
)

Key = TypeVar("Key")
Entity = TypeVar("Entity")


class GenericLightDictionaryRepoBase(Generic[Key, Entity], ABC):
    """
    We require both the key and an Entity itself to be immutable, hashable and thread safe (the recommended way
    to achieve this is to use @dataclass(frozen=True) on class used as an Entity. The same for Key if it's need to
    be class otherwise builtin immutables (str, int, tuple, ...) will do.
    We also assume that a key value can be derived from Entity and is stable (means every time derived for the same
    entity instance yields the same value) and uniquely identifies the Entity instance.

    Concrete repositories must implement tho methods (NOTE: the second one is python static method not instance.)

    def _get_fresh_dictionary_content(self) -> Iterable[Entity]:
    def _get_key_for_entity_instance(cls, instance: Entity) -> Key:

    and optionally the third one:

    def _needs_refreshment(self) -> bool

    Concrete repositories are expected to provide some public methods (without leading underscore) which are specific
    to a domain object they host and implemented them with _find_all, _find_by_key and/or _key_exists methods provided
    by this base class.

    """

    @abstractmethod
    def _get_fresh_dictionary_content(self) -> Iterable[Entity]:
        """
        The method is supposed to return an Iterable with full content of the repository (all Entities). It's instance
        method so it can use some resources injected into the into the instance (usually will use some DB transaction
        or connection).
        :return: Iterable with all instances of the Entity.
        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _get_key_for_entity_instance(instance: Entity) -> Key:
        """
        The method is supposed to extract a key value from instance of the Entity.
        It MUST use only information contained in instance, return different value for every instance.
        It MUST be independent of any other resources. Usual implementation is probably returning one of the properties
        of the instance.

        :param instance:  Entity instance to extract key from
        :return: extracted Key
        """
        raise NotImplementedError

    def _needs_refreshment(self) -> bool:
        """
        The method is expected to return True if theres a need to refresh in-memory cached content of the dictionary.
        Here comes the logic which decides whether cached content is too old or not. It may be simple as always False
        (which is the default if superclass does not override the method and means the content will be loaded only once
        at first use of the repository class and every subsequent instance is going to use the same content forever,
        until application restart), may by just simple last_refresh_date and datetime.today() comparison yielding True
        if the difference is too large or even may contain some queries to external resources (which makes sense only
        in case this query has some significant advantage over just retrieving new data).
        It's consulted at most once per repository instance (may be not consulted if repository instance is not used).
        It's instance method so if necessary it can use some resources injected into the instance (e.g. some database
        transaction/connection).

        :return: False - no need to refresh, otherwise True (means there's need to refresh)
        """
        return False

    __cache: Optional[MutableMapping] = None
    __cache_refresh_date: Optional[datetime] = None
    __cache_lock: Optional[Lock] = None
    __lock_creation_lock: Lock = Lock()

    @classmethod
    def __get_cache_lock(cls) -> Lock:
        if cls.__cache_lock is None:
            with cls.__lock_creation_lock:  # this assures no other thread is executing this section in parallel
                if cls.__cache_lock is None:
                    cls.__cache_lock = Lock()
        return cls.__cache_lock

    @classmethod
    def __set_cache(cls, new_cache: MutableMapping[Key, Entity]) -> None:
        cls.__cache = new_cache
        cls.__cache_refresh_date = datetime.today()

    @classmethod
    def __get_cache(cls) -> MutableMapping[Key, Entity]:
        assert cls.__cache is not None
        return cls.__cache

    @classmethod
    def __get_cache_refresh_date(cls) -> Optional[datetime]:
        return cls.__cache_refresh_date

    # for testing rather then use (however works as expected)
    def _get_as_dict(self) -> Mapping[Key, Entity]:
        """
        Returns the content of the repository as Mapping[Key, Entity]. Intended mainly for testing purposes.
        For application use find_by_id, find_all and key_exists methods.
        :return:
        """
        self._refresh_if_needed()
        return dict(self.__get_cache())

    __refresh_checked = False

    def _refresh_if_needed(self) -> None:
        """
        This method should be invoked in the beginning ov every finder in the repository.
        _find_by_id, _find_all, _key_exists are already doing this. So finders based on those need not.
        However there may be some special cases (like a subclass which stores some additional class wide info
        on _get_fresh_dictionary_content invocation, and implements some finder based on that rather than _find_by_id,
        _find_all or _key_exists. Superfluous invocation of this are harmless (so no big worries then).
        :return:
        """
        if self.__refresh_checked:
            return  # we do only one check per instance

        # we note that check is performed (we assure it's done at most once per instance)
        self.__refresh_checked = True

        cache_refresh_date = self.__get_cache_refresh_date()
        if cache_refresh_date is not None and not self._needs_refreshment():
            return  # no need to refresh

        cache_lock: Lock = self.__get_cache_lock()
        if not cache_lock.acquire(blocking=False):
            # it means some other thread is refreshing
            # we need not to wait if we have some data in repo (we have to wait if there is no data)
            # if cache_refresh_data is None then it means we have nothing in cache (never been refreshed)
            if cache_refresh_date is None:
                # if that's the case we have to wait on this lock (only wait - nothing to do)
                # pylint:disable=not-context-manager
                with cache_lock:
                    pass

            # at this point there must be some data in the cache
            # we cannot proceed if the cache has never been refreshed
            # however unless there is some flaw in this implementation that should never happen
            # (in fact it is possible in the case the other thread fails on refreshing, than we fail too
            # ... if there's no connection to the DB or whatever the issue, there is no point in trying impossible)
            assert self.__get_cache_refresh_date() is not None

            #  and we can return to whatever called us
            return

        # this is what we do after successfully acquiring cache_lock
        # (now we are the only thread in this section of code)
        try:
            # now we check if may be some other thread has just managed to refreshed before we acquired a lock
            # we will know that if current cache_refresh_date is different than the one we stored in the beginning
            # (it means some other thread refreshed the cache meanwhile)
            if self.__get_cache_refresh_date() != cache_refresh_date:
                return  # yes, some other thread was faster, so w return (finally clause will release the lock)

            # now we do our job
            # NOTE: we build a new cache as local variable, hence the current cache
            # remains intact and can be safely used by other threads. That's wy we do not need to block other threads
            # while we are refreshing (besides the case when cache has never been refreshed)
            new_cache: Dict[
                Key, Entity
            ] = {}  # this is going to be our new cache content

            # This is the key operation here. It actually retrieves new data from whatever it source is.
            # This operation can be I/O bound.
            new_content: Iterable[Entity] = self._get_fresh_dictionary_content()

            # now we just put new content into dictionary
            for entity_instance in new_content:
                assert isinstance(
                    entity_instance, collections.abc.Hashable
                ), "entity_instance not hashable"
                entity_instance_key = self._get_key_for_entity_instance(entity_instance)
                assert new_cache.get(entity_instance_key) is None, "non unique key"
                new_cache[entity_instance_key] = entity_instance

            # and replace the old_cache (NOTE: set_cache method also stores cache_refresh_date)
            self.__set_cache(new_cache)
        finally:
            # when we are done (with whatever result) we must release the lock
            cache_lock.release()

    def _find_all(self) -> Collection[Entity]:
        """
        Returns all Entities in the repository.
        :return: Collection[Entity]
        """
        self._refresh_if_needed()
        return frozenset(self.__get_cache().values())

    def _find_by_key(self, key: Key) -> Optional[Entity]:
        """
        Finds the Entity by given Key (or returns None if there is none)
        :param key: Key
        :return: Optional[Entity] (i.e. None if does not exists)
        """
        self._refresh_if_needed()
        result = self.__get_cache().get(key)
        assert result is None or self._get_key_for_entity_instance(result) == key
        return result

    def _key_exists(self, key: Key) -> bool:
        """
        Checks whether there is Entity instance identified by given Key in the repository.
        :param key: Key
        :return: True if Entity instance with given key exists (otherwise False)
        """
        return self._find_by_key(key) is not None

    def close(self) -> None:
        """
        This method will be implemented in subclasses.
        It should close any resources used by the repository.
        :return:
        """

    def __del__(self):
        self.close()
