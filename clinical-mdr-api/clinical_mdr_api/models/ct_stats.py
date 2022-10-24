from enum import Enum
from typing import Sequence

from pydantic import Field

from clinical_mdr_api.models.ct_codelist import CTCodelistNameAndAttributes
from clinical_mdr_api.models.utils import BaseModel


class CodelistCount(BaseModel):
    libraryName: str
    count: int


class TermCount(BaseModel):
    libraryName: str
    count: int


class CountTypeEnum(str, Enum):
    ADDED = "added"
    DELETED = "deleted"
    UPDATED = "updated"


class CountByType(BaseModel):
    type: CountTypeEnum
    count: int


class CountByTypeByYear(BaseModel):
    year: int
    counts: Sequence[CountByType]


class CTStats(BaseModel):
    catalogues: int = Field(
        ..., title="catalogues", description="Number of catalogues in the database"
    )
    packages: int = Field(
        ..., title="packages", description="Number of packages in the database"
    )
    codelistCounts: Sequence[CodelistCount] = Field(
        ..., title="codelistCounts", description="Count of codelists grouped by Library"
    )
    termCounts: Sequence[TermCount] = Field(
        ..., title="termCounts", description="Count of terms grouped by Library"
    )
    codelistChangePercentage: float = Field(
        ...,
        title="codelistChangePercentage",
        description="Mean percentage of evolution for codelists",
    )
    termChangePercentage: float = Field(
        ...,
        title="termChangePercentage",
        description="Mean percentage of evolution for terms",
    )
    codelistChangeDetails: Sequence[CountByTypeByYear] = Field(
        ...,
        title="codelistChangeDetails",
        description="Codelist changes, grouped by type and year",
    )
    termChangeDetails: Sequence[CountByTypeByYear] = Field(
        ...,
        title="termChangeDetails",
        description="Term changes, grouped by type and year",
    )
    latestAddedCodelists: Sequence[CTCodelistNameAndAttributes] = Field(
        ..., title="latestAddedCodelists", description="List of latest added codelists"
    )
