from pytest_bdd import given, parsers, scenarios, then, when

# Scenarios
scenarios("../../../../features/library/concepts/odms/descriptions.feature")


@given("ODM Descriptions exist")
def descriptions_exist():
    pass


@given("the ODM Description exists")
def the_description_exists():
    pass


@given(parsers.parse("the ODM Description is in '{status}' status"))
def description_is_in_status(status):
    pass


@then("a response with json body is received with the ODM Descriptions")
def reponse_contents(response):
    pass


# assert len(response.json()["items"]) > 0


@then("a response with json body is received with the specific ODM Description")
def reponse_contents(response):
    pass


# assert type(response.json()) is dict
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the versions of the specific ODM Description"
)
def reponse_contents(response):
    pass


# assert type(response.json()) is list
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the newly created version of the ODM Description"
)
def reponse_contents(response):
    pass
