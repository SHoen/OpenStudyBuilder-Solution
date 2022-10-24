from datetime import date, datetime
from typing import Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_package import CTPackageAR
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.models.utils import BaseModel


class CTPackage(BaseModel):
    @classmethod
    def from_ct_package_ar(cls, ct_package_ar: CTPackageAR) -> "CTPackage":
        return cls(
            uid=ct_package_ar.uid,
            catalogueName=ct_package_ar.catalogue_name,
            name=ct_package_ar.name,
            label=ct_package_ar.label,
            description=ct_package_ar.description,
            href=ct_package_ar.href,
            registrationStatus=ct_package_ar.registration_status,
            source=ct_package_ar.source,
            importDate=ct_package_ar.import_date,
            effectiveDate=ct_package_ar.effective_date,
            userInitials=ct_package_ar.user_initials,
        )

    uid: str = Field(
        ...,
        title="uid",
        description="",
    )

    catalogueName: str = Field(
        ...,
        title="catalogueName",
        description="",
    )
    name: str = Field(
        ...,
        title="name",
        description="",
    )
    label: Optional[str] = Field(
        None,
        title="label",
        description="",
    )
    description: Optional[str] = Field(
        None,
        title="description",
        description="",
    )
    href: Optional[str] = Field(
        None,
        title="href",
        description="",
    )
    registrationStatus: Optional[str] = Field(
        None,
        title="registrationStatus",
        description="",
    )
    source: Optional[str] = Field(
        None,
        title="source",
        description="",
    )
    importDate: datetime = Field(
        ...,
        title="importDate",
        description="",
    )
    effectiveDate: date = Field(
        ...,
        title="effectiveDate",
        description="",
    )
    userInitials: str = Field(
        ...,
        title="userInitials",
        description="",
    )


class CodelistChangeItem(BaseModel):
    uid: str
    value_node: dict
    change_date: datetime
    is_change_of_codelist: bool

    @classmethod
    def from_repository_output(cls, query_output) -> "CodelistChangeItem":
        return cls(
            uid=query_output["uid"],
            value_node=query_output["value_node"],
            change_date=convert_to_datetime(value=query_output["change_date"]),
            is_change_of_codelist=query_output.get("is_change_of_codelist", True),
        )


class TermChangeItem(BaseModel):
    uid: str
    value_node: dict
    change_date: datetime
    codelists: Sequence

    @classmethod
    def from_repository_output(cls, query_output) -> "TermChangeItem":
        return cls(
            uid=query_output["uid"],
            value_node=query_output["value_node"],
            change_date=convert_to_datetime(value=query_output["change_date"]),
            codelists=query_output["codelists"],
        )


class CTPackageChanges(BaseModel):
    fromPackage: str
    toPackage: str
    newCodelists: Sequence[CodelistChangeItem]
    deletedCodelists: Sequence[CodelistChangeItem]
    updatedCodelists: Sequence[CodelistChangeItem]

    newTerms: Sequence[TermChangeItem]
    deletedTerms: Sequence[TermChangeItem]
    updatedTerms: Sequence[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> "CTPackageChanges":
        return cls(
            fromPackage=old_package_name,
            toPackage=new_package_name,
            newCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["new_codelists"]
            ],
            updatedCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["updated_codelists"]
            ],
            deletedCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["deleted_codelists"]
            ],
            newTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["new_terms"]
            ],
            updatedTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["updated_terms"]
            ],
            deletedTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["deleted_terms"]
            ],
        )


class CTPackageChangesSpecificCodelist(CTPackageChanges):
    notModifiedTerms: Sequence[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> "CTPackageChangesSpecificCodelist":
        return cls(
            fromPackage=old_package_name,
            toPackage=new_package_name,
            newCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["new_codelists"]
            ],
            updatedCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["updated_codelists"]
            ],
            deletedCodelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["deleted_codelists"]
            ],
            newTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["new_terms"]
            ],
            updatedTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["updated_terms"]
            ],
            deletedTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["deleted_terms"]
            ],
            notModifiedTerms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["not_modified_terms"]
            ],
        )


class CTPackageDates(BaseModel):
    @classmethod
    def from_repository_output(
        cls, catalogue_name: str, effective_dates: Sequence[date]
    ) -> "CTPackageDates":

        return cls(catalogueName=catalogue_name, effectiveDates=effective_dates)

    catalogueName: str = Field(
        ...,
        title="catalogueName",
        description="",
    )
    effectiveDates: Sequence[date] = Field(..., title="effectiveDates", description="")
