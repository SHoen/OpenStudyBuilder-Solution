from typing import Any, Callable, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import CTTermNameAR
from clinical_mdr_api.models.ct_term_attributes import CTTermAttributes
from clinical_mdr_api.models.ct_term_name import CTTermName
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class CTTerm(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> "CTTerm":
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
            sponsorPreferredName=ct_term_name_ar.ct_term_vo.name,
            sponsorPreferredNameSentenceCase=ct_term_name_ar.ct_term_vo.name_sentence_case,
            order=ct_term_name_ar.ct_term_vo.order,
            possibleActions=sorted(
                [_.value for _ in ct_term_attributes_ar.get_possible_actions()]
            ),
        )

    termUid: str = Field(
        ...,
        title="termUid",
        description="",
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

    libraryName: str
    possibleActions: Optional[List[str]] = Field(
        None,
        description=(
            "Holds those actions that can be performed on the CTTerm. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )


class CTTermCreateInput(BaseModel):
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

    codeSubmissionValue: str = Field(
        ...,
        title="codeSubmissionValue",
        description="",
    )

    nameSubmissionValue: Optional[str] = Field(
        None,
        title="nameSubmissionValue",
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
    libraryName: str = Field(
        ...,
        title="libraryName",
        description="",
    )


class CTTermNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_term_ars(
        cls, ct_term_name_ar: CTTermNameAR, ct_term_attributes_ar: CTTermAttributesAR
    ) -> "CTTermNameAndAttributes":
        if not ct_term_name_ar or not ct_term_attributes_ar:
            return None
        term_name_and_attributes = cls(
            termUid=ct_term_attributes_ar.uid,
            catalogueName=ct_term_attributes_ar.ct_term_vo.catalogue_name,
            codelistUid=ct_term_attributes_ar.ct_term_vo.codelist_uid,
            libraryName=Library.from_library_vo(ct_term_attributes_ar.library).name
            if ct_term_attributes_ar.library
            else None,
            name=CTTermName.from_ct_term_ar_without_common_term_fields(ct_term_name_ar),
            attributes=CTTermAttributes.from_ct_term_ar_without_common_term_fields(
                ct_term_attributes_ar
            ),
        )

        return term_name_and_attributes

    termUid: str = Field(
        ...,
        title="codelistUid",
        description="",
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

    libraryName: Optional[str]

    name: CTTermName = Field(
        ...,
        title="CTTermName",
        description="",
    )

    attributes: CTTermAttributes = Field(
        ...,
        title="CTTermAttributes",
        description="",
    )


class CTTermNewOrder(BaseModel):
    codelistUid: str = Field(
        ...,
        title="codelistUid",
        description="",
    )
    newOrder: int = Field(
        999999,
        title="newOrder",
        description="",
    )


class SimpleCTTermAttributes(BaseModel):
    @classmethod
    def from_term_uid(
        cls, uid: str, find_term_by_uid: Callable[[str], Optional[Any]]
    ) -> Optional["SimpleCTTermAttributes"]:
        term_model = None
        if uid is not None:
            term = find_term_by_uid(uid)
            if term is not None:
                term_model = cls(
                    uid=uid,
                    codeSubmissionValue=term.ct_term_vo.code_submission_value,
                    preferredTerm=term.ct_term_vo.preferred_term,
                )
            else:
                term_model = cls(uid=uid, codeSubmissionValue=None, preferredTerm=None)
        else:
            term_model = None
        return term_model

    uid: str = Field(..., title="uid", description="")
    codeSubmissionValue: Optional[str] = Field(
        None, title="codeSubmissionValue", description=""
    )
    preferredTerm: Optional[str] = Field(None, title="preferredTerm", description="")


class SimpleTermModel(BaseModel):
    @classmethod
    def from_ct_code(
        cls, c_code: str, find_term_by_uid: Callable[[str], Optional[Any]]
    ) -> Optional["SimpleTermModel"]:
        simple_term_model = None
        if c_code is not None:
            term = find_term_by_uid(c_code)

            if term is not None:
                if hasattr(term, "ct_term_vo"):
                    simple_term_model = cls(termUid=c_code, name=term.ct_term_vo.name)
                elif hasattr(term, "dictionary_term_vo"):
                    simple_term_model = SimpleDictionaryTermModel(
                        termUid=c_code,
                        name=term.dictionary_term_vo.name,
                        dictionaryId=getattr(
                            term.dictionary_term_vo, "dictionary_id", None
                        ),
                    )
            else:
                simple_term_model = cls(termUid=c_code, name=None)
        else:
            simple_term_model = None
        return simple_term_model

    termUid: str = Field(..., title="termUid", description="")
    name: Optional[str] = Field(None, title="name", description="")


class SimpleDictionaryTermModel(SimpleTermModel):
    dictionaryId: Optional[str] = Field(
        None, title="dictionaryId", description="Id if item in the external dictionary"
    )
