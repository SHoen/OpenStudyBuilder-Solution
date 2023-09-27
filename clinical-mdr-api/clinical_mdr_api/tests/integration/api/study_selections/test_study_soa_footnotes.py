"""
Tests for /studies/{uid}/study-soa-footnotes endpoints
"""
import json
import logging
from functools import reduce

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api import models
from clinical_mdr_api.domains.study_selections.study_soa_footnote import SoAItemType
from clinical_mdr_api.main import app
from clinical_mdr_api.models import Footnote, FootnoteTemplate, StudyVisit
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_soa_footnote import (
    ReferencedItem,
    StudySoAFootnote,
)
from clinical_mdr_api.models.syntax_templates.template_parameter_term import (
    IndexedTemplateParameterTerm,
    MultiTemplateParameterTerm,
)
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)
from clinical_mdr_api.tests.integration.utils.factory_epoch import create_study_epoch
from clinical_mdr_api.tests.integration.utils.factory_visit import (
    create_study_visit_codelists,
    generate_default_input_data_for_visit,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments


log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
second_study: Study
footnotes: list[Footnote]
footnote_templates: list[FootnoteTemplate]
soa_footnotes: list[StudySoAFootnote]
ct_term_schedule_of_activities: models.CTTerm
dictionary_term_indication: models.DictionaryTerm
indications_codelist: models.DictionaryCodelist
indications_library_name: str
activity: models.Activity
activity_group: models.ActivityGroup
activity_subgroup: models.ActivitySubGroup
text_value_1: models.TextValue
text_value_2: models.TextValue
randomized_sas: models.StudyActivitySchedule
body_mes_sas: models.StudyActivitySchedule
weight_sas: models.StudyActivitySchedule
study_epoch: StudyEpoch
first_visit: StudyVisit
sa_weight: models.StudySelectionActivity


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studysoafootnotesapi"
    inject_and_clear_db(db_name)
    global second_study
    second_study = inject_base_data()
    global study
    study = TestUtils.create_study()
    global footnotes
    global footnote_templates
    global soa_footnotes
    global ct_term_schedule_of_activities
    global dictionary_term_indication
    global indications_codelist
    global indications_library_name
    global activity
    global activity_group
    global activity_subgroup
    global text_value_1
    global text_value_2
    global randomized_sas
    global body_mes_sas
    global weight_sas
    global study_epoch
    global first_visit
    global sa_weight

    # Create Template Parameter
    TestUtils.create_template_parameter("TextValue")

    activity = TestUtils.create_activity(name="test activity", library_name="Sponsor")
    activity_group = TestUtils.create_activity_group(name="test activity group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        name="test activity subgroup", activity_groups=[activity_group.uid]
    )

    text_value_1 = TestUtils.create_text_value()
    text_value_2 = TestUtils.create_text_value()

    # Create Dictionary/CT Terms
    ct_term_schedule_of_activities = TestUtils.create_ct_term(
        sponsor_preferred_name="Schedule of Activities"
    )
    flowchart_group_codelist = TestUtils.create_ct_codelist(
        sponsor_preferred_name="Flowchart Group", extensible=True, approve=True
    )
    flowchart_group = TestUtils.create_ct_term(
        sponsor_preferred_name="Subject Information",
        codelist_uid=flowchart_group_codelist.codelist_uid,
    )
    indications_library_name = "SNOMED"
    indications_codelist = TestUtils.create_dictionary_codelist(
        name="DiseaseDisorder", library_name=indications_library_name
    )
    dictionary_term_indication = TestUtils.create_dictionary_term(
        codelist_uid=indications_codelist.codelist_uid,
        library_name=indications_library_name,
    )

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

    footnote_templates = []
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Default name with [TextValue]",
            study_uid=None,
            type_uid=ct_term_schedule_of_activities.term_uid,
            library_name="Sponsor",
            default_parameter_terms=parameter_terms,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    footnote_templates.append(
        TestUtils.create_footnote_template(
            name="Another name with [TextValue]",
            study_uid=None,
            type_uid=ct_term_schedule_of_activities.term_uid,
            library_name="Sponsor",
            default_parameter_terms=parameter_terms,
            indication_uids=[dictionary_term_indication.term_uid],
            activity_uids=[activity.uid],
            activity_group_uids=[activity_group.uid],
            activity_subgroup_uids=[activity_subgroup.uid],
        )
    )
    # Create some footnote
    footnotes = []
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_templates[0].uid,
            library_name="Sponsor",
            parameter_terms=parameter_terms,
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_templates[1].uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
        )
    )
    footnotes.append(
        TestUtils.create_footnote(
            footnote_template_uid=footnote_templates[1].uid,
            library_name="Sponsor",
            parameter_terms=generate_parameter_terms(),
            approve=False,
        )
    )
    TestUtils.create_ct_catalogue()
    # create epoch and visits
    create_study_visit_codelists(use_test_utils=True, create_unit_definitions=False)
    study_epoch = create_study_epoch("EpochSubType_0001", study_uid=study.uid)
    visits_basic_data = generate_default_input_data_for_visit().copy()
    anchor_visit = visits_basic_data.copy()
    anchor_visit.update({"is_global_anchor_visit": True})
    anchor_visit.update({"time_value": 0})
    first_visit = TestUtils.create_study_visit(
        study_uid=study.uid, study_epoch_uid=study_epoch.uid, **anchor_visit
    )
    second_visit = TestUtils.create_study_visit(
        study_uid=study.uid, study_epoch_uid=study_epoch.uid, **visits_basic_data
    )

    # create activities
    general_activity_group = TestUtils.create_activity_group(name="General")
    randomisation_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Randomisation", activity_groups=[general_activity_group.uid]
    )
    randomized_activity = TestUtils.create_activity(
        name="Randomized",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )

    # Randomized Study Activity
    sa_randomized = create_study_activity(
        study_uid=study.uid,
        activity_uid=randomized_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        flowchart_group_uid=flowchart_group.term_uid,
    )
    randomized_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_randomized.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )
    soa_footnotes = []
    randomized_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=randomized_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )
    soa_footnotes.append(randomized_sas_footnote)
    body_mes_activity = TestUtils.create_activity(
        name="Body Measurement activity",
        activity_subgroups=[randomisation_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )
    sa_body_mes = create_study_activity(
        study_uid=study.uid,
        activity_uid=body_mes_activity.uid,
        activity_subgroup_uid=randomisation_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        flowchart_group_uid=flowchart_group.term_uid,
    )
    body_mes_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_body_mes.study_activity_uid,
        study_visit_uid=first_visit.uid,
    )

    body_measurements_activity_subgroup = TestUtils.create_activity_subgroup(
        name="Body Measurements", activity_groups=[general_activity_group.uid]
    )
    weight_activity = TestUtils.create_activity(
        name="Weight",
        activity_subgroups=[body_measurements_activity_subgroup.uid],
        activity_groups=[general_activity_group.uid],
        library_name="Sponsor",
    )

    # Weight Study Activity
    sa_weight = create_study_activity(
        study_uid=study.uid,
        activity_uid=weight_activity.uid,
        activity_subgroup_uid=body_measurements_activity_subgroup.uid,
        activity_group_uid=general_activity_group.uid,
        flowchart_group_uid=flowchart_group.term_uid,
    )
    weight_sas = TestUtils.create_study_activity_schedule(
        study_uid=study.uid,
        study_activity_uid=sa_weight.study_activity_uid,
        study_visit_uid=second_visit.uid,
    )
    weight_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[1].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=weight_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )
    soa_footnotes.append(weight_sas_footnote)
    yield

    drop_db(db_name)


STUDY_FOOTNOTE_FIELDS_ALL = [
    "uid",
    "study_uid",
    "order",
    "footnote",
    "footnote_template",
    "referenced_items",
    "modified",
]

STUDY_FOOTNOTE_FIELDS_NOT_NULL = [
    "uid",
    "study_uid",
    "order",
    "referenced_items",
    "modified",
]


def test_get_study_soa_footnote(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    res = response.json()

    assert response.status_code == 200

    # Check fields included in the response
    fields_all_set = set(STUDY_FOOTNOTE_FIELDS_ALL)
    assert set(list(res.keys())) == fields_all_set
    for key in STUDY_FOOTNOTE_FIELDS_NOT_NULL:
        assert res[key] is not None
    assert res["uid"] == soa_footnotes[0].uid
    assert res["study_uid"] == study.uid
    assert res["order"] == 1
    assert len(res["referenced_items"]) == 1
    assert (
        res["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res["footnote_template"]["uid"] == footnote_templates[0].uid


def test_get_soa_footnotes_pagination(api_client):
    url = f"/studies/{study.uid}/study-soa-footnotes"
    results_paginated: dict = {}
    sort_by = '{"uid": true}'
    for page_number in range(1, 4):
        response = api_client.get(
            f"{url}?page_number={page_number}&page_size=10&sort_by={sort_by}"
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
        f"{url}?page_number=1&page_size=100&sort_by={sort_by}"
    ).json()
    results_all_in_one_page = list(map(lambda x: x["uid"], res_all["items"]))
    log.info("All rows in one page: %s", results_all_in_one_page)
    assert len(results_all_in_one_page) == len(results_paginated_merged)


@pytest.mark.parametrize(
    "page_size, page_number, total_count, sort_by, expected_result_len",
    [
        pytest.param(None, None, True, None, 2),
        pytest.param(3, 1, True, None, 2),
        pytest.param(3, 2, True, None, 0),
        pytest.param(10, 2, True, None, 0),
        pytest.param(10, 3, True, None, 0),
        pytest.param(10, 1, True, '{"uid": false}', 2),
        pytest.param(10, 2, True, '{"uid": true}', 0),
    ],
)
def test_get_study_soa_footnotes(
    api_client, page_size, page_number, total_count, sort_by, expected_result_len
):
    url = f"/studies/{study.uid}/study-soa-footnotes"
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
    assert res["total"] == (
        len([footnote for footnote in footnotes if footnote.status == "Final"])
        if total_count
        else 0
    )
    assert res["page"] == (page_number if page_number else 1)
    assert res["size"] == (page_size if page_size else 10)

    for item in res["items"]:
        assert set(list(item.keys())) == set(STUDY_FOOTNOTE_FIELDS_ALL)
        for key in STUDY_FOOTNOTE_FIELDS_NOT_NULL:
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


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result_prefix",
    [
        pytest.param(
            '{"*": {"v": ["FootnoteTemplate_000001"]}}',
            "footnote_template.uid",
            "FootnoteTemplate_000001",
        ),
        pytest.param('{"*": {"v": ["ccc"]}}', None, None),
    ],
)
def test_filtering_wildcard(
    api_client, filter_by, expected_matched_field, expected_result_prefix
):
    url = f"/studies/{study.uid}/study-soa-footnotes?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result_prefix:
        assert len(res["items"]) > 0
        nested_path = None

        # if we expect a nested property to be equal to specified value
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field that starts with the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(row, list):
                any(
                    item[expected_matched_field].startswith(expected_result_prefix)
                    for item in row
                )
            else:
                assert row[expected_matched_field].startswith(expected_result_prefix)
    else:
        assert len(res["items"]) == 0


@pytest.mark.parametrize(
    "filter_by, expected_matched_field, expected_result",
    [
        pytest.param(
            '{"footnote_template.uid": {"v": ["FootnoteTemplate_000001"]}}',
            "footnote_template.uid",
            "FootnoteTemplate_000001",
        ),
        pytest.param(
            '{"referenced_items.item_uid": {"v": ["StudyActivitySchedule_000001"]}}',
            "referenced_items.item_uid",
            "StudyActivitySchedule_000001",
        ),
    ],
)
def test_filtering_exact(
    api_client, filter_by, expected_matched_field, expected_result
):
    url = f"/studies/{study.uid}/study-soa-footnotes?filters={filter_by}"
    response = api_client.get(url)
    res = response.json()

    assert response.status_code == 200
    if expected_result:
        assert len(res["items"]) > 0

        # if we expect a nested property to be equal to specified value
        nested_path = None
        if isinstance(expected_matched_field, str) and "." in expected_matched_field:
            nested_path = expected_matched_field.split(".")
            expected_matched_field = nested_path[-1]
            nested_path = nested_path[:-1]

        # Each returned row has a field whose value is equal to the specified filter value
        for row in res["items"]:
            if nested_path:
                for prop in nested_path:
                    row = row[prop]
            if isinstance(expected_result, list):
                assert all(
                    item in row[expected_matched_field] for item in expected_result
                )
            else:
                if isinstance(row, list):
                    all(item[expected_matched_field] == expected_result for item in row)
                else:
                    assert row[expected_matched_field] == expected_result
    else:
        assert len(res["items"]) == 0


def test_footnote_reordering_when_adding_new_footnote(api_client):
    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert response.status_code == 200
    res = response.json()["items"]

    assert len(res) == 2

    assert (
        res[0]["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res[0]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[0]["order"] == 1
    assert res[0]["footnote_template"]["uid"] == footnote_templates[0].uid

    assert (
        res[1]["referenced_items"][0]["item_uid"]
        == weight_sas.study_activity_schedule_uid
    )
    assert (
        res[1]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[1]["order"] == 2
    assert res[1]["footnote_template"]["uid"] == footnote_templates[1].uid

    body_mes_sas_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=body_mes_sas.study_activity_schedule_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SCHEDULE,
            )
        ],
    )

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{body_mes_sas_footnote.uid}"
    )
    assert response.status_code == 200
    res = response.json()
    assert res["order"] == 2

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert response.status_code == 200
    res = response.json()["items"]

    assert len(res) == 3

    assert (
        res[0]["referenced_items"][0]["item_uid"]
        == randomized_sas.study_activity_schedule_uid
    )
    assert (
        res[0]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[0]["footnote_template"]["uid"] == footnote_templates[0].uid
    assert res[0]["order"] == 1

    assert (
        res[1]["referenced_items"][0]["item_uid"]
        == body_mes_sas.study_activity_schedule_uid
    )
    assert (
        res[1]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[1]["footnote_template"]["uid"] == footnote_templates[0].uid
    assert res[1]["order"] == 2

    assert (
        res[2]["referenced_items"][0]["item_uid"]
        == weight_sas.study_activity_schedule_uid
    )
    assert (
        res[2]["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
    )
    assert res[2]["footnote_template"]["uid"] == footnote_templates[1].uid
    assert res[2]["order"] == 3


def test_edit(api_client):
    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}",
        json={"footnote_template_uid": footnote_templates[1].uid},
    )
    assert response.status_code == 200

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    assert response.status_code == 200
    res = response.json()
    assert res["footnote_template"]["uid"] == footnote_templates[1].uid

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[1].uid}"
    )

    assert response.status_code == 200
    res = response.json()
    assert res["order"] == 3

    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[1].uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": first_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                }
            ]
        },
    )
    assert response.status_code == 200
    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert response.status_code == 200
    res = response.json()["items"]
    assert res[0]["referenced_items"][0]["item_uid"] == first_visit.uid
    assert res[0]["referenced_items"][0]["item_type"] == SoAItemType.STUDY_VISIT.value
    for order, soa_footnote in enumerate(res, start=1):
        assert soa_footnote["order"] == order

    TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[0].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=study_epoch.uid,
                item_type=SoAItemType.STUDY_EPOCH,
            )
        ],
    )

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert response.status_code == 200
    res = response.json()["items"]
    assert res[0]["referenced_items"][0]["item_uid"] == study_epoch.uid
    assert res[0]["referenced_items"][0]["item_type"] == SoAItemType.STUDY_EPOCH.value
    for order, soa_footnote in enumerate(res, start=1):
        assert soa_footnote["order"] == order


def test_delete(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    assert response.status_code == 200

    response = api_client.delete(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    assert response.status_code == 204

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnotes[0].uid}"
    )
    assert response.status_code == 404

    response = api_client.get(f"/studies/{study.uid}/study-soa-footnotes")
    assert response.status_code == 200
    res = response.json()["items"]

    # removed the first element make sure that the orders are reassigned
    assert res[0]["order"] == 1


def test_batch_create(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert response.status_code == 200
    res = response.json()
    amount_of_soa_footnotes = res["total"]

    text_value1 = TestUtils.create_text_value()
    text_value2 = TestUtils.create_text_value()

    batch_input = [
        {
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
        {
            "footnote_data": {
                "footnote_template_uid": footnote_templates[1].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value2.name,
                                "uid": text_value2.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    ]
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes/batch-select",
        json=batch_input,
    )
    assert response.status_code == 201

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert response.status_code == 200
    res = response.json()
    assert res["total"] == amount_of_soa_footnotes + len(batch_input)
    for idx, soa_footnote in enumerate(res["items"], start=1):
        assert soa_footnote["order"] == idx


def test_get_all_across_studies(api_client):
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes?total_count=True"
    )
    assert response.status_code == 200
    res = response.json()
    total_in_first_study = res["total"]

    api_client.post(
        f"/studies/{second_study.uid}/study-soa-footnotes/batch-select",
        json={
            "footnote_template_uid": footnote_templates[0].uid,
            "referenced_items": [],
        },
    )
    response = api_client.get(
        f"/studies/{second_study.uid}/study-soa-footnotes?total_count=True"
    )
    assert response.status_code == 200
    res = response.json()
    total_in_second_study = res["total"]

    response = api_client.get("/study-soa-footnotes?total_count=True")
    assert response.status_code == 200
    res = response.json()
    total_across_studies = res["total"]
    assert total_across_studies == total_in_second_study + total_in_first_study


def test_preview_study_soa_footnote(api_client):
    text_value1 = TestUtils.create_text_value()
    response = api_client.post(
        f"/studies/{second_study.uid}/study-soa-footnotes/preview",
        json={
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["footnote"]["parameter_terms"][0]["terms"][0]["uid"] == text_value1.uid
    assert res["footnote"]["footnote_template"]["uid"] == footnote_templates[0].uid
    assert res["footnote"]["footnote_template"]["name"] == footnote_templates[0].name
    assert res["footnote"]["footnote_template"]["name_plain"] == footnote_templates[
        0
    ].name.replace("[TextValue]", text_value1.name_sentence_case)


@pytest.mark.parametrize(
    "field_name",
    [
        pytest.param("order"),
        pytest.param("footnote.uid"),
        pytest.param("footnote_template.uid"),
    ],
)
def test_headers(api_client, field_name):
    url = f"/studies/{study.uid}/study-soa-footnotes/headers?field_name={field_name}&result_count=100"
    response = api_client.get(
        url,
    )
    res = response.json()

    assert response.status_code == 200
    expected_result = []

    nested_path = None
    if isinstance(field_name, str) and "." in field_name:
        nested_path = field_name.split(".")
        expected_matched_field = nested_path[-1]
        nested_path = nested_path[:-1]
    all_soa_footnotes = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes"
    ).json()["items"]
    for study_soa_footnote in all_soa_footnotes:
        if nested_path:
            for prop in nested_path:
                study_soa_footnote = study_soa_footnote.get(prop)
            if not study_soa_footnote:
                continue
            if isinstance(study_soa_footnote, list):
                for item in study_soa_footnote:
                    value = item.get(expected_matched_field)
                    expected_result.append(value)
            else:
                value = study_soa_footnote.get(expected_matched_field)
                expected_result.append(value)

        else:
            value = study_soa_footnote.get(field_name)
            expected_result.append(value)
    expected_result = [result for result in expected_result if result is not None]
    log.info("Expected result is %s", expected_result)
    log.info("Returned %s", res)
    if expected_result:
        assert len(res) > 0
        assert len(set(expected_result)) == len(res)
        assert all(item in res for item in expected_result)
    else:
        assert len(res) == 0


def test_audit_trail_specific_soa_footnote(api_client):
    text_value1 = TestUtils.create_text_value()
    response = api_client.post(
        f"/studies/{study.uid}/study-soa-footnotes",
        params={"create_footnote": True},
        json={
            "footnote_data": {
                "footnote_template_uid": footnote_templates[0].uid,
                "library_name": "Sponsor",
                "parameter_terms": [
                    {
                        "position": 1,
                        "conjunction": "",
                        "terms": [
                            {
                                "index": 1,
                                "name": text_value1.name,
                                "uid": text_value1.uid,
                                "type": "TextValue",
                            }
                        ],
                    }
                ],
            },
            "referenced_items": [],
        },
    )
    assert response.status_code == 201
    res = response.json()
    uid = res["uid"]
    response = api_client.patch(
        f"/studies/{study.uid}/study-soa-footnotes/{uid}",
        json={
            "referenced_items": [
                {
                    "item_uid": first_visit.uid,
                    "item_type": SoAItemType.STUDY_VISIT.value,
                }
            ]
        },
    )
    assert response.status_code == 200
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{uid}/audit-trail"
    )
    assert response.status_code == 200
    res = response.json()
    assert res[0]["changes"]["referenced_items"] is True
    assert res[0]["changes"]["order"] is True
    assert res[-1]["changes"] == {}


def test_add_footnotes_to_subgroup_and_group(api_client):
    soa_footnote = TestUtils.create_study_soa_footnote(
        study_uid=study.uid,
        footnote_template_uid=footnote_templates[1].uid,
        referenced_items=[
            ReferencedItem(
                item_uid=sa_weight.study_activity_subgroup.study_activity_subgroup_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_SUBGROUP,
            ),
            ReferencedItem(
                item_uid=sa_weight.study_activity_group.study_activity_group_uid,
                item_type=SoAItemType.STUDY_ACTIVITY_GROUP,
            ),
        ],
    )
    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes/{soa_footnote.uid}",
    )
    assert response.status_code == 200
    res = response.json()
    assert (
        res["referenced_items"][0]["item_uid"]
        == sa_weight.study_activity_subgroup.study_activity_subgroup_uid
    )
    assert (
        res["referenced_items"][0]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value
    )
    assert (
        res["referenced_items"][1]["item_uid"]
        == sa_weight.study_activity_group.study_activity_group_uid
    )
    assert (
        res["referenced_items"][1]["item_type"]
        == SoAItemType.STUDY_ACTIVITY_GROUP.value
    )

    response = api_client.get(
        f"/studies/{study.uid}/study-soa-footnotes",
    )
    assert response.status_code == 200
