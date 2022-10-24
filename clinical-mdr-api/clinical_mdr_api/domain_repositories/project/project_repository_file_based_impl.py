import os
from typing import Collection, Optional

from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.domain_repositories._utils.json_file_based_static_repo import (
    JsonFileBasedStaticRepo,  # type: ignore
)
from clinical_mdr_api.domain_repositories.project.project_repository import (
    ProjectRepository,  # type: ignore
)

_DEFAULT_PROJECTS_JSON_FILE_PATH = os.path.join(
    os.path.dirname(__file__), "projects.json"
)


class ProjectRepositoryFileBasedImpl(
    JsonFileBasedStaticRepo[str, ProjectAR], ProjectRepository
):
    def _json_object_hook(self, dct: dict) -> ProjectAR:
        return ProjectAR(**dct)

    @staticmethod
    def _get_key_for_entity_instance(instance: ProjectAR) -> str:
        return instance.project_number

    def find_all(self) -> Collection[ProjectAR]:
        return self._find_all()

    def project_number_exists(self, project_number: str) -> bool:
        return self._key_exists(project_number)

    def __init__(self, project_json_file_path: str = _DEFAULT_PROJECTS_JSON_FILE_PATH):
        super().__init__(json_file_path=project_json_file_path)

    def find_by_project_number(self, project_number: str) -> Optional[ProjectAR]:
        return self._find_by_key(project_number)
