from neomodel import db  # type: ignore

from clinical_mdr_api import models
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.models import ClinicalProgrammeInput
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore


def _models_clinical_programme_from_clinical_programme_ar(
    clinical_programme_ar: ClinicalProgrammeAR,
) -> models.ClinicalProgramme:
    return models.ClinicalProgramme(
        uid=clinical_programme_ar.uid, name=clinical_programme_ar.name
    )


def get_all_clinical_programmes() -> list[models.ClinicalProgramme]:
    repos = MetaRepository()
    try:
        all_clinical_programmes = repos.clinical_programme_repository.find_all()
        repos.clinical_programme_repository.close()
        return [
            _models_clinical_programme_from_clinical_programme_ar(clinical_programme)
            for clinical_programme in all_clinical_programmes
        ]
    finally:
        repos.close()


@db.transaction
def create(
    clinical_programme_create_input: ClinicalProgrammeInput,
) -> models.ClinicalProgramme:
    repos = MetaRepository()
    try:
        clinical_programme_ar = ClinicalProgrammeAR.from_input_values(
            name=clinical_programme_create_input.name,
            generate_uid_callback=repos.clinical_programme_repository.generate_uid,
        )
        repos.clinical_programme_repository.save(clinical_programme_ar)
        return _models_clinical_programme_from_clinical_programme_ar(
            clinical_programme_ar
        )
    finally:
        repos.close()
