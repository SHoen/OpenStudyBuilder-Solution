import logging

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from opencensus.trace import execution_context
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from clinical_mdr_api.models.error import ErrorResponse

log = logging.getLogger(__name__)


class ExceptionTracebackMiddleware:
    """Middleware for unhandled exceptions: sets tracing attributes, logs exception traceback, returns error response"""

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def _send(message: Message) -> None:
            nonlocal response_started, send

            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, _send)

        # pylint:disable=broad-except
        except Exception as exc:
            # add tracing attributes
            tracer = execution_context.get_opencensus_tracer()
            tracer.add_attribute_to_current_span(
                COMMON_ATTRIBUTES["ERROR_NAME"], exc.__class__.__name__
            )
            tracer.add_attribute_to_current_span(
                COMMON_ATTRIBUTES["ERROR_MESSAGE"], str(exc)
            )

            # log traceback
            log.exception(exc)

            request = Request(scope)
            response = self.error_response(request, exc)

            if not response_started:
                await response(scope, receive, send)

    @staticmethod
    def error_response(request: Request, exception: Exception) -> Response:
        """Returns a 500 error response with JSON payload from Exception"""

        # TODO we should not return the exception cause in production
        # rather consider doing the following instead:
        # if production:
        # user_exception = Exception("No detailed information available.")
        # else:
        user_exception = exception

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=jsonable_encoder(ErrorResponse(request, user_exception)),
        )

        return response
