from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTTermAttributes(BaseModel):
    @classmethod
    def from_ct_term_ar(
        cls, ct_term_attributes_ar: CTTermAttributesAR
    ) -> "CTTermAttributes":
        return cls(
            termUid=ct_term_attributes_ar.uid,
            catalogueName=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            codelistUid=ct_term_attributes_ar.ct_term_vo.codelist_uid,
            conceptId=ct_term_attributes_ar.ct_term_vo.concept_id,
            codeSubmissionValue=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            nameSubmissionValue=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nciPreferredName=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            libraryName=Library.from_library_vo(ct_term_attributes_ar.library).name,
            possibleActions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
            startDate=ct_term_attributes_ar.item_metadata.start_date,
            endDate=ct_term_attributes_ar.item_metadata.end_date,
            status=ct_term_attributes_ar.item_metadata.status.value,
            version=ct_term_attributes_ar.item_metadata.version,
            changeDescription=ct_term_attributes_ar.item_metadata.change_description,
            userInitials=ct_term_attributes_ar.item_metadata.user_initials,
        )

    @classmethod
    def from_ct_term_ar_without_common_term_fields(
        cls, ct_term_attributes_ar: CTTermAttributesAR
    ) -> "CTTermAttributes":
        return cls(
            conceptId=ct_term_attributes_ar.ct_term_vo.concept_id,
            codeSubmissionValue=ct_term_attributes_ar.ct_term_vo.code_submission_value,
            nameSubmissionValue=ct_term_attributes_ar.ct_term_vo.name_submission_value,
            nciPreferredName=ct_term_attributes_ar.ct_term_vo.preferred_term,
            definition=ct_term_attributes_ar.ct_term_vo.definition,
            possibleActions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
            startDate=ct_term_attributes_ar.item_metadata.start_date,
            endDate=ct_term_attributes_ar.item_metadata.end_date,
            status=ct_term_attributes_ar.item_metadata.status.value,
            version=ct_term_attributes_ar.item_metadata.version,
            changeDescription=ct_term_attributes_ar.item_metadata.change_description,
            userInitials=ct_term_attributes_ar.item_metadata.user_initials,
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

    conceptId: Optional[str] = Field(
        ...,
        title="conceptId",
        description="",
    )

    codeSubmissionValue: Optional[str] = Field(
        ...,
        title="codeSubmissionValue",
        description="",
    )

    nameSubmissionValue: Optional[str] = Field(
        ...,
        title="nameSubmissionValue",
        description="",
    )

    nciPreferredName: str = Field(
        ...,
        title="nciPreferredName",
        description="",
    )

    definition: str = Field(
        ..., title="definition", description="", removeFromWildcard=True
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
            "Holds those actions that can be performed on the CTTermAttributes. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTTermAttributesVersion(CTTermAttributes):
    """
    Class for storing CTTermAttributes and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )


class CTTermAttributesInput(BaseModel):

    codeSubmissionValue: Optional[str] = Field(
        None,
        title="codeSubmissionValue",
        description="",
    )

    nameSubmissionValue: Optional[str] = Field(
        None,
        title="nameSubmissionValue",
        description="",
    )

    nciPreferredName: Optional[str] = Field(
        None,
        title="nciPreferredName",
        description="",
    )

    definition: Optional[str] = Field(
        None,
        title="definition",
        description="",
    )


class CTTermAttributesEditInput(CTTermAttributesInput):
    changeDescription: str = Field(None, title="changeDescription", description="")
