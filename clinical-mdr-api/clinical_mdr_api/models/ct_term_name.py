from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTTermName(BaseModel):
    @classmethod
    def from_ct_term_ar(cls, ct_term_name_ar: CTTermNameAR) -> "CTTermName":
        return cls(
            termUid=ct_term_name_ar.uid,
            catalogueName=ct_term_name_ar.ct_term_vo.catalogue_name,
            codelistUid=ct_term_name_ar.ct_term_vo.codelist_uid,
            sponsorPreferredName=ct_term_name_ar.ct_term_vo.name,
            sponsorPreferredNameSentenceCase=ct_term_name_ar.ct_term_vo.name_sentence_case,
            order=ct_term_name_ar.ct_term_vo.order,
            libraryName=Library.from_library_vo(ct_term_name_ar.library).name,
            possibleActions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            startDate=ct_term_name_ar.item_metadata.start_date,
            endDate=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            changeDescription=ct_term_name_ar.item_metadata.change_description,
            userInitials=ct_term_name_ar.item_metadata.user_initials,
        )

    @classmethod
    def from_ct_term_ar_without_common_term_fields(
        cls, ct_term_name_ar: CTTermNameAR
    ) -> "CTTermName":
        return cls(
            sponsorPreferredName=ct_term_name_ar.ct_term_vo.name,
            sponsorPreferredNameSentenceCase=ct_term_name_ar.ct_term_vo.name_sentence_case,
            order=ct_term_name_ar.ct_term_vo.order,
            possibleActions=sorted(
                [_.value for _ in ct_term_name_ar.get_possible_actions()]
            ),
            startDate=ct_term_name_ar.item_metadata.start_date,
            endDate=ct_term_name_ar.item_metadata.end_date,
            status=ct_term_name_ar.item_metadata.status.value,
            version=ct_term_name_ar.item_metadata.version,
            changeDescription=ct_term_name_ar.item_metadata.change_description,
            userInitials=ct_term_name_ar.item_metadata.user_initials,
        )

    termUid: Optional[str] = Field(
        None,
        title="termUid",
        description="",
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

    sponsorPreferredName: str = Field(
        ...,
        title="sponsorPreferredName",
        description="",
    )

    sponsorPreferredNameSentenceCase: str = Field(
        ...,
        title="sponsorPreferredNameSentenceCase",
        description="",
    )

    order: Optional[int] = Field(
        999999,
        title="order",
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
            "Holds those actions that can be performed on the CTTermName. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTTermNameVersion(CTTermName):
    """
    Class for storing CTTermName and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )


class CTTermNameInput(BaseModel):

    sponsorPreferredName: Optional[str] = Field(
        None,
        title="sponsorPreferredName",
        description="",
    )

    sponsorPreferredNameSentenceCase: Optional[str] = Field(
        None,
        title="sponsorPreferredNameSentenceCase",
        description="",
    )


class CTTermNameEditInput(CTTermNameInput):
    changeDescription: str = Field(None, title="changeDescription", description="")
