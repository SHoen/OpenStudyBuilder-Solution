from fastapi import Header
from starlette_context import context

from clinical_mdr_api.oauth.config import OAUTH_ENABLED

# We leave this function located in clinical_mdr_api.oauth module until tons of services import by this name
if OAUTH_ENABLED:

    def get_current_user_id() -> str:
        """Returns the current client id

        In Novo Nordisk realm, those are the initials, which are the first part of the corp. email before the @ sign.
        For applications authenticated with client secret, it is the `azp` claim from the access token
        """

        # UserInfo object is stored in context, if get_authenticated_user_info global dependency is active
        user_info = context.get("user_info")
        if user_info and user_info.username:
            return user_info.username.split("@", 1)[0]

        # IdTokenClaims is stored in context by validate_token global dependency
        claims = context.get("access_token_claims")
        if claims:

            # in case we have openid scope claimed, we should have a preferred_username claim
            username = claims.preferred_username
            if username:
                return username.split("@", 1)[0]

            # in case we did client-credentials flow (ex. import or tests) we have an
            if claims.azp:
                # authorization party: the application ID of the client using the token
                return claims.azp

        raise RuntimeError(
            "Nor user info nor access token claims were found in context, this should not happen."
        )

else:

    def get_current_user_id(
        x_test_user_id: str = Header(
            "unknown-user",  # type: ignore
            description="A value to be injected into service as user id.",
        )
    ) -> str:
        return x_test_user_id
