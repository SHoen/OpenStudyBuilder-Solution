from pytest_bdd import given, parsers, scenarios, then

# Scenarios
scenarios("../../../../features/library/concepts/odms/item_groups.feature")


@given("ODM Item Groups exist")
def item_groups_exist():
    pass


@given("the ODM Item Group exists")
def the_item_group_exists():
    pass


@given("the ODM Items exist")
def the_item_groups_exist():
    pass


@given(parsers.parse("the ODM Item Group is in '{status}' status"))
def item_group_is_in_status(status):
    pass


@given("a Library exists")
def library_exists():
    pass


@given("an Odm Description exists")
def description_exists():
    pass


@then("a response with json body is received with the ODM Item Groups")
def reponse_contents(response):
    pass


# assert len(response.json()["items"]) > 0


@then("a response with json body is received with the specific ODM Item Group")
def reponse_contents(response):
    pass


# assert type(response.json()) is dict
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the versions of the specific ODM Item Group"
)
def reponse_contents(response):
    pass


# assert type(response.json()) is list
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the newly created version of the ODM Item Group"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form including the added ODM Items"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form without the removed ODM Items"
)
def reponse_contents(response):
    pass
