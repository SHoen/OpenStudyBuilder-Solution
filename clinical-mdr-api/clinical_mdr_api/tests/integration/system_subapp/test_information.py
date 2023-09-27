from clinical_mdr_api import models
from clinical_mdr_api.tests.utils.checks import (
    JSON_CONTENT_TYPE,
    PLAIN_TEXT_CONTENT_TYPE,
    assert_response_content_type,
    assert_response_status_code,
)


def test_information(app_client):
    response = app_client.request("GET", "/system/information")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, JSON_CONTENT_TYPE)
    info = models.SystemInformation(**response.json())
    assert info.api_version
    assert info.db_version
    assert info.build_id


def test_build_id(app_client):
    response = app_client.request("GET", "/system/information/build-id")
    assert_response_status_code(response, 200)
    assert_response_content_type(response, PLAIN_TEXT_CONTENT_TYPE)
    assert len(response.text) < 20
    assert "{" not in response.text, "Response body should be plain text"
    assert "\n" not in response.text.strip(), "Response body should be a one liner"
    assert " " not in response.text.strip(), "Response body should be one word"
