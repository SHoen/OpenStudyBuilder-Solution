from pytest_bdd import given, parsers, scenarios, then

# Scenarios
scenarios("../../../../features/library/concepts/odms/templates.feature")


@given("ODM Templates exist")
def template_exist():
    pass


@given("the ODM Template exists")
def the_template_exists():
    pass


@given(parsers.parse("the ODM Template is in '{status}' status"))
def template_is_in_status(status):
    pass


@given("a Library exists")
def library_exists():
    pass


@then("a response with json body is received with the ODM Templates")
def reponse_contents(response):
    pass


# assert len(response.json()["items"]) > 0


@then("a response with json body is received with the specific ODM Template")
def reponse_contents(response):
    pass


# assert type(response.json()) is dict
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the versions of the specific ODM Template"
)
def reponse_contents(response):
    pass


# assert type(response.json()) is list
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the newly created version of the ODM Template"
)
def reponse_contents(response):
    pass
