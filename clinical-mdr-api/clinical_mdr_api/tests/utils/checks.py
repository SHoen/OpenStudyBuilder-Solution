from typing import Optional

import requests


def assert_response_status_code(response: requests.Response, status: int):
    """Assert request.Response status code"""
    # pylint:disable=unused-variable
    __tracebackhide__ = True

    assert response.status_code == status, (
        f"Expected HTTP status code {status}, got {response.status_code}, "
        f"response text: {response.text[:1024]}"
    )


def assert_response_content_type(
    response: requests.Response, content_type: Optional[str] = "application/json"
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
