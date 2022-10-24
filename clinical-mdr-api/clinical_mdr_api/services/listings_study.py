from clinical_mdr_api import exceptions
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.models.listings_study import (
    RegistryIdentifiersListingModel,
    StudyPopulationListingModel,
    StudyTypeListingModel,
)
from clinical_mdr_api.services._meta_repository import MetaRepository


class StudyListingService:
    _repos = MetaRepository()

    def _close_all_repos(self) -> None:
        self._repos.close()

    def _ct_attr_repos(self):
        return self._repos.ct_term_attributes_repository

    def _dict_term_repos(self):
        return self._repos.dictionary_term_generic_repository

    def get_registry_identifiers(
        self, study_number: int
    ) -> RegistryIdentifiersListingModel:
        try:
            uid = StudyDefinitionRepository.find_uid_by_study_number(study_number)
            if uid is None:
                raise exceptions.NotFoundException(
                    f"Study number '{study_number}' not found."
                )
            study_definition = self._repos.study_definition_repository.find_by_uid(uid)
            if study_definition is None:
                raise exceptions.NotFoundException(
                    f"Study definition '{uid}' not found."
                )
            registry_identifiers = (
                study_definition.current_metadata.id_metadata.registry_identifiers
            )
            result = RegistryIdentifiersListingModel.from_study_registry_identifiers_vo_to_listing(
                registry_identifiers, find_term_by_uid=self._ct_attr_repos().find_by_uid
            )
            return result
        finally:
            self._close_all_repos()

    def get_study_type(self, study_number: int) -> StudyTypeListingModel:
        try:
            uid = StudyDefinitionRepository.find_uid_by_study_number(study_number)
            if uid is None:
                raise exceptions.NotFoundException(
                    f"Study number '{study_number}' not found."
                )
            study_definition = self._repos.study_definition_repository.find_by_uid(uid)
            if study_definition is None:
                raise exceptions.NotFoundException(f"Study '{uid}' not found.")
            high_level_study_design = (
                study_definition.current_metadata.high_level_study_design
            )
            result = StudyTypeListingModel.from_high_level_study_design_vo_to_listing(
                high_level_study_design,
                find_term_by_uid=self._ct_attr_repos().find_by_uid,
            )
            return result
        finally:
            self._close_all_repos()

    def get_study_population(self, study_number: int) -> StudyPopulationListingModel:
        try:
            uid = StudyDefinitionRepository.find_uid_by_study_number(study_number)
            if uid is None:
                raise exceptions.NotFoundException(
                    f"Study number '{study_number}' not found."
                )
            study_definition = self._repos.study_definition_repository.find_by_uid(uid)
            if study_definition is None:
                raise exceptions.NotFoundException(f"Study '{uid}' not found.")
            study_population = study_definition.current_metadata.study_population
            result = StudyPopulationListingModel.from_study_population_vo_to_listing(
                study_population,
                find_term_by_uid=self._ct_attr_repos().find_by_uid,
                find_dictionary_term_by_uid=self._dict_term_repos().find_by_uid,
            )
            return result
        finally:
            self._close_all_repos()
