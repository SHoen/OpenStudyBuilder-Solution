import json

from fastapi.openapi.utils import get_openapi

from clinical_mdr_api.main import app

with open("openapi.json", "w") as f:
    json.dump(
        get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        ),
        f,
    )
print("Successfully created openapi.json")
