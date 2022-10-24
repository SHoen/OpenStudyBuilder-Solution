import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "clinical_mdr_api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_config=os.environ.get("UVICORN_LOG_CONFIG"),
    )
