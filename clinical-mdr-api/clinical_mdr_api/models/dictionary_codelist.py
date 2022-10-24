from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from clinical_mdr_api.domain.dictionaries.dictionary_codelist import (
    DictionaryCodelistAR,
)
from clinical_mdr_api.models import Library
from clinical_mdr_api.models.utils import BaseModel


class DictionaryCodelist(BaseModel):
    @classmethod
    def from_dictionary_codelist_ar(
        cls, dictionary_codelist_ar: DictionaryCodelistAR
    ) -> "DictionaryCodelist":
        return cls(
            codelistUid=dictionary_codelist_ar.uid,
            name=dictionary_codelist_ar.name,
            libraryName=Library.from_library_vo(dictionary_codelist_ar.library).name,
            templateParameter=dictionary_codelist_ar.dictionary_codelist_vo.is_template_parameter,
            startDate=dictionary_codelist_ar.item_metadata.start_date,
            endDate=dictionary_codelist_ar.item_metadata.end_date,
            status=dictionary_codelist_ar.item_metadata.status.value,
            version=dictionary_codelist_ar.item_metadata.version,
            changeDescription=dictionary_codelist_ar.item_metadata.change_description,
            userInitials=dictionary_codelist_ar.item_metadata.user_initials,
            possibleActions=sorted(
                [_.value for _ in dictionary_codelist_ar.get_possible_actions()]
            ),
        )

    codelistUid: str = Field(
        ...,
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

    possibleActions: List[str] = Field(
        ...,
        description=(
            "Holds those actions that can be performed on the DictionaryCodelist. "
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


class DictionaryCodelistInput(BaseModel):
    name: Optional[str] = Field(
        None,
        title="name",
        description="",
    )

    templateParameter: Optional[bool] = Field(
        None,
        title="templateParameter",
        description="",
    )


class DictionaryCodelistEditInput(DictionaryCodelistInput):
    changeDescription: str = Field(None, title="changeDescription", description="")


class DictionaryCodelistCreateInput(DictionaryCodelistInput):
    libraryName: str


class DictionaryCodelistTermInput(BaseModel):
    termUid: str = Field(
        ...,
        title="termUid",
        description="",
    )


class DictionaryCodelistVersion(DictionaryCodelist):
    """
    Class for storing DictionaryCodelist and calculation of differences
    """

    changes: Dict[str, bool] = Field(
        None,
        description=(
            "Denotes whether or not there was a change in a specific field/property compared to the previous version. "
            "The field names in this object here refer to the field names of the objective (e.g. name, startDate, ..)."
        ),
    )
