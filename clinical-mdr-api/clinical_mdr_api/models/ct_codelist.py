from typing import List, Optional, Sequence

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.ct_codelist_attributes import CTCodelistAttributes
from clinical_mdr_api.models.ct_codelist_name import CTCodelistName
from clinical_mdr_api.models.utils import BaseModel


class CTCodelist(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> "CTCodelist":
        return cls(
            catalogueName=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelistUid=ct_codelist_attributes_ar.uid,
            parentCodelistUid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            childCodelistUids=ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids,
            name=ct_codelist_attributes_ar.name,
            submissionValue=ct_codelist_attributes_ar.ct_codelist_vo.submission_value,
            nciPreferredName=ct_codelist_attributes_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_attributes_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_attributes_ar.ct_codelist_vo.extensible,
            libraryName=Library.from_library_vo(ct_codelist_attributes_ar.library).name,
            sponsorPreferredName=ct_codelist_name_ar.name,
            templateParameter=ct_codelist_name_ar.ct_codelist_vo.is_template_parameter,
            possibleActions=sorted(
                [_.value for _ in ct_codelist_attributes_ar.get_possible_actions()]
            ),
        )

    catalogueName: str = Field(
        ...,
        title="catalogueName",
        description="",
    )

    codelistUid: str = Field(
        ...,
        title="codelistUid",
        description="",
    )

    parentCodelistUid: Optional[str] = Field(
        ...,
        title="parentCodelistUid",
        description="",
    )

    childCodelistUids: Optional[Sequence[str]] = Field(
        ...,
        title="childCodelistUids",
        description="",
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

    sponsorPreferredName: str = Field(
        ...,
        title="sponsorPreferredName",
        description="",
    )

    templateParameter: bool = Field(
        ...,
        title="templateParameter",
        description="",
    )

    libraryName: str
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the CTCodelistAttributes. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTCodelistTermInput(BaseModel):
    termUid: str = Field(
        ...,
        title="termUid",
        description="",
    )
    order: Optional[int] = Field(
        999999,
        title="order",
        description="",
    )


class CTCodelistCreateInput(BaseModel):
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

    sponsorPreferredName: str = Field(
        ...,
        title="sponsorPreferredName",
        description="",
    )

    templateParameter: bool = Field(
        ...,
        title="templateParameter",
        description="",
    )

    parentCodelistUid: Optional[str] = Field(
        None,
        title="parentCodelistUid",
        description="",
    )

    terms: Sequence[CTCodelistTermInput]

    libraryName: str


class CTCodelistNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> "CTCodelistNameAndAttributes":
        codelist_name_and_attributes = cls(
            catalogueName=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelistUid=ct_codelist_attributes_ar.uid,
            parentCodelistUid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            childCodelistUids=ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids,
            libraryName=Library.from_library_vo(ct_codelist_attributes_ar.library).name,
            name=CTCodelistName.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_name_ar
            ),
            attributes=CTCodelistAttributes.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_attributes_ar
            ),
        )

        return codelist_name_and_attributes

    catalogueName: str = Field(
        ...,
        title="catalogueName",
        description="",
    )

    codelistUid: str = Field(
        ...,
        title="codelistUid",
        description="",
    )

    parentCodelistUid: str = Field(
        None,
        title="parentCodelistUid",
        description="",
    )

    childCodelistUids: Sequence = Field(
        None,
        title="childCodelistUids",
        description="",
    )

    libraryName: str

    name: CTCodelistName = Field(
        ...,
        title="CTCodelistName",
        description="",
    )

    attributes: CTCodelistAttributes = Field(
        ...,
        title="CTCodelistAttributes",
        description="",
    )
