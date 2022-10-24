from typing import List, Optional

from pydantic import BaseModel, validator

AUTHORIZATION_ERROR_CODES = {
    "invalid_request",
    "unauthorized_client",
    "access_denied",
    "unsupported_response_type",
    "invalid_scope",
    "server_error",
    "temporarily_unavailable",
    # OpenID Connect Core 1.0
    "login_required",
    "interaction_required",
    # https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow#error-codes-for-authorization-endpoint-errors
    "invalid_resource",
}


class JWTTokenClaims(BaseModel):
    """ID Token claims -- as per OpenID Connect 1.0 specification"""

    # RFC-7519 defines them optional, but mandated by OpenID Connect Core 1.0 for id-tokens (except nbf and jti)
    iss: str
    sub: str
    aud: List[str]
    exp: int
    nbf: Optional[int]
    iat: int
    jti: Optional[str]

    # RFC-8693 #4.2 common for both id and access token
    scp: Optional[List[str]] = None

    @validator("aud", "scp", pre=True)
    # pylint:disable=no-self-argument
    def split_str(cls, v):
        """Splits claim space-separated-string into a list of str elements"""
        if isinstance(v, str):
            return v.split()
        return v


class IdTokenClaims(JWTTokenClaims):
    """ID Token claims -- as per OpenID Connect 1.0 specification"""

    # Optional by OpenID Connect Core 1.0
    auth_time: Optional[int]
    nonce: Optional[str]
    acr: Optional[str]
    amr: Optional[str]
    azp: Optional[str]

    # OpenID Connect Core 1.0 Standard Claims
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    middle_name: Optional[str] = None
    nickname: Optional[str] = None
    preferred_username: Optional[str] = None
    profile: Optional[str] = None
    picture: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[str] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    zoneinfo: Optional[str] = None
    locale: Optional[str] = None
    phone_number: Optional[str] = None
    phone_number_verified: Optional[str] = None
    address: Optional[str] = None
    updated_at: Optional[str] = None

    # Seen in Microsoft tokens
    username: Optional[str] = None
    idtyp: Optional[str] = None
    oid: Optional[str] = None
    tid: Optional[str] = None


class UserInfo(BaseModel):
    """Model"""

    sub: str
    name: str
    username: str
    email: str
    initials: str
