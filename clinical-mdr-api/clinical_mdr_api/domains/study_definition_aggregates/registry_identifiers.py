from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api import exceptions
from clinical_mdr_api.domains._utils import normalize_string


@dataclass(frozen=True)
class RegistryIdentifiersVO:
    ct_gov_id: str | None
    ct_gov_id_null_value_code: str | None
    eudract_id: str | None
    eudract_id_null_value_code: str | None
    universal_trial_number_utn: str | None
    universal_trial_number_utn_null_value_code: str | None
    japanese_trial_registry_id_japic: str | None
    japanese_trial_registry_id_japic_null_value_code: str | None
    investigational_new_drug_application_number_ind: str | None
    investigational_new_drug_application_number_ind_null_value_code: str | None
    eu_trial_number: str | None
    eu_trial_number_null_value_code: str | None
    civ_id_sin_number: str | None
    civ_id_sin_number_null_value_code: str | None
    national_clinical_trial_number: str | None
    national_clinical_trial_number_null_value_code: str | None
    japanese_trial_registry_number_jrct: str | None
    japanese_trial_registry_number_jrct_null_value_code: str | None
    national_medical_products_administration_nmpa_number: str | None
    national_medical_products_administration_nmpa_number_null_value_code: str | None
    eudamed_srn_number: str | None
    eudamed_srn_number_null_value_code: str | None
    investigational_device_exemption_ide_number: str | None
    investigational_device_exemption_ide_number_null_value_code: str | None

    @classmethod
    def from_input_values(
        cls,
        ct_gov_id: str | None,
        ct_gov_id_null_value_code: str | None,
        eudract_id: str | None,
        eudract_id_null_value_code: str | None,
        universal_trial_number_utn: str | None,
        universal_trial_number_utn_null_value_code: str | None,
        japanese_trial_registry_id_japic: str | None,
        japanese_trial_registry_id_japic_null_value_code: str | None,
        investigational_new_drug_application_number_ind: str | None,
        investigational_new_drug_application_number_ind_null_value_code: str | None,
        eu_trial_number: str | None,
        eu_trial_number_null_value_code: str | None,
        civ_id_sin_number: str | None,
        civ_id_sin_number_null_value_code: str | None,
        national_clinical_trial_number: str | None,
        national_clinical_trial_number_null_value_code: str | None,
        japanese_trial_registry_number_jrct: str | None,
        japanese_trial_registry_number_jrct_null_value_code: str | None,
        national_medical_products_administration_nmpa_number: str | None,
        national_medical_products_administration_nmpa_number_null_value_code: str
        | None,
        eudamed_srn_number: str | None,
        eudamed_srn_number_null_value_code: str | None,
        investigational_device_exemption_ide_number: str | None,
        investigational_device_exemption_ide_number_null_value_code: str | None,
        is_subpart: bool = False,
    ) -> Self:
        if not is_subpart:
            return cls(
                ct_gov_id=normalize_string(ct_gov_id),
                ct_gov_id_null_value_code=normalize_string(ct_gov_id_null_value_code),
                eudract_id=normalize_string(eudract_id),
                eudract_id_null_value_code=normalize_string(eudract_id_null_value_code),
                universal_trial_number_utn=normalize_string(universal_trial_number_utn),
                universal_trial_number_utn_null_value_code=normalize_string(
                    universal_trial_number_utn_null_value_code
                ),
                japanese_trial_registry_id_japic=normalize_string(
                    japanese_trial_registry_id_japic
                ),
                japanese_trial_registry_id_japic_null_value_code=normalize_string(
                    japanese_trial_registry_id_japic_null_value_code
                ),
                investigational_new_drug_application_number_ind=normalize_string(
                    investigational_new_drug_application_number_ind
                ),
                investigational_new_drug_application_number_ind_null_value_code=normalize_string(
                    investigational_new_drug_application_number_ind_null_value_code
                ),
                eu_trial_number=normalize_string(eu_trial_number),
                eu_trial_number_null_value_code=normalize_string(
                    eu_trial_number_null_value_code
                ),
                civ_id_sin_number=normalize_string(civ_id_sin_number),
                civ_id_sin_number_null_value_code=normalize_string(
                    civ_id_sin_number_null_value_code
                ),
                national_clinical_trial_number=normalize_string(
                    national_clinical_trial_number
                ),
                national_clinical_trial_number_null_value_code=normalize_string(
                    national_clinical_trial_number_null_value_code
                ),
                japanese_trial_registry_number_jrct=normalize_string(
                    japanese_trial_registry_number_jrct
                ),
                japanese_trial_registry_number_jrct_null_value_code=normalize_string(
                    japanese_trial_registry_number_jrct_null_value_code
                ),
                national_medical_products_administration_nmpa_number=normalize_string(
                    national_medical_products_administration_nmpa_number
                ),
                national_medical_products_administration_nmpa_number_null_value_code=normalize_string(
                    national_medical_products_administration_nmpa_number_null_value_code
                ),
                eudamed_srn_number=normalize_string(eudamed_srn_number),
                eudamed_srn_number_null_value_code=normalize_string(
                    eudamed_srn_number_null_value_code
                ),
                investigational_device_exemption_ide_number=normalize_string(
                    investigational_device_exemption_ide_number
                ),
                investigational_device_exemption_ide_number_null_value_code=normalize_string(
                    investigational_device_exemption_ide_number_null_value_code
                ),
            )
        return cls(
            ct_gov_id=None,
            ct_gov_id_null_value_code=None,
            eudract_id=None,
            eudract_id_null_value_code=None,
            universal_trial_number_utn=None,
            universal_trial_number_utn_null_value_code=None,
            japanese_trial_registry_id_japic=None,
            japanese_trial_registry_id_japic_null_value_code=None,
            investigational_new_drug_application_number_ind=None,
            investigational_new_drug_application_number_ind_null_value_code=None,
            eu_trial_number=None,
            eu_trial_number_null_value_code=None,
            civ_id_sin_number=None,
            civ_id_sin_number_null_value_code=None,
            national_clinical_trial_number=None,
            national_clinical_trial_number_null_value_code=None,
            japanese_trial_registry_number_jrct=None,
            japanese_trial_registry_number_jrct_null_value_code=None,
            national_medical_products_administration_nmpa_number=None,
            national_medical_products_administration_nmpa_number_null_value_code=None,
            eudamed_srn_number=None,
            eudamed_srn_number_null_value_code=None,
            investigational_device_exemption_ide_number=None,
            investigational_device_exemption_ide_number_null_value_code=None,
        )

    def validate(
        self, null_value_exists_callback: Callable[[str], bool] = (lambda _: True)
    ) -> None:
        """Raises ValueError if values do not comply with relevant business rules."""
        if (
            self.ct_gov_id_null_value_code is not None
            and not null_value_exists_callback(self.ct_gov_id_null_value_code)
        ):
            raise exceptions.ValidationException(
                "Unknown null value code provided for Reason For Missing in ClinicalTrials.gov ID"
            )

        if (
            self.eudract_id_null_value_code is not None
            and not null_value_exists_callback(self.eudract_id_null_value_code)
        ):
            raise exceptions.ValidationException(
                "Unknown null value code provided for Reason For Missing in EUDRACT ID"
            )

        if (
            self.universal_trial_number_utn_null_value_code is not None
            and not null_value_exists_callback(
                self.universal_trial_number_utn_null_value_code
            )
        ):
            raise exceptions.ValidationException(
                "Unknown null value code provided for Reason For Missing in Universal Trial Number (UTN)"
            )

        if (
            self.japanese_trial_registry_id_japic_null_value_code is not None
            and not null_value_exists_callback(
                self.japanese_trial_registry_id_japic_null_value_code
            )
        ):
            raise exceptions.ValidationException(
                "Unknown null value code provided for Reason For Missing in Japanese Trial Registry ID (JAPIC)"
            )

        if (
            self.investigational_new_drug_application_number_ind_null_value_code
            is not None
            and not null_value_exists_callback(
                self.investigational_new_drug_application_number_ind_null_value_code
            )
        ):
            raise exceptions.ValidationException(
                "Unknown null value code provided for Reason For Missing in Investigational New Drug Application (IND) Number"
            )

        if self.ct_gov_id_null_value_code is not None and self.ct_gov_id is not None:
            raise exceptions.ValidationException(
                "If reason_for_missing_null_value_uid has a value, then field ct_gov_id must be None or empty string"
            )

        if self.eudract_id_null_value_code is not None and self.eudract_id is not None:
            raise exceptions.ValidationException(
                "If reason_for_missing_null_value_uid has a value, then field eudract_id must be None or empty string"
            )

        if (
            self.universal_trial_number_utn_null_value_code is not None
            and self.universal_trial_number_utn is not None
        ):
            raise exceptions.ValidationException(
                "If reason_for_missing_null_value_uid has a value, then field universal_trial_number_utn must be None or empty string"
            )

        if (
            self.japanese_trial_registry_id_japic_null_value_code is not None
            and self.japanese_trial_registry_id_japic is not None
        ):
            raise exceptions.ValidationException(
                "If reason_for_missing_null_value_uid has a value, then field japanese_trial_registry_id_japic must be None or empty string"
            )

        if (
            self.investigational_new_drug_application_number_ind_null_value_code
            is not None
            and self.investigational_new_drug_application_number_ind is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field investigational_new_drug_application_number_ind must be None or empty string"
                )
            )

        if (
            self.eu_trial_number is not None
            and self.eu_trial_number_null_value_code is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field eu_trial_number must be None or empty string"
                )
            )

        if (
            self.civ_id_sin_number is not None
            and self.civ_id_sin_number_null_value_code is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field civ_id_sin_number must be None or empty string"
                )
            )

        if (
            self.national_clinical_trial_number is not None
            and self.national_clinical_trial_number_null_value_code is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field national_clinical_trial_number must be None or empty string"
                )
            )

        if (
            self.japanese_trial_registry_number_jrct is not None
            and self.japanese_trial_registry_number_jrct_null_value_code is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field japanese_trial_registry_number_jrct must be None or empty string"
                )
            )

        if (
            self.national_medical_products_administration_nmpa_number is not None
            and self.national_medical_products_administration_nmpa_number_null_value_code
            is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field national_medical_products_administration_nmpa_number must be None or empty string"
                )
            )

        if (
            self.eudamed_srn_number is not None
            and self.eudamed_srn_number_null_value_code is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field eudamed_srn_number must be None or empty string"
                )
            )

        if (
            self.investigational_device_exemption_ide_number is not None
            and self.investigational_device_exemption_ide_number_null_value_code
            is not None
        ):
            raise exceptions.ValidationException(
                (
                    "If reason_for_missing_null_value_uid has a value, "
                    "then field investigational_device_exemption_ide_number must be None or empty string"
                )
            )
