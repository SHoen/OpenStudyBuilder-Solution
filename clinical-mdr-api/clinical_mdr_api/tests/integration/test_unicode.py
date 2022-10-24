import random
from json import dumps as _json_dumps
from typing import Any

from clinical_mdr_api.tests.utils.checks import assert_response_status_code

SYMBOLS = "®≥≤≠°©™"
GREEKS = "αβγμπφω"


def create_unicode_test_string():
    """creates a test string with some unicode characters"""
    chars = list(f"helloツ {SYMBOLS} {GREEKS}")
    random.shuffle(chars)
    test_string = "".join(chars).strip()
    test_string = f"testing {test_string}"
    return test_string


def json_dumps(obj: Any, **kwds: Any):
    """Serialize obj to JSON but do not escape non-ASCII characters"""
    kwds["ensure_ascii"] = False
    return _json_dumps(obj, **kwds)


def request_with_json_payload(app_client, method, url, payload):
    data = json_dumps(payload).encode("utf-8")
    return app_client.request(
        method, url, data=data, headers={"content-type": "application/json"}
    )


def create_unicode_brand_name_for_testing(app_client, test_string):
    response = request_with_json_payload(
        app_client, "POST", "/brands", {"name": test_string}
    )
    response.raise_for_status()
    payload = response.json()
    return payload


def create_unicode_configuration_property_for_testing(app_client, test_string):
    response = request_with_json_payload(
        app_client, "POST", "/configurations", {"studyFieldNameProperty": test_string}
    )
    response.raise_for_status()
    payload = response.json()
    return payload


def test_unicode_input(app_client):
    """Validates if we can send unicode characters as properties"""
    test_string = create_unicode_test_string()
    payload = create_unicode_brand_name_for_testing(app_client, test_string)
    uid = payload.get("uid")

    try:
        name = payload.get("name")
        assert name
        assert name == test_string, "unicode value does not match after creation"
    finally:
        if uid:
            app_client.delete(f"/brands/{uid}")


def test_unicode_retrieval(app_client):
    """Validates the retrieval of a node with unicode chars in a property"""
    test_string = create_unicode_test_string()
    payload = create_unicode_brand_name_for_testing(app_client, test_string)
    uid = payload.get("uid")
    assert uid

    try:
        response = app_client.get(f"/brands/{uid}")
        response.raise_for_status()
        payload = response.json()
        name = payload.get("name")
        assert name
        assert name == test_string, "unicode value does not match after retrieval"
    finally:
        if uid:
            app_client.delete(f"/brands/{uid}")


def test_unicode_patch(app_client):
    """Validates that a resource maintains unicode value of a property after patching"""
    test_string = create_unicode_test_string()
    property_name = "studyFieldNameProperty"
    response = request_with_json_payload(
        app_client, "POST", "/configurations", {property_name: test_string}
    )
    response.raise_for_status()
    payload = response.json()
    uid = payload.get("uid")
    assert uid

    try:
        value = payload.get(property_name)
        assert value
        assert value == test_string, "unicode name did not match after creation"

        test_string = create_unicode_test_string()
        response = request_with_json_payload(
            app_client,
            "PATCH",
            f"/configurations/{uid}",
            {property_name: test_string, "changeDescription": "testing"},
        )
        response.raise_for_status()
        payload = response.json()
        value = payload.get(property_name)
        assert value
        assert value == test_string, "unicode name did not match after patching"

        response = app_client.get(f"/configurations/{uid}")
        response.raise_for_status()
        payload = response.json()
        value = payload.get(property_name)
        assert value
        assert value == test_string, "unicode name did not match after retrieval"

    finally:
        if uid:
            app_client.delete(f"/configurations/{uid}")


def test_non_unicode_input_error_response(app_client):
    """Validates that API rejects non-UTF-8/16 and non-ASCII-escaped JSON payload on POST request"""
    test_string = f"testing {GREEKS}"
    payload = {"name": test_string}
    data = json_dumps(payload)
    data = data.encode("iso-8859-7")
    assert isinstance(data, bytes)

    response = app_client.post(
        "/brands", data=data, headers={"content-type": "application/json"}
    )
    assert_response_status_code(response, 400)


def test_non_unicode_patch_error_response(app_client):
    """Validates that API rejects on-UTF-8/16 and non-ASCII-escaped JSON payload on PATCH request"""
    test_string = create_unicode_test_string()
    property_name = "studyFieldNameProperty"
    response = request_with_json_payload(
        app_client, "POST", "/configurations", {property_name: test_string}
    )
    response.raise_for_status()
    payload = response.json()
    uid = payload.get("uid")
    assert uid

    try:
        test_string = f"testing {GREEKS}"
        payload = {"name": test_string}
        data = json_dumps(payload)
        data = data.encode("iso-8859-7")
        assert isinstance(data, bytes)

        response = app_client.patch(
            f"/configurations/{uid}",
            data=data,
            headers={"content-type": "application/json"},
        )
        assert_response_status_code(response, 400)

    finally:
        if uid:
            app_client.delete(f"/configurations/{uid}")
