from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class CTPackageAR:
    _uid: str
    catalogue_name: str
    name: str
    label: Optional[str]
    description: Optional[str]
    href: Optional[str]
    registration_status: Optional[str]
    source: Optional[str]
    import_date: datetime
    effective_date: date
    user_initials: str

    @property
    def uid(self) -> str:
        return self._uid

    @staticmethod
    def from_repository_values(
        uid: str,
        catalogue_name: str,
        name: str,
        label: Optional[str],
        description: Optional[str],
        href: Optional[str],
        registration_status: Optional[str],
        source: Optional[str],
        import_date: datetime,
        effective_date: date,
        user_initials: str,
    ):

        return CTPackageAR(
            _uid=uid,
            catalogue_name=catalogue_name,
            name=name,
            label=label,
            description=description,
            href=href,
            registration_status=registration_status,
            source=source,
            import_date=import_date,
            effective_date=effective_date,
            user_initials=user_initials,
        )
