# OAuth 2 Configuration 

## Environment variables

`OAUTH_ENABLED=false`
: Authentication is disabled when the value is `false`, `0` or `off` (case-insensitive).
  Unset to enable authentication.
  When authentication is disabled, user initials can be mocked with the `X-Test-User-Id` HTTP header on each request. 

`OIDC_METADATA_DOCUMENT='https://login.microsoftonline.com/YOUR_TENANT_ID/v2.0/.well-known/openid-configuration'`
: URL of the OpenID Connect metadata document of the OAuth authority, used for fetching configuration for OAuth 2 and
  OpenID Connect related endpoints.

`OAUTH_AUTHORIZATION_URL='https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/authroize'`
: The endpoint used for authentication by the Swagger UI in the API documentation.

`OAUTH_TOKEN_URL='https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token'`
: The endpoint used for retrieving tokens, when using the Swagger UI for authentication.

`OAUTH_APP_ID='YOUR_APPLICATION_ID'`
: Application id as was registered with the Oauth authority.
  The `aud` claim of the access token must match this value.

`OAUTH_APP_ID_URI='api://YOUR_APPLICATION_ID'`
: Application id in URI format. Application-defined scopes will get prefixed like `${OAUTH_APP_ID_URI}/API.call`

`OUATH_CLIENT_ID='YOUR_CLIENT_ID'`
: The client id of the Swagger UI, registered with the OAuth authority.
  Used when authenticating from the Swagger UI


## Registering the API application with Azure Active Directory aka. Microsoft Identity Platform

**Note:** You need to register at least one scope for your API app and also claim it on authentication, otherwise
the Microsoft Identity Platform (Ms. Idp) may give you an access token for a different API (for Ms. Graph API),
and then the issued JWT token can not be validated with standard tools (and also the audience would not match).
A clear symphtom is that the value of the `aud` claim of the access token is
`00000003-0000-0000-c000-000000000000`. With a correct setup the `aud` claim of the access tokens shall
be your application id registered with Ms. Idp.

* Pick or create a tenant (note its id as tenant-id)
  
* Create new app registration (note its application id as client-id)
    * Choose supported account types as _Accounts in this organizational directory only (... only - Single Tenant)_

* define single scope for the app and make it require only admin consent

* set redirect URI for `.../docs/oauth2-redirect`
  (where `...` stays for protocol and host name where swagger UI is exposed, you can use e.g. 
  `http://localhost:8000/docs/oauth2-redirect` if setting up for local dev environment). **Note**: You must register
  redirect in _Single Page Application (SPA)_ as platform (by default azure portal proposes _Web_ platform, which will 
  not work with Swagger UI).

* register redirect URIs of UI apps
  
* in _API permissions_ page of the application registration add a permission for the app to use scope you defined
  above for API Server (and choose _Grant admin consent for mdr_test_)
  
## Grant admin consent for all tenant for both registered applications

* You can do that in _Enterprise applications > ... > Permissions_


## Put noted values into your local `.env` file

* put/replace values of `TENANT_ID`, `SERVER_ID`, `SWAGGER_CLIENT_ID` and `SCOPE` you noted from above steps as 
  environment constants in `.env` file (leave other values intact unless you know what you're doing)
  
## Requiring authorization for the API

* Set value of `OAUTH_ENABLED` constant:
  * To disable authentication: `False`, `0` or `off` (case-insensitive)
  * Unset, `True`, `1`, or anything else: requires a valid JWT token for all endpoints except the path under `/auth`
    
**Note**: When authorization is disabled, the app is going to use a pre-set default value for user initials (id) 
unless client provides a mock value with the `X-Test-User-Id` HTTP request header.
