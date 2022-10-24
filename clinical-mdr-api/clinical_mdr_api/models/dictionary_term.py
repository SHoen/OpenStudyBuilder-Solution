from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.domain.dictionaries.dictionary_term_substance import (
    DictionaryTermSubstanceAR,
)
from clinical_mdr_api.models.ct_term import SimpleDictionaryTermModel
from clinical_mdr_api.models.library import Library
from clinical_mdr_api.models.utils import BaseModel


class DictionaryTerm(BaseModel):
    @classmethod
    def from_dictionary_term_ar(
        cls, dictionary_term_ar: DictionaryTermAR
    ) -> "DictionaryTerm":
        if not dictionary_term_ar:
            return None
        return cls(
            termUid=dictionary_term_ar.uid,
            dictionaryId=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            nameSentenceCase=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            libraryName=Library.from_library_vo(dictionary_term_ar.library).name,
            startDate=dictionary_term_ar.item_metadata.start_date,
            endDate=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            changeDescription=dictionary_term_ar.item_metadata.change_description,
            userInitials=dictionary_term_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )

    termUid: str
    dictionaryId: str
    name: str
    nameSentenceCase: str
    abbreviation: Optional[str]
    definition: Optional[str]

    possibleActions: List[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the DictionaryTerm. "
            "Actions are: 'approve', 'edit', 'newVersion'."
        ),
    )

    libraryName: str
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    status: Optional[str] = None
    version: Optional[str] = None
    changeDescription: Optional[str] = None
    userInitials: Optional[str] = None


class DictionaryTermEditInput(BaseModel):
    dictionaryId: Optional[str] = None
    name: Optional[str] = None
    nameSentenceCase: Optional[str] = None
    abbreviation: Optional[str] = None
    definition: Optional[str] = None
    changeDescription: str = Field(None, title="changeDescription", description="")


class DictionaryTermCreateInput(BaseModel):
    dictionaryId: str
    name: str
    nameSentenceCase: Optional[str] = None
    abbreviation: Optional[str] = None
    definition: Optional[str] = None
    codelistUid: str = Field(..., title="codelistUid", description="")
    libraryName: str


class DictionaryTermSubstance(DictionaryTerm):
    pclass: Optional[SimpleDictionaryTermModel]

    @classmethod
    def from_dictionary_term_ar(
        cls,
        dictionary_term_ar: DictionaryTermSubstanceAR,
        find_dictionary_term_by_uid: Callable[[str], Optional[DictionaryTermAR]],
    ) -> "DictionaryTermSubstance":
        if not dictionary_term_ar:
            return None
        return cls(
            termUid=dictionary_term_ar.uid,
            dictionaryId=dictionary_term_ar.dictionary_term_vo.dictionary_id,
            name=dictionary_term_ar.name,
            nameSentenceCase=dictionary_term_ar.dictionary_term_vo.name_sentence_case,
            abbreviation=dictionary_term_ar.dictionary_term_vo.abbreviation,
            definition=dictionary_term_ar.dictionary_term_vo.definition,
            libraryName=Library.from_library_vo(dictionary_term_ar.library).name,
            pclass=SimpleDictionaryTermModel.from_ct_code(
                c_code=dictionary_term_ar.dictionary_term_vo.pclass_uid,
                find_term_by_uid=find_dictionary_term_by_uid,
            ),
            startDate=dictionary_term_ar.item_metadata.start_date,
            endDate=dictionary_term_ar.item_metadata.end_date,
            status=dictionary_term_ar.item_metadata.status.value,
            version=dictionary_term_ar.item_metadata.version,
            changeDescription=dictionary_term_ar.item_metadata.change_description,
            userInitials=dictionary_term_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in dictionary_term_ar.get_possible_actions()]
            ),
        )


class CompoundSubstance(BaseModel):

    substanceTermUid: str
    substanceName: str
    substanceUnii: str
    pclassTermUid: Optional[str]
    pclassName: Optional[str]
    pclassId: Optional[str]

    @classmethod
    def from_term_uid(
        cls,
        uid: str,
        find_term_by_uid: Callable[[str], Optional[Any]],
        find_substance_by_uid: Callable[[str], Optional[Any]],
    ) -> Optional["DictionaryTermSubstance"]:
        substance = None
        if uid is not None:
            substance_term: DictionaryTermSubstanceAR = find_substance_by_uid(uid)

            if substance_term is not None:
                pclass_term: SimpleDictionaryTermModel = (
                    SimpleDictionaryTermModel.from_ct_code(
                        c_code=substance_term.dictionary_term_vo.pclass_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                )

                substance = cls(
                    substanceTermUid=uid,
                    substanceName=substance_term.dictionary_term_vo.name,
                    substanceUnii=substance_term.dictionary_term_vo.dictionary_id,
                    pclassTermUid=pclass_term.termUid if pclass_term else None,
                    pclassName=pclass_term.name if pclass_term else None,
                    pclassId=pclass_term.dictionaryId if pclass_term else None,
                )

        return substance


class DictionaryTermSubstanceCreateInput(DictionaryTermCreateInput):
    pclassUid: Optional[str] = None


class DictionaryTermSubstanceEditInput(DictionaryTermEditInput):
    pclassUid: Optional[str] = None


class DictionaryTermVersion(DictionaryTerm):
    """
    Class for storing DictionaryTerm and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
