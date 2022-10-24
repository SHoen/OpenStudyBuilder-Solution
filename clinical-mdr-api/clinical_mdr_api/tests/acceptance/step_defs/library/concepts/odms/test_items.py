from pytest_bdd import given, parsers, scenarios, then, when

# Scenarios
scenarios("../../../../features/library/concepts/odms/items.feature")


@given("ODM Items exist")
def item_exist():
    pass


@given("the ODM Item exists")
def the_item_exists():
    pass


@given(parsers.parse("the ODM Item is in '{status}' status"))
def item_is_in_status(status):
    pass


@given("the Activities exist")
def the_activities_exist():
    pass


@given("a Library exists")
def library_exists():
    pass


@given("an ODM Description exists")
def description_exists():
    pass


@then("a response with json body is received with the ODM Items")
def reponse_contents(response):
    pass


# assert len(response.json()["items"]) > 0


@then("a response with json body is received with the specific ODM Item")
def reponse_contents(response):
    pass


# assert type(response.json()) is dict
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the versions of the specific ODM Item"
)
def reponse_contents(response):
    pass


# assert type(response.json()) is list
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the newly created version of the ODM Item"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Item including the added Activities"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Item without the removed Activities"
)
def reponse_contents(response):
    pass
