import logging
import time
from typing import Any, List, Mapping, Sequence, Union

from authlib.integrations.base_client import OAuth2Mixin
from authlib.jose import JsonWebKey, Key, KeySet, jwt
from httpx import AsyncClient

log = logging.getLogger(__name__)


class JWKService(KeySet):
    """JWK store and JWT validator, relies on AsyncRemoteApp for metadata and HTTP client"""

    keys: Mapping[str, Key]
    cooldown = 120

    def __init__(
        self,
        oauth_client: OAuth2Mixin,
        audience: Union[str, List[str]],
        leeway_seconds: Union[int, float] = 15,
    ):
        self.oauth_client = oauth_client
        self.audience = audience
        self._keys_updated = 0.0
        self._http_client = AsyncClient()
        self.jwks_uri = None
        self.leeway = leeway_seconds
        self.claims_options = {}
        super().__init__({})

    async def init(self) -> None:
        """Async initializer, as we depend on async oauth_client"""

        if self._keys_updated:
            # Already initialized
            return

        # authlib.integrations.base_client.async_app.AsyncRemoteApp.load_server_metadata() caches forever
        metadata = await self.oauth_client.load_server_metadata()

        self.jwks_uri = metadata.get("jwks_uri")
        if not self.jwks_uri:
            raise RuntimeError("OpenID Provider Info does not have jwks_uri")

        iss = metadata.get("issuer")
        if iss:
            if isinstance(iss, str):
                iss = [iss]
            self.claims_options["iss"] = {"values": iss}

        aud = self.audience
        if aud:
            if isinstance(aud, str):
                aud = [aud]
            self.claims_options["aud"] = {"values": aud}

        log.info(
            "JWKService: required claims of access tokens are %s",
            repr(self.claims_options),
        )

        await self.fetch_jwk_set()

    def find_by_kid(self, kid: str) -> Key:
        """KeySet interface for jwt.decode()"""
        try:
            return self.keys[kid]
        except KeyError as exc:
            # KeySet interface
            raise ValueError(f"Unknown key id: {kid!s}") from exc

    async def fetch_jwk_set(self) -> Mapping[str, Key]:
        log.debug("Fetching JWKs: %s", self.jwks_uri)

        payload = await self._fetch_json(self.jwks_uri)
        if not isinstance(payload, dict):
            raise RuntimeError(f"JWKS data is not dict, but {type(payload)}")

        keys = payload.get("keys", {})
        keys_dict = self.update_keys(keys)

        return keys_dict

    def update_keys(
        self, keys: Sequence[Mapping[str, Union[str, Sequence[str]]]]
    ) -> Mapping[str, Key]:
        keys_dict = {}

        for key in keys:
            if not isinstance(key, dict) or "kid" not in key:
                log.debug("Invalid key: %s", repr(key))
            keys_dict[key["kid"]] = JsonWebKey.import_key(key)

        self.keys = keys_dict
        self._keys_updated = time.time()

        return keys_dict

    async def refresh_jwk_set(self) -> bool:
        """Update keys only if cooldown seconds has elapsed"""

        if self._keys_updated + self.cooldown < time.time():
            await self.fetch_jwk_set()
            return True

        return False

    async def _fetch_json(self, url: str) -> Any:
        # pylint:disable=protected-access
        resp = await self._http_client.request("GET", url)
        resp.raise_for_status()
        return resp.json()

    async def validate_jwt(self, token: Union[str, bytes]):
        """Validates JWT, fetching JWKs, checking signature and iss & aud claims (if init), then returns claims."""
        await self.init()

        try:
            claims = jwt.decode(
                token,
                key=self,
                claims_options=self.claims_options,
            )

        except ValueError as exc:
            # Re-fetch the list of keys if key-id was not found in local key-set
            if not await self.refresh_jwk_set():
                # Keys were not fetched again, withing cooldown seconds, so no need to retry signature validation
                raise exc

            claims = jwt.decode(token, key=self, claims_options=self.claims_options)

        claims.validate(leeway=self.leeway)

        return claims
