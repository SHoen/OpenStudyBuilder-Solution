import unittest
from typing import Callable

from clinical_mdr_api.domain.concepts.activities.special_purpose import (
    SpecialPurposeAR,
    SpecialPurposeVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_special_purpose_vo() -> SpecialPurposeVO:
    random_special_purpose_vo = SpecialPurposeVO.from_repository_values(
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
    return random_special_purpose_vo


def create_random_special_purpose_ar(
    # pylint:disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> SpecialPurposeAR:
    random_special_purpose_ar = SpecialPurposeAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_special_purpose_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        concept_exists_by_name_callback=lambda _: False,
        activity_hierarchy_exists_by_uid_callback=lambda _: True,
        ct_term_exists_callback=lambda _: True,
    )

    return random_special_purpose_ar


class TestSpecialPurpose(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        special_purpose_ar = create_random_special_purpose_ar()

        # then
        self.assertIsNone(special_purpose_ar.item_metadata._end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata._start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "0.1")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()

        # when
        special_purpose_ar.approve(author="TODO")

        # then
        self.assertIsNone(special_purpose_ar.item_metadata._end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata._start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "1.0")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()
        special_purpose_ar.approve(author="TODO")

        # when
        special_purpose_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(special_purpose_ar.item_metadata._end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata._start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "1.1")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__inactivate_final__version_created(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()
        special_purpose_ar.approve(author="TODO")

        # when
        special_purpose_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(special_purpose_ar.item_metadata._end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata._start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "1.0")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()
        special_purpose_ar.approve(author="TODO")
        special_purpose_ar.inactivate(author="TODO")

        # when
        special_purpose_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(special_purpose_ar.item_metadata._end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata._start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "1.0")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()

        # when
        special_purpose_ar.soft_delete()

        # then
        self.assertTrue(special_purpose_ar.is_deleted)

    def test__edit_draft_version__version_created(self):
        # given
        special_purpose_ar = create_random_special_purpose_ar()

        special_purpose_ar.approve(author="Test")
        special_purpose_ar.create_new_version(author="TODO")

        # when
        compound_dosing_vo = create_random_special_purpose_vo()

        special_purpose_ar.edit_draft(
            author="TODO",
            change_description="Test",
            concept_vo=compound_dosing_vo,
            concept_exists_by_name_callback=lambda _: False,
            activity_hierarchy_exists_by_uid_callback=lambda _: True,
            ct_term_exists_callback=lambda _: True,
        )
        # then
        self.assertIsNone(special_purpose_ar.item_metadata.end_date)
        self.assertIsNotNone(special_purpose_ar.item_metadata.start_date)
        self.assertEqual(special_purpose_ar.item_metadata.version, "1.2")
        self.assertEqual(
            special_purpose_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(special_purpose_ar.item_metadata.user_initials, "TODO")
        self.assertEqual(special_purpose_ar.item_metadata.change_description, "Test")
        self.assertEqual(special_purpose_ar.name, compound_dosing_vo.name)
        self.assertEqual(
            special_purpose_ar.concept_vo.name_sentence_case,
            compound_dosing_vo.name_sentence_case,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.definition, compound_dosing_vo.definition
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.topic_code, compound_dosing_vo.topic_code
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.adam_param_code,
            compound_dosing_vo.adam_param_code,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.legacy_description,
            compound_dosing_vo.legacy_description,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.sdtm_variable_uid,
            compound_dosing_vo.sdtm_variable_uid,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.sdtm_subcat_uid,
            compound_dosing_vo.sdtm_subcat_uid,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.sdtm_cat_uid, compound_dosing_vo.sdtm_cat_uid
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.sdtm_domain_uid,
            compound_dosing_vo.sdtm_domain_uid,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.activity_uids,
            compound_dosing_vo.activity_uids,
        )
        self.assertEqual(
            special_purpose_ar.concept_vo.activity_type,
            compound_dosing_vo.activity_type,
        )
