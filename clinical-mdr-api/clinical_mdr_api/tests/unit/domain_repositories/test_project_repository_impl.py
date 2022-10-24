import unittest
from typing import Collection, Optional, Sequence
from unittest.mock import Mock, patch

from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.project.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.tests.unit.domain.utils import random_opt_str, random_str


class MockClinicalProgramme:
    def __init__(self):
        self._uid = random_str()

    @property
    def uid(self):
        return self._uid


def create_random_project_node() -> Project:
    mocked_relationship = Mock()
    mocked_clinical_programme = MockClinicalProgramme()
    mocked_relationship.single = lambda: mocked_clinical_programme
    random_project = Project(
        uid=random_str(),
        project_number=random_str(),
        name=random_str(),
        holds_project=mocked_relationship,
        description=random_opt_str(),
    )
    return random_project


class TestProjectRepositoryImpl(unittest.TestCase):
    @patch(ProjectRepository.__module__ + ".Project")
    def test__project_number_exists_mocked_project_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        project: Project = create_random_project_node()
        projectMock.nodes.first_or_none.return_value = project

        # when
        doesProjectNumberExist: bool = repo.project_number_exists(
            project.project_number
        )

        # then
        self.assertTrue(doesProjectNumberExist)

    @patch(ProjectRepository.__module__ + ".Project")
    def test__project_number_exists_mocked_project_not_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        projectMock.nodes.first_or_none.return_value = None

        # when
        doesProjectNumberExist: bool = repo.project_number_exists(random_str())

        # then
        self.assertFalse(doesProjectNumberExist)

    @patch(ProjectRepository.__module__ + ".Project")
    def test__find_by_uid_mocked_project_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        project: Project = create_random_project_node()
        projectMock.nodes.get_or_none.return_value = project
        # when
        projectAR: Optional[ProjectAR] = repo.find_by_uid(project.uid)

        # then
        self.assertEqual(project.uid, projectAR.uid)
        self.assertEqual(project.project_number, projectAR.project_number)
        self.assertEqual(project.name, projectAR.name)
        self.assertEqual(
            project.holds_project.single().uid, projectAR.clinical_programme_uid
        )
        self.assertEqual(project.description, projectAR.description)

    @patch(ProjectRepository.__module__ + ".Project")
    def test__find_by_uid_mocked_project_not_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        projectMock.nodes.get_or_none.return_value = None

        # when
        projectAR: Optional[ProjectAR] = repo.find_by_uid(random_str())

        # then
        self.assertIsNone(projectAR)

    @patch(ProjectRepository.__module__ + ".Project")
    def test__find_all_mocked_projects_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        projects: Sequence[Project] = [create_random_project_node() for _ in range(10)]
        projectMock.nodes.all.return_value = projects

        # when
        projectARs: Collection[ProjectAR] = repo.find_all()

        # then
        for project, projectAR in zip(projects, projectARs):
            with self.subTest():
                self.assertEqual(project.uid, projectAR.uid)
                self.assertEqual(project.project_number, projectAR.project_number)
                self.assertEqual(project.name, projectAR.name)
                self.assertEqual(
                    project.holds_project.single().uid, projectAR.clinical_programme_uid
                )
                self.assertEqual(project.description, projectAR.description)

    @patch(ProjectRepository.__module__ + ".Project")
    def test__find_all_mocked_project_not_exist(self, projectMock):
        # given
        repo = ProjectRepository()
        projects: Sequence[Project] = []
        projectMock.nodes.all.return_value = projects

        # when
        projectARs: Collection[ProjectAR] = repo.find_all()

        # then
        self.assertTrue(len(projectARs) == 0)
