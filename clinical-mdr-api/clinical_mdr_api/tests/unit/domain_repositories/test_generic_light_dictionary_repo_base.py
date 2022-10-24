import unittest
from dataclasses import dataclass
from typing import Iterable

# noinspection PyProtectedMember
from clinical_mdr_api.domain_repositories._utils.generic_light_dictionary_repo_base import (
    GenericLightDictionaryRepoBase,
)


@dataclass(frozen=True)
class AnEntity:
    key: str
    value: str


class AnEntityRepository(GenericLightDictionaryRepoBase[str, AnEntity]):
    def _needs_refreshment(self) -> bool:
        raise NotImplementedError

    def _get_fresh_dictionary_content(self) -> Iterable[AnEntity]:
        raise NotImplementedError

    @staticmethod
    def _get_key_for_entity_instance(instance: AnEntity) -> str:
        return instance.key


a_repository_refresh_counter = 0


class ARepository(AnEntityRepository):
    def _needs_refreshment(self) -> bool:
        # this repository will be refreshed only once (on very first use)
        return False

    def _get_fresh_dictionary_content(self) -> Iterable[AnEntity]:
        global a_repository_refresh_counter
        a_repository_refresh_counter += 1
        return {
            AnEntity("ak1", "av1"),
            AnEntity("ak2", "av2"),
        }


b_repository_refresh_counter = 0


class BRepository(AnEntityRepository):
    def _needs_refreshment(self) -> bool:
        # this repository is refreshed once for every instance
        return True

    def _get_fresh_dictionary_content(self) -> Iterable[AnEntity]:
        global b_repository_refresh_counter
        b_repository_refresh_counter += 1
        return {
            AnEntity("bk1", "bv1"),
            AnEntity("bk2", "bv2"),
        }


def do_something_with_entity(entity: AnEntity) -> None:
    assert entity is not None


class TestGenericLightDictionaryRepoBase(unittest.TestCase):
    def test__cache_is_shared_between_instances_and_not_shared_between_classes(self):
        # given
        instance_a_1 = ARepository()
        instance_b_1 = BRepository()
        do_something_with_entity(instance_a_1._find_by_key("ak1"))
        do_something_with_entity(instance_b_1._find_by_key("bk1"))

        # when
        instance_a_2 = ARepository()
        instance_b_2 = BRepository()
        do_something_with_entity(instance_a_2._find_by_key("ak2"))
        do_something_with_entity(instance_b_2._find_by_key("bk2"))

        # then
        self.assertEqual(instance_a_1._get_as_dict(), instance_a_2._get_as_dict())
        self.assertEqual(instance_b_1._get_as_dict(), instance_b_2._get_as_dict())
        self.assertNotEqual(instance_a_2._get_as_dict(), instance_b_2._get_as_dict())
        self.assertEqual(a_repository_refresh_counter, 1)
        self.assertEqual(b_repository_refresh_counter, 2)
