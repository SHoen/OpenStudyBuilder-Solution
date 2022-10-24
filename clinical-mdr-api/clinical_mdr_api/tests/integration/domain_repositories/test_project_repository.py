import unittest
from typing import Dict

from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.domain_repositories.clinical_programme.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.project.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.tests.integration.domain_repositories._utils import (
    wipe_clinical_programme_repository,
    wipe_project_repository,
)
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str


class TestProjectRepository(unittest.TestCase):
    @classmethod
    def setUp(cls) -> None:
        wipe_project_repository()

    @classmethod
    def setUpClass(cls) -> None:
        clinical_programme_repo = ClinicalProgrammeRepository()
        cls.created_clinical_programme = create_random_clinical_programme(
            clinical_programme_repo.generate_uid
        )
        clinical_programme_repo.save(cls.created_clinical_programme)

    @classmethod
    def tearDownClass(cls) -> None:
        wipe_clinical_programme_repository()

    def test__project_number_exist__non_existing_pr__returns_False(self):
        # given
        non_existing_project_number = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
        repo = ProjectRepository()

        # when
        result = repo.project_number_exists(non_existing_project_number)
        repo.close()

        # then
        self.assertFalse(result)

    def test__project_number_exist__existing_pr__returns_True(self):
        # given
        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)
        result = repo.project_number_exists(created_project.project_number)
        repo.close()

        # then
        self.assertTrue(result)

    def test__find_by_uid__non_existing_uid__returns_none(self):
        # given
        non_existing_uid = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
        repo = ProjectRepository()

        # when
        result = repo.find_by_uid(non_existing_uid)
        repo.close()

        # then
        self.assertIsNone(result)

    def test__find_by_uid__existing_uid__returns_projectAR(self):
        # given
        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)
        result = repo.find_by_uid(created_project.uid)
        repo.close()

        # then
        self.assertEqual(result, created_project)

    def test__create__exists(self):
        # given

        repo = ProjectRepository()
        created_project = create_random_project(
            clinical_programme_uid=self.created_clinical_programme.uid,
            generate_uid_callback=repo.generate_uid,
        )

        # when
        repo.save(created_project)

        # clinical_programme_node = ClinicalProgramme.nodes.get(uid=project.holds_project)
        # project_node.holds_project.connect(clinical_programme_node)

        repo.close()

        # then
        repo = ProjectRepository()
        retrieved_project = repo.find_by_uid(created_project.uid)
        repo.close()

        self.assertEqual(retrieved_project, created_project)

    def test__find_all__existing_projects__returns_projects(self):
        # given
        repo = ProjectRepository()
        test_projects = [
            create_random_project(
                clinical_programme_uid=self.created_clinical_programme.uid,
                generate_uid_callback=repo.generate_uid,
            )
            for _ in range(0, 10)
        ]
        for project in test_projects:
            repo.save(project)
        repo.close()

        # when
        repo = ProjectRepository()
        all_projects_in_db = repo.find_all()
        repo.close()

        # then
        # we check if all test_projects are in all_projects_in_db
        # to achieve this we build a dictionary first
        db_projects: Dict[str, ProjectAR] = {}
        for _project in all_projects_in_db:
            db_projects[_project.uid] = _project

        # then we go by test_projects and assert all of them are in the dictionary
        for test_project in test_projects:
            with self.subTest():
                self.assertEqual(db_projects[test_project.uid], test_project)

    def test__find_all__non_existing_projects__returns_empty_seq(self):
        # given
        repo = ProjectRepository()

        # when
        all_projects_in_db = repo.find_all()
        print(all_projects_in_db)
        repo.close()

        # then
        self.assertTrue(len(all_projects_in_db) == 0)
