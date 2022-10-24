import urllib.parse

from clinical_mdr_api import config, models
from clinical_mdr_api.repositories import system as repository


def get_system_information():
    return models.SystemInformation(
        api_version=config.settings.api_running_version,
        db_version=repository.get_neo4j_version(),
        db_name=get_database_name(),
        build_id=config.BUILD_ID,
        commit_id=config.COMMIT_ID,
    )


def get_build_id() -> str:
    return config.BUILD_ID


def get_database_name() -> str:
    """Returns database name part of neomodel config database URL"""
    return urllib.parse.urlparse(config.config.DATABASE_URL).path.split("/", 1)[-1]
