from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, List, MutableSequence, Optional, Sequence

from clinical_mdr_api.domain.study_definition_aggregate._utils import (
    default_failure_callback_for_variable,  # type: ignore
)
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_configuration import (
    FieldConfiguration,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (  # type: ignore
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


@dataclass
class StudyDefinitionSnapshot:
    """
    Memento object representing StudyDefinition state passed to/from repository.

    *Attributes*:
        * uid - unique id (mandatory)
        * draft_metadata - if provided also implies Study is in DRAFT state (otherwise Study is considered LOCKED)
        * released_metadata - only valid if draft_metadata provided
        * locked_metadata_versions - sequence of locked versions in order of version increasing version numbers
            (version 1 goes first)
    """

    @dataclass
    class StudyMetadataSnapshot:
        """
        Class for representing values of Study metadata in some particular version (DRAFT, RELEASED or LOCKED).
        """

        study_number: Optional[str] = None
        study_acronym: Optional[str] = None
        study_id_prefix: Optional[str] = None
        project_number: Optional[str] = None
        ct_gov_id: Optional[str] = None
        ct_gov_id_null_value_code: Optional[str] = None
        eudract_id: Optional[str] = None
        eudract_id_null_value_code: Optional[str] = None
        universal_trial_number_UTN: Optional[str] = None
        universal_trial_number_UTN_null_value_code: Optional[str] = None
        japanese_trial_registry_id_JAPIC: Optional[str] = None
        japanese_trial_registry_id_JAPIC_null_value_code: Optional[str] = None
        investigational_new_drug_application_number_IND: Optional[str] = None
        investigational_new_drug_application_number_IND_null_value_code: Optional[
            str
        ] = None
        version_timestamp: Optional[datetime] = None
        locked_version_author: Optional[str] = None
        locked_version_info: Optional[str] = None
        study_type_code: Optional[str] = None
        study_type_null_value_code: Optional[str] = None
        trial_intent_type_codes: Sequence[str] = ()
        trial_intent_type_null_value_code: Optional[str] = None
        trial_type_codes: Sequence[str] = ()
        trial_type_null_value_code: Optional[str] = None
        trial_phase_code: Optional[str] = None
        trial_phase_null_value_code: Optional[str] = None
        is_extension_trial: Optional[bool] = None
        is_extension_trial_null_value_code: Optional[str] = None
        is_adaptive_design: Optional[bool] = None
        is_adaptive_design_null_value_code: Optional[str] = None
        post_auth_indicator: Optional[bool] = None
        post_auth_indicator_null_value_code: Optional[str] = None
        study_stop_rules: Optional[str] = None
        study_stop_rules_null_value_code: Optional[str] = None

        therapeutic_area_codes: Sequence[str] = ()
        therapeutic_area_null_value_code: Optional[str] = None

        disease_condition_or_indication_codes: Sequence[str] = ()
        disease_condition_or_indication_null_value_code: Optional[str] = None

        diagnosis_group_codes: Sequence[str] = ()
        diagnosis_group_null_value_code: Optional[str] = None

        sex_of_participants_code: Optional[str] = None
        sex_of_participants_null_value_code: Optional[str] = None

        rare_disease_indicator: Optional[bool] = None
        rare_disease_indicator_null_value_code: Optional[str] = None

        healthy_subject_indicator: Optional[bool] = None
        healthy_subject_indicator_null_value_code: Optional[str] = None

        planned_minimum_age_of_subjects: Optional[str] = None
        planned_minimum_age_of_subjects_null_value_code: Optional[str] = None

        planned_maximum_age_of_subjects: Optional[str] = None
        planned_maximum_age_of_subjects_null_value_code: Optional[str] = None

        stable_disease_minimum_duration: Optional[str] = None
        stable_disease_minimum_duration_null_value_code: Optional[str] = None

        pediatric_study_indicator: Optional[bool] = None
        pediatric_study_indicator_null_value_code: Optional[str] = None

        pediatric_postmarket_study_indicator: Optional[bool] = None
        pediatric_postmarket_study_indicator_null_value_code: Optional[str] = None

        pediatric_investigation_plan_indicator: Optional[bool] = None
        pediatric_investigation_plan_indicator_null_value_code: Optional[str] = None

        relapse_criteria: Optional[str] = None
        relapse_criteria_null_value_code: Optional[str] = None

        number_of_expected_subjects: Optional[int] = None
        number_of_expected_subjects_null_value_code: Optional[str] = None

        intervention_type_code: Optional[str] = None
        intervention_type_null_value_code: Optional[str] = None

        add_on_to_existing_treatments: Optional[bool] = None
        add_on_to_existing_treatments_null_value_code: Optional[str] = None

        control_type_code: Optional[str] = None
        control_type_null_value_code: Optional[str] = None

        intervention_model_code: Optional[str] = None
        intervention_model_null_value_code: Optional[str] = None

        is_trial_randomised: Optional[bool] = None
        is_trial_randomised_null_value_code: Optional[str] = None

        stratification_factor: Optional[str] = None
        stratification_factor_null_value_code: Optional[str] = None

        trial_blinding_schema_code: Optional[str] = None
        trial_blinding_schema_null_value_code: Optional[str] = None

        planned_study_length: Optional[str] = None
        planned_study_length_null_value_code: Optional[str] = None

        drug_study_indication: Optional[bool] = None
        drug_study_indication_null_value_code: Optional[str] = None

        device_study_indication: Optional[bool] = None
        device_study_indication_null_value_code: Optional[str] = None

        confirmed_response_minimum_duration: Optional[str] = None
        confirmed_response_minimum_duration_null_value_code: Optional[str] = None

        study_title: Optional[str] = None
        study_short_title: Optional[str] = None

    uid: Optional[str]  # = None
    current_metadata: Optional[StudyMetadataSnapshot]  # = None
    released_metadata: Optional[StudyMetadataSnapshot]  # = None
    locked_metadata_versions: MutableSequence[
        StudyMetadataSnapshot
    ]  # = field(default_factory=list)
    study_status: Optional[str]
    deleted: bool  # = False


# a global helper variables used as a default for some methods arguments in the StudyDefinitionAR class
_DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN = HighLevelStudyDesignVO(
    study_type_code=None,
    study_stop_rules=None,
    is_adaptive_design=None,
    trial_type_codes=[],
    trial_phase_code=None,
    is_extension_trial=None,
    is_adaptive_design_null_value_code=None,
    study_stop_rules_null_value_code=None,
    study_type_null_value_code=None,
    trial_type_null_value_code=None,
    is_extension_trial_null_value_code=None,
    trial_phase_null_value_code=None,
    confirmed_response_minimum_duration=None,
    confirmed_response_minimum_duration_null_value_code=None,
)

_DEF_INITIAL_STUDY_POPULATION = StudyPopulationVO(
    therapeutic_area_codes=[],
    therapeutic_area_null_value_code=None,
    disease_condition_or_indication_codes=[],
    disease_condition_or_indication_null_value_code=None,
    diagnosis_group_codes=[],
    diagnosis_group_null_value_code=None,
    sex_of_participants_code=None,
    sex_of_participants_null_value_code=None,
    healthy_subject_indicator=None,
    healthy_subject_indicator_null_value_code=None,
    rare_disease_indicator=None,
    rare_disease_indicator_null_value_code=None,
    planned_minimum_age_of_subjects=None,
    planned_minimum_age_of_subjects_null_value_code=None,
    planned_maximum_age_of_subjects=None,
    planned_maximum_age_of_subjects_null_value_code=None,
    stable_disease_minimum_duration=None,
    stable_disease_minimum_duration_null_value_code=None,
    pediatric_study_indicator=None,
    pediatric_study_indicator_null_value_code=None,
    pediatric_postmarket_study_indicator=None,
    pediatric_postmarket_study_indicator_null_value_code=None,
    pediatric_investigation_plan_indicator=None,
    pediatric_investigation_plan_indicator_null_value_code=None,
    relapse_criteria=None,
    relapse_criteria_null_value_code=None,
    number_of_expected_subjects=None,
    number_of_expected_subjects_null_value_code=None,
)

_DEF_INITIAL_STUDY_INTERVENTION = StudyInterventionVO(
    intervention_type_code=None,
    intervention_type_null_value_code=None,
    add_on_to_existing_treatments=None,
    add_on_to_existing_treatments_null_value_code=None,
    control_type_code=None,
    control_type_null_value_code=None,
    intervention_model_code=None,
    intervention_model_null_value_code=None,
    is_trial_randomised=None,
    is_trial_randomised_null_value_code=None,
    stratification_factor=None,
    stratification_factor_null_value_code=None,
    trial_blinding_schema_code=None,
    trial_blinding_schema_null_value_code=None,
    planned_study_length=None,
    planned_study_length_null_value_code=None,
    drug_study_indication=None,
    drug_study_indication_null_value_code=None,
    device_study_indication=None,
    device_study_indication_null_value_code=None,
    trial_intent_type_codes=[],
    trial_intent_type_null_value_code=None,
)

_DEF_INITIAL_STUDY_DESCRIPTION = StudyDescriptionVO(
    study_title=None, study_short_title=None
)


@dataclass
class StudyDefinitionAR:
    _uid: str
    _draft_metadata: Optional[StudyMetadataVO]
    _released_metadata: Optional[StudyMetadataVO]

    # index on list corresponds to locked version number (so earliest goes first)
    _locked_metadata_versions: List[StudyMetadataVO]
    _deleted: bool

    @property
    def uid(self) -> str:
        self._check_deleted()
        return self._uid

    @property
    def current_metadata(self) -> StudyMetadataVO:
        if self._draft_metadata is not None:
            self._check_deleted()
            return self._draft_metadata
        ll = self.latest_locked_metadata
        assert ll is not None
        return ll

    def _can_edit_metadata(self, raise_error: bool = False) -> bool:
        if self.current_metadata.ver_metadata.study_status != StudyStatus.DRAFT:
            if raise_error:
                raise ValueError(
                    f"Study {self.uid}: not in DRAFT state - edit not allowed."
                )
            return False
        return True

    def edit_metadata(
        self,
        *,
        new_id_metadata: Optional[StudyIdentificationMetadataVO] = None,
        new_high_level_study_design: Optional[HighLevelStudyDesignVO] = None,
        new_study_population: Optional[StudyPopulationVO] = None,
        new_study_intervention: Optional[StudyInterventionVO] = None,
        new_study_description: Optional[StudyDescriptionVO] = None,
        therapeutic_area_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("therapeutic_area"),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            default_failure_callback_for_variable("disease_condition_or_indication")
        ),
        diagnosis_group_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("diagnosis_group"),
        sex_of_participants_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("sex_of_participants"),
        project_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("project_number"),
        study_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_type"),
        trial_intent_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_intent_type"),
        trial_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_type"),
        trial_phase_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_phase"),
        null_value_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("null_value_code"),
        intervention_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_type_code"),
        control_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("control_type_code"),
        intervention_model_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_model_code"),
        trial_blinding_schema_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_blinding_schema_code"),
        study_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_title"),
        study_short_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_short_title"),
    ) -> None:
        self._can_edit_metadata(raise_error=True)

        new_ver_metadata = StudyVersionMetadataVO(
            study_status=StudyStatus.DRAFT,
            locked_version_number=None,
            version_timestamp=datetime.today(),
        )

        # If nothing is set, we return an error.
        if not (
            new_id_metadata is not None
            or new_high_level_study_design is not None
            or new_study_population is not None
            or new_study_intervention is not None
            or new_study_description is not None
        ):
            raise AssertionError("No data to patch was provided.")

        # otherwise the call is pointless
        if new_id_metadata is not None:

            if (
                self.current_metadata.id_metadata.study_number
                != new_id_metadata.study_number
            ):
                raise BusinessLogicException(
                    f"The study number for a study {self.uid} can't be changed."
                )

            if self.latest_locked_metadata is None:
                # if the study has no locked versions study_id_prefix is set after project_number
                new_id_metadata = StudyIdentificationMetadataVO(
                    _study_id_prefix=new_id_metadata.project_number,  # here comes the substitution
                    project_number=new_id_metadata.project_number,
                    study_number=new_id_metadata.study_number,
                    study_acronym=new_id_metadata.study_acronym,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_UTN=new_id_metadata.registry_identifiers.universal_trial_number_UTN,
                        universal_trial_number_UTN_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
                        japanese_trial_registry_id_JAPIC=new_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
                        japanese_trial_registry_id_JAPIC_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code
                        ),
                        investigational_new_drug_application_number_IND=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND
                        ),
                        investigational_new_drug_application_number_IND_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code
                        ),
                    ),
                )
            else:
                # if the study has locked versions study_id_prefix and study_number stays the same
                new_id_metadata = StudyIdentificationMetadataVO(
                    _study_id_prefix=self.current_metadata.id_metadata.study_id_prefix,  # here comes the substitution
                    project_number=new_id_metadata.project_number,
                    study_number=self.current_metadata.id_metadata.study_number,
                    study_acronym=new_id_metadata.study_acronym,
                    registry_identifiers=RegistryIdentifiersVO(
                        ct_gov_id=new_id_metadata.registry_identifiers.ct_gov_id,
                        ct_gov_id_null_value_code=new_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                        eudract_id=new_id_metadata.registry_identifiers.eudract_id,
                        eudract_id_null_value_code=new_id_metadata.registry_identifiers.eudract_id_null_value_code,
                        universal_trial_number_UTN=new_id_metadata.registry_identifiers.universal_trial_number_UTN,
                        universal_trial_number_UTN_null_value_code=new_id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
                        japanese_trial_registry_id_JAPIC=new_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
                        japanese_trial_registry_id_JAPIC_null_value_code=(
                            new_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code
                        ),
                        investigational_new_drug_application_number_IND=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND
                        ),
                        investigational_new_drug_application_number_IND_null_value_code=(
                            new_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code
                        ),
                    ),
                )

            assert new_id_metadata is not None  # making linter happy
            if new_id_metadata != self.current_metadata.id_metadata:
                new_id_metadata.validate(
                    project_exists_callback=project_exists_callback
                )
                self._draft_metadata = StudyMetadataVO(
                    id_metadata=new_id_metadata,
                    high_level_study_design=self.current_metadata.high_level_study_design,
                    ver_metadata=new_ver_metadata,
                    study_population=self.current_metadata.study_population,
                    study_intervention=self.current_metadata.study_intervention,
                    study_description=self.current_metadata.study_description,
                )

        if (
            new_high_level_study_design is not None
            and new_high_level_study_design
            != self.current_metadata.high_level_study_design
        ):
            new_high_level_study_design.validate(
                study_type_exists_callback=study_type_exists_callback,
                trial_phase_exists_callback=trial_phase_exists_callback,
                trial_type_exists_callback=trial_type_exists_callback,
                trial_intent_type_exists_callback=trial_intent_type_exists_callback,
                null_value_exists_callback=null_value_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=new_high_level_study_design,
                ver_metadata=new_ver_metadata,
                study_population=self.current_metadata.study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_population is not None
            and new_study_population != self.current_metadata.study_population
        ):
            new_study_population.validate(
                null_value_exists_callback=null_value_exists_callback,
                therapeutic_area_exists_callback=therapeutic_area_exists_callback,
                disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
                diagnosis_group_exists_callback=diagnosis_group_exists_callback,
                sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=new_study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_intervention is not None
            and new_study_intervention != self.current_metadata.study_intervention
        ):
            new_study_intervention.validate(
                null_value_exists_callback=null_value_exists_callback,
                intervention_type_exists_callback=intervention_type_exists_callback,
                control_type_exists_callback=control_type_exists_callback,
                intervention_model_exists_callback=intervention_model_exists_callback,
                trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=self.current_metadata.study_population,
                study_intervention=new_study_intervention,
                study_description=self.current_metadata.study_description,
            )

        if (
            new_study_description is not None
            and new_study_description != self.current_metadata.study_description
        ):
            new_study_description.validate(
                study_title_exists_callback=study_title_exists_callback,
                study_short_title_exists_callback=study_short_title_exists_callback,
                study_number=self.current_metadata.id_metadata.study_number,
            )

            self._draft_metadata = StudyMetadataVO(
                ver_metadata=new_ver_metadata,
                id_metadata=self.current_metadata.id_metadata,
                high_level_study_design=self.current_metadata.high_level_study_design,
                study_population=self.current_metadata.study_population,
                study_intervention=self.current_metadata.study_intervention,
                study_description=new_study_description,
            )

    def release(self) -> None:
        """
        Creates new RELEASED version of study metadata (replacing previous one if exists).
        Only allowed if current state of Study is DRAFT. Current state of the study remains DRAFT.
        """
        current_metadata = self.current_metadata
        if current_metadata.ver_metadata.study_status != StudyStatus.DRAFT:
            raise ValueError(
                f"Study {self.uid}: not in DRAFT state - release not allowed."
            )

        # we update timestamp on draft metadata (to avoid having draft older then release)
        self._draft_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT,
                version_timestamp=datetime.today(),
                locked_version_number=None,
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

        # and replace released metadata
        self._released_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.RELEASED,
                locked_version_number=None,
                version_timestamp=self.current_metadata.ver_metadata.version_timestamp,
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

    def lock(self, locked_version_info: str, locked_version_author: str) -> None:
        current_metadata = self.current_metadata
        if current_metadata.ver_metadata.study_status != StudyStatus.DRAFT:
            raise ValueError(
                f"Study {self.uid}: not in DRAFT state - lock not allowed."
            )

        if (
            current_metadata.id_metadata.study_id_prefix is None
            or current_metadata.id_metadata.study_number is None
        ):
            raise ValueError(
                f"Study {self.uid}: cannot lock study without study_id_prefix nor study_number."
            )

        # first we create a new locked version
        locked_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.LOCKED,
                locked_version_number=len(self._locked_metadata_versions) + 1,
                version_timestamp=datetime.today(),
                locked_version_info=locked_version_info,
                locked_version_author=locked_version_author,
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

        # append that version to teh list
        self._locked_metadata_versions.append(locked_metadata)

        # then assume it replaces current draft and released
        self._released_metadata = None
        self._draft_metadata = None

    def unlock(self) -> None:
        current_metadata = self.current_metadata
        if current_metadata.ver_metadata.study_status != StudyStatus.LOCKED:
            raise ValueError(
                f"Study {self.uid}: not in LOCKED state - unlock not allowed."
            )

        # it just takes to create a draft version
        self._draft_metadata = StudyMetadataVO(
            id_metadata=current_metadata.id_metadata,
            high_level_study_design=current_metadata.high_level_study_design,
            study_population=current_metadata.study_population,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT, version_timestamp=datetime.today()
            ),
            study_intervention=current_metadata.study_intervention,
            study_description=current_metadata.study_description,
        )

    def _check_deleted(self) -> None:
        if self._deleted:
            raise ValueError(
                f"Study {self._uid}: no operations allowed on deleted study."
            )

    def mark_deleted(self) -> None:
        if self.latest_locked_metadata is not None:
            raise ValueError(
                f"Study {self.uid}: cannot delete a StudyDefinition having some locked versions."
            )
        self._deleted = True

    @property
    def latest_locked_metadata(self) -> Optional[StudyMetadataVO]:
        self._check_deleted()
        if len(self._locked_metadata_versions) > 0:
            return self._locked_metadata_versions[
                len(self._locked_metadata_versions) - 1
            ]
        return None

    @property
    def latest_released_or_locked_metadata(self) -> Optional[StudyMetadataVO]:
        if self._released_metadata is not None:
            self._check_deleted()
            return self._released_metadata
        return self.latest_locked_metadata

    def get_all_locked_versions(self) -> Sequence[StudyMetadataVO]:
        self._check_deleted()
        # we do copy to assure immutability of list stored inside our instance
        return list(self._locked_metadata_versions)

    def get_specific_locked_metadata_version(
        self, locked_version_number: int
    ) -> StudyMetadataVO:
        self._check_deleted()
        if locked_version_number > len(self._locked_metadata_versions):
            raise ValueError(
                f"Study {self.uid} has no locked version with number {locked_version_number}"
            )
        return self._locked_metadata_versions[locked_version_number - 1]

    # it would be nice to factor it out to a super class (since we consider each aggregate having this closure)
    # to avoid repeating this lines in every aggregate
    # they are excluded from the constructor and from comparisons either
    # however they are included in repr (so they can be conveniently inspected on console log or what so ever)
    repository_closure_data: Any = field(
        init=False, compare=False, repr=True, default=None
    )

    def get_snapshot(self) -> StudyDefinitionSnapshot:
        """
        :return: a memento (StudyDefinitionSnapshot) object representing a current state of the whole aggregate
            (see Memento design pattern)
        """

        # helper function for creating StudyMetadataSnapshots
        def snapshot_from_study_metadata(
            study_metadata: StudyMetadataVO,
        ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot:

            snapshot_dict = {}
            for config_item in FieldConfiguration.default_field_config():
                if "." in config_item.study_field_grouping:
                    accessors = config_item.study_field_grouping.split(".")
                    value_object = study_metadata
                    for accessor in accessors:
                        value_object = getattr(value_object, accessor)
                else:
                    value_object = getattr(
                        study_metadata, config_item.study_field_grouping
                    )
                value = getattr(value_object, config_item.study_field_name)
                snapshot_dict[config_item.study_field_name] = value
            result = StudyDefinitionSnapshot.StudyMetadataSnapshot(**snapshot_dict)
            return result

        # initiating snapshot
        released_metadata = None
        locked_metadata_versions = []
        current_metadata = None
        study_status = None
        if self._deleted:
            # short path for deletion
            deleted = True
        else:
            deleted = False
            # saving aggregate state to snapshot
            current_metadata = snapshot_from_study_metadata(self.current_metadata)
            study_status = self.current_metadata.ver_metadata.study_status.value

            if self._released_metadata is not None:
                released_metadata = snapshot_from_study_metadata(
                    self._released_metadata
                )

            # and whatever state there always is a list of locked metadata versions (perhaps empty one)
            locked_metadata_versions = [
                snapshot_from_study_metadata(sm)
                for sm in self._locked_metadata_versions
            ]

        return StudyDefinitionSnapshot(
            uid=self._uid,
            deleted=deleted,
            released_metadata=released_metadata,
            locked_metadata_versions=locked_metadata_versions,
            current_metadata=current_metadata,
            study_status=study_status,
        )

    @staticmethod
    def from_snapshot(study_snapshot: StudyDefinitionSnapshot) -> "StudyDefinitionAR":
        """
        A factory static method for rehydrating persisted instance of aggregate.
        Assumes that data are consistent with relevant business rules (does little or no validation).

        :param study_snapshot: a memento (Snapshot) object containing a representation of the Study aggregate

        :return: and instance of StudyDefinitionAR created from above data
        """

        def study_metadata_values_from_snapshot(
            study_metadata_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot,
            study_state: StudyStatus,
            locked_version_number: int = None,
        ) -> StudyMetadataVO:

            study_metadata_dict = {}
            meta_classes = {}
            for config_item in FieldConfiguration.default_field_config():
                if config_item.study_field_grouping not in study_metadata_dict:
                    study_metadata_dict[config_item.study_field_grouping] = {}
                    meta_classes[
                        config_item.study_field_grouping
                    ] = config_item.study_value_object_class
                study_metadata_dict[config_item.study_field_grouping][
                    config_item.study_field_name
                ] = getattr(study_metadata_snapshot, config_item.study_field_name)
            study_creation_dict = {}
            for value_object_name, value_object_class in meta_classes.items():
                if value_object_name == "id_metadata":
                    id_metadata = StudyIdentificationMetadataVO(
                        study_number=study_metadata_snapshot.study_number,
                        project_number=study_metadata_snapshot.project_number,
                        study_acronym=study_metadata_snapshot.study_acronym,
                        _study_id_prefix=study_metadata_snapshot.study_id_prefix,
                        registry_identifiers=RegistryIdentifiersVO(
                            ct_gov_id=study_metadata_snapshot.ct_gov_id,
                            ct_gov_id_null_value_code=study_metadata_snapshot.ct_gov_id_null_value_code,
                            eudract_id=study_metadata_snapshot.eudract_id,
                            eudract_id_null_value_code=study_metadata_snapshot.eudract_id_null_value_code,
                            universal_trial_number_UTN=study_metadata_snapshot.universal_trial_number_UTN,
                            universal_trial_number_UTN_null_value_code=study_metadata_snapshot.universal_trial_number_UTN_null_value_code,
                            japanese_trial_registry_id_JAPIC=study_metadata_snapshot.japanese_trial_registry_id_JAPIC,
                            japanese_trial_registry_id_JAPIC_null_value_code=(
                                study_metadata_snapshot.japanese_trial_registry_id_JAPIC_null_value_code
                            ),
                            investigational_new_drug_application_number_IND=study_metadata_snapshot.investigational_new_drug_application_number_IND,
                            investigational_new_drug_application_number_IND_null_value_code=(
                                study_metadata_snapshot.investigational_new_drug_application_number_IND_null_value_code
                            ),
                        ),
                    )
                    study_creation_dict[value_object_name] = id_metadata
                elif value_object_name == "ver_metadata":
                    ver_metadata = StudyVersionMetadataVO(
                        study_status=study_state,
                        locked_version_number=locked_version_number,
                        version_timestamp=study_metadata_snapshot.version_timestamp,
                        locked_version_author=study_metadata_snapshot.locked_version_author,
                        locked_version_info=study_metadata_snapshot.locked_version_info,
                    )
                    study_creation_dict[value_object_name] = ver_metadata
                elif value_object_name != "id_metadata.registry_identifiers":
                    vo_object = value_object_class(
                        **(study_metadata_dict[value_object_name])
                    )
                    study_creation_dict[value_object_name] = vo_object
            return StudyMetadataVO(**study_creation_dict)

        assert study_snapshot.current_metadata is not None
        assert study_snapshot.study_status == StudyStatus.DRAFT.value or (
            study_snapshot.locked_metadata_versions[
                len(study_snapshot.locked_metadata_versions) - 1
            ]
            == study_snapshot.current_metadata
        )
        assert (
            study_snapshot.study_status == StudyStatus.DRAFT.value
            or study_snapshot.released_metadata is None
        )
        assert study_snapshot.uid is not None

        # we assume repository does not rehydrate deleted objects
        assert not study_snapshot.deleted

        draft_metadata: Optional[StudyMetadataVO] = None
        released_metadata: Optional[StudyMetadataVO] = None
        uid = study_snapshot.uid

        if study_snapshot.study_status == StudyStatus.DRAFT.value:
            draft_metadata = study_metadata_values_from_snapshot(
                study_snapshot.current_metadata, StudyStatus.DRAFT
            )
            if study_snapshot.released_metadata is not None:
                released_metadata = study_metadata_values_from_snapshot(
                    study_snapshot.released_metadata, StudyStatus.RELEASED
                )

        locked_metadata_versions = [
            study_metadata_values_from_snapshot(
                study_snapshot.locked_metadata_versions[i], StudyStatus.LOCKED, i + 1
            )
            for i in range(0, len(study_snapshot.locked_metadata_versions))
        ]

        return StudyDefinitionAR(
            _uid=uid,
            _draft_metadata=draft_metadata,
            _released_metadata=released_metadata,
            _locked_metadata_versions=locked_metadata_versions,
            _deleted=False,
        )

    @staticmethod
    def from_initial_values(
        *,
        generate_uid_callback: Callable[[], str],
        initial_id_metadata: StudyIdentificationMetadataVO,
        project_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("project_number"),
        study_number_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_number"),
        initial_high_level_study_design: HighLevelStudyDesignVO = _DEF_INITIAL_HIGH_LEVEL_STUDY_DESIGN,
        initial_study_population: StudyPopulationVO = _DEF_INITIAL_STUDY_POPULATION,
        initial_study_intervention: StudyInterventionVO = _DEF_INITIAL_STUDY_INTERVENTION,
        initial_study_description: StudyDescriptionVO = _DEF_INITIAL_STUDY_DESCRIPTION,
        therapeutic_area_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("therapeutic_area"),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            default_failure_callback_for_variable("disease_condition_or_indication")
        ),
        diagnosis_group_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("diagnosis_group"),
        sex_of_participants_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("sex_of_participants"),
        study_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_type_code"),
        trial_intent_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_intent_type_code"),
        trial_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_type_code"),
        trial_phase_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_phase_code"),
        null_value_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("null_value_code"),
        intervention_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_type_code"),
        control_type_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("control_type_code"),
        intervention_model_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("intervention_model_code"),
        trial_blinding_schema_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("trial_blinding_schema_code"),
        study_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_title"),
        study_short_title_exists_callback: Callable[
            [str], bool
        ] = default_failure_callback_for_variable("study_short_title"),
    ) -> "StudyDefinitionAR":
        """
        A factory supporting user story concerned with brand new study creation with some initial information
        provided by the user.

        :param initial_id_metadata: initial identification values for newly created study metadata

        :param project_exists_callback: a callback function for checking of existence of project by given project_number
            initial_id_metadata

        :param study_number_exists_callback: a callback function for checking of existence of study_number in the database

        :param initial_high_level_study_design: stored as current_metadata.high_level_study_design in created object
            (if not provided default value with empty parameters is assumed)

        :param initial_study_population: stored as current_metadata.study_population in created object (if not provided
            default value with empty parameters is assumed)

        :param initial_study_intervention: stored as current_metadata.study_intervention in created object
            (if not provided default value with empty parameters is assumed)

        :param initial_study_description: stored as current_metadata.study_title in created object
            (if not provided default value with empty parameters is assumed)

        :param generate_uid_callback: optional, repository callback to generate unique id (since generating id may
            involve some repository capabilities). If None provided, the instance will be created with None as uid.
            The uid property then can be set later (but only once).

        :param study_type_exists_callback: (optional) callback for checking study_type_codes

        :param trial_intent_type_exists_callback: (optional) callback for checking intent_type_codes

        :param trial_type_exists_callback: (optional) callback for checking trail_type_codes

        :param trial_phase_exists_callback: (optional) callback for checking trial_phase_codes

        :param null_value_exists_callback: (optional) callback for checking null_value_codes

        :param therapeutic_area_exists_callback: (optional) callback for checking therapeutic_area_codes

        :param disease_condition_or_indication_exists_callback: (optional) callback for checking relevant codes

        :param diagnosis_group_exists_callback:  (optional) callback for checking relevant codes

        :param sex_of_participants_exists_callback:  (optional) callback for checking relevant codes

        :param intervention_type_exists_callback:  (optional) callback for checking intervention_type_code

        :param control_type_exists_callback:  (optional) callback for checking control_type_code

        :param intervention_model_exists_callback:  (optional) callback for checking intervention_model_code

        :param trial_blinding_schema_exists_callback:  (optional) callback for checking trial_blinding_schema_code

        :param study_title_exists_callback:  (optional) callback for checking study_title

        :param study_short_title_exists_callback:  (optional) callback for checking study_short_title

        :raises: ValueError -- when passed arguments do not comply with business rules relevant to Study creation

        :return: instance of new StudyDefinitionAR (aggregate root) created from provided initial values
        """

        # when we create a new study we assume study_id_prefix is taken from project_number (aby value provided is lost)
        initial_id_metadata = StudyIdentificationMetadataVO(
            project_number=initial_id_metadata.project_number,
            study_number=initial_id_metadata.study_number,
            study_acronym=initial_id_metadata.study_acronym,
            registry_identifiers=RegistryIdentifiersVO(
                ct_gov_id=initial_id_metadata.registry_identifiers.ct_gov_id,
                ct_gov_id_null_value_code=initial_id_metadata.registry_identifiers.ct_gov_id_null_value_code,
                eudract_id=initial_id_metadata.registry_identifiers.eudract_id,
                eudract_id_null_value_code=initial_id_metadata.registry_identifiers.eudract_id_null_value_code,
                universal_trial_number_UTN=initial_id_metadata.registry_identifiers.universal_trial_number_UTN,
                universal_trial_number_UTN_null_value_code=initial_id_metadata.registry_identifiers.universal_trial_number_UTN_null_value_code,
                japanese_trial_registry_id_JAPIC=initial_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC,
                japanese_trial_registry_id_JAPIC_null_value_code=(
                    initial_id_metadata.registry_identifiers.japanese_trial_registry_id_JAPIC_null_value_code
                ),
                investigational_new_drug_application_number_IND=(
                    initial_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND
                ),
                investigational_new_drug_application_number_IND_null_value_code=(
                    initial_id_metadata.registry_identifiers.investigational_new_drug_application_number_IND_null_value_code
                ),
            ),
            _study_id_prefix=initial_id_metadata.project_number,
        )

        initial_study_metadata = StudyMetadataVO(
            id_metadata=initial_id_metadata,
            high_level_study_design=initial_high_level_study_design,
            study_population=initial_study_population,
            study_intervention=initial_study_intervention,
            ver_metadata=StudyVersionMetadataVO(
                study_status=StudyStatus.DRAFT,
                locked_version_number=None,
                version_timestamp=datetime.today(),
            ),
            study_description=initial_study_description,
        )

        initial_study_metadata.validate(
            study_type_exists_callback=study_type_exists_callback,
            trial_phase_exists_callback=trial_phase_exists_callback,
            trial_type_exists_callback=trial_type_exists_callback,
            trial_intent_type_exists_callback=trial_intent_type_exists_callback,
            project_exists_callback=project_exists_callback,
            study_number_exists_callback=study_number_exists_callback,
            null_value_exists_callback=null_value_exists_callback,
            diagnosis_group_exists_callback=diagnosis_group_exists_callback,
            disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
            sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            therapeutic_area_exists_callback=therapeutic_area_exists_callback,
            intervention_type_exists_callback=intervention_type_exists_callback,
            control_type_exists_callback=control_type_exists_callback,
            intervention_model_exists_callback=intervention_model_exists_callback,
            trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            study_title_exists_callback=study_title_exists_callback,
            study_short_title_exists_callback=study_short_title_exists_callback,
        )

        # seems all relevant business rules are ok. Now get the uid (using callback)
        # or set to None if no callback provided
        uid = generate_uid_callback()

        # and lets return an instance
        return StudyDefinitionAR(
            _uid=uid,
            _draft_metadata=initial_study_metadata,
            _released_metadata=None,
            _locked_metadata_versions=[],
            _deleted=False,
        )
