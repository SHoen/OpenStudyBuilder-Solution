import unittest
from typing import Callable

from clinical_mdr_api.domain.concepts.activities.numeric_finding import (
    NumericFindingAR,
    NumericFindingVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_numeric_finding_vo() -> NumericFindingVO:
    random_numeric_finding_vo = NumericFindingVO.from_repository_values(
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
        molecular_weight=0,
        convert_to_si_unit=True,
        convert_to_us_conventional_unit=False,
        unit_definition_uid=random_str(),
        unit_dimension_uid=random_str(),
    )
    return random_numeric_finding_vo


def create_random_numeric_finding_ar(
    # pylint:disable=unnecessary-lambda
    generate_uid_callback: Callable[[], str] = lambda: random_str(),
    library: str = "Library",
    is_editable: bool = True,
) -> NumericFindingAR:
    random_numeric_finding_ar = NumericFindingAR.from_input_values(
        generate_uid_callback=generate_uid_callback,
        concept_vo=create_random_numeric_finding_vo(),
        library=LibraryVO.from_repository_values(
            library_name=library, is_editable=is_editable
        ),
        author="TODO Initials",
        numeric_finding_exists_by_name_callback=lambda _: False,
        activity_hierarchy_exists_by_uid_callback=lambda _: True,
        ct_term_exists_callback=lambda _: True,
        unit_definition_exists_callback=lambda _: True,
    )

    return random_numeric_finding_ar


class TestNumericFinding(unittest.TestCase):
    def test__init__ar_created(self):
        # given

        # when
        numeric_finding_ar = create_random_numeric_finding_ar()

        # then
        self.assertIsNone(numeric_finding_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata._start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "0.1")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__approve__version_created(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()

        # when
        numeric_finding_ar.approve(author="TODO")

        # then
        self.assertIsNone(numeric_finding_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata._start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "1.0")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__create_new_version__version_created(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()
        numeric_finding_ar.approve(author="TODO")

        # when
        numeric_finding_ar.create_new_version(author="TODO")

        # then
        self.assertIsNone(numeric_finding_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata._start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "1.1")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )

    def test__inactivate_final__version_created(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()
        numeric_finding_ar.approve(author="TODO")

        # when
        numeric_finding_ar.inactivate(author="TODO")

        # then
        self.assertIsNone(numeric_finding_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata._start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "1.0")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.RETIRED
        )

    def test__reactivate_retired__version_created(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()
        numeric_finding_ar.approve(author="TODO")
        numeric_finding_ar.inactivate(author="TODO")

        # when
        numeric_finding_ar.reactivate(author="TODO")

        # then
        self.assertIsNone(numeric_finding_ar.item_metadata._end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata._start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "1.0")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.FINAL
        )

    def test__delete_draft__object_deleted(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()

        # when
        numeric_finding_ar.soft_delete()

        # then
        self.assertTrue(numeric_finding_ar.is_deleted)

    def test__edit_draft_version__version_created(self):
        # given
        numeric_finding_ar = create_random_numeric_finding_ar()

        numeric_finding_ar.approve(author="Test")
        numeric_finding_ar.create_new_version(author="TODO")

        # when
        numeric_finding_vo = create_random_numeric_finding_vo()

        numeric_finding_ar.edit_draft(
            author="TODO",
            change_description="Test",
            concept_vo=numeric_finding_vo,
            concept_exists_by_name_callback=lambda _: False,
            activity_hierarchy_exists_by_uid_callback=lambda _: True,
            ct_term_exists_callback=lambda _: True,
            unit_definition_exists_callback=lambda _: True,
        )
        # then
        self.assertIsNone(numeric_finding_ar.item_metadata.end_date)
        self.assertIsNotNone(numeric_finding_ar.item_metadata.start_date)
        self.assertEqual(numeric_finding_ar.item_metadata.version, "1.2")
        self.assertEqual(
            numeric_finding_ar.item_metadata.status, LibraryItemStatus.DRAFT
        )
        self.assertEqual(numeric_finding_ar.item_metadata.user_initials, "TODO")
        self.assertEqual(numeric_finding_ar.item_metadata.change_description, "Test")
        self.assertEqual(numeric_finding_ar.name, numeric_finding_vo.name)
        self.assertEqual(
            numeric_finding_ar.concept_vo.name_sentence_case,
            numeric_finding_vo.name_sentence_case,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.definition, numeric_finding_vo.definition
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.topic_code, numeric_finding_vo.topic_code
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.adam_param_code,
            numeric_finding_vo.adam_param_code,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.legacy_description,
            numeric_finding_vo.legacy_description,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.sdtm_variable_uid,
            numeric_finding_vo.sdtm_variable_uid,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.sdtm_subcat_uid,
            numeric_finding_vo.sdtm_subcat_uid,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.sdtm_cat_uid, numeric_finding_vo.sdtm_cat_uid
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.sdtm_domain_uid,
            numeric_finding_vo.sdtm_domain_uid,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.activity_uids,
            numeric_finding_vo.activity_uids,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.activity_type,
            numeric_finding_vo.activity_type,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.specimen_uid, numeric_finding_vo.specimen_uid
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.test_code_uid,
            numeric_finding_vo.test_code_uid,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.molecular_weight,
            numeric_finding_vo.molecular_weight,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.convert_to_si_unit,
            numeric_finding_vo.convert_to_si_unit,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.convert_to_us_conventional_unit,
            numeric_finding_vo.convert_to_us_conventional_unit,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.unit_dimension_uid,
            numeric_finding_vo.unit_dimension_uid,
        )
        self.assertEqual(
            numeric_finding_ar.concept_vo.unit_definition_uid,
            numeric_finding_vo.unit_definition_uid,
        )
