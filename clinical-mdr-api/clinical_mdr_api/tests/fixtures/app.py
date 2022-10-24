import logging

import pytest

__all__ = ["main_app"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def main_app():
    """Fixture to load the API application

    Intention to move this to a fixture is to increase the initial startup time,
    save on loading and initializing the whole app (which does tons of DB queries) if only a unit test is requested,
    and to isolate where the startup time is spent.
    """
    log.info("main_app fixture: loading FastAPI application")
    from clinical_mdr_api.main import app

    log.info("main_app fixture: application loading completed")
    return app
