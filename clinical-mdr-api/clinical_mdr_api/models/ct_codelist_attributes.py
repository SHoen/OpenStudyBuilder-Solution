from datetime import datetime
from typing import Callable, Dict, List, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTCodelistAttributes(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls, ct_codelist_ar: CTCodelistAttributesAR
    ) -> "CTCodelistAttributes":
        return cls(
            catalogueName=ct_codelist_ar.ct_codelist_vo.catalogue_name,
            codelistUid=ct_codelist_ar.uid,
            parentCodelistUid=ct_codelist_ar.ct_codelist_vo.parent_codelist_uid,
            childCodelistUids=ct_codelist_ar.ct_codelist_vo.child_codelist_uids,
            name=ct_codelist_ar.name,
            submissionValue=ct_codelist_ar.ct_codelist_vo.submission_value,
            nciPreferredName=ct_codelist_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_ar.ct_codelist_vo.extensible,
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
        cls, ct_codelist_ar: CTCodelistAttributesAR
    ) -> "CTCodelistAttributes":
        return cls(
            name=ct_codelist_ar.name,
            submissionValue=ct_codelist_ar.ct_codelist_vo.submission_value,
            nciPreferredName=ct_codelist_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_ar.ct_codelist_vo.extensible,
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

    parentCodelistUid: str = Field(
        None, title="parentCodelistUid", description="", removeFromWildcard=True
    )

    childCodelistUids: Optional[Sequence[str]] = Field(
        None, title="childCodelistUids", description="", removeFromWildcard=True
    )

    name: str = Field(
        ...,
        title="name",
        description="",
    )

    submissionValue: str = Field(
        ...,
        title="submissionValue",
        description="",
    )

    nciPreferredName: str = Field(
        ...,
        title="nciPreferredName",
        description="",
    )

    definition: str = Field(
        ...,
        title="definition",
        description="",
    )

    extensible: bool = Field(
        ...,
        title="extensible",
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
            "Holds those actions that can be performed on the CTCodelistAttributes. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTCodelistAttributesSimpleModel(BaseModel):
    @classmethod
    def from_codelist_uid(
        cls,
        uid: str,
        find_codelist_attribute_by_codelist_uid: Callable[
            [str], Optional[CTCodelistAttributesAR]
        ],
    ) -> Optional["CTCodelistAttributesSimpleModel"]:
        if uid is not None:
            codelist_attribute = find_codelist_attribute_by_codelist_uid(uid)

            if codelist_attribute is not None:
                simple_codelist_attribute_model = cls(
                    uid=uid,
                    name=codelist_attribute._ct_codelist_attributes_vo.name,
                    submissionValue=codelist_attribute._ct_codelist_attributes_vo.submission_value,
                    preferredTerm=codelist_attribute._ct_codelist_attributes_vo.preferred_term,
                )
            else:
                simple_codelist_attribute_model = cls(
                    uid=uid,
                    name=None,
                    submissionValue=None,
                    preferredTerm=None,
                )
        else:
            simple_codelist_attribute_model = None
        return simple_codelist_attribute_model

    uid: str = Field(..., title="uid", description="")
    name: Optional[str] = Field(None, title="name", description="")
    submissionValue: Optional[str] = Field(
        None, title="submissionValue", description=""
    )
    preferredTerm: Optional[str] = Field(None, title="preferredTerm", description="")


class CTCodelistAttributesVersion(CTCodelistAttributes):
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


class CTCodelistAttributesInput(BaseModel):
    name: Optional[str] = Field(
        None,
        title="name",
        description="",
    )

    submissionValue: Optional[str] = Field(
        None,
        title="submissionValue",
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

    extensible: Optional[bool] = Field(
        None,
        title="extensible",
        description="",
    )


class CTCodelistAttributesEditInput(CTCodelistAttributesInput):
    changeDescription: str = Field(None, title="changeDescription", description="")
