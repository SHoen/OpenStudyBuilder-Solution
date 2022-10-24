"""Custom exceptions."""

from fastapi import status
from starlette.datastructures import MutableHeaders


class MDRApiBaseException(Exception):
    status_code: int = None

    def __init__(self, msg):
        self.msg = msg
        self.headers = MutableHeaders()


class NotFoundException(MDRApiBaseException):
    status_code = status.HTTP_404_NOT_FOUND


class ForbiddenException(MDRApiBaseException):
    """Client is identified, but does not have the right to perform the requested action on the resource"""

    status_code = status.HTTP_403_FORBIDDEN


class ValidationException(MDRApiBaseException):
    """Submitted form or document did not pass validation"""

    status_code = status.HTTP_400_BAD_REQUEST


class BusinessLogicException(MDRApiBaseException):
    """The request could not be completed because it did not pass a business rule check"""

    status_code = status.HTTP_400_BAD_REQUEST


class InternalErrorException(MDRApiBaseException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ConflictErrorException(MDRApiBaseException):
    status_code = status.HTTP_409_CONFLICT
