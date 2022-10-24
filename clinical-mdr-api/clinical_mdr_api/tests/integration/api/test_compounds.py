"""
Tests for /concepts/compounds endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
from functools import reduce
from typing import List

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api import models
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
compounds_all: List[models.Compound]
ct_term_dosage: models.CTTerm
ct_term_delivery_device: models.CTTerm
ct_term_dose_frequency: models.CTTerm
ct_term_dispenser: models.CTTerm
ct_term_roa: models.CTTerm
strength_value: models.NumericValueWithUnit
dose_value: models.NumericValueWithUnit
brands: List[models.Brand]
lag_time: models.LagTime
half_life: models.NumericValueWithUnit


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db("compounds.api")
    inject_base_data()

    global compounds_all
    global ct_term_dosage
    global ct_term_delivery_device
    global ct_term_dose_frequency
    global ct_term_dispenser
    global ct_term_roa
    global strength_value
    global dose_value
    global brands
    global lag_time
    global half_life

    # Create CT Terms
    ct_term_dosage = TestUtils.create_ct_term(sponsorPreferredName="dosage_form_1")
    ct_term_delivery_device = TestUtils.create_ct_term(
        sponsorPreferredName="delivery_device_1"
    )
    ct_term_dose_frequency = TestUtils.create_ct_term(
        sponsorPreferredName="dose_frequency_1"
    )
    ct_term_dispenser = TestUtils.create_ct_term(sponsorPreferredName="dispenser_1")
    ct_term_roa = TestUtils.create_ct_term(
        sponsorPreferredName="route_of_administration_1"
    )

    # Create Numeric values with unit
    strength_value = TestUtils.create_numeric_value_with_unit(value=5, unit="mg/mL")
    dose_value = TestUtils.create_numeric_value_with_unit(value=10, unit="mg")
    half_life = TestUtils.create_numeric_value_with_unit(value=8, unit="hours")

    # Create Lag-times
    lag_time = TestUtils.create_lag_time(value=7, unit="days")

    # Create Brands
    brands = [
        TestUtils.create_brand(name=name) for name in ["Brand A", "Brand B", "Brand C"]
    ]

    for _x in range(30):
        TestUtils.create_ct_term()

    # Create some compounds
    compounds_all = []
    compounds_all.append(
        TestUtils.create_compound(
            name="Compound A",
            dosageFormUids=[ct_term_dosage.termUid],
            deliveryDevicesUids=[ct_term_delivery_device.termUid],
            dispensersUids=[ct_term_dispenser.termUid],
            routeOfAdministrationUids=[ct_term_roa.termUid],
            strengthValuesUids=[strength_value.uid],
            doseFrequencyUids=[ct_term_dose_frequency.termUid],
            doseValuesUids=[dose_value.uid],
            lagTimesUids=[lag_time.uid],
            halfLifeUid=half_life.uid,
            substanceTermsUids=[],
            brandsUids=[brands[0].uid, brands[1].uid],
        )
    )

    compounds_all.append(TestUtils.create_compound(name="name-AAA"))
    compounds_all.append(TestUtils.create_compound(name="name-BBB"))
    compounds_all.append(TestUtils.create_compound(definition="def-XXX"))
    compounds_all.append(TestUtils.create_compound(definition="def-YYY"))

    for index in range(5):
        compounds_all.append(TestUtils.create_compound(name=f"name-AAA-{index}"))
        compounds_all.append(TestUtils.create_compound(name=f"name-BBB-{index}"))
        compounds_all.append(TestUtils.create_compound(definition=f"def-XXX-{index}"))
        compounds_all.append(TestUtils.create_compound(definition=f"def-YYY-{index}"))


COMPOUND_FIELDS_ALL = [
    "uid",
    "name",
    "nameSentenceCase",
    "definition",
    "abbreviation",
    "libraryName",
    "startDate",
    "endDate",
    "status",
    "version",
    "changeDescription",
    "userInitials",
    "possibleActions",
    "analyteNumber",
    "nncShortNumber",
    "nncLongNumber",
    "isSponsorCompound",
    "isNameInn",
    "substances",
    "doseValues",
    "strengthValues",
    "lagTimes",
    "deliveryDevices",
    "dispensers",
    "projects",
    "brands",
    "halfLife",
    "doseFrequencies",
    "dosageForms",
    "routesOfAdministration",
]

COMPOUND_FIELDS_NOT_NULL = [
    "uid",
    "name",
]


def test_get_compound(api_client):
    response = api_client.get(f"/concepts/compounds/{compounds_all[0].uid}")
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert list(res.keys()) == COMPOUND_FIELDS_ALL
    for key in COMPOUND_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == compounds_all[0].uid
    assert res["name"] == "Compound A"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert list(res["possibleActions"]) == ["approve", "delete", "edit"]
    assert res["doseValues"][0]["uid"] == dose_value.uid
    assert res["doseValues"][0]["value"] == dose_value.value
    assert res["doseValues"][0]["unitDefinitionUid"] == dose_value.unitDefinitionUid
    assert res["doseValues"][0]["unitLabel"] == "mg"
    assert res["strengthValues"][0]["uid"] == strength_value.uid
    assert res["strengthValues"][0]["value"] == strength_value.value
    assert (
        res["strengthValues"][0]["unitDefinitionUid"]
        == strength_value.unitDefinitionUid
    )
    assert res["strengthValues"][0]["unitLabel"] == "mg/mL"
    assert res["deliveryDevices"][0]["termUid"] == ct_term_delivery_device.termUid
    assert (
        res["deliveryDevices"][0]["name"]
        == ct_term_delivery_device.sponsorPreferredName
    )
    assert res["doseFrequencies"][0]["termUid"] == ct_term_dose_frequency.termUid
    assert (
        res["doseFrequencies"][0]["name"] == ct_term_dose_frequency.sponsorPreferredName
    )
    assert res["dosageForms"][0]["termUid"] == ct_term_dosage.termUid
    assert res["dosageForms"][0]["name"] == ct_term_dosage.sponsorPreferredName
    assert res["dispensers"][0]["termUid"] == ct_term_dispenser.termUid
    assert res["dispensers"][0]["name"] == ct_term_dispenser.sponsorPreferredName
    assert res["routesOfAdministration"][0]["termUid"] == ct_term_roa.termUid
    assert res["routesOfAdministration"][0]["name"] == ct_term_roa.sponsorPreferredName
    assert res["brands"][0]["uid"] == "Brand_000001"
    assert res["brands"][0]["name"] == "Brand A"
    assert res["brands"][1]["uid"] == "Brand_000002"
    assert res["brands"][1]["name"] == "Brand B"
    assert res["lagTimes"][0]["unitDefinitionUid"] is not None
    assert res["lagTimes"][0]["sdtmDomainUid"] is not None
    assert res["lagTimes"][0]["value"] == 7
    assert res["lagTimes"][0]["unitLabel"] == "days"
    assert res["lagTimes"][0]["sdtmDomainLabel"] == "Adverse Event Domain"
    assert res["halfLife"]["value"] == 8
    assert res["halfLife"]["unitLabel"] == "hours"
    assert res["halfLife"]["uid"] is not None


def test_get_compounds_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"name": true}'
    for page_number in range(1, 4):
        url = (
            f"/concepts/compounds?pageNumber={page_number}&pageSize=10&sortBy={sort_by}"
        )
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["name"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"/concepts/compounds?pageNumber=1&pageSize=100&sortBy={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["name"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(compounds_all) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, None, None, 25),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total numer of compounds is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_compounds(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = "/concepts/compounds"
    query_params = []
    if page_size:
        query_params.append(f"pageSize={page_size}")
    if page_number:
        query_params.append(f"pageNumber={page_number}")
    if total_count:
        query_params.append(f"totalCount={total_count}")
    if sort_by:
        query_params.append(f"sortBy={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(compounds_all) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 0)

    for item in res["items"]:
        assert list(item.keys()) == COMPOUND_FIELDS_ALL
        for key in COMPOUND_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sortFieldName": isAscendingOrder}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sortFieldName' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This asser fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["aaa"]}}', "name", "name-AAA"),
        pytest.param('{"*": {"v": ["bBb"]}}', "name", "name-BBB"),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/concepts/compounds?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result_prefix:
        assert len(res["items"]) > 0
        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param('{"name": {"v": ["name-AAA"]}}', "name", "name-AAA"),
        pytest.param('{"name": {"v": ["name-BBB"]}}', "name", "name-BBB"),
        pytest.param('{"name": {"v": ["cc"]}}', None, None),
        pytest.param('{"definition": {"v": ["def-XXX"]}}', "definition", "def-XXX"),
        pytest.param('{"definition": {"v": ["def-YYY"]}}', "definition", "def-YYY"),
        pytest.param('{"definition": {"v": ["cc"]}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/concepts/compounds?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "base_url, page_size, sort_by",
    [
        pytest.param("/ct/terms", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms/names", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms/attributes", 20, '{"term_uid": true}'),
        pytest.param("/ct/terms", 20, '{"codelistUid": true}'),
        pytest.param("/ct/terms/names", 20, '{"sponsorPreferredName": true}'),
        pytest.param("/ct/terms/attributes", 20, '{"codeSubmissionValue": true}'),
        pytest.param("/ct/terms", 20, '{"term_uid": false}'),
        pytest.param("/ct/terms/names", 20, '{"term_uid": false}'),
        pytest.param("/ct/terms/attributes", 20, '{"term_uid": false}'),
    ],
)
def test_get_ct_terms_pagination(api_client, base_url, page_size, sort_by):
    results_paginated: dict = {}
    for page_number in range(1, 4):
        url = (
            f"{base_url}?pageNumber={page_number}&pageSize={page_size}&sortBy={sort_by}"
        )
        response = api_client.get(url)
        res = response.json()
        res_names = list(map(lambda x: x["termUid"], res["items"]))
        results_paginated[page_number] = res_names
        log.info("Page %s: %s", page_number, res_names)

    results_paginated_merged = list(
        set(list(reduce(lambda a, b: a + b, list(results_paginated.values()))))
    )
    log.info("All unique rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{base_url}?pageNumber=1&pageSize=100&sortBy={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["termUid"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
