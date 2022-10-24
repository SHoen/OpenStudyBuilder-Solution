import unittest
from typing import Callable

from clinical_mdr_api.domain.concepts.activities.activity_instance import (
    ActivityInstanceAR,
    ActivityInstanceVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_activity_instance_vo() -> ActivityInstanceVO:
    random_activity_instance_vo = ActivityInstanceVO.from_repository_values(
        name=random_str(),
        name_sentence_case=random_str(),
        definition=random_str(),
        abbreviation=random_str(),
        activity_type=random_str(),
        topic_code=random_str(),
        adam_param_code=random_str(),
        legacy_description=random_str(),
        sdtm_variable_uid=random_str(),
        sdtm_variable_name=random_str(),
        sdtm_subcat_uid=random_str(),
        sdtm_subcat_name=random_str(),
        sdtm_cat_uid=random_str(),
        sdtm_cat_name=random_str(),
        sdtm_domain_uid=random_str(),
        sdtm_domain_name=random_str(),
        activity_uids=[random_str(), random_str()],
        specimen_uid=random_str(),
        specimen_name=random_str(),
    )
    return random_activity_instance_vo


def create_random_activity_instance_ar(
    # pylint:disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> ActivityInstanceAR:

    random_activity_instance_ar = ActivityInstanceAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_activity_instance_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        concept_exists_by_name_callback=lambda _: False,
        activity_hierarchy_exists_by_uid_callback=lambda _: True,
        ct_term_exists_callback=lambda _: True,
    )

    return random_activity_instance_ar


class TestActivityInstance(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        activity_instance_ar = create_random_activity_instance_ar()

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "0.1")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()

        # when
        activity_instance_ar.approve(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")

        # when
        activity_instance_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.1")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__inactivate_final__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")

        # when
        activity_instance_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()
        activity_instance_ar.approve(author="TODO")
        activity_instance_ar.inactivate(author="TODO")

        # when
        activity_instance_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(activity_instance_ar.item_metadata._end_date)
        self.assertIsNotNone(activity_instance_ar.item_metadata._start_date)
        self.assertEqual(activity_instance_ar.item_metadata.version, "1.0")
        self.assertEqual(
            activity_instance_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        activity_instance_ar = create_random_activity_instance_ar()

        # when
        activity_instance_ar.soft_delete()

        # then
        self.assertTrue(activity_instance_ar.is_deleted)
