import logging

import pytest
from fastapi.testclient import TestClient

__all__ = ["app_client"]

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def app_client(main_app):
    log.debug("app_client fixture: creating shared TestClient")
    return TestClient(main_app)
