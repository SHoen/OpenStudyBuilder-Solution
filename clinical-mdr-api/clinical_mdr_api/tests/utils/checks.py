import httpx

JSON_CONTENT_TYPE = "application/json"
PLAIN_TEXT_CONTENT_TYPE = "text/plain"
MARKDOWN_TEXT_CONTENT_TYPE = "text/markdown"


def assert_response_status_code(response: httpx.Response, status: int | list[int]):
    """Assert request.Response status code"""
    # pylint:disable=unused-variable
    __tracebackhide__ = True

    if isinstance(status, int):
        status = (status,)

    assert response.status_code in status, (
        f"Expected HTTP status code in [{', '.join(map(str, status))}]. \n"
        f"Actual response: {response.status_code} {response.reason_phrase}: {response.text[:1024]}"
    )


def assert_response_content_type(
    response: httpx.Response, content_type: str | None = JSON_CONTENT_TYPE
):
    """Assert request.Response content type is (application/json by default)"""
    # pylint:disable=unused-variable
    __tracebackhide__ = True

    content_type_header = response.headers.get("content-type")
    if content_type_header:
        content_type_header = content_type_header.split(";", 1)[0].lower()

    assert (
        content_type_header == content_type.lower()
    ), f"Expected Content-Type header '{content_type}' got '{content_type_header}' (compared both lowercase)"
