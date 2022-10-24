from typing import Collection, Optional, Sequence

from clinical_mdr_api.domain.controlled_terminology.ct_catalogue import CTCatalogueAR
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCatalogue,
)


class CTCatalogueRepository:
    def catalogue_exists(self, catalogue_name: str) -> bool:
        catalogue_node = CTCatalogue.nodes.get_or_none(name=catalogue_name)
        return bool(catalogue_node)

    def find_all(self, library_name: Optional[str]) -> Collection[CTCatalogueAR]:
        ct_catalogues: Sequence[CTCatalogue] = CTCatalogue.nodes.order_by("name").all()

        if library_name is not None:
            ct_catalogues = [
                ct_catalogue
                for ct_catalogue in ct_catalogues
                if ct_catalogue.contains_catalogue.single().name == library_name
            ]

        # projecting results to CTCatalogueAR instances
        ct_catalogues: Sequence[CTCatalogueAR] = [
            CTCatalogueAR.from_input_values(
                name=catalogue.name,
                library_name=catalogue.contains_catalogue.single().name,
            )
            for catalogue in ct_catalogues
        ]

        return ct_catalogues

    def count_all(self) -> int:
        """
        Returns the count of CT Catalogues in the database

        :return: int - count of CT Catalogues
        """
        return len(CTCatalogue.nodes)

    def close(self) -> None:
        pass
