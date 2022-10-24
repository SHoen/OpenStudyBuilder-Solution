from typing import Optional, Sequence

from clinical_mdr_api.models.ct_codelist import CTCodelistNameAndAttributes
from clinical_mdr_api.models.ct_stats import (
    CountByType,
    CountByTypeByYear,
    CountTypeEnum,
    CTStats,
)
from clinical_mdr_api.repositories.ct_packages import get_package_changes_by_year
from clinical_mdr_api.services._meta_repository import MetaRepository


class CTStatsService:
    _repos: MetaRepository
    user_initials: Optional[str]

    def __init__(self, user: Optional[str] = None):
        self.user_initials = user if user is not None else "TODO user initials"
        self._repos = MetaRepository(self.user_initials)

    def _close_all_repos(self) -> None:
        self._repos.close()

    def get_stats(
        self, latest_codelists=Sequence[CTCodelistNameAndAttributes]
    ) -> CTStats:

        # Get change details
        yearly_aggregates = get_package_changes_by_year()

        codelist_change_details: Sequence[CountByTypeByYear] = []
        term_change_details: Sequence[CountByTypeByYear] = []
        for aggregate in yearly_aggregates:
            codelist_counts_by_type = [
                CountByType(
                    type=CountTypeEnum.ADDED, count=aggregate["added_codelists"]
                ),
                CountByType(
                    type=CountTypeEnum.DELETED, count=aggregate["deleted_codelists"]
                ),
                CountByType(
                    type=CountTypeEnum.UPDATED, count=aggregate["updated_codelists"]
                ),
            ]
            term_counts_by_type = [
                CountByType(type=CountTypeEnum.ADDED, count=aggregate["added_terms"]),
                CountByType(
                    type=CountTypeEnum.DELETED, count=aggregate["deleted_terms"]
                ),
                CountByType(
                    type=CountTypeEnum.UPDATED, count=aggregate["updated_terms"]
                ),
            ]
            codelist_change_details.append(
                CountByTypeByYear(
                    year=aggregate["year"], counts=codelist_counts_by_type
                )
            )
            term_change_details.append(
                CountByTypeByYear(year=aggregate["year"], counts=term_counts_by_type)
            )
        return CTStats(
            catalogues=self._repos.ct_catalogue_repository.count_all(),
            packages=self._repos.ct_package_repository.count_all(),
            codelistCounts=self._repos.ct_codelist_aggregated_repository.count_all(),
            termCounts=self._repos.ct_term_aggregated_repository.count_all(),
            codelistChangePercentage=self._repos.ct_codelist_aggregated_repository.get_change_percentage(),
            termChangePercentage=self._repos.ct_term_aggregated_repository.get_change_percentage(),
            codelistChangeDetails=codelist_change_details,
            termChangeDetails=term_change_details,
            latestAddedCodelists=latest_codelists,
        )
