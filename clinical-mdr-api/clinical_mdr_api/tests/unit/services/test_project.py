import unittest
from unittest.mock import PropertyMock, patch

from clinical_mdr_api.domain_repositories.projects.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.services.projects.project import ProjectService


class TestProjectService(unittest.TestCase):
    service = ProjectService()

    @patch(
        service.get_all_projects.__module__ + ".MetaRepository.project_repository",
        new_callable=PropertyMock,
    )
    def test__get_all_study_types__mocked_repo__result(
        self, project_repository_property_mock: PropertyMock
    ):
        # given
        repo_instance = ProjectRepository()
        project_repository_property_mock.return_value = repo_instance

        # when
        service_response = self.service.get_all_projects(page_size=0)

        # then
        # we check if project sets are equal (by project_number)
        self.assertEqual(
            {_.project_number for _ in service_response.items},
            {_.project_number for _ in repo_instance.find_all()},
        )

        # then we check whether values retrieved by service agree with those from mocked repo
        for service_response_item in service_response.items:
            self.assertIsNotNone(service_response_item.project_number)
            assert service_response_item.project_number is not None
            repo_item = repo_instance.find_by_project_number(
                service_response_item.project_number
            )
            assert repo_item is not None  # we already check that (by comparing sets)
            self.assertEqual(repo_item.name, service_response_item.name)
            self.assertEqual(repo_item.description, service_response_item.description)
            self.assertEqual(
                repo_item.clinical_programme_uid,
                service_response_item.clinical_programme.uid,
            )
            self.assertEqual(
                repo_item.project_number, service_response_item.project_number
            )
