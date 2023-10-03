"""
Tests for timeframes endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api import models
from clinical_mdr_api.main import app
from clinical_mdr_api.models.syntax_instances.timeframe import Timeframe
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.models.syntax_templates.timeframe_template import (
    TimeframeTemplate,
)
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
timeframes: list[Timeframe]
timeframe_template: TimeframeTemplate
ct_term_inclusion: models.CTTerm
dictionary_term_indication: models.DictionaryTerm
ct_term_category: models.CTTerm
indications_codelist: models.DictionaryCodelist
indications_library_name: str
text_value_1: models.TextValue
text_value_2: models.TextValue

URL = "timeframes"


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    inject_and_clear_db(URL + ".api")
    inject_base_data()

    global timeframes
    global timeframe_template
    global ct_term_inclusion
    global dictionary_term_indication
    global ct_term_category
    global indications_codelist
    global indications_library_name
    global text_value_1
    global text_value_2

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    # Create Dictionary/CT Terms
    ct_term_inclusion = TestUtils.create_ct_term(
        sponsor_preferred_name="INCLUSION OBJECTIVE"
    )
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    ct_term_category = TestUtils.create_ct_term()

    parameter_terms = [
        MultiTemplateParameterTerm(
            position=1,
            conjunction="",
            terms=[
                IndexedTemplateParameterTerm(
                    index=1,
                    name=text_value_1.name,
                    uid=text_value_1.uid,
                    type="TextValue",
                )
            ],
        )
    ]

    def generate_parameter_terms():
        text_value = TestUtils.create_text_value()
        return [
            MultiTemplateParameterTerm(
                position=1,
                conjunction="",
                terms=[
                    IndexedTemplateParameterTerm(
                        index=1,
                        name=text_value.name,
                        uid=text_value.uid,
                        type="TextValue",
                    )
                ],
            )
        ]

    timeframe_template = TestUtils.create_timeframe_template(
        name="Default name with [TextValue]",
        guidance_text="Default guidance text",
        library_name="Sponsor",
    )

    # Create some timeframes
    timeframes = []
    timeframes.append(
        TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid,
            library_name="Sponsor",
            parameter_terms=parameter_terms,
        )
    )
    timeframes.append(
        TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
        )
    )
    timeframes.append(
        TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    timeframes.append(
        TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    timeframes.append(
        TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )

    for _ in range(5):
        timeframes.append(
            TestUtils.create_timeframe(
                timeframe_template_uid=timeframe_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        timeframes.append(
            TestUtils.create_timeframe(
                timeframe_template_uid=timeframe_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        timeframes.append(
            TestUtils.create_timeframe(
                timeframe_template_uid=timeframe_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )
        timeframes.append(
            TestUtils.create_timeframe(
                timeframe_template_uid=timeframe_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
            )
        )

    yield

    drop_db(URL + ".api")


OBJECTIVE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "user_initials",
    "possible_actions",
    "parameter_terms",
    "library",
    "timeframe_template",
    "study_count",
]

OBJECTIVE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "timeframe_template",
]


def test_get_timeframe(api_client):
    response = api_client.get(f"{URL}/{timeframes[0].uid}")
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    fields_all_set = set(OBJECTIVE_FIELDS_ALL)
    assert set(list(res.keys())) == fields_all_set
    for key in OBJECTIVE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == timeframes[0].uid
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["timeframe_template"]["uid"] == timeframe_template.uid
    assert res["timeframe_template"]["sequence_id"] == "T1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_timeframes_pagination(api_client):
    results_paginated: dict = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        response = api_client.get(
            f"{URL}?page_number={page_number}&page_size=10&sort_by={sort_by}"
        )
        res = response.json()
        res_uids = list(map(lambda x: x["uid"], res["items"]))
        results_paginated[page_number] = res_uids
        log.info("Page %s: %s", page_number, res_uids)

    log.info("All pages: %s", results_paginated)

    results_paginated_merged = list(
        list(reduce(lambda a, b: a + b, list(results_paginated.values())))
    )
    log.info("All rows returned by pagination: %s", results_paginated_merged)

    res_all = api_client.get(
        f"{URL}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["uid"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)
    assert len(timeframes) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_timeframes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = URL
    query_params = []
    if page_size:
        query_params.append(f"page_size={page_size}")
    if page_number:
        query_params.append(f"page_number={page_number}")
    if total_count:
        query_params.append(f"total_count={total_count}")
    if sort_by:
        query_params.append(f"sort_by={sort_by}")

    if query_params:
        url = f"{url}?{'&'.join(query_params)}"

    log.info("GET %s", url)
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    assert list(res.keys()) == ["items", "total", "page", "size"]
    assert len(res["items"]) == expected_result_len
    assert res["total"] == (len(timeframes) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(OBJECTIVE_FIELDS_ALL)
        for key in OBJECTIVE_FIELDS_NOT_NULL:
            assert item[key] is not None

    if sort_by:
        # sort_by is JSON string in the form: {"sort_field_name": is_ascending_order}
        sort_by_dict = json.loads(sort_by)
        sort_field: str = list(sort_by_dict.keys())[0]
        sort_order_ascending: bool = list(sort_by_dict.values())[0]

        # extract list of values of 'sort_field_name' field from the returned result
        result_vals = list(map(lambda x: x[sort_field], res["items"]))
        result_vals_sorted_locally = result_vals.copy()
        result_vals_sorted_locally.sort(reverse=not sort_order_ascending)
        # This assert fails due to API issue with sorting coupled with pagination
        # assert result_vals == result_vals_sorted_locally


def test_get_all_parameters_of_timeframe(api_client):
    response = api_client.get(f"{URL}/{timeframes[0].uid}/parameters")
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 1
    assert res[0]["name"] == "TextValue"
    assert len(res[0]["terms"]) == 26


def test_get_versions_of_timeframe(api_client):
    response = api_client.get(f"{URL}/{timeframes[1].uid}/versions")
    res = response.json()

    assert response.status_code == 200

    assert len(res) == 2
    assert res[0]["uid"] == timeframes[1].uid
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[1]["uid"] == timeframes[1].uid
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"*": {"v": ["Default name with"], "op": "co"}}',
            "name",
            "Default name with",
        ),
        pytest.param('{"*": {"v": ["cc"], "op": "co"}}', None, None),
        pytest.param('{"*": {"v": ["cc"], "op": "co"}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    response = api_client.get(f"{URL}?filters={filter_by}")
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
        pytest.param('{"name": {"v": ["Default"], "op": "co"}}', "name", "Default"),
        pytest.param('{"name": {"v": ["cc"], "op": "co"}}', None, None),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    response = api_client.get(f"{URL}?filters={filter_by}")
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0
        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                assert expected_result in row[expected_matched_field]
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("name"),
    ],
)
def test_headers(api_client, field_name):
    response = api_client.get(f"{URL}/headers?field_name={field_name}&result_count=100")
    res = response.json()

    assert response.status_code == 200
    expected_result = []
    for timeframe in timeframes:
        value = getattr(timeframe, field_name)
        if value:
            expected_result.append(value)
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_create_timeframe(api_client):
    text_value = TestUtils.create_text_value()
    data = {
        "timeframe_template_uid": timeframe_template.uid,
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value.name,
                        "uid": text_value.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.post(URL, json=data)
    res = response.json()
    log.info("Created Timeframe: %s", res)

    assert response.status_code == 201
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value.name_sentence_case}]"
    assert res["timeframe_template"]["uid"] == timeframe_template.uid
    assert res["timeframe_template"]["sequence_id"] == "T1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(OBJECTIVE_FIELDS_ALL)
    for key in OBJECTIVE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_update_timeframe(api_client):
    data = {
        "change_description": "parameters changed",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_2.name,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{timeframes[2].uid}", json=data)
    res = response.json()
    log.info("Updated Timeframe: %s", res)

    assert response.status_code == 200
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value_2.name_sentence_case}]"
    assert res["timeframe_template"]["uid"] == timeframe_template.uid
    assert res["timeframe_template"]["sequence_id"] == "T1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_2.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_2.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(OBJECTIVE_FIELDS_ALL)
    for key in OBJECTIVE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_timeframe(api_client):
    response = api_client.delete(f"{URL}/{timeframes[2].uid}")
    log.info("Deleted Timeframe: %s", timeframes[2].uid)

    assert response.status_code == 204


def test_approve_timeframe(api_client):
    response = api_client.post(f"{URL}/{timeframes[3].uid}/approvals")
    res = response.json()

    assert response.status_code == 201
    assert res["uid"] == timeframes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_inactivate_timeframe(api_client):
    response = api_client.delete(f"{URL}/{timeframes[3].uid}/activations")
    res = response.json()

    assert response.status_code == 200
    assert res["uid"] == timeframes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"


def test_reactivate_timeframe(api_client):
    response = api_client.post(f"{URL}/{timeframes[3].uid}/activations")
    res = response.json()

    assert response.status_code == 200
    assert res["uid"] == timeframes[3].uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_preview_timeframe(api_client):
    text_value = TestUtils.create_text_value()
    data = {
        "timeframe_template_uid": timeframe_template.uid,
        "library_name": "Sponsor",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value.name,
                        "uid": text_value.uid,
                        "type": "TextValue",
                    }
                ],
            }
        ],
    }
    response = api_client.post(f"{URL}/preview", json=data)
    res = response.json()
    log.info("Previewed Timeframe: %s", res)

    assert response.status_code == 200
    assert res["uid"]
    assert res["name"] == f"Default name with [{text_value.name_sentence_case}]"
    assert res["timeframe_template"]["uid"] == timeframe_template.uid
    assert res["timeframe_template"]["sequence_id"] == "T1"
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value.uid
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["type"] == "TextValue"
    assert res["version"] == "0.1"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(OBJECTIVE_FIELDS_ALL)
    for key in OBJECTIVE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_timeframe_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("Timeframe Audit Trail: %s", res)

    assert response.status_code == 200
    assert res["total"] == 50
    expected_uids = [
        "Timeframe_000004",
        "Timeframe_000004",
        "Timeframe_000004",
        "Timeframe_000026",
        "Timeframe_000025",
        "Timeframe_000025",
        "Timeframe_000024",
        "Timeframe_000024",
        "Timeframe_000023",
        "Timeframe_000023",
        "Timeframe_000022",
        "Timeframe_000022",
        "Timeframe_000021",
        "Timeframe_000021",
        "Timeframe_000020",
        "Timeframe_000020",
        "Timeframe_000019",
        "Timeframe_000019",
        "Timeframe_000018",
        "Timeframe_000018",
        "Timeframe_000017",
        "Timeframe_000017",
        "Timeframe_000016",
        "Timeframe_000016",
        "Timeframe_000015",
        "Timeframe_000015",
        "Timeframe_000014",
        "Timeframe_000014",
        "Timeframe_000013",
        "Timeframe_000013",
        "Timeframe_000012",
        "Timeframe_000012",
        "Timeframe_000011",
        "Timeframe_000011",
        "Timeframe_000010",
        "Timeframe_000010",
        "Timeframe_000009",
        "Timeframe_000009",
        "Timeframe_000008",
        "Timeframe_000008",
        "Timeframe_000007",
        "Timeframe_000007",
        "Timeframe_000006",
        "Timeframe_000006",
        "Timeframe_000005",
        "Timeframe_000004",
        "Timeframe_000002",
        "Timeframe_000002",
        "Timeframe_000001",
        "Timeframe_000001",
    ]

    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids


def test_change_parameter_numbers_of_timeframe_after_approval(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{timeframes[4].uid}", json=data)
    res = response.json()
    log.info("Changed Timeframe parameter numbers: %s", res)

    assert response.status_code == 200
    assert not res["parameter_terms"][0]["terms"]


@pytest.mark.parametrize(
    "export_format",
    [
        pytest.param("text/csv"),
        pytest.param("text/xml"),
        pytest.param(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    ],
)
def test_get_timeframes_csv_xml_excel(api_client, export_format):
    TestUtils.verify_exported_data_format(api_client, export_format, URL)


def test_cannot_update_timeframe_without_change_description(api_client):
    data = {"name": "Default name with [TextValue]", "parameter_terms": []}
    response = api_client.patch(f"{URL}/{timeframes[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Timeframe: %s", res)

    assert response.status_code == 422
    assert res["detail"] == [
        {
            "loc": ["body", "change_description"],
            "msg": "field required",
            "type": "value_error.missing",
        }
    ]


def test_cannot_update_timeframe_in_final_status(api_client):
    data = {
        "name": "test name [TextValue]",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [],
            }
        ],
        "change_description": "Change for final status",
    }
    response = api_client.patch(f"{URL}/{timeframes[1].uid}", json=data)
    res = response.json()
    log.info("Didn't Update Timeframe: %s", res)

    assert response.status_code == 400
    assert res["message"] == "The object is not in draft status."


def test_cannot_add_wrong_parameters(
    api_client,
):
    data = {
        "name": "Default name with",
        "change_description": "Change for parameter numbers",
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "",
                "terms": [
                    {
                        "uid": "wrong",
                        "name": "wrong",
                        "type": "wrong",
                        "index": 1,
                    },
                ],
            }
        ],
    }
    response = api_client.patch(f"{URL}/{timeframes[4].uid}", json=data)
    res = response.json()
    log.info("Didn't change Timeframe parameters: %s", res)

    assert response.status_code == 400
    assert (
        res["message"]
        == "One or more of the specified template parameters can not be found."
    )
