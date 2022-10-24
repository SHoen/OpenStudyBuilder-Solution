from typing import Optional

from fastapi.security import SecurityScopes
from starlette import status

from clinical_mdr_api.exceptions import MDRApiBaseException


class NotAuthenticatedException(MDRApiBaseException):
    """The client must authenticate itself, or get a fresh token"""

    status_code = status.HTTP_401_UNAUTHORIZED

    def __init__(self, msg: str, security_scopes: Optional[SecurityScopes] = None):
        super().__init__(msg)
        if security_scopes.scopes:
            self.headers[
                "WWW-Authenticate"
            ] = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            self.headers["WWW-Authenticate"] = "Bearer"
