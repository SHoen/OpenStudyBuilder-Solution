from pytest_bdd import given, parsers, scenarios, then, when

# Scenarios
scenarios("../../../../features/library/concepts/odms/forms.feature")


@given("ODM Forms exist")
def forms_exist():
    pass


@given("the ODM Form exists")
def the_form_exists():
    pass


@given(parsers.parse("the ODM Form is in '{status}' status"))
def form_is_in_status(status):
    pass


@given("the Activity Groups exist")
def the_activity_groups_exist():
    pass


@given("the ODM Item Groups exist")
def the_item_groups_exist():
    pass


@given("a Library exists")
def library_exists():
    pass


@given("an ODM Description exists")
def description_exists():
    pass


@then("a response with json body is received with the ODM Forms")
def reponse_contents(response):
    pass


# assert len(response.json()["items"]) > 0


@then("a response with json body is received with the specific ODM Form")
def reponse_contents(response):
    pass


# assert type(response.json()) is dict
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the versions of the specific ODM Form"
)
def reponse_contents(response):
    pass


# assert type(response.json()) is list
# assert len(response.json()) > 0


@then(
    "a response with json body is received with the newly created version of the ODM Form"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form including the added Activity Groups"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form without the removed Activity Groups"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form including the added ODM Item Groups"
)
def reponse_contents(response):
    pass


@then(
    "a response with json body is received with the ODM Form without the removed ODM Item Groups"
)
def reponse_contents(response):
    pass
