from typing import Optional, Sequence

from neomodel import db  # type: ignore

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.models import ProjectCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore


class ProjectService:

    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"

    def get_all_projects(self) -> Sequence[models.Project]:
        repos = MetaRepository()
        try:
            all_projects = repos.project_repository.find_all()
            repos.project_repository.close()
            return [
                models.Project.from_project_ar(
                    project_ar, repos.clinical_programme_repository.find_by_uid
                )
                for project_ar in all_projects
            ]
        finally:
            repos.close()

    def get_by_study_uid(self, study_uid: str) -> models.Project:
        repos = MetaRepository()
        project_ar = repos.project_repository.find_by_study_uid(study_uid)
        return models.Project.from_project_ar(
            project_ar, repos.clinical_programme_repository.find_by_uid
        )

    @db.transaction
    def create(self, project_create_input: ProjectCreateInput) -> models.Project:
        repos = MetaRepository()
        try:
            try:
                project_ar = ProjectAR.from_input_values(
                    project_number=project_create_input.projectNumber,
                    name=project_create_input.name,
                    clinical_programme_uid=project_create_input.clinicalProgrammeUid,
                    description=project_create_input.description,
                    generate_uid_callback=repos.project_repository.generate_uid,
                    clinical_programme_exists_callback=repos.clinical_programme_repository.clinical_programme_exists,
                )
            except ValueError as value_error:
                raise exceptions.ValidationException(value_error.args[0])

            repos.project_repository.save(project_ar)
            return models.Project.from_uid(
                uid=project_ar.uid,
                find_by_uid=repos.project_repository.find_by_uid,
                find_clinical_programme_by_uid=repos.clinical_programme_repository.find_by_uid,
            )
        finally:
            repos.close()
