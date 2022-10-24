from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.domain.concepts.compound import CompoundAR, CompoundVO
from clinical_mdr_api.domain.versioned_object_aggregate import VersioningException
from clinical_mdr_api.domain_repositories.concepts.compound_repository import (
    CompoundRepository,
)
from clinical_mdr_api.models.compound import (
    Compound,
    CompoundCreateInput,
    CompoundEditInput,
    CompoundVersion,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)


class CompoundService(ConceptGenericService[CompoundAR]):
    aggregate_class = CompoundAR
    version_class = CompoundVersion
    repository_interface = CompoundRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CompoundAR
    ) -> Compound:
        return Compound.from_compound_ar(
            compound_ar=item_ar,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid_2,
            find_substance_term_by_uid=self._repos.dictionary_term_substance_repository.find_by_uid_2,
            find_numeric_value_by_uid=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            find_lag_time_by_uid=self._repos.lag_time_repository.find_by_uid_2,
            find_unit_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_project_by_uid=self._repos.project_repository.find_by_uid,
            find_brand_by_uid=self._repos.brand_repository.find_by_uid,
            find_clinical_programme_by_uid=self._repos.clinical_programme_repository.find_by_uid,
        )

    def _create_aggregate_root(
        self, concept_input: CompoundCreateInput, library
    ) -> _AggregateRootType:
        return CompoundAR.from_input_values(
            author=self.user_initials,
            concept_vo=CompoundVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.nameSentenceCase,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                dose_frequency_uids=concept_input.doseFrequencyUids,
                dose_values_uids=concept_input.doseValuesUids,
                strength_values_uids=concept_input.strengthValuesUids,
                lag_time_uids=concept_input.lagTimesUids,
                dosage_form_uids=concept_input.dosageFormUids,
                route_of_administration_uids=concept_input.routeOfAdministrationUids,
                half_life_uid=concept_input.halfLifeUid,
                analyte_number=concept_input.analyteNumber,
                nnc_short_number=concept_input.nncShortNumber,
                nnc_long_number=concept_input.nncLongNumber,
                is_sponsor_compound=concept_input.isSponsorCompound,
                is_name_inn=concept_input.isNameInn,
                substance_terms_uids=concept_input.substanceTermsUids,
                delivery_devices_uids=concept_input.deliveryDevicesUids,
                dispensers_uids=concept_input.dispensersUids,
                projects_uids=concept_input.projectsUids,
                brands_uids=concept_input.brandsUids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            compound_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            dictionary_term_exists_callback=self._repos.dictionary_term_generic_repository.find_by_uid_2,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            lag_time_exists_callback=self._repos.lag_time_repository.find_by_uid_2,
            project_exists_callback=self._repos.project_repository.find_by_uid,
            brand_exists_callback=self._repos.brand_repository.find_by_uid,
        )

    def _edit_aggregate(
        self, item: CompoundAR, concept_edit_input: CompoundEditInput
    ) -> CompoundAR:
        item.edit_draft(
            author=self.user_initials,
            change_description=concept_edit_input.changeDescription,
            concept_vo=CompoundVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.nameSentenceCase,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                dose_values_uids=concept_edit_input.doseValuesUids,
                strength_values_uids=concept_edit_input.strengthValuesUids,
                lag_time_uids=concept_edit_input.lagTimesUids,
                dose_frequency_uids=concept_edit_input.doseFrequencyUids,
                dosage_form_uids=concept_edit_input.dosageFormUids,
                route_of_administration_uids=concept_edit_input.routeOfAdministrationUids,
                half_life_uid=concept_edit_input.halfLifeUid,
                analyte_number=concept_edit_input.analyteNumber,
                nnc_short_number=concept_edit_input.nncShortNumber,
                nnc_long_number=concept_edit_input.nncLongNumber,
                is_sponsor_compound=concept_edit_input.isSponsorCompound,
                is_name_inn=concept_edit_input.isNameInn,
                substance_terms_uids=concept_edit_input.substanceTermsUids,
                delivery_devices_uids=concept_edit_input.deliveryDevicesUids,
                dispensers_uids=concept_edit_input.dispensersUids,
                projects_uids=concept_edit_input.projectsUids,
                brands_uids=concept_edit_input.brandsUids,
            ),
            compound_uid_by_property_value_callback=self.repository.get_uid_by_property_value,
            ct_term_exists_callback=self._repos.ct_term_name_repository.term_exists,
            dictionary_term_exists_callback=self._repos.dictionary_term_generic_repository.find_by_uid_2,
            numeric_value_exists_callback=self._repos.numeric_value_with_unit_repository.find_by_uid_2,
            lag_time_exists_callback=self._repos.lag_time_repository.find_by_uid_2,
            project_exists_callback=self._repos.project_repository.find_by_uid,
            brand_exists_callback=self._repos.brand_repository.find_by_uid,
        )
        return item

    @db.transaction
    def soft_delete(self, uid: str) -> None:
        try:
            # find all aliases and delete them
            aliases_uids = (
                self._repos.compound_alias_repository.get_aliases_by_compound_uid(
                    compound_uid=uid,
                )
            )
            compound_alias_service = CompoundAliasService(user=self.user_initials)
            for alias_uid in aliases_uids:
                compound_alias = compound_alias_service._find_by_uid_or_raise_not_found(
                    alias_uid, for_update=True
                )
                compound_alias.soft_delete()
                self._repos.compound_alias_repository.save(compound_alias)

            compound = self._find_by_uid_or_raise_not_found(uid, for_update=True)
            compound.soft_delete()
            self.repository.save(compound)
        except VersioningException as e:
            raise exceptions.BusinessLogicException(e.msg)
