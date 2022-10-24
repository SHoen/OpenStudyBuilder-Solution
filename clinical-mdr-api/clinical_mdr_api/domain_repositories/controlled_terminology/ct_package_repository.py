from datetime import date
from typing import Collection, Optional, Sequence

from neomodel import db

from clinical_mdr_api.domain.controlled_terminology.ct_package import CTPackageAR
from clinical_mdr_api.domain_repositories.models.controlled_terminology import CTPackage


class CTPackageRepository:
    def package_exists(self, package_name: str) -> bool:
        package_node = CTPackage.nodes.get_or_none(name=package_name)
        return bool(package_node)

    def find_all(self, catalogue_name: Optional[str]) -> Collection[CTPackageAR]:
        if catalogue_name is not None:
            where_clause = "WHERE catalogue.name=$catalogue_name"
        else:
            where_clause = ""
        query = f"""
            MATCH (catalogue:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            {where_clause}
            RETURN package
            ORDER BY catalogue.name, package.effective_date
            """

        result, _ = db.cypher_query(
            query, {"catalogue_name": catalogue_name}, resolve_objects=True
        )

        if len(result) == 0:
            return []
        # projecting results to CTPackageAR instances
        ct_packages: Sequence[CTPackageAR] = [
            CTPackageAR.from_repository_values(
                uid=ct_package[0].uid,
                catalogue_name=ct_package[0].contains_package.single().name,
                name=ct_package[0].name,
                label=ct_package[0].label,
                description=ct_package[0].description,
                href=ct_package[0].href,
                registration_status=ct_package[0].registration_status,
                source=ct_package[0].source,
                import_date=ct_package[0].import_date,
                effective_date=ct_package[0].effective_date,
                user_initials=ct_package[0].user_initials,
            )
            for ct_package in result
        ]
        return ct_packages

    def count_all(self) -> int:
        """
        Returns the count of CT Packages in the database

        :return: int - count of CT Packages
        """
        return len(CTPackage.nodes)

    def find_by_catalogue_and_date(
        self, catalogue_name: str, package_date: date
    ) -> Optional[CTPackageAR]:
        query = """
            MATCH (:CTCatalogue {name: $catalogue_name})-[:CONTAINS_PACKAGE]->
            (package:CTPackage {effective_date:date($date)})
            RETURN package
            """
        result, _ = db.cypher_query(
            query,
            {"catalogue_name": catalogue_name, "date": package_date},
            resolve_objects=True,
        )
        if len(result) > 0 and len(result[0]) > 0:
            ct_package = result[0][0]
            return CTPackageAR.from_repository_values(
                uid=ct_package.uid,
                catalogue_name=ct_package.contains_package.single().name,
                name=ct_package.name,
                label=ct_package.label,
                description=ct_package.description,
                href=ct_package.href,
                registration_status=ct_package.registration_status,
                source=ct_package.source,
                import_date=ct_package.import_date,
                effective_date=ct_package.effective_date,
                user_initials=ct_package.user_initials,
            )
        return None

    def close(self) -> None:
        pass
