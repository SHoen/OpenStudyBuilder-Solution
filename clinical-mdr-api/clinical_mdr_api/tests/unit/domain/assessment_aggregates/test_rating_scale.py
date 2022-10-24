import unittest
from typing import Callable

from clinical_mdr_api.domain.concepts.activities.rating_scale import (
    RatingScaleAR,
    RatingScaleVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_rating_scale_vo() -> RatingScaleVO:
    random_rating_scale_vo = RatingScaleVO.from_repository_values(
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
        value_sas_display_format=random_str(),
        specimen_uid=random_str(),
        specimen_name=random_str(),
        test_code_uid=random_str(),
        categoric_response_value_uid=random_str(),
        categoric_response_list_uid=random_str(),
    )
    return random_rating_scale_vo


def create_random_rating_scale_ar(
    # pylint:disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> RatingScaleAR:
    random_rating_scale_ar = RatingScaleAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_rating_scale_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        categoric_finding_exists_by_name_callback=lambda _: False,
        activity_hierarchy_exists_by_uid_callback=lambda _: True,
        ct_term_exists_callback=lambda _: True,
    )

    return random_rating_scale_ar


class TestRatingScale(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        rating_scale_ar = create_random_rating_scale_ar()

        # then
        self.assertIsNone(rating_scale_ar.item_metadata._end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata._start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "0.1")
        self.assertEqual(rating_scale_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()

        # when
        rating_scale_ar.approve(author="TODO")

        # then
        self.assertIsNone(rating_scale_ar.item_metadata._end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata._start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "1.0")
        self.assertEqual(rating_scale_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()
        rating_scale_ar.approve(author="TODO")

        # when
        rating_scale_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(rating_scale_ar.item_metadata._end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata._start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "1.1")
        self.assertEqual(rating_scale_ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__inactivate_final__version_created(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()
        rating_scale_ar.approve(author="TODO")

        # when
        rating_scale_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(rating_scale_ar.item_metadata._end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata._start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "1.0")
        self.assertEqual(
            rating_scale_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()
        rating_scale_ar.approve(author="TODO")
        rating_scale_ar.inactivate(author="TODO")

        # when
        rating_scale_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(rating_scale_ar.item_metadata._end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata._start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "1.0")
        self.assertEqual(rating_scale_ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__delete_draft__object_deleted(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()

        # when
        rating_scale_ar.soft_delete()

        # then
        self.assertTrue(rating_scale_ar.is_deleted)

    def test__edit_draft_version__version_created(self):
        # given
        rating_scale_ar = create_random_rating_scale_ar()

        rating_scale_ar.approve(author="Test")
        rating_scale_ar.create_new_version(author="TODO")

        # when
        rating_scale_vo = create_random_rating_scale_vo()

        rating_scale_ar.edit_draft(
            author="TODO",
            change_description="Test",
            concept_vo=rating_scale_vo,
            concept_exists_by_name_callback=lambda _: False,
            activity_hierarchy_exists_by_uid_callback=lambda _: True,
            ct_term_exists_callback=lambda _: True,
        )
        # then
        self.assertIsNone(rating_scale_ar.item_metadata.end_date)
        self.assertIsNotNone(rating_scale_ar.item_metadata.start_date)
        self.assertEqual(rating_scale_ar.item_metadata.version, "1.2")
        self.assertEqual(rating_scale_ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(rating_scale_ar.item_metadata.user_initials, "TODO")
        self.assertEqual(rating_scale_ar.item_metadata.change_description, "Test")
        self.assertEqual(rating_scale_ar.name, rating_scale_vo.name)
        self.assertEqual(
            rating_scale_ar.concept_vo.name_sentence_case,
            rating_scale_vo.name_sentence_case,
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.definition, rating_scale_vo.definition
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.topic_code, rating_scale_vo.topic_code
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.adam_param_code, rating_scale_vo.adam_param_code
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.legacy_description,
            rating_scale_vo.legacy_description,
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.sdtm_variable_uid,
            rating_scale_vo.sdtm_variable_uid,
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.sdtm_subcat_uid, rating_scale_vo.sdtm_subcat_uid
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.sdtm_cat_uid, rating_scale_vo.sdtm_cat_uid
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.sdtm_domain_uid, rating_scale_vo.sdtm_domain_uid
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.activity_uids, rating_scale_vo.activity_uids
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.activity_type, rating_scale_vo.activity_type
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.specimen_uid, rating_scale_vo.specimen_uid
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.test_code_uid, rating_scale_vo.test_code_uid
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.categoric_response_value_uid,
            rating_scale_vo.categoric_response_value_uid,
        )
        self.assertEqual(
            rating_scale_ar.concept_vo.categoric_response_list_uid,
            rating_scale_vo.categoric_response_list_uid,
        )
