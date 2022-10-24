from datetime import datetime

from fastapi import Request
from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class ErrorResponse(BaseModel):
    type: str = Field(..., description="Exception class.")
    message: str = Field(..., description="More information about the error.")
    time: datetime = Field(
        ..., description="The point in time when the error occurred."
    )
    path: str = Field(..., description="The url/path of the request.")
    method: str = Field(..., description="The HTTP method of the request.")

    def __init__(self, request: Request, exception: Exception, **data) -> None:
        super().__init__(
            type=type(exception).__name__,
            message=str(getattr(exception, "msg", None) or exception),
            time=datetime.now(),
            path=str(request.url),
            method=request.method,
            **data
        )


class BatchErrorResponse(BaseModel):
    message: str = Field(None, description="More information about the error.")
    time: datetime = Field(
        ..., description="The point in time when the error occurred."
    )

    def __init__(self, **data) -> None:
        if "time" not in data:
            data["time"] = datetime.now()
        super().__init__(**data)
