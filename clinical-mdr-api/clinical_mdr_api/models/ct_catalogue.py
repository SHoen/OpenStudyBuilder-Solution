from datetime import datetime
from typing import Optional, Sequence

from pydantic import Field

from clinical_mdr_api.models.ct_package import CodelistChangeItem, TermChangeItem
from clinical_mdr_api.models.utils import BaseModel


class CTCatalogue(BaseModel):
    name: str = Field(
        ...,
        title="name",
        description="",
    )

    libraryName: Optional[str] = Field(
        ...,
        title="libraryName",
        description="",
    )


class CTCatalogueChanges(BaseModel):
    startDatetime: datetime
    endDatetime: datetime
    newCodelists: Sequence[CodelistChangeItem]
    deletedCodelists: Sequence[CodelistChangeItem]
    updatedCodelists: Sequence[CodelistChangeItem]
    newTerms: Sequence[TermChangeItem]
    deletedTerms: Sequence[TermChangeItem]
    updatedTerms: Sequence[TermChangeItem]

    @classmethod
    def from_repository_output(
        cls, start_datetime: datetime, end_datetime: datetime, query_output
    ) -> "CTCatalogueChanges":
        return cls(
            startDatetime=start_datetime,
            endDatetime=end_datetime,
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
