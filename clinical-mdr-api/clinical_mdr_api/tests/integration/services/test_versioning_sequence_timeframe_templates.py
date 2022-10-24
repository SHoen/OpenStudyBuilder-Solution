from unittest import TestCase

from pydantic import BaseModel

import clinical_mdr_api.models.timeframe_template as models
import clinical_mdr_api.services.libraries as library_service
import clinical_mdr_api.services.timeframe_templates as tt_service
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    library_data,
    template_data,
)

service = tt_service.TimeframeTemplateService()


class TestCreate(TestCase):
    TEST_DB_NAME = "ttfversioning"
    ot: BaseModel

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)

    def test_create(self):
        data = {"name": template_data["name"], "libraryName": self.library["name"]}
        timeframe_template = models.TimeframeTemplateCreateInput(**data)
        result = service.create(timeframe_template)
        self.assertIsInstance(result, models.TimeframeTemplate)
        self.assertEqual(result.name, template_data["name"])
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.version, "0.1")
        self.ot = result


# @pytest.mark.skip
class TestDraftEdit(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = models.TimeframeTemplateCreateInput(**template_data)
        cls.ot = service.create(timeframe_template)

    def test_edit(self):
        data = {
            "name": template_data["name"] + " edited",
            "changeDescription": "tested",
        }
        ot = models.TimeframeTemplateEditInput(**data)
        assert isinstance(self.ot, models.TimeframeTemplate)
        result = service.edit_draft(self.ot.uid, ot)
        assert isinstance(result, models.TimeframeTemplate)
        self.assertEqual(result.version, "0.2")
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.name, data["name"])

        data = {
            "name": template_data["name"] + " edited again",
            "changeDescription": "tested",
        }
        ot = models.TimeframeTemplateEditInput(**data)
        result = service.edit_draft(self.ot.uid, ot)
        assert isinstance(result, models.TimeframeTemplate)
        self.assertEqual(result.version, "0.3")
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.name, data["name"])


# @pytest.mark.skip
class TestApprove(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = models.TimeframeTemplateCreateInput(**template_data)
        ot = service.create(timeframe_template)
        assert isinstance(ot, models.TimeframeTemplate)
        cls.ot = ot

    def test_approve(self):
        result = service.approve(self.ot.uid)
        assert isinstance(result, models.TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")


class TestActivation(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = models.TimeframeTemplateCreateInput(**template_data)
        ot = service.create(timeframe_template)
        assert isinstance(ot, models.TimeframeTemplate)
        ot = service.approve(ot.uid)
        assert isinstance(ot, models.TimeframeTemplate)
        cls.ot = ot

    def test_activation(self):
        result = service.inactivate_final(self.ot.uid)
        assert isinstance(result, models.TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Retired")
        with self.assertRaises(BusinessLogicException):
            service.inactivate_final(self.ot.uid)

        result = service.reactivate_retired(self.ot.uid)
        assert isinstance(result, models.TimeframeTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")
        with self.assertRaises(BusinessLogicException):
            service.reactivate_retired(self.ot.uid)


# @pytest.mark.skip
class TestSoftDelete(TestCase):
    TEST_DB_NAME = "ttfversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        timeframe_template = models.TimeframeTemplateCreateInput(**template_data)
        ot = service.create(timeframe_template)
        assert isinstance(ot, models.TimeframeTemplate)
        cls.ot = ot

    def test_softdelete(self):
        service.soft_delete(self.ot.uid)
        repos = MetaRepository()
        item = repos.timeframe_template_repository.find_by_uid_2(self.ot.uid)
        self.assertIsNone(item)
