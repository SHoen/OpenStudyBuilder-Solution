import logging
from typing import Union

import pydantic
from authlib.integrations.starlette_client import OAuth
from authlib.jose.errors import JoseError
from fastapi import Depends, Request, Security
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from opencensus.trace import execution_context
from opencensus.trace.tracer import Tracer
from pydantic import ValidationError
from starlette_context import context

from clinical_mdr_api.oauth import config
from clinical_mdr_api.oauth.exceptions import NotAuthenticatedException
from clinical_mdr_api.oauth.jwk_service import JWKService
from clinical_mdr_api.oauth.models import IdTokenClaims, UserInfo

log = logging.getLogger(__name__)

oauth_client = OAuth().register(
    "default",
    server_metadata_url=config.OIDC_METADATA_URL,
    client_id=config.OAUTH_CLIENT_ID,
    client_kwargs={"scope": config.OAUTH_CLIENT_SCOPES},
)

jwks_service = JWKService(
    oauth_client, audience=config.OAUTH_APP_ID, leeway_seconds=config.JWT_LEEWAY_SECONDS
)

oauth_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=config.OAUTH_AUTHORIZATION_URL,
    tokenUrl=config.OAUTH_TOKEN_URL,
    scopes=config.OUR_SCOPES,
)


async def validate_token(
    security_scopes: SecurityScopes,
    request: Request,
    token: str = Depends(oauth_scheme),
) -> IdTokenClaims:
    """Decodes and validates JWT token claims"""

    try:
        claims = await jwks_service.validate_jwt(token)
        request.state.id_claims = id_claims = IdTokenClaims.parse_obj(claims)

    except JoseError as exc:
        log.info("%s: %s", exc.error, exc.description)
        raise NotAuthenticatedException(
            f"Token validation error: {exc.description or exc.error}", security_scopes
        ) from exc

    except ValidationError as exc:
        log.info(str(exc))
        raise NotAuthenticatedException(
            "Model validation error", security_scopes
        ) from exc

    _update_context(id_claims)

    _validate_scopes(security_scopes, id_claims)

    log.debug("Valid token with claims: %s", id_claims)

    return id_claims


def _validate_scopes(security_scopes: SecurityScopes, id_claims: IdTokenClaims) -> None:
    """Checks if all items of required scopes are within claimed scopes"""

    if not security_scopes.scopes:
        return

    if not id_claims.scp:
        raise NotAuthenticatedException("No scopes claimed", security_scopes)

    for scope in security_scopes.scopes:
        if scope not in id_claims.scp:
            NotAuthenticatedException(
                f"Scope '{scope}' is not within claimed scopes: {id_claims.scp}",
                security_scopes,
            )


def _update_context(id_claims: IdTokenClaims) -> None:
    """Saves some attributes from access token claims to context"""

    # Attributes to current tracing span
    tracer: Tracer = execution_context.get_opencensus_tracer()
    tracer.add_attribute_to_current_span(
        "ai.user.authUserId", id_claims.preferred_username
    )
    tracer.add_attribute_to_current_span(
        "ai.user.accountId", id_claims.oid or id_claims.sub
    )
    tracer.add_attribute_to_current_span("ai.device.id", id_claims.azp)

    # Save to context
    context["access_token_claims"] = id_claims


async def get_authenticated_user_info(
    request: Request,
    token_claims: IdTokenClaims = Security(validate_token),
) -> Union[UserInfo, None]:
    """Returns UserInfo object populated from id token claims, or None on validation error"""

    data = token_claims.dict(exclude_unset=True)

    if token_claims.preferred_username:
        data.setdefault("email", token_claims.preferred_username)
        data.setdefault("initials", token_claims.preferred_username.split("@", 1)[0])
        data.setdefault("username", token_claims.preferred_username)

    try:
        request.state.user_info = user_info = UserInfo(**data)

    except pydantic.ValidationError as exc:
        log.debug(
            "Could not create UserInfo object, perhaps missing claims: %s", str(exc)
        )
        user_info = None

    context["user_info"] = user_info
    return user_info
