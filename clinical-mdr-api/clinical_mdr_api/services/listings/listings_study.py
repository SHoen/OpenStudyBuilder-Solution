from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domains.study_selections.study_epoch import TimelineAR
from clinical_mdr_api.models.listings.listings_study import StudyMetadataListingModel
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService


class StudyMetadataListingService:
    _repos = MetaRepository()

    def _close_all_repos(self) -> None:
        self._repos.close()

    @property
    def ct_attr_repo(self):
        return self._repos.ct_term_attributes_repository

    @property
    def dict_term_repo(self):
        return self._repos.dictionary_term_generic_repository

    @property
    def arm_repo(self):
        return self._repos.study_arm_repository

    @property
    def branch_arm_repo(self):
        return self._repos.study_branch_arm_repository

    @property
    def cohort_repo(self):
        return self._repos.study_cohort_repository

    @property
    def element_repo(self):
        return self._repos.study_element_repository

    @property
    def design_cell_repo(self):
        return self._repos.study_design_cell_repository

    @property
    def visit_repo(self):
        return self._repos.study_visit_repository

    @property
    def study_criteria_repo(self):
        return self._repos.study_criteria_repository

    @property
    def criteria_repo(self):
        return self._repos.criteria_repository

    @property
    def study_objective_repo(self):
        return self._repos.study_objective_repository

    @property
    def objective_repo(self):
        return self._repos.objective_repository

    @property
    def study_endpoint_repo(self):
        return self._repos.study_endpoint_repository

    @property
    def endpoint_repo(self):
        return self._repos.endpoint_repository

    @property
    def timeframe_repo(self):
        return self._repos.timeframe_repository

    def get_all_visits(self, study_uid: str, study_value_version: str | None = None):
        study_visits = self.visit_repo.find_all_visits_by_study_uid(
            study_uid=study_uid, study_value_version=study_value_version
        )
        timeline = TimelineAR(study_uid=study_uid, _visits=study_visits)
        assert study_visits is not None
        return timeline.ordered_study_visits

    def get_study_metadata(
        self, study_number: int, version: str | None = None, datetime: str | None = None
    ) -> StudyMetadataListingModel:
        try:
            # To be implemented, replace by real api version
            api_ver = "TBA"

            if version and datetime:
                raise exceptions.ValidationException(
                    "Please specify either version or datetime, not both."
                )
            if version is None and datetime is None:
                raise exceptions.ValidationException(
                    "No version nor datetime was specified, please specify either one of them."
                )
            study_uid = StudyDefinitionRepository.find_uid_by_study_number(study_number)
            if study_uid is None:
                raise exceptions.NotFoundException(
                    f"Study number '{study_number}' not found."
                )
            if datetime:
                version = self._repos.study_definition_repository.get_latest_released_version_from_specific_datetime(
                    study_uid=study_uid, specified_datetime=datetime
                )
                if version is None:
                    raise exceptions.NotFoundException(
                        f"Study number '{study_number}' has no released version before '{datetime}'."
                    )
            study_definition = self._repos.study_definition_repository.find_by_uid(
                uid=study_uid, study_value_version=version
            )
            if study_definition is None:
                raise exceptions.NotFoundException(
                    f"Study definition '{study_uid}' not found."
                )

            project_id = (
                study_definition.version_specific_metadata.id_metadata.project_number
                if study_definition.version_specific_metadata.id_metadata.project_number
                else ""
            )
            study_nr = (
                study_definition.version_specific_metadata.id_metadata.study_number
                if study_definition.version_specific_metadata.id_metadata.study_number
                else ""
            )
            subpart = (
                study_definition.version_specific_metadata.id_metadata.subpart_id
                if study_definition.version_specific_metadata.id_metadata.subpart_id
                else ""
            )

            study_id = project_id + "-" + study_nr + subpart

            result = StudyMetadataListingModel.from_study_metadata_vo(
                api_ver=api_ver,
                study_id=study_id,
                study_ver=version,
                specified_dt=datetime,
                study_metadata_vo=study_definition.version_specific_metadata,
                study_selection_arm_ar=self.arm_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_selection_branch_arm_ar=self.branch_arm_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_selection_cohort_ar=self.cohort_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_epochs=StudyEpochService()
                .get_all_epochs(
                    study_uid=study_uid,
                    study_value_version=version,
                )
                .items,
                study_element_ar=self.element_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_design_cells=self.design_cell_repo.find_all_design_cells_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_visits=self.get_all_visits(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_criteria_ar=self.study_criteria_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_objective_ar=self.study_objective_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                study_endpoint_ar=self.study_endpoint_repo.find_by_study(
                    study_uid=study_uid,
                    study_value_version=version,
                ),
                find_term_by_uid=self.ct_attr_repo.find_by_uid,
                find_dictionary_term_by_uid=self.dict_term_repo.find_by_uid,
                find_criteria_by_uid=self.criteria_repo.find_by_uid,
                find_objective_by_uid=self.objective_repo.find_by_uid,
                find_endpoint_by_uid=self.endpoint_repo.find_by_uid,
                find_timeframe_by_uid=self.timeframe_repo.find_by_uid,
            )
            return result
        finally:
            self._close_all_repos()
