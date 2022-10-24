from unittest import TestCase

from pydantic import BaseModel

import clinical_mdr_api.models.objective_template as models
import clinical_mdr_api.services.libraries as library_service
import clinical_mdr_api.services.objective_templates as service
from clinical_mdr_api.exceptions import BusinessLogicException
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    library_data,
    template_data,
)


class TestCreate(TestCase):
    TEST_DB_NAME = "utversioning"
    ot = None

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)

    def test_create(self):
        data = {"name": template_data["name"], "libraryName": self.library["name"]}
        objective_template = models.ObjectiveTemplateCreateInput(**data)
        result = service.ObjectiveTemplateService().create(objective_template)
        self.assertIsInstance(result, models.ObjectiveTemplate)
        self.assertEqual(result.name, template_data["name"])
        self.assertEqual(result.status, "Draft")
        self.assertEqual(result.version, "0.1")
        self.ot = result.dict()


class TestDraftEdit(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = models.ObjectiveTemplateCreateInput(**template_data)
        cls.ot = service.ObjectiveTemplateService().create(objective_template)
        if isinstance(cls.ot, BaseModel):
            cls.ot = cls.ot.dict()

    def test_edit(self):
        data = {
            "name": template_data["name"] + " edited",
            "changeDescription": "tested",
        }
        ot = models.ObjectiveTemplateEditInput(**data)
        result = service.ObjectiveTemplateService().edit_draft(self.ot["uid"], ot)
        if isinstance(result, BaseModel):
            result = result.dict()
        self.assertEqual(result["version"], "0.2")
        self.assertEqual(result["status"], "Draft")
        self.assertEqual(result["name"], data["name"])

        data = {
            "name": template_data["name"] + " edited again",
            "changeDescription": "tested",
        }
        ot = models.ObjectiveTemplateEditInput(**data)
        result = service.ObjectiveTemplateService().edit_draft(self.ot["uid"], ot)
        if isinstance(result, BaseModel):
            result = result.dict()
        self.assertEqual(result["version"], "0.3")
        self.assertEqual(result["status"], "Draft")
        self.assertEqual(result["name"], data["name"])


class TestApprove(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = models.ObjectiveTemplateCreateInput(**template_data)
        cls.ot = service.ObjectiveTemplateService().create(objective_template)
        if isinstance(cls.ot, BaseModel):
            cls.ot = cls.ot.dict()

    def test_approve(self):
        result = service.ObjectiveTemplateService().approve(self.ot["uid"])
        assert isinstance(result, models.ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")


class TestActivation(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = models.ObjectiveTemplateCreateInput(**template_data)
        ot = service.ObjectiveTemplateService().create(objective_template)
        cls.ot = service.ObjectiveTemplateService().approve(ot.uid)
        if isinstance(cls.ot, BaseModel):
            cls.ot = cls.ot.dict()

    def test_activation(self):
        result = service.ObjectiveTemplateService().inactivate_final(self.ot["uid"])
        assert isinstance(result, models.ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Retired")
        with self.assertRaises(BusinessLogicException):
            service.ObjectiveTemplateService().inactivate_final(self.ot["uid"])

        result = service.ObjectiveTemplateService().reactivate_retired(self.ot["uid"])
        assert isinstance(result, models.ObjectiveTemplate)
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.status, "Final")
        with self.assertRaises(BusinessLogicException):
            service.ObjectiveTemplateService().reactivate_retired(self.ot["uid"])


class TestSoftDelete(TestCase):
    TEST_DB_NAME = "utversioning"

    @classmethod
    def setUp(cls):
        inject_and_clear_db(cls.TEST_DB_NAME)
        cls.library = library_service.create(**library_data)
        objective_template = models.ObjectiveTemplateCreateInput(**template_data)
        cls.ot = service.ObjectiveTemplateService().create(objective_template)
        if isinstance(cls.ot, BaseModel):
            cls.ot = cls.ot.dict()

    def test_softdelete(self):
        service.ObjectiveTemplateService().soft_delete(self.ot["uid"])
        repos = MetaRepository()
        item = repos.objective_template_repository.find_by_uid_2(self.ot["uid"])
        self.assertIsNone(item)
