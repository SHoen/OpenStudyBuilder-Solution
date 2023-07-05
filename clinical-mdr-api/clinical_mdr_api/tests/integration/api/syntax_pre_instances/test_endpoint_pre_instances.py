"""
Tests for endpoint-templates endpoints
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
from clinical_mdr_api.models.syntax_pre_instances.endpoint_pre_instance import (
    EndpointPreInstance,
)
from clinical_mdr_api.models.syntax_templates.endpoint_template import EndpointTemplate
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
endpoint_pre_instances: List[EndpointPreInstance]
endpoint_template: EndpointTemplate
dictionary_term_indication: models.DictionaryTerm
ct_term_category: models.CTTerm
ct_term_subcategory: models.CTTerm
indications_codelist: models.DictionaryCodelist
indications_library_name: str
text_value_1: models.TextValue
text_value_2: models.TextValue

URL = "endpoint-pre-instances"


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

    global endpoint_pre_instances
    global endpoint_template
    global dictionary_term_indication
    global ct_term_category
    global ct_term_subcategory
    global indications_codelist
    global indications_library_name
    global text_value_1
    global text_value_2

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    # Create Dictionary/CT Terms
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    ct_term_category = TestUtils.create_ct_term()
    ct_term_subcategory = TestUtils.create_ct_term()

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

    endpoint_template = TestUtils.create_endpoint_template(
        name="Default name with [TextValue]",
        guidance_text="Default guidance text",
        study_uid=None,
        library_name="Sponsor",
        default_parameter_terms=parameter_terms,
        indication_uids=[dictionary_term_indication.term_uid],
        category_uids=[ct_term_category.term_uid],
        sub_category_uids=[ct_term_subcategory.term_uid],
    )

    # Create some endpoint_pre_instances
    endpoint_pre_instances = []
    endpoint_pre_instances.append(
        TestUtils.create_endpoint_pre_instance(
            template_uid=endpoint_template.uid,
            library_name="Sponsor",
            parameter_terms=parameter_terms,
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            sub_category_uids=[ct_term_subcategory.term_uid],
        )
    )
    endpoint_pre_instances.append(
        TestUtils.create_endpoint_pre_instance(
            template_uid=endpoint_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            sub_category_uids=[ct_term_subcategory.term_uid],
        )
    )
    endpoint_pre_instances.append(
        TestUtils.create_endpoint_pre_instance(
            template_uid=endpoint_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            sub_category_uids=[ct_term_subcategory.term_uid],
        )
    )
    endpoint_pre_instances.append(
        TestUtils.create_endpoint_pre_instance(
            template_uid=endpoint_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            sub_category_uids=[ct_term_subcategory.term_uid],
            approve=False,
        )
    )
    endpoint_pre_instances.append(
        TestUtils.create_endpoint_pre_instance(
            template_uid=endpoint_template.uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            indication_uids=[dictionary_term_indication.term_uid],
            category_uids=[ct_term_category.term_uid],
            sub_category_uids=[ct_term_subcategory.term_uid],
            approve=False,
        )
    )

    for _ in range(5):
        endpoint_pre_instances.append(
            TestUtils.create_endpoint_pre_instance(
                template_uid=endpoint_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
                sub_category_uids=[ct_term_subcategory.term_uid],
            )
        )
        endpoint_pre_instances.append(
            TestUtils.create_endpoint_pre_instance(
                template_uid=endpoint_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
                sub_category_uids=[ct_term_subcategory.term_uid],
            )
        )
        endpoint_pre_instances.append(
            TestUtils.create_endpoint_pre_instance(
                template_uid=endpoint_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
                sub_category_uids=[ct_term_subcategory.term_uid],
            )
        )
        endpoint_pre_instances.append(
            TestUtils.create_endpoint_pre_instance(
                template_uid=endpoint_template.uid,
                library_name="Sponsor",
                parameter_terms=generate_parameter_terms(),
                indication_uids=[dictionary_term_indication.term_uid],
                category_uids=[ct_term_category.term_uid],
                sub_category_uids=[ct_term_subcategory.term_uid],
            )
        )

    yield

    drop_db(URL + ".api")


ENDPOINT_PRE_INSTANCE_FIELDS_ALL = [
    "name",
    "name_plain",
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "status",
    "version",
    "change_description",
    "start_date",
    "end_date",
    "user_initials",
    "possible_actions",
    "parameter_terms",
    "library",
    "indications",
    "categories",
    "sub_categories",
]

ENDPOINT_PRE_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "sequence_id",
    "template_uid",
    "template_name",
    "name",
]


def test_get_endpointz(api_client):
    response = api_client.get(f"{URL}/{endpoint_pre_instances[0].uid}")
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    fields_all_set = set(ENDPOINT_PRE_INSTANCE_FIELDS_ALL)
    assert set(list(res.keys())) == fields_all_set
    for key in ENDPOINT_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None

    assert res["uid"] == endpoint_pre_instances[0].uid
    assert res["sequence_id"] == "ET1P1"
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_get_endpoint_pre_instances_pagination(api_client):
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
    assert len(endpoint_pre_instances) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 10),
        pytest.param(3, 1, True, None, 3),
        pytest.param(3, 2, True, None, 3),
        pytest.param(10, 2, True, None, 10),
        pytest.param(10, 3, True, None, 5),  # Total number of data models is 25
        pytest.param(10, 1, True, '{"name": false}', 10),
        pytest.param(10, 2, True, '{"name": true}', 10),
    ],
)
def test_get_endpoint_pre_instances(
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
    assert res["total"] == (len(endpoint_pre_instances) if total_count else 0)
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(ENDPOINT_PRE_INSTANCE_FIELDS_ALL)
        for key in ENDPOINT_PRE_INSTANCE_FIELDS_NOT_NULL:
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


def test_get_versions_of_endpoint_pre_instance(api_client):
    response = api_client.get(f"{URL}/{endpoint_pre_instances[1].uid}/versions")
    res = response.json()

    assert response.status_code == 200

    assert len(res) == 2
    assert res[0]["uid"] == endpoint_pre_instances[1].uid
    assert res[0]["sequence_id"] == "ET1P2"
    assert res[0]["template_uid"] == endpoint_template.uid
    assert res[0]["template_name"] == endpoint_template.name
    assert res[0]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res[0]["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res[0]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[0]["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res[0]["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res[0]["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res[0]["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res[0]["sub_categories"][0]["catalogue_name"]
        == ct_term_subcategory.catalogue_name
    )
    assert (
        res[0]["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    )
    assert res[0]["version"] == "1.0"
    assert res[0]["status"] == "Final"
    assert res[0]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["uid"] == endpoint_pre_instances[1].uid
    assert res[1]["sequence_id"] == "ET1P2"
    assert res[1]["template_uid"] == endpoint_template.uid
    assert res[1]["template_name"] == endpoint_template.name
    assert res[1]["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res[1]["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res[1]["indications"][0]["name"] == dictionary_term_indication.name
    assert res[1]["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res[1]["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res[1]["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res[1]["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res[1]["sub_categories"][0]["catalogue_name"]
        == ct_term_subcategory.catalogue_name
    )
    assert (
        res[1]["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    )
    assert res[1]["version"] == "0.1"
    assert res[1]["status"] == "Draft"
    assert res[1]["possible_actions"] == ["approve", "delete", "edit"]


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param('{"*": {"v": ["Default"], "op": "co"}}', "name", "Default name"),
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
    for endpoint_pre_instance in endpoint_pre_instances:
        value = getattr(endpoint_pre_instance, field_name)
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


def test_create_new_version_of_endpoint_pre_instance(api_client):
    response = api_client.post(f"{URL}/{endpoint_pre_instances[2].uid}/versions")
    res = response.json()
    log.info("Created new version of Endpoint Pre-Instance: %s", res)

    assert response.status_code == 201
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == endpoint_template.uid
    assert res["template_name"] == endpoint_template.name
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["version"] == "1.1"
    assert res["status"] == "Draft"


def test_update_endpoint_pre_instance(api_client):
    data = {
        "parameter_terms": [
            {
                "position": 1,
                "conjunction": "and",
                "terms": [
                    {
                        "index": 1,
                        "name": text_value_1.name,
                        "uid": text_value_1.uid,
                        "type": "TextValue",
                    },
                    {
                        "index": 2,
                        "name": text_value_2.name,
                        "uid": text_value_2.uid,
                        "type": "TextValue",
                    },
                ],
            }
        ],
        "change_description": "added term",
    }
    response = api_client.patch(f"{URL}/{endpoint_pre_instances[3].uid}", json=data)
    res = response.json()
    log.info("Updated Endpoint Pre-Instance: %s", res)

    assert response.status_code == 200
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == endpoint_template.uid
    assert res["template_name"] == endpoint_template.name
    assert (
        res["name"]
        == f"Default name with [{text_value_1.name_sentence_case} and {text_value_2.name_sentence_case}]"
    )
    assert (
        res["parameter_terms"][0]["terms"][0]["name"] == text_value_1.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][0]["uid"] == text_value_1.uid
    assert (
        res["parameter_terms"][0]["terms"][1]["name"] == text_value_2.name_sentence_case
    )
    assert res["parameter_terms"][0]["terms"][1]["uid"] == text_value_2.uid
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["version"] == "0.2"
    assert res["status"] == "Draft"
    assert set(list(res.keys())) == set(ENDPOINT_PRE_INSTANCE_FIELDS_ALL)
    for key in ENDPOINT_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_change_endpoint_pre_instance_indexings(api_client):
    indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )
    subcategory = TestUtils.create_ct_term()
    category = TestUtils.create_ct_term()

    data = {
        "indication_uids": [dictionary_term_indication.term_uid, indication.term_uid],
        "sub_category_uids": [
            ct_term_subcategory.term_uid,
            subcategory.term_uid,
        ],
        "category_uids": [
            ct_term_category.term_uid,
            category.term_uid,
        ],
    }
    response = api_client.patch(
        f"{URL}/{endpoint_pre_instances[0].uid}/indexings",
        json=data,
    )
    res = response.json()
    log.info("Changed Endpoint Pre-Instance indexings: %s", res)

    assert response.status_code == 200
    assert res["uid"]
    assert res["sequence_id"]
    assert res["template_uid"] == endpoint_template.uid
    assert res["template_name"] == endpoint_template.name
    assert res["name"] == f"Default name with [{text_value_1.name_sentence_case}]"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["indications"][1]["term_uid"] == indication.term_uid
    assert res["indications"][1]["dictionary_id"] == indication.dictionary_id
    assert res["indications"][1]["name"] == indication.name
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["sub_categories"][1]["term_uid"] == subcategory.term_uid
    assert res["sub_categories"][1]["catalogue_name"] == subcategory.catalogue_name
    assert res["sub_categories"][1]["codelist_uid"] == subcategory.codelist_uid
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["categories"][1]["term_uid"] == category.term_uid
    assert res["categories"][1]["catalogue_name"] == category.catalogue_name
    assert res["categories"][1]["codelist_uid"] == category.codelist_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"
    assert set(list(res.keys())) == set(ENDPOINT_PRE_INSTANCE_FIELDS_ALL)
    for key in ENDPOINT_PRE_INSTANCE_FIELDS_NOT_NULL:
        assert res[key] is not None


def test_delete_endpoint_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{endpoint_pre_instances[3].uid}")
    log.info("Deleted Endpoint Pre-Instance: %s", endpoint_pre_instances[3].uid)

    assert response.status_code == 204


def test_approve_endpoint_pre_instance(api_client):
    response = api_client.post(f"{URL}/{endpoint_pre_instances[4].uid}/approvals")
    res = response.json()

    assert response.status_code == 201
    assert res["uid"] == endpoint_pre_instances[4].uid
    assert res["sequence_id"] == "ET1P5"
    assert res["template_uid"] == endpoint_template.uid
    assert res["template_name"] == endpoint_template.name
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_inactivate_endpoint_pre_instance(api_client):
    response = api_client.delete(f"{URL}/{endpoint_pre_instances[4].uid}/activations")
    res = response.json()

    assert response.status_code == 200
    assert res["uid"] == endpoint_pre_instances[4].uid
    assert res["sequence_id"] == "ET1P5"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Retired"


def test_reactivate_endpoint_pre_instance(api_client):
    response = api_client.post(f"{URL}/{endpoint_pre_instances[4].uid}/activations")
    res = response.json()

    assert response.status_code == 200
    assert res["uid"] == endpoint_pre_instances[4].uid
    assert res["sequence_id"] == "ET1P5"
    assert res["indications"][0]["term_uid"] == dictionary_term_indication.term_uid
    assert (
        res["indications"][0]["dictionary_id"]
        == dictionary_term_indication.dictionary_id
    )
    assert res["indications"][0]["name"] == dictionary_term_indication.name
    assert res["categories"][0]["term_uid"] == ct_term_category.term_uid
    assert res["categories"][0]["catalogue_name"] == ct_term_category.catalogue_name
    assert res["categories"][0]["codelist_uid"] == ct_term_category.codelist_uid
    assert res["sub_categories"][0]["term_uid"] == ct_term_subcategory.term_uid
    assert (
        res["sub_categories"][0]["catalogue_name"] == ct_term_subcategory.catalogue_name
    )
    assert res["sub_categories"][0]["codelist_uid"] == ct_term_subcategory.codelist_uid
    assert res["version"] == "1.0"
    assert res["status"] == "Final"


def test_endpoint_pre_instance_audit_trail(api_client):
    response = api_client.get(f"{URL}/audit-trail?page_size=100&total_count=true")
    res = response.json()
    log.info("EndpointPreInstance Audit Trail: %s", res)

    assert response.status_code == 200
    assert res["total"] == 51
    expected_uids = [
        "EndpointPreInstance_000005",
        "EndpointPreInstance_000005",
        "EndpointPreInstance_000005",
        "EndpointPreInstance_000003",
        "EndpointPreInstance_000025",
        "EndpointPreInstance_000025",
        "EndpointPreInstance_000024",
        "EndpointPreInstance_000024",
        "EndpointPreInstance_000023",
        "EndpointPreInstance_000023",
        "EndpointPreInstance_000022",
        "EndpointPreInstance_000022",
        "EndpointPreInstance_000021",
        "EndpointPreInstance_000021",
        "EndpointPreInstance_000020",
        "EndpointPreInstance_000020",
        "EndpointPreInstance_000019",
        "EndpointPreInstance_000019",
        "EndpointPreInstance_000018",
        "EndpointPreInstance_000018",
        "EndpointPreInstance_000017",
        "EndpointPreInstance_000017",
        "EndpointPreInstance_000016",
        "EndpointPreInstance_000016",
        "EndpointPreInstance_000015",
        "EndpointPreInstance_000015",
        "EndpointPreInstance_000014",
        "EndpointPreInstance_000014",
        "EndpointPreInstance_000013",
        "EndpointPreInstance_000013",
        "EndpointPreInstance_000012",
        "EndpointPreInstance_000012",
        "EndpointPreInstance_000011",
        "EndpointPreInstance_000011",
        "EndpointPreInstance_000010",
        "EndpointPreInstance_000010",
        "EndpointPreInstance_000009",
        "EndpointPreInstance_000009",
        "EndpointPreInstance_000008",
        "EndpointPreInstance_000008",
        "EndpointPreInstance_000007",
        "EndpointPreInstance_000007",
        "EndpointPreInstance_000006",
        "EndpointPreInstance_000006",
        "EndpointPreInstance_000005",
        "EndpointPreInstance_000003",
        "EndpointPreInstance_000003",
        "EndpointPreInstance_000002",
        "EndpointPreInstance_000002",
        "EndpointPreInstance_000001",
        "EndpointPreInstance_000001",
    ]
    actual_uids = [item["uid"] for item in res["items"]]
    assert actual_uids == expected_uids
