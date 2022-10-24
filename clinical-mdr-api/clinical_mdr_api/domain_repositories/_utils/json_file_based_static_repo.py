import json
from abc import ABC, abstractmethod
from typing import Iterable, Optional, TypeVar

from clinical_mdr_api.domain_repositories._utils.generic_light_dictionary_repo_base import (
    GenericLightDictionaryRepoBase,  # type: ignore
)

Key = TypeVar("Key")
Entity = TypeVar("Entity")


class JsonFileBasedStaticRepo(GenericLightDictionaryRepoBase[Key, Entity], ABC):

    _json_filepath: Optional[str] = None

    def _get_fresh_dictionary_content(self) -> Iterable[Entity]:
        """
        Implementation of the base class abstract method. Gets content form a file.
        Subclasses are expected to set _json_file_path at latest on construction of the instance.
        :return:
        """
        if self._json_filepath is None:
            return []
        with open(self._json_filepath, "r", encoding="UTF-8") as data_file:
            return json.load(data_file, object_hook=self._json_object_hook)

    @abstractmethod
    def _json_object_hook(self, dct: dict) -> Entity:
        """
        A json_object hook which is passed to json.load when parsing file. It's supposed to construct the Entity
        instance from given dictionary. See json.load documentation for details (object_hook parameter).
        :param dct:
        :return:
        """
        raise NotImplementedError

    def __init__(self, json_file_path: str = None):
        if json_file_path is not None:
            self._json_filepath = json_file_path
