import logging
from collections import defaultdict
from typing import Tuple

import pytest
import starlette.routing

__all__ = ["main_app_all_route_paths"]

log = logging.getLogger(__name__)

# A Mapping type that returns a placeholder for missing keys
PATH_PARAMETERS = defaultdict(
    lambda: "Missing",
    **{
        "codelistuid": "1",
        "cataloguename": "1",
        "study_number": "1",
        "termuid": "1",
        "uid": "1",
        "version": "0.1",
    },
)


@pytest.fixture(scope="session")
def main_app_all_route_paths(main_app) -> Tuple[Tuple[str, Tuple[str]], ...]:
    log.debug("Compiling a list of all route paths")

    paths = []
    for route in main_app.routes:
        if isinstance(route, starlette.routing.Route):
            path = route.path.format_map(PATH_PARAMETERS)
            paths.append((path, tuple(route.methods)))

    return tuple(paths)
