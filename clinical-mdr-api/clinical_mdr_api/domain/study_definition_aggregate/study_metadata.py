import re
from collections import abc
from dataclasses import Field, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Iterable, List, Optional, Sequence

from clinical_mdr_api.domain._utils import normalize_string
from clinical_mdr_api.domain.study_definition_aggregate._utils import (  # type: ignore
    call_default_init,
    dataclass_with_default_init,
)
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.exceptions import BusinessLogicException


class StudyStatus(Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    LOCKED = "LOCKED"


class StudyComponentEnum(str, Enum):
    STUDY_DESIGN = "highLevelStudyDesign"
    STUDY_INTERVENTION = "studyIntervention"
    STUDY_POPULATION = "studyPopulation"


_STUDY_NUMBER_PATTERN = re.compile("[0-9]{1,4}")


@dataclass_with_default_init(frozen=True)
class StudyIdentificationMetadataVO:
    project_number: Optional[str]
    study_number: Optional[str]
    study_acronym: Optional[str]
    study_id_prefix: Optional[str]
    registry_identifiers: RegistryIdentifiersVO

    def __init__(
        self,
        project_number: Optional[str],
        study_number: Optional[str],
        study_acronym: Optional[str],
        registry_identifiers: RegistryIdentifiersVO,
        _study_id_prefix: Optional[str] = None
        # we denote this param with underscore, for "internal" use
        # (i.e.) use with caution and where You know what You are doing (setting an arbitrary value here)
    ):
        def norm_str(s: Optional[str]) -> Optional[str]:
            return normalize_string(s)

        call_default_init(
            self,
            project_number=norm_str(project_number),
            study_number=norm_str(study_number),
            study_acronym=norm_str(study_acronym),
            study_id_prefix=norm_str(_study_id_prefix),
            registry_identifiers=registry_identifiers,
        )

    @classmethod
    def from_input_values(
        cls,
        project_number: Optional[str],
        study_number: Optional[str],
        study_acronym: Optional[str],
        registry_identifiers: RegistryIdentifiersVO,
    ) -> "StudyIdentificationMetadataVO":
        return cls(
            study_number=study_number,
            study_acronym=study_acronym,
            project_number=project_number,
            registry_identifiers=registry_identifiers,
        )

    @property
    def study_id(self) -> Optional[str]:
        if self.study_number is None or self.study_id_prefix is None:
            return None
        return f"{self.study_id_prefix}-{self.study_number}"

    def validate(
        self,
        project_exists_callback: Callable[[str], bool] = (lambda _: True),
        study_number_exists_callback: Callable[[str], bool] = (lambda _: False),
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Raises ValueError if values do not comply with relevant business rules.

        :param null_value_exists_callback:
        :param project_exists_callback: optional, if provided makes the method to include validity (existence)
            check on project_number value.
        :param study_number_exists_callback: checks whether given study_number already exist in the database

        """
        self.registry_identifiers.validate(
            null_value_exists_callback=null_value_exists_callback
        )

        if self.study_number is None and self.study_acronym is None:
            raise ValueError(
                "Either study number or study acronym must be given in study metadata."
            )

        if self.study_number is not None and not _STUDY_NUMBER_PATTERN.fullmatch(
            self.study_number
        ):
            raise ValueError(
                f"Provided study number can only be up to 4 digits string ({self.study_number})."
            )

        if (
            self.project_number is not None
            and project_exists_callback is not None
            and not project_exists_callback(self.project_number)
        ):
            raise ValueError(
                f"There is no project identified by provided project_number ({self.project_number})"
            )
        if self.study_number is not None and study_number_exists_callback(
            self.study_number
        ):
            raise BusinessLogicException(
                f"The following study number already exists in the database ({self.study_number})"
            )

    def is_valid(
        self,
        project_exists_callback: Callable[[str], bool] = (lambda _: True),
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises ValueError (True otherwise)
        """
        try:
            self.validate(
                project_exists_callback=project_exists_callback,
                null_value_exists_callback=null_value_exists_callback,
            )
        except ValueError:
            return False
        return True

    def fix_some_values(
        self,
        *,
        project_number: Optional[str] = field(),
        study_number: Optional[str] = field(),
        study_acronym: Optional[str] = field(),
        study_id_prefix: Optional[str] = field(),
        registry_identifiers: Optional[RegistryIdentifiersVO] = field(),
    ) -> "StudyIdentificationMetadataVO":
        """
        Helper function to produce a new object with some of values different from self.
        All parameters are optional. Those provided will have provided value in the new object (the rest if the object
        will be the same). It's particularly handy for testing.
        :return:
        """

        def helper(parameter: Any, def_value: Any):
            return def_value if isinstance(parameter, Field) else parameter

        return StudyIdentificationMetadataVO(
            project_number=helper(project_number, self.project_number),
            study_number=helper(study_number, self.study_number),
            study_acronym=helper(study_acronym, self.study_acronym),
            registry_identifiers=helper(
                registry_identifiers, self.registry_identifiers
            ),
            _study_id_prefix=helper(study_id_prefix, self.study_id_prefix),
        )


@dataclass_with_default_init(frozen=True)
class StudyVersionMetadataVO:
    study_status: StudyStatus = StudyStatus.DRAFT
    locked_version_number: Optional[int] = None
    version_timestamp: Optional[datetime] = field(default_factory=datetime.today)
    locked_version_author: Optional[str] = None
    locked_version_info: Optional[str] = None

    def __init__(
        self,
        study_status: StudyStatus = StudyStatus.DRAFT,
        locked_version_number: Optional[int] = None,
        version_timestamp: Optional[datetime] = field(default_factory=datetime.today),
        locked_version_author: Optional[str] = None,
        locked_version_info: Optional[str] = None,
    ):
        if isinstance(version_timestamp, Field):
            version_timestamp = datetime.today()
        assert version_timestamp is None or isinstance(version_timestamp, datetime)

        def norm_str(s: Optional[str]) -> Optional[str]:
            return normalize_string(s)

        call_default_init(
            self,
            study_status=study_status,
            locked_version_number=locked_version_number,
            version_timestamp=version_timestamp,
            locked_version_author=norm_str(locked_version_author),
            locked_version_info=norm_str(locked_version_info),
        )

    def validate(self) -> None:
        """
        Raises ValueError if values do not comply with relevant business rules.
        Only business rules relevant to content of this object are evaluated.
        """

        if (
            self.study_status == StudyStatus.LOCKED
            and self.locked_version_number is None
        ):
            raise ValueError("LOCKED study must have locked version number.")

        if (
            self.study_status != StudyStatus.LOCKED
            and self.locked_version_number is not None
        ):
            raise ValueError("Non-LOCKED study must not have locked version number.")

        if (
            self.study_status != StudyStatus.LOCKED
            and self.locked_version_number is not None
        ):
            raise ValueError("Non-LOCKED study must not have locked version number.")

        if self.version_timestamp is None:
            raise ValueError("timestamp mandatory in VersionMetadataVO")

        if self.study_status == StudyStatus.LOCKED and (
            self.locked_version_author is None or self.locked_version_info is None
        ):
            raise ValueError(
                "version_info and version_author mandatory for LOCKED version"
            )

    def is_valid(self) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises ValueError (True otherwise)
        """
        try:
            self.validate()
        except ValueError:
            return False
        return True


@dataclass(frozen=True)
class HighLevelStudyDesignVO:
    study_type_code: Optional[str] = None
    study_type_null_value_code: Optional[str] = None

    trial_type_codes: Sequence[str] = field(default_factory=list)
    trial_type_null_value_code: Optional[str] = None

    trial_phase_code: Optional[str] = None
    trial_phase_null_value_code: Optional[str] = None

    is_extension_trial: Optional[bool] = None
    is_extension_trial_null_value_code: Optional[str] = None

    is_adaptive_design: Optional[bool] = None
    is_adaptive_design_null_value_code: Optional[str] = None

    study_stop_rules: Optional[str] = None
    study_stop_rules_null_value_code: Optional[str] = None

    confirmed_response_minimum_duration: Optional[str] = None
    confirmed_response_minimum_duration_null_value_code: Optional[str] = None

    post_auth_indicator: Optional[bool] = None
    post_auth_indicator_null_value_code: Optional[str] = None

    def normalize_code_set(self, codes: Iterable[str]) -> Sequence[str]:
        return list(
            dict.fromkeys(
                [_ for _ in [normalize_string(_) for _ in codes] if _ is not None]
            )
        )

    def validate(
        self,
        study_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_intent_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_phase_exists_callback: Callable[[str], bool] = (lambda _: True),
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        """
        Validates content disregarding state of the study. Optionally (if relevant callback are provided as
        parameters) validates also values of codes referring to various coded values. Raises ValueError with proper
        message on first failure (order of checking is indeterminate, however starts with lightest tests).
        :param study_type_exists_callback: (optional) callback for checking study_type_codes
        :param trial_intent_type_exists_callback: (optional) callback for checking intent_type_codes
        :param trial_type_exists_callback: (optional) callback for checking trail_type_codes
        :param trial_phase_exists_callback: (optional) callback for checking trial_phase_codes
        :param null_value_exists_callback: (optional) callback for checking null_value_code for all specific values
        """

        # pylint: disable=unused-argument
        # TODO: Investigate which of the callbacks should actually be used!

        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: Optional[str],
            name_of_verified_value: str,
        ) -> None:
            if associated_null_value_code is not None and not (
                value is None or (isinstance(value, abc.Collection) and len(value) == 0)
            ):
                raise ValueError(
                    f"{name_of_verified_value} and associated null value code cannot be both provided."
                )

            if (
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code)
            ):
                raise ValueError(
                    f"Unknown null value code (reason for missing) provided for {name_of_verified_value}"
                )

        validate_value_and_associated_null_value_valid(
            self.study_type_code, self.study_type_null_value_code, "study_type_code"
        )

        validate_value_and_associated_null_value_valid(
            self.trial_type_codes, self.trial_type_null_value_code, "trial_type_codes"
        )

        validate_value_and_associated_null_value_valid(
            self.trial_phase_code, self.trial_phase_null_value_code, "trial_phase_code"
        )

        validate_value_and_associated_null_value_valid(
            self.is_extension_trial,
            self.is_extension_trial_null_value_code,
            "is_extension_trial",
        )

        validate_value_and_associated_null_value_valid(
            self.is_adaptive_design,
            self.is_adaptive_design_null_value_code,
            "is_adaptive_design",
        )

        validate_value_and_associated_null_value_valid(
            self.study_stop_rules,
            self.study_stop_rules_null_value_code,
            "study_stop_rules",
        )

        validate_value_and_associated_null_value_valid(
            self.confirmed_response_minimum_duration,
            self.confirmed_response_minimum_duration_null_value_code,
            "confirmed_response_minimum_duration",
        )

        validate_value_and_associated_null_value_valid(
            self.post_auth_indicator,
            self.post_auth_indicator_null_value_code,
            "confirmed_response_minimum_duration",
        )

        if self.trial_phase_code is not None and not trial_phase_exists_callback(
            self.trial_phase_code
        ):
            raise ValueError(
                f"Non-existing trial phase code provided ({self.trial_phase_code})"
            )

        if self.study_type_code is not None and not study_type_exists_callback(
            self.study_type_code
        ):
            raise ValueError(
                f"Non-existing study type code provided ({self.study_type_code})"
            )

        for trial_type_code in self.trial_type_codes:
            if not trial_type_exists_callback(trial_type_code):
                raise ValueError(
                    f"Non-existing trial type code provided ({trial_type_code})"
                )

    def is_valid(
        self,
        study_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_intent_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_phase_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises ValueError (True otherwise)
        """
        try:
            self.validate(
                study_type_exists_callback=study_type_exists_callback,
                trial_intent_type_exists_callback=trial_intent_type_exists_callback,
                trial_type_exists_callback=trial_type_exists_callback,
                trial_phase_exists_callback=trial_phase_exists_callback,
            )
        except ValueError:
            return False
        return True

    def fix_some_values(
        self,
        study_type_code: Optional[str] = field(),
        study_type_null_value_code: Optional[str] = field(),
        trial_type_codes: Iterable[str] = field(),
        trial_type_null_value_code: Optional[str] = field(),
        trial_phase_code: Optional[str] = field(),
        trial_phase_null_value_code: Optional[str] = field(),
        is_extension_trial: Optional[bool] = field(),
        is_extension_trial_null_value_code: Optional[str] = field(),
        is_adaptive_design: Optional[bool] = field(),
        is_adaptive_design_null_value_code: Optional[str] = field(),
        study_stop_rules: Optional[str] = field(),
        study_stop_rules_null_value_code: Optional[str] = field(),
        confirmed_response_minimum_duration: Optional[str] = field(),
        confirmed_response_minimum_duration_null_value_code: Optional[str] = field(),
        post_auth_indicator: Optional[bool] = field(),
        post_auth_indicator_null_value_code: Optional[str] = field(),
    ) -> "HighLevelStudyDesignVO":
        """
        Helper function to produce a new HighLevelStudyDesignVO object with some of values different from self.
        All parameters are optional. Those provided will have provided value in the new object (the rest if the object
        will be the same). It's particularly handy for testing.
        :param study_type_code:
        :param study_type_null_value_code:
        :param trial_type_codes:
        :param trial_type_null_value_code:
        :param trial_phase_code:
        :param trial_phase_null_value_code:
        :param is_extension_trial:
        :param is_extension_trial_null_value_code:
        :param is_adaptive_design:
        :param is_adaptive_design_null_value_code:
        :param study_stop_rules:
        :param study_stop_rules_null_value_code:
        :param confirmed_response_minimum_duration:
        :param confirmed_response_minimum_duration_null_value_code:
        :param post_auth_indicator:
        :param post_auth_indicator_null_value_code:
        :return:
        """

        def helper(parameter: Any, def_value: Any):
            return def_value if isinstance(parameter, Field) else parameter

        return HighLevelStudyDesignVO(
            study_type_code=helper(study_type_code, self.study_type_code),
            study_type_null_value_code=helper(
                study_type_null_value_code, self.study_type_null_value_code
            ),
            trial_type_codes=helper(trial_type_codes, self.trial_type_codes),
            trial_type_null_value_code=helper(
                trial_type_null_value_code, self.trial_type_null_value_code
            ),
            trial_phase_code=helper(trial_phase_code, self.trial_phase_code),
            trial_phase_null_value_code=helper(
                trial_phase_null_value_code, self.trial_phase_null_value_code
            ),
            is_extension_trial=helper(is_extension_trial, self.is_extension_trial),
            is_extension_trial_null_value_code=helper(
                is_extension_trial_null_value_code,
                self.is_extension_trial_null_value_code,
            ),
            is_adaptive_design=helper(is_adaptive_design, self.is_adaptive_design),
            is_adaptive_design_null_value_code=helper(
                is_adaptive_design_null_value_code,
                self.is_adaptive_design_null_value_code,
            ),
            study_stop_rules=helper(study_stop_rules, self.study_stop_rules),
            study_stop_rules_null_value_code=helper(
                study_stop_rules_null_value_code, self.study_stop_rules_null_value_code
            ),
            confirmed_response_minimum_duration=helper(
                confirmed_response_minimum_duration,
                self.confirmed_response_minimum_duration,
            ),
            confirmed_response_minimum_duration_null_value_code=helper(
                confirmed_response_minimum_duration_null_value_code,
                self.confirmed_response_minimum_duration_null_value_code,
            ),
            post_auth_indicator=helper(post_auth_indicator, self.post_auth_indicator),
            post_auth_indicator_null_value_code=helper(
                post_auth_indicator_null_value_code,
                self.post_auth_indicator_null_value_code,
            ),
        )

    @staticmethod
    def from_input_values(
        *,
        study_type_code: Optional[str],
        study_type_null_value_code: Optional[str],
        trial_type_codes: Optional[Iterable[str]],
        trial_type_null_value_code: Optional[str],
        trial_phase_code: Optional[str],
        trial_phase_null_value_code: Optional[str],
        is_extension_trial: Optional[bool],
        is_extension_trial_null_value_code: Optional[str],
        is_adaptive_design: Optional[bool],
        is_adaptive_design_null_value_code: Optional[str],
        study_stop_rules: Optional[str],
        study_stop_rules_null_value_code: Optional[str],
        confirmed_response_minimum_duration: Optional[str],
        confirmed_response_minimum_duration_null_value_code: Optional[str],
        post_auth_indicator: Optional[bool],
        post_auth_indicator_null_value_code: Optional[str],
    ) -> "HighLevelStudyDesignVO":
        return HighLevelStudyDesignVO(
            study_type_code=study_type_code,
            study_type_null_value_code=study_type_null_value_code,
            trial_type_codes=[] if trial_type_codes is None else trial_type_codes,
            trial_type_null_value_code=trial_type_null_value_code,
            trial_phase_code=trial_phase_code,
            trial_phase_null_value_code=trial_phase_null_value_code,
            is_extension_trial=is_extension_trial,
            is_extension_trial_null_value_code=is_extension_trial_null_value_code,
            is_adaptive_design=is_adaptive_design,
            is_adaptive_design_null_value_code=is_adaptive_design_null_value_code,
            study_stop_rules=study_stop_rules,
            study_stop_rules_null_value_code=study_stop_rules_null_value_code,
            confirmed_response_minimum_duration=confirmed_response_minimum_duration,
            confirmed_response_minimum_duration_null_value_code=confirmed_response_minimum_duration_null_value_code,
            post_auth_indicator=post_auth_indicator,
            post_auth_indicator_null_value_code=post_auth_indicator_null_value_code,
        )


@dataclass(frozen=True)
class StudyPopulationVO:
    therapeutic_area_codes: Sequence[str] = field(default_factory=list)
    therapeutic_area_null_value_code: Optional[str] = None

    disease_condition_or_indication_codes: Sequence[str] = field(default_factory=list)
    disease_condition_or_indication_null_value_code: Optional[str] = None

    diagnosis_group_codes: Sequence[str] = field(default_factory=list)
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

    @staticmethod
    def from_input_values(
        *,
        therapeutic_area_codes: Iterable[str],
        therapeutic_area_null_value_code: Optional[str],
        disease_condition_or_indication_codes: Iterable[str],
        disease_condition_or_indication_null_value_code: Optional[str],
        diagnosis_group_codes: Iterable[str],
        diagnosis_group_null_value_code: Optional[str],
        sex_of_participants_code: Optional[str],
        sex_of_participants_null_value_code: Optional[str],
        rare_disease_indicator: Optional[bool],
        rare_disease_indicator_null_value_code: Optional[str],
        healthy_subject_indicator: Optional[bool],
        healthy_subject_indicator_null_value_code: Optional[str],
        planned_minimum_age_of_subjects: Optional[str],
        planned_minimum_age_of_subjects_null_value_code: Optional[str],
        planned_maximum_age_of_subjects: Optional[str],
        planned_maximum_age_of_subjects_null_value_code: Optional[str],
        stable_disease_minimum_duration: Optional[str],
        stable_disease_minimum_duration_null_value_code: Optional[str],
        pediatric_study_indicator: Optional[bool],
        pediatric_study_indicator_null_value_code: Optional[str],
        pediatric_postmarket_study_indicator: Optional[bool],
        pediatric_postmarket_study_indicator_null_value_code: Optional[str],
        pediatric_investigation_plan_indicator: Optional[bool],
        pediatric_investigation_plan_indicator_null_value_code: Optional[str],
        relapse_criteria: Optional[str],
        relapse_criteria_null_value_code: Optional[str],
        number_of_expected_subjects: Optional[int],
        number_of_expected_subjects_null_value_code: Optional[str],
    ) -> "StudyPopulationVO":
        def normalize_code_set(codes: Optional[Iterable[str]]) -> Sequence[str]:
            if codes is None:
                codes = []
            return list(
                dict.fromkeys(
                    [_ for _ in [normalize_string(_) for _ in codes] if _ is not None]
                )
            )

        return StudyPopulationVO(
            therapeutic_area_codes=normalize_code_set(therapeutic_area_codes),
            therapeutic_area_null_value_code=normalize_string(
                therapeutic_area_null_value_code
            ),
            disease_condition_or_indication_codes=normalize_code_set(
                disease_condition_or_indication_codes
            ),
            disease_condition_or_indication_null_value_code=normalize_string(
                disease_condition_or_indication_null_value_code
            ),
            diagnosis_group_codes=normalize_code_set(diagnosis_group_codes),
            diagnosis_group_null_value_code=normalize_string(
                diagnosis_group_null_value_code
            ),
            sex_of_participants_code=normalize_string(sex_of_participants_code),
            sex_of_participants_null_value_code=normalize_string(
                sex_of_participants_null_value_code
            ),
            rare_disease_indicator=rare_disease_indicator,
            rare_disease_indicator_null_value_code=normalize_string(
                rare_disease_indicator_null_value_code
            ),
            healthy_subject_indicator=healthy_subject_indicator,
            healthy_subject_indicator_null_value_code=normalize_string(
                healthy_subject_indicator_null_value_code
            ),
            planned_maximum_age_of_subjects=planned_maximum_age_of_subjects,
            planned_maximum_age_of_subjects_null_value_code=normalize_string(
                planned_maximum_age_of_subjects_null_value_code
            ),
            planned_minimum_age_of_subjects=planned_minimum_age_of_subjects,
            planned_minimum_age_of_subjects_null_value_code=normalize_string(
                planned_minimum_age_of_subjects_null_value_code
            ),
            stable_disease_minimum_duration=stable_disease_minimum_duration,
            stable_disease_minimum_duration_null_value_code=normalize_string(
                stable_disease_minimum_duration_null_value_code
            ),
            pediatric_study_indicator=pediatric_study_indicator,
            pediatric_study_indicator_null_value_code=normalize_string(
                pediatric_study_indicator_null_value_code
            ),
            pediatric_postmarket_study_indicator=pediatric_postmarket_study_indicator,
            pediatric_postmarket_study_indicator_null_value_code=normalize_string(
                pediatric_postmarket_study_indicator_null_value_code
            ),
            pediatric_investigation_plan_indicator=pediatric_investigation_plan_indicator,
            pediatric_investigation_plan_indicator_null_value_code=normalize_string(
                pediatric_investigation_plan_indicator_null_value_code
            ),
            relapse_criteria=normalize_string(relapse_criteria),
            relapse_criteria_null_value_code=normalize_string(
                relapse_criteria_null_value_code
            ),
            number_of_expected_subjects=number_of_expected_subjects,
            number_of_expected_subjects_null_value_code=normalize_string(
                number_of_expected_subjects_null_value_code
            ),
        )

    def validate(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
        therapeutic_area_exists_callback: Callable[[str], bool] = (lambda _: True),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = (lambda _: True),
        sex_of_participants_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: Optional[str],
            name_of_verified_value: str,
        ) -> None:
            if associated_null_value_code is not None and not (
                value is None or (isinstance(value, abc.Collection) and len(value) == 0)
            ):
                raise ValueError(
                    f"{name_of_verified_value} and associated null value code cannot be both provided."
                )

            if (
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code)
            ):
                raise ValueError(
                    f"Unknown null value code (reason for missing) provided for {name_of_verified_value}"
                )

        validate_value_and_associated_null_value_valid(
            value=self.therapeutic_area_codes,
            associated_null_value_code=self.therapeutic_area_null_value_code,
            name_of_verified_value="therapeutic_area_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.diagnosis_group_codes,
            associated_null_value_code=self.diagnosis_group_null_value_code,
            name_of_verified_value="diagnosis_group_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.disease_condition_or_indication_codes,
            associated_null_value_code=self.disease_condition_or_indication_null_value_code,
            name_of_verified_value="disease_condition_or_indication_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.sex_of_participants_code,
            associated_null_value_code=self.sex_of_participants_null_value_code,
            name_of_verified_value="sex_of_participants_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.healthy_subject_indicator,
            associated_null_value_code=self.healthy_subject_indicator_null_value_code,
            name_of_verified_value="healthy_subject_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.rare_disease_indicator,
            associated_null_value_code=self.rare_disease_indicator_null_value_code,
            name_of_verified_value="rare_disease_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_minimum_age_of_subjects,
            associated_null_value_code=self.planned_minimum_age_of_subjects_null_value_code,
            name_of_verified_value="planned_minimum_age_of_subjects",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_maximum_age_of_subjects,
            associated_null_value_code=self.planned_maximum_age_of_subjects_null_value_code,
            name_of_verified_value="planned_maximum_age_of_subjects",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_study_indicator,
            associated_null_value_code=self.pediatric_study_indicator_null_value_code,
            name_of_verified_value="pediatric_study_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_postmarket_study_indicator,
            associated_null_value_code=self.pediatric_postmarket_study_indicator_null_value_code,
            name_of_verified_value="pediatric_postmarket_study_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_investigation_plan_indicator,
            associated_null_value_code=self.pediatric_investigation_plan_indicator_null_value_code,
            name_of_verified_value="pediatric_investigation_plan_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.relapse_criteria,
            associated_null_value_code=self.relapse_criteria_null_value_code,
            name_of_verified_value="relapse_criteria",
        )

        validate_value_and_associated_null_value_valid(
            value=self.number_of_expected_subjects,
            associated_null_value_code=self.number_of_expected_subjects_null_value_code,
            name_of_verified_value="number_of_expected_subjects",
        )

        for therapeutic_area_code in self.therapeutic_area_codes:
            if not therapeutic_area_exists_callback(therapeutic_area_code):
                raise ValueError(
                    f"Unknown therapeutic area code ({therapeutic_area_code})"
                )

        for diagnosis_group_code in self.diagnosis_group_codes:
            if not diagnosis_group_exists_callback(diagnosis_group_code):
                raise ValueError(
                    f"Unknown diagnosis group code ({diagnosis_group_code})"
                )

        for (
            disease_condition_or_indication_code
        ) in self.disease_condition_or_indication_codes:
            if not disease_condition_or_indication_exists_callback(
                disease_condition_or_indication_code
            ):
                raise ValueError(
                    f"Unknown disease_condition_or_indication_code "
                    f"({disease_condition_or_indication_code})"
                )

        if (
            self.sex_of_participants_code is not None
            and not sex_of_participants_exists_callback(self.sex_of_participants_code)
        ):
            raise ValueError(
                f"Unknown sex of participants code({self.sex_of_participants_code})"
            )

    def is_valid(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
        therapeutic_area_exists_callback: Callable[[str], bool] = (lambda _: True),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = (lambda _: True),
        sex_of_participants_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> bool:
        try:
            self.validate(
                null_value_exists_callback=null_value_exists_callback,
                diagnosis_group_exists_callback=diagnosis_group_exists_callback,
                therapeutic_area_exists_callback=therapeutic_area_exists_callback,
                disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
                sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            )
        except ValueError:
            return False
        return True

    def fix_some_values(
        self,
        *,
        therapeutic_area_codes: Iterable[str] = field(),
        therapeutic_area_null_value_code: Optional[str] = field(),
        disease_condition_or_indication_codes: Iterable[str] = field(),
        disease_condition_or_indication_null_value_code: Optional[str] = field(),
        diagnosis_group_codes: Iterable[str] = field(),
        diagnosis_group_null_value_code: Optional[str] = field(),
        sex_of_participants_code: Optional[str] = field(),
        sex_of_participants_null_value_code: Optional[str] = field(),
        rare_disease_indicator: Optional[bool] = field(),
        rare_disease_indicator_null_value_code: Optional[str] = field(),
        healthy_subject_indicator: Optional[bool] = field(),
        healthy_subject_indicator_null_value_code: Optional[str] = field(),
        planned_minimum_age_of_subjects: Optional[str] = field(),
        planned_minimum_age_of_subjects_null_value_code: Optional[str] = field(),
        planned_maximum_age_of_subjects: Optional[str] = field(),
        planned_maximum_age_of_subjects_null_value_code: Optional[str] = field(),
        stable_disease_minimum_duration: Optional[str] = field(),
        stable_disease_minimum_duration_null_value_code: Optional[str] = field(),
        pediatric_study_indicator: Optional[bool] = field(),
        pediatric_study_indicator_null_value_code: Optional[str] = field(),
        pediatric_postmarket_study_indicator: Optional[bool] = field(),
        pediatric_postmarket_study_indicator_null_value_code: Optional[str] = field(),
        pediatric_investigation_plan_indicator: Optional[bool] = field(),
        pediatric_investigation_plan_indicator_null_value_code: Optional[str] = field(),
        relapse_criteria: Optional[str] = field(),
        relapse_criteria_null_value_code: Optional[str] = field(),
        number_of_expected_subjects: Optional[int] = field(),
        number_of_expected_subjects_null_value_code: Optional[str] = field(),
    ) -> "StudyPopulationVO":
        def helper(parameter: Any, def_value: Any):
            if isinstance(parameter, Field):
                if isinstance(def_value, tuple):
                    return list(def_value)
                return def_value
            return parameter

        return StudyPopulationVO.from_input_values(
            therapeutic_area_codes=helper(
                therapeutic_area_codes, self.therapeutic_area_codes
            ),
            therapeutic_area_null_value_code=helper(
                therapeutic_area_null_value_code, self.therapeutic_area_null_value_code
            ),
            disease_condition_or_indication_codes=helper(
                disease_condition_or_indication_codes,
                self.disease_condition_or_indication_codes,
            ),
            disease_condition_or_indication_null_value_code=helper(
                disease_condition_or_indication_null_value_code,
                self.disease_condition_or_indication_null_value_code,
            ),
            diagnosis_group_codes=helper(
                diagnosis_group_codes, self.diagnosis_group_codes
            ),
            diagnosis_group_null_value_code=helper(
                diagnosis_group_null_value_code, self.diagnosis_group_null_value_code
            ),
            sex_of_participants_code=helper(
                sex_of_participants_code, self.sex_of_participants_code
            ),
            sex_of_participants_null_value_code=helper(
                sex_of_participants_null_value_code,
                self.sex_of_participants_null_value_code,
            ),
            healthy_subject_indicator=helper(
                healthy_subject_indicator, self.healthy_subject_indicator
            ),
            healthy_subject_indicator_null_value_code=helper(
                healthy_subject_indicator_null_value_code,
                self.healthy_subject_indicator_null_value_code,
            ),
            rare_disease_indicator=helper(
                rare_disease_indicator, self.rare_disease_indicator
            ),
            rare_disease_indicator_null_value_code=helper(
                rare_disease_indicator_null_value_code,
                self.rare_disease_indicator_null_value_code,
            ),
            planned_minimum_age_of_subjects=helper(
                planned_minimum_age_of_subjects, self.planned_minimum_age_of_subjects
            ),
            planned_minimum_age_of_subjects_null_value_code=helper(
                planned_minimum_age_of_subjects_null_value_code,
                self.planned_minimum_age_of_subjects_null_value_code,
            ),
            planned_maximum_age_of_subjects=helper(
                planned_maximum_age_of_subjects, self.planned_maximum_age_of_subjects
            ),
            planned_maximum_age_of_subjects_null_value_code=helper(
                planned_maximum_age_of_subjects_null_value_code,
                self.planned_maximum_age_of_subjects_null_value_code,
            ),
            stable_disease_minimum_duration=helper(
                stable_disease_minimum_duration, self.stable_disease_minimum_duration
            ),
            stable_disease_minimum_duration_null_value_code=helper(
                stable_disease_minimum_duration_null_value_code,
                self.stable_disease_minimum_duration_null_value_code,
            ),
            pediatric_study_indicator=helper(
                pediatric_study_indicator, self.pediatric_study_indicator
            ),
            pediatric_study_indicator_null_value_code=helper(
                pediatric_study_indicator_null_value_code,
                self.pediatric_study_indicator_null_value_code,
            ),
            pediatric_postmarket_study_indicator=helper(
                pediatric_postmarket_study_indicator,
                self.pediatric_postmarket_study_indicator,
            ),
            pediatric_postmarket_study_indicator_null_value_code=helper(
                pediatric_postmarket_study_indicator_null_value_code,
                self.pediatric_postmarket_study_indicator_null_value_code,
            ),
            pediatric_investigation_plan_indicator=helper(
                pediatric_investigation_plan_indicator,
                self.pediatric_investigation_plan_indicator,
            ),
            pediatric_investigation_plan_indicator_null_value_code=helper(
                pediatric_investigation_plan_indicator_null_value_code,
                self.pediatric_investigation_plan_indicator_null_value_code,
            ),
            relapse_criteria=helper(relapse_criteria, self.relapse_criteria),
            relapse_criteria_null_value_code=helper(
                relapse_criteria_null_value_code, self.relapse_criteria_null_value_code
            ),
            number_of_expected_subjects=helper(
                number_of_expected_subjects, self.number_of_expected_subjects
            ),
            number_of_expected_subjects_null_value_code=helper(
                number_of_expected_subjects_null_value_code,
                self.number_of_expected_subjects_null_value_code,
            ),
        )


@dataclass(frozen=True)
class StudyInterventionVO:
    intervention_type_code: Optional[str] = None
    intervention_type_null_value_code: Optional[str] = None

    add_on_to_existing_treatments: Optional[bool] = None
    add_on_to_existing_treatments_null_value_code: Optional[str] = None

    control_type_code: Optional[str] = None
    control_type_null_value_code: Optional[str] = None

    intervention_model_code: Optional[str] = None
    intervention_model_null_value_code: Optional[str] = None

    trial_intent_type_codes: Sequence[str] = field(default_factory=list)
    trial_intent_type_null_value_code: Optional[str] = None

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

    @staticmethod
    def from_input_values(
        *,
        intervention_type_code: Optional[str],
        intervention_type_null_value_code: Optional[str],
        add_on_to_existing_treatments: Optional[bool],
        add_on_to_existing_treatments_null_value_code: Optional[str],
        control_type_code: Optional[str],
        control_type_null_value_code: Optional[str],
        intervention_model_code: Optional[str],
        intervention_model_null_value_code: Optional[str],
        is_trial_randomised: Optional[bool],
        is_trial_randomised_null_value_code: Optional[str],
        stratification_factor: Optional[str],
        stratification_factor_null_value_code: Optional[str],
        trial_blinding_schema_code: Optional[str],
        trial_blinding_schema_null_value_code: Optional[str],
        planned_study_length: Optional[str],
        planned_study_length_null_value_code: Optional[str],
        drug_study_indication: Optional[bool],
        drug_study_indication_null_value_code: Optional[str],
        device_study_indication: Optional[bool],
        device_study_indication_null_value_code: Optional[str],
        trial_intent_type_codes: Sequence[str],
        trial_intent_type_null_value_code: Optional[str],
    ) -> "StudyInterventionVO":

        return StudyInterventionVO(
            intervention_type_code=normalize_string(intervention_type_code),
            intervention_type_null_value_code=normalize_string(
                intervention_type_null_value_code
            ),
            add_on_to_existing_treatments=add_on_to_existing_treatments,
            add_on_to_existing_treatments_null_value_code=normalize_string(
                add_on_to_existing_treatments_null_value_code
            ),
            control_type_code=normalize_string(control_type_code),
            control_type_null_value_code=normalize_string(control_type_null_value_code),
            intervention_model_code=intervention_model_code,
            intervention_model_null_value_code=normalize_string(
                intervention_model_null_value_code
            ),
            is_trial_randomised=is_trial_randomised,
            is_trial_randomised_null_value_code=normalize_string(
                is_trial_randomised_null_value_code
            ),
            stratification_factor=normalize_string(stratification_factor),
            stratification_factor_null_value_code=normalize_string(
                stratification_factor_null_value_code
            ),
            trial_blinding_schema_code=normalize_string(trial_blinding_schema_code),
            trial_blinding_schema_null_value_code=normalize_string(
                trial_blinding_schema_null_value_code
            ),
            planned_study_length=planned_study_length,
            planned_study_length_null_value_code=normalize_string(
                planned_study_length_null_value_code
            ),
            drug_study_indication=drug_study_indication,
            drug_study_indication_null_value_code=normalize_string(
                drug_study_indication_null_value_code
            ),
            device_study_indication=device_study_indication,
            device_study_indication_null_value_code=normalize_string(
                device_study_indication_null_value_code
            ),
            trial_intent_type_codes=(
                [] if trial_intent_type_codes is None else trial_intent_type_codes
            ),
            trial_intent_type_null_value_code=trial_intent_type_null_value_code,
        )

    def validate(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        control_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_model_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_blinding_schema_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: Optional[str],
            name_of_verified_value: str,
        ) -> None:
            if associated_null_value_code is not None and not (
                value is None or (isinstance(value, abc.Collection) and len(value) == 0)
            ):
                raise ValueError(
                    f"{name_of_verified_value} and associated null value code cannot be both provided."
                )

            if (
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code)
            ):
                raise ValueError(
                    f"Unknown null value code (reason for missing) provided for {name_of_verified_value}"
                )

        validate_value_and_associated_null_value_valid(
            value=self.intervention_type_code,
            associated_null_value_code=self.intervention_type_null_value_code,
            name_of_verified_value="intervention_type",
        )

        validate_value_and_associated_null_value_valid(
            value=self.add_on_to_existing_treatments,
            associated_null_value_code=self.add_on_to_existing_treatments_null_value_code,
            name_of_verified_value="add_on_to_existing_treatments",
        )

        validate_value_and_associated_null_value_valid(
            value=self.control_type_code,
            associated_null_value_code=self.control_type_null_value_code,
            name_of_verified_value="control_type",
        )

        validate_value_and_associated_null_value_valid(
            self.trial_intent_type_codes,
            self.trial_intent_type_null_value_code,
            "trial_intent_type_codes",
        )

        validate_value_and_associated_null_value_valid(
            value=self.intervention_model_code,
            associated_null_value_code=self.intervention_model_null_value_code,
            name_of_verified_value="intervention_model",
        )

        validate_value_and_associated_null_value_valid(
            value=self.is_trial_randomised,
            associated_null_value_code=self.is_trial_randomised_null_value_code,
            name_of_verified_value="is_trial_randomised",
        )

        validate_value_and_associated_null_value_valid(
            value=self.stratification_factor,
            associated_null_value_code=self.stratification_factor_null_value_code,
            name_of_verified_value="stratification_factor",
        )

        validate_value_and_associated_null_value_valid(
            value=self.trial_blinding_schema_code,
            associated_null_value_code=self.trial_blinding_schema_null_value_code,
            name_of_verified_value="trial_blinding_schema",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_study_length,
            associated_null_value_code=self.planned_study_length_null_value_code,
            name_of_verified_value="planned_study_length",
        )

        if (
            self.intervention_type_code is not None
            and not intervention_type_exists_callback(self.intervention_type_code)
        ):
            raise ValueError(
                f"Unknown intervention type code ({self.intervention_type_code})"
            )

        if self.control_type_code is not None and not control_type_exists_callback(
            self.control_type_code
        ):
            raise ValueError(f"Unknown control  type code ({self.control_type_code})")

        if (
            self.intervention_model_code is not None
            and not intervention_model_exists_callback(self.intervention_model_code)
        ):
            raise ValueError(
                f"Unknown intervention model code ({self.intervention_model_code})"
            )

        if (
            self.trial_blinding_schema_code is not None
            and not trial_blinding_schema_exists_callback(
                self.trial_blinding_schema_code
            )
        ):
            raise ValueError(
                f"Unknown trial blinding schema code({self.trial_blinding_schema_code})"
            )

    def is_valid(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        control_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_model_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_blinding_schema_exists_callback: Callable[[str], bool] = (lambda _: True),
    ) -> bool:
        try:
            self.validate(
                null_value_exists_callback=null_value_exists_callback,
                intervention_type_exists_callback=intervention_type_exists_callback,
                control_type_exists_callback=control_type_exists_callback,
                intervention_model_exists_callback=intervention_model_exists_callback,
                trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            )
        except ValueError:
            return False
        return True

    def fix_some_values(
        self,
        *,
        intervention_type_code: Optional[str] = field(),
        intervention_type_null_value_code: Optional[str] = field(),
        add_on_to_existing_treatments: Optional[bool] = field(),
        add_on_to_existing_treatments_null_value_code: Optional[str] = field(),
        control_type_code: Optional[str] = field(),
        control_type_null_value_code: Optional[str] = field(),
        intervention_model_code: Optional[bool] = field(),
        intervention_model_null_value_code: Optional[str] = field(),
        is_trial_randomised: Optional[bool] = field(),
        is_trial_randomised_null_value_code: Optional[str] = field(),
        stratification_factor: Optional[str] = field(),
        stratification_factor_null_value_code: Optional[str] = field(),
        trial_blinding_schema_code: Optional[str] = field(),
        trial_blinding_schema_null_value_code: Optional[str] = field(),
        planned_study_length: Optional[str] = field(),
        planned_study_length_null_value_code: Optional[str] = field(),
        drug_study_indication: Optional[bool] = field(),
        drug_study_indication_null_value_code: Optional[str] = field(),
        device_study_indication: Optional[bool] = field(),
        device_study_indication_null_value_code: Optional[str] = field(),
        trial_intent_type_codes: Sequence[str] = field(),
        trial_itent_type_null_value_code: Optional[str] = field(),
    ) -> "StudyInterventionVO":
        def helper(parameter: Any, def_value: Any):
            return def_value if isinstance(parameter, Field) else parameter

        return StudyInterventionVO.from_input_values(
            intervention_type_code=helper(
                intervention_type_code, self.intervention_type_code
            ),
            intervention_type_null_value_code=helper(
                intervention_type_null_value_code,
                self.intervention_type_null_value_code,
            ),
            add_on_to_existing_treatments=helper(
                add_on_to_existing_treatments, self.add_on_to_existing_treatments
            ),
            add_on_to_existing_treatments_null_value_code=helper(
                add_on_to_existing_treatments_null_value_code,
                self.add_on_to_existing_treatments_null_value_code,
            ),
            control_type_code=helper(control_type_code, self.control_type_code),
            control_type_null_value_code=helper(
                control_type_null_value_code, self.control_type_null_value_code
            ),
            intervention_model_code=helper(
                intervention_model_code, self.intervention_model_code
            ),
            intervention_model_null_value_code=helper(
                intervention_model_null_value_code,
                self.intervention_model_null_value_code,
            ),
            is_trial_randomised=helper(is_trial_randomised, self.is_trial_randomised),
            is_trial_randomised_null_value_code=helper(
                is_trial_randomised_null_value_code,
                self.is_trial_randomised_null_value_code,
            ),
            stratification_factor=helper(
                stratification_factor, self.stratification_factor
            ),
            stratification_factor_null_value_code=helper(
                stratification_factor_null_value_code,
                self.stratification_factor_null_value_code,
            ),
            trial_blinding_schema_code=helper(
                trial_blinding_schema_code, self.trial_blinding_schema_code
            ),
            trial_blinding_schema_null_value_code=helper(
                trial_blinding_schema_null_value_code,
                self.trial_blinding_schema_null_value_code,
            ),
            planned_study_length=helper(
                planned_study_length, self.planned_study_length
            ),
            planned_study_length_null_value_code=helper(
                planned_study_length_null_value_code,
                self.planned_study_length_null_value_code,
            ),
            drug_study_indication=helper(
                drug_study_indication, self.drug_study_indication
            ),
            drug_study_indication_null_value_code=helper(
                drug_study_indication_null_value_code,
                self.drug_study_indication_null_value_code,
            ),
            device_study_indication=helper(
                device_study_indication, self.device_study_indication
            ),
            device_study_indication_null_value_code=helper(
                device_study_indication_null_value_code,
                self.device_study_indication_null_value_code,
            ),
            trial_intent_type_codes=helper(
                trial_intent_type_codes, self.trial_intent_type_codes
            ),
            trial_intent_type_null_value_code=helper(
                trial_itent_type_null_value_code, self.trial_intent_type_null_value_code
            ),
        )


@dataclass(frozen=True)
class StudyDescriptionVO:
    study_title: Optional[str] = None
    study_short_title: Optional[str] = None

    @staticmethod
    def from_input_values(
        study_title: Optional[str], study_short_title: Optional[str]
    ) -> "StudyDescriptionVO":
        return StudyDescriptionVO(
            study_title=normalize_string(study_title),
            study_short_title=normalize_string(study_short_title),
        )

    def validate(
        self,
        study_number: str,
        *,
        study_title_exists_callback: Callable[[str], bool] = (
            lambda _, study_number: True
        ),
        study_short_title_exists_callback: Callable[[str], bool] = (
            lambda _, study_number: True
        ),
    ) -> None:

        if study_title_exists_callback(self.study_title, study_number):
            raise ValueError(f"Study title already exists ({self.study_title})")
        if study_short_title_exists_callback(self.study_short_title, study_number):
            raise ValueError(
                f"Study short title already exists ({self.study_short_title})"
            )

    def is_valid(
        self,
        study_number: str,
        *,
        title_exists_callback: Callable[[str], bool] = (lambda _, study_number: True),
        short_title_exists_callback: Callable[[str], bool] = (
            lambda _, study_number: True
        ),
    ) -> bool:
        try:
            self.validate(
                study_title_exists_callback=title_exists_callback,
                study_short_title_exists_callback=short_title_exists_callback,
                study_number=study_number,
            )
        except ValueError:
            return False
        return True

    def fix_some_values(
        self,
        *,
        study_title: Optional[str] = field(),
        study_short_title: Optional[str] = field(),
    ) -> "StudyDescriptionVO":
        def helper(parameter: Any, def_value: Any):
            return def_value if isinstance(parameter, Field) else parameter

        return StudyDescriptionVO.from_input_values(
            study_title=helper(study_title, self.study_title),
            study_short_title=helper(study_short_title, self.study_short_title),
        )


@dataclass(frozen=True)
class StudyFieldAuditTrailActionVO:
    """
    A single "Action" entry in an audit trail.
    An action is a tuple [Section, Field, Action, Before value, After value].
    """

    section: str
    field_name: str
    before_value: Optional[str]
    after_value: Optional[str]
    action: str

    @staticmethod
    def from_input_values(
        field_name: Optional[str],
        section: Optional[str],
        before_value: Optional[str],
        after_value: Optional[str],
        action: Optional[str],
    ) -> "StudyFieldAuditTrailActionVO":
        return StudyFieldAuditTrailActionVO(
            field_name=normalize_string(field_name),
            section=normalize_string(section),
            before_value=normalize_string(before_value),
            after_value=normalize_string(after_value),
            action=normalize_string(action),
        )


@dataclass(frozen=True)
class StudyFieldAuditTrailEntryAR:
    """
    A dated entry in an audit trail.
    An entry has a specific study and specific user, and contain one or more actions.
    """

    study_uid: str
    user_initials: str
    date: str
    actions: List[StudyFieldAuditTrailActionVO]

    @staticmethod
    def from_input_values(
        study_uid: Optional[str],
        user_initials: Optional[str],
        date: Optional[str],
        actions: List[StudyFieldAuditTrailActionVO],
    ) -> "StudyFieldAuditTrailEntryAR":
        return StudyFieldAuditTrailEntryAR(
            study_uid=normalize_string(study_uid),
            user_initials=normalize_string(user_initials),
            date=normalize_string(date),
            actions=actions,
        )


@dataclass(frozen=True)
class StudyMetadataVO:
    id_metadata: Optional[StudyIdentificationMetadataVO] = None
    ver_metadata: Optional[StudyVersionMetadataVO] = None
    high_level_study_design: Optional[HighLevelStudyDesignVO] = None
    study_population: Optional[StudyPopulationVO] = None
    study_intervention: Optional[StudyInterventionVO] = None
    study_description: Optional[StudyDescriptionVO] = None

    def validate(
        self,
        *,
        project_exists_callback: Callable[[str], bool] = (lambda _: True),
        study_number_exists_callback: Callable[[str], bool] = (lambda _: False),
        study_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_intent_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_phase_exists_callback: Callable[[str], bool] = (lambda _: True),
        null_value_exists_callback: Callable[[str], bool] = (lambda _: True),
        therapeutic_area_exists_callback: Callable[[str], bool] = (lambda _: True),
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = (lambda _: True),
        sex_of_participants_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        control_type_exists_callback: Callable[[str], bool] = (lambda _: True),
        intervention_model_exists_callback: Callable[[str], bool] = (lambda _: True),
        trial_blinding_schema_exists_callback: Callable[[str], bool] = (lambda _: True),
        study_title_exists_callback: Callable[[str], bool] = (
            lambda _, study_number: False
        ),
        study_short_title_exists_callback: Callable[[str], bool] = (
            lambda _, study_number: False
        ),
    ) -> None:
        """
        Raises ValueError if values do not comply with relevant business rules. As a parameters takes
        callback which are supposed to verify validity (existence) of relevant coded values. If not provided
        codes are assumed valid.
        """
        self.id_metadata.validate(
            project_exists_callback=project_exists_callback,
            study_number_exists_callback=study_number_exists_callback,
        )
        self.ver_metadata.validate()
        self.study_description.validate(
            study_title_exists_callback=study_title_exists_callback,
            study_short_title_exists_callback=study_short_title_exists_callback,
            study_number=self.id_metadata.study_number,
        )
        self.high_level_study_design.validate(
            study_type_exists_callback=study_type_exists_callback,
            trial_phase_exists_callback=trial_phase_exists_callback,
            trial_type_exists_callback=trial_type_exists_callback,
            trial_intent_type_exists_callback=trial_intent_type_exists_callback,
            null_value_exists_callback=null_value_exists_callback,
        )
        self.study_population.validate(
            therapeutic_area_exists_callback=therapeutic_area_exists_callback,
            disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
            diagnosis_group_exists_callback=diagnosis_group_exists_callback,
            sex_of_participants_exists_callback=sex_of_participants_exists_callback,
        )
        self.study_intervention.validate(
            intervention_type_exists_callback=intervention_type_exists_callback,
            control_type_exists_callback=control_type_exists_callback,
            intervention_model_exists_callback=intervention_model_exists_callback,
            trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
        )
