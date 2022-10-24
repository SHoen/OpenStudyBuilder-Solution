from dataclasses import dataclass
from typing import Callable, Optional

from clinical_mdr_api.domain._utils import normalize_string  # type: ignore


@dataclass(frozen=True)
class RegistryIdentifiersVO:
    ct_gov_id: Optional[str]
    ct_gov_id_null_value_code: Optional[str]
    eudract_id: Optional[str]
    eudract_id_null_value_code: Optional[str]
    universal_trial_number_UTN: Optional[str]
    universal_trial_number_UTN_null_value_code: Optional[str]
    japanese_trial_registry_id_JAPIC: Optional[str]
    japanese_trial_registry_id_JAPIC_null_value_code: Optional[str]
    investigational_new_drug_application_number_IND: Optional[str]
    investigational_new_drug_application_number_IND_null_value_code: Optional[str]

    @classmethod
    def from_input_values(
        cls,
        ct_gov_id: Optional[str],
        ct_gov_id_null_value_code: Optional[str],
        eudract_id: Optional[str],
        eudract_id_null_value_code: Optional[str],
        universal_trial_number_UTN: Optional[str],
        universal_trial_number_UTN_null_value_code: Optional[str],
        japanese_trial_registry_id_JAPIC: Optional[str],
        japanese_trial_registry_id_JAPIC_null_value_code: Optional[str],
        investigational_new_drug_application_number_IND: Optional[str],
        investigational_new_drug_application_number_IND_null_value_code: Optional[str],
    ) -> "RegistryIdentifiersVO":
        def norm_str(s: Optional[str]) -> Optional[str]:
            return normalize_string(s)

        return cls(
            ct_gov_id=norm_str(ct_gov_id),
            ct_gov_id_null_value_code=norm_str(ct_gov_id_null_value_code),
            eudract_id=norm_str(eudract_id),
            eudract_id_null_value_code=norm_str(eudract_id_null_value_code),
            universal_trial_number_UTN=norm_str(universal_trial_number_UTN),
            universal_trial_number_UTN_null_value_code=norm_str(
                universal_trial_number_UTN_null_value_code
            ),
            japanese_trial_registry_id_JAPIC=norm_str(japanese_trial_registry_id_JAPIC),
            japanese_trial_registry_id_JAPIC_null_value_code=norm_str(
                japanese_trial_registry_id_JAPIC_null_value_code
            ),
            investigational_new_drug_application_number_IND=norm_str(
                investigational_new_drug_application_number_IND
            ),
            investigational_new_drug_application_number_IND_null_value_code=norm_str(
                investigational_new_drug_application_number_IND_null_value_code
            ),
        )

    def validate(
        self, null_value_exists_callback: Callable[[str], bool] = (lambda _: True)
    ) -> None:
        """Raises ValueError if values do not comply with relevant business rules."""
        if (
            self.ct_gov_id_null_value_code is not None
            and not null_value_exists_callback(self.ct_gov_id_null_value_code)
        ):
            raise ValueError(
                "Unknown null value code provided for Reason For Missing in ClinicalTrials.gov ID"
            )

        if (
            self.eudract_id_null_value_code is not None
            and not null_value_exists_callback(self.eudract_id_null_value_code)
        ):
            raise ValueError(
                "Unknown null value code provided for Reason For Missing in EUDRACT ID"
            )

        if (
            self.universal_trial_number_UTN_null_value_code is not None
            and not null_value_exists_callback(
                self.universal_trial_number_UTN_null_value_code
            )
        ):
            raise ValueError(
                "Unknown null value code provided for Reason For Missing in Universal Trial Number (UTN)"
            )

        if (
            self.japanese_trial_registry_id_JAPIC_null_value_code is not None
            and not null_value_exists_callback(
                self.japanese_trial_registry_id_JAPIC_null_value_code
            )
        ):
            raise ValueError(
                "Unknown null value code provided for Reason For Missing in Japanese Trial Registry ID (JAPIC)"
            )

        if (
            self.investigational_new_drug_application_number_IND_null_value_code
            is not None
            and not null_value_exists_callback(
                self.investigational_new_drug_application_number_IND_null_value_code
            )
        ):
            raise ValueError(
                "Unknown null value code provided for Reason For Missing in Investigational New Drug Application (IND) Number"
            )

        if self.ct_gov_id_null_value_code is not None and self.ct_gov_id is not None:
            raise ValueError(
                "If reasonForMissingNullValueUid has a value, then field ctGovId must be None or empty string"
            )

        if self.eudract_id_null_value_code is not None and self.eudract_id is not None:
            raise ValueError(
                "If reasonForMissingNullValueUid has a value, then field eudractId must be None or empty string"
            )

        if (
            self.universal_trial_number_UTN_null_value_code is not None
            and self.universal_trial_number_UTN is not None
        ):
            raise ValueError(
                "If reasonForMissingNullValueUid has a value, then field universalTrialNumberUTN must be None or empty string"
            )

        if (
            self.japanese_trial_registry_id_JAPIC_null_value_code is not None
            and self.japanese_trial_registry_id_JAPIC is not None
        ):
            raise ValueError(
                "If reasonForMissingNullValueUid has a value, then field japaneseTrialRegistryIdJAPIC must be None or empty string"
            )

        if (
            self.investigational_new_drug_application_number_IND_null_value_code
            is not None
            and self.investigational_new_drug_application_number_IND is not None
        ):
            raise ValueError(
                "If reasonForMissingNullValueUid has a value, then field investigationalNewDrugApplicationNumberIND must be None or empty string"
            )
