from os import environ

AUTH_APP_ROOT_PATH = "/oauth"
JWT_LEEWAY_SECONDS = 10
OAUTH_ENABLED = environ.get("OAUTH_ENABLED", "").upper().strip() not in (
    "FALSE",
    "0",
    "OFF",
)
OAUTH_APP_ID = environ.get("OAUTH_APP_ID")
OAUTH_APP_ID_URI = environ.get("OAUTH_APP_ID_URI", f"api://{OAUTH_APP_ID}")
OAUTH_CLIENT_ID = environ.get("OAUTH_CLIENT_ID")
OUR_SCOPES = {
    f"{OAUTH_APP_ID_URI}/API.call": "Make calls to the API",
}
OAUTH_CLIENT_SCOPES = ["openid", "profile", "email", "offline_access"] + list(
    OUR_SCOPES.keys()
)
OIDC_METADATA_URL = environ.get("OIDC_METADATA_DOCUMENT")
OAUTH_AUTHORIZATION_URL = environ.get("OAUTH_AUTHORIZATION_URL", "UnSet")
OAUTH_TOKEN_URL = environ.get("OAUTH_TOKEN_URL", "UnSet")

SWAGGER_UI_INIT_OAUTH = (
    {
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": OAUTH_CLIENT_ID,
        "scopes": OAUTH_CLIENT_SCOPES,
        "additionalQueryStringParams": {
            "response_mode": "fragment",
        },
    }
    if OAUTH_ENABLED
    else None
)
