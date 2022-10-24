import logging
from typing import Iterable, List, Optional, Union

from opencensus.log import get_log_attrs
from opencensus.trace import Span, execution_context
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
from opencensus.trace.base_exporter import Exporter
from opencensus.trace.base_span import BaseSpan
from opencensus.trace.print_exporter import PrintExporter
from opencensus.trace.propagation.trace_context_http_header_format import (
    TraceContextPropagator,
)
from opencensus.trace.samplers import AlwaysOnSampler, Sampler
from opencensus.trace.span import SpanKind
from opencensus.trace.tracer import Tracer
from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette_context import context

TRACE_RESPONSE_HEADER_NAME = "traceresponse"

log = logging.getLogger(__name__)


class TracingMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Iterable[str] = None,
        exclude_hosts: Iterable[str] = None,
        sampler: Sampler = None,
        exporter: Exporter = None,
        propagator=None,
    ) -> None:
        self.app = app
        self.exclude_paths = tuple(exclude_paths or [])
        self.exclude_hosts = set(exclude_hosts or [])
        self.sampler = sampler or AlwaysOnSampler()
        self.exporter = exporter or PrintExporter()
        self.propagator = propagator or TraceContextPropagator()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            log.debug(
                "Bypassing middleware %s because of request type is {scope['type']}",
                self.__class__.__name__,
            )
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        host: str = headers.get("host")  # always lowercase, may contain :port

        # Skip tracing if hostname is in the exclusion list
        if host in self.exclude_hosts or host.split(":", 1)[0] in self.exclude_hosts:
            log.debug(
                "Bypassing middleware %s because '%s' is in exclude list: %s",
                self.__class__.__name__,
                host,
                self.exclude_hosts,
            )
            await self.app(scope, receive, send)
            return

        # Skip tracing if URL matches the exclusion list
        path = scope.get("path", "")
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                await self.app(scope, receive, send)
                return

        # noinspection PyTypeChecker
        span_context = self.propagator.from_headers(headers)

        tracer = Tracer(
            span_context=span_context,
            sampler=self.sampler,
            exporter=self.exporter,
            propagator=self.propagator,
        )

        with tracer.span(f"{scope.get('method')} {scope.get('path')}") as span:
            span.span_kind = SpanKind.SERVER

            self.add_attributes_form_request_scope(span, scope, headers=headers)

            async def send_wrapped(message: Message) -> None:

                if message["type"] == "http.response.start":
                    self.add_traceresponse_header(message)
                    self.log_access(scope, message)
                    self.add_attributes_from_response(message, tracer)

                await send(message)

            await self.app(scope, receive, send_wrapped)

    @staticmethod
    def add_attributes_form_request_scope(
        span: BaseSpan, scope: Scope, headers: Optional[Headers] = None
    ) -> None:
        """Adds attributes and properties from request scope to current tracing span.

        Known attribute names can be looked up from `opencensus.trace.attributes_helper.COMMON_ATTRIBUTES` and
        https://github.com/microsoft/ApplicationInsights-JS/blob/17ef50442f73fd02a758fbd74134933d92607ecf/legacy/JavaScript/JavaScriptSDK.Interfaces/Contracts/Generated/ContextTagKeys.ts#L208-L262
        however isn't guaranteed that they will work as expected in Application Insights
        """

        if headers is None:
            headers = Headers(scope=scope)

        span.add_attribute(
            COMMON_ATTRIBUTES["HTTP_HOST"], headers.get("host", "None").split(":", 1)[0]
        )
        user_agent = headers.get("user-agent")
        if user_agent:
            span.add_attribute(COMMON_ATTRIBUTES["HTTP_USER_AGENT"], user_agent)
            span.add_attribute("ai.user.userAgent", user_agent)

        path_qs = TracingMiddleware.get_path_qs(scope)
        query_string = scope.get("query_string")
        if query_string:
            query_string = query_string.decode("utf-8", "replace")

        span.add_attribute(COMMON_ATTRIBUTES["HTTP_METHOD"], scope.get("method"))
        span.add_attribute(COMMON_ATTRIBUTES["HTTP_PATH"], path_qs[0])
        span.add_attribute(
            COMMON_ATTRIBUTES["HTTP_URL"],
            "?".join(path_qs),
        )
        span.add_attribute(
            COMMON_ATTRIBUTES["HTTP_CLIENT_PROTOCOL"],
            f"{scope.get('type', '').upper()}/{scope.get('http_version')}",
        )

        client = scope.get("client", [])
        if len(client):
            span.add_attribute("http.client_ip", client[0])
            span.add_attribute("ai.device.ip", client[0])

    @staticmethod
    def add_attributes_from_response(
        response: Union[Response, Message], tracer: Optional[Tracer] = None
    ) -> None:
        """Adds attributes and properties to the current tracing span from the response and request state"""

        if not tracer:
            tracer = execution_context.get_opencensus_tracer()

        if isinstance(response, Response):
            headers = response.headers
            status_code = response.status_code
        else:
            headers = Headers(raw=response.get("headers", []))
            status_code = response.get("status")

        # noinspection PyTypeChecker
        tracer.add_attribute_to_current_span(
            COMMON_ATTRIBUTES["HTTP_STATUS_CODE"], int(status_code)
        )

        content_length = headers.get("content-length")
        if content_length is not None:
            tracer.add_attribute_to_current_span(
                COMMON_ATTRIBUTES["HTTP_RESPONSE_SIZE"], content_length
            )

        content_type = headers.get("content-type")
        if content_type:
            content_type = content_type.split(";", 1)[0]
            tracer.add_attribute_to_current_span("http.content_type", content_type)

    @staticmethod
    def log_access(scope: Scope, response: Union[Response, Message]) -> None:
        """Logs an access-log style line"""

        if isinstance(response, Response):
            headers = response.headers
            status = response.status_code
        else:
            headers = Headers(raw=response.get("headers", []))
            status = response.get("status")

        client = scope.get("client", "")
        if len(client) == 2:
            client = f"{client[0]}:{client[1]}"

        path = "?".join(TracingMiddleware.get_path_qs(scope))

        protocol = f"{scope.get('type', '').upper()}/{scope.get('http_version')}"

        user = "-"
        access_token_claims = context.get("access_token_claims")
        if access_token_claims:
            if access_token_claims.preferred_username:
                user = access_token_claims.preferred_username
            elif access_token_claims.azp:
                user = access_token_claims.azp

        content_type = headers.get("content-type", "-")
        content_type = content_type.split(";", 1)[0] if content_type else "-"

        content_length = headers.get("content-length", "-")

        log.info(
            '%s %s "%s %s %s" %s %s %s',
            client,
            user,
            scope.get("method"),
            path,
            protocol,
            status,
            content_type,
            content_length,
        )

    @staticmethod
    def get_path_qs(scope) -> List[str]:
        path_qs = [TracingMiddleware.get_path(scope)]

        qs = scope.get("query_string")
        if qs:
            qs = qs.decode("utf-8", "replace")
            path_qs.append(qs)

        return path_qs

    @staticmethod
    def get_path(scope):
        return "".join(filter(None, (scope.get("root_path"), scope.get("path"))))

    @staticmethod
    def add_traceresponse_header(
        response: Union[Response, Message],
        expose_header: bool = False,
        span: Optional[Span] = None,
        flags: Optional[Union[int, float]] = None,
    ) -> None:
        """Add trace id either from trace context or `traceparent` request header to `traceresponse` response header.

        `traceresponse` response header is proposed by W3C - Trace Context Level 2 - Editor's Draft 13 April 2022
        """
        if span:
            log_attrs = (span.context_tracer.trace_id, span.span_id, flags)
        else:
            log_attrs = get_log_attrs()
        value = f"00-{log_attrs[0]:s}-{log_attrs[1]:s}-{log_attrs[2]:02d}"

        if isinstance(response, Response):
            headers = response.headers
        else:
            headers = MutableHeaders(scope=response)

        headers.append(TRACE_RESPONSE_HEADER_NAME, value)
        if expose_header:
            headers.setdefault(
                "Access-Control-Expose-Headers", TRACE_RESPONSE_HEADER_NAME
            )
