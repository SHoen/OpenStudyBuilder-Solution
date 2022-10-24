import unittest

from clinical_mdr_api.domain.templates.timeframe_templates import TimeframeTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    TemplateVO,
)


class TestTimeframeTemplateDomain(unittest.TestCase):
    default_template_name = "Test timeframe template"
    changed_template_name = "New name"

    def test__init__ar_created(self):
        # given

        # when
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )

        # then
        self.assertIsNone(ar.item_metadata._end_date)
        self.assertIsNotNone(ar.item_metadata._start_date)
        self.assertEqual(ar.item_metadata.version, "0.1")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__approve__version_created(self):
        # given
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )

        # when
        ar.approve(author="TODO")

        # then
        self.assertIsNone(ar.item_metadata._end_date)
        self.assertIsNotNone(ar.item_metadata._start_date)
        self.assertEqual(ar.item_metadata.version, "1.0")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.FINAL)

    def test__create_new_version__version_created(self):
        # given
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )
        ar.approve(author="TODO")

        # when
        ntv = TemplateVO.from_repository_values(
            template_name=self.changed_template_name,
            template_name_plain=self.changed_template_name,
        )
        ar.create_new_version(author="TODO", template=ntv, change_description="Test")

        # then
        self.assertIsNone(ar.item_metadata._end_date)
        self.assertIsNotNone(ar.item_metadata._start_date)
        self.assertEqual(ar.item_metadata.version, "1.1")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.DRAFT)

    def test__edit_draft_version__version_created(self):
        # given
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )
        ar.approve(author="Test")
        ntv = TemplateVO.from_repository_values(
            template_name=self.changed_template_name,
            template_name_plain=self.changed_template_name,
        )
        ar.create_new_version(author="TODO", template=ntv, change_description="Test")

        # when
        changed_name_once_more = f"{self.changed_template_name} again"
        ntv = TemplateVO.from_repository_values(
            template_name=changed_name_once_more,
            template_name_plain=changed_name_once_more,
        )
        ar.edit_draft(author="TODO", change_description="Test", template=ntv)

        # then
        self.assertIsNone(ar.item_metadata.end_date)
        self.assertIsNotNone(ar.item_metadata.start_date)
        self.assertEqual(ar.item_metadata.version, "1.2")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.DRAFT)
        self.assertEqual(ar.item_metadata.user_initials, "TODO")
        self.assertEqual(ar.item_metadata.change_description, "Test")
        self.assertEqual(ar.template_value.name, changed_name_once_more)

    def test__inactivate__version_created(self):
        # given
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )
        ar.approve(author="test")

        # when
        ar.inactivate(author="Test")

        # then
        self.assertIsNone(ar.item_metadata._end_date)
        self.assertIsNotNone(ar.item_metadata._start_date)
        self.assertEqual(ar.item_metadata.version, "1.0")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.RETIRED)
        self.assertEqual(ar.item_metadata._author, "Test")
        self.assertEqual(ar.template_value.name, self.default_template_name)

    def test__reactivate__version_created(self):
        # given
        tv = TemplateVO.from_repository_values(
            template_name=self.default_template_name,
            template_name_plain=self.default_template_name,
        )
        lib = LibraryVO.from_repository_values(library_name="Library", is_editable=True)
        # ar = TimeframeTemplateAR(_template=tv, _library=lib)
        ar = TimeframeTemplateAR.from_repository_values(
            template=tv,
            uid="some-uid",
            library=lib,
            item_metadata=LibraryItemMetadataVO.get_initial_item_metadata(
                author="who ever"
            ),
            editable_instance=False,
        )
        ar.approve(author="test")
        ar.inactivate(author="test")

        # when
        ar.reactivate(author="Test")

        # then
        self.assertIsNone(ar.item_metadata.end_date)
        self.assertIsNotNone(ar.item_metadata.start_date)
        self.assertEqual(ar.item_metadata.version, "1.0")
        self.assertEqual(ar.item_metadata.status, LibraryItemStatus.FINAL)
        self.assertEqual(ar.item_metadata.user_initials, "Test")
        self.assertEqual(ar.template_value.name, self.default_template_name)
