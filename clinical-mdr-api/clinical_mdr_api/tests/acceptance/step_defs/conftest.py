"""
This module contains shared fixtures, steps, and hooks.
"""
# pylint: disable=unused-argument
from pytest_bdd import given, parsers, then, when


def pytest_bdd_step_error(
    request, feature, scenario, step, step_func, step_func_args, exception
):
    print(f"Step failed: {step}")


def pytest_bdd_before_scenario(request, feature, scenario):
    print(f"Running before scenario [{scenario.name}] of feature [{feature.name}]\n")


def pytest_bdd_after_scenario(request, feature, scenario):
    print(f"Running after scenario [{scenario.name}] of feature [{feature.name}]\n")


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    print(
        f"Running before step [{step}] in scenario [{scenario.name}] of feature [{feature.name}]\n"
    )


def pytest_bdd_after_step(request, feature, scenario, step, step_func):
    print(
        f"Running after step [{step}] in scenario [{scenario.name}] of feature [{feature.name}]\n"
    )


@given(parsers.parse("Authentication token of '{role}' is obtained"))
def authenticated_user(role):
    assert role == "Standards Developer"


@when(
    parsers.parse("a '{method}' request is sent to '{path}'"), target_fixture="response"
)
def request_without_body(method, path):
    pass


# response = test_client.request(method=method, url=path)
# return response


@when(
    parsers.parse("a '{method}' request is sent to '{path}' with\n{data}"),
    target_fixture="response",
)
def request_with_body(method, path, data):
    pass


# response = test_client.request(method=method, url=path, data=data)
# return response


@then(parsers.parse("the response has status code '{code:d}'"))
def response_code(response, code):
    pass


# assert response.status_code == code


@then(parsers.parse("a response with json body is received containing\n{data}"))
def reponse_json(response, data):
    pass


# expected = loads(data)
# actual = response.json()

# for k, v in expected.items():
#     assert actual[k] == v


@then("a response with empty body is received")
def reponse_empty(response):
    pass


# assert response.json() is None


@then("a response with json body is received with the header values")
def reponse_contents(response):
    pass


# assert len(response.json()) > 0
