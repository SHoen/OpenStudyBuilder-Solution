from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTCodelistName(BaseModel):
    @classmethod
    def from_ct_codelist_ar(cls, ct_codelist_ar: CTCodelistNameAR) -> "CTCodelistName":
        return cls(
            catalogueName=ct_codelist_ar.ct_codelist_vo.catalogue_name,
            codelistUid=ct_codelist_ar.uid,
            name=ct_codelist_ar.name,
            templateParameter=ct_codelist_ar.ct_codelist_vo.is_template_parameter,
            libraryName=Library.from_library_vo(ct_codelist_ar.library).name,
            startDate=ct_codelist_ar.item_metadata.start_date,
            endDate=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            changeDescription=ct_codelist_ar.item_metadata.change_description,
            userInitials=ct_codelist_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_ct_codelist_ar_without_common_codelist_fields(
        cls, ct_codelist_ar: CTCodelistNameAR
    ) -> "CTCodelistName":
        return cls(
            name=ct_codelist_ar.name,
            templateParameter=ct_codelist_ar.ct_codelist_vo.is_template_parameter,
            startDate=ct_codelist_ar.item_metadata.start_date,
            endDate=ct_codelist_ar.item_metadata.end_date,
            status=ct_codelist_ar.item_metadata.status.value,
            version=ct_codelist_ar.item_metadata.version,
            changeDescription=ct_codelist_ar.item_metadata.change_description,
            userInitials=ct_codelist_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in ct_codelist_ar.get_possible_actions()]
            ),
        )

    catalogueName: Optional[str] = Field(
        None,
        title="catalogueName",
        description="",
    )

    codelistUid: Optional[str] = Field(
        None,
        title="codelistUid",
        description="",
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    templateParameter: bool = Field(
        ...,
        title="templateParameter",
        description="",
    )
    libraryName: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the CTCodelistName. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTCodelistNameVersion(CTCodelistName):
    """
    Class for storing CTCodelistAttributes and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )


class CTCodelistNameInput(BaseModel):
    name: Optional[str] = Field(
        None,
        title="name",
        description="",
    )

    templateParameter: Optional[bool] = Field(
        None, title="templateParameter", description=""
    )


class CTCodelistNameEditInput(CTCodelistNameInput):
    changeDescription: str = Field(None, title="changeDescription", description="")


class CTCodelistNameCreateInput(CTCodelistNameInput):
    codelistUid: str = Field(None, title="changeDescription", description="")
