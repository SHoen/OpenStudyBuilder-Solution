import datetime

from clinical_mdr_api.domain.controlled_terminology.ct_package import CTPackageAR
from clinical_mdr_api.tests.unit.domain.utils import random_str


def create_random_ct_package() -> CTPackageAR:
    random_ct_package = CTPackageAR.from_repository_values(
        uid=random_str(),
        catalogue_name=random_str(),
        name=random_str(),
        label=random_str(),
        description=random_str(),
        href=random_str(),
        registration_status=random_str(),
        source=random_str(),
        import_date=datetime.datetime.now(),
        effective_date=datetime.date(year=2020, month=6, day=26),
        user_initials=random_str(),
    )
    return random_ct_package
