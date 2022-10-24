"""
Tests for /study/{uid}/study-criteria endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
# pylint: disable=too-many-statements

import copy
import json
import logging

import pytest
from deepdiff import DeepDiff
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
study_uid: str
url_prefix: str
ct_term_inclusion_criteria: models.CTTerm
ct_term_exclusion_criteria: models.CTTerm
incl_criteria_template_1: models.CriteriaTemplate
incl_criteria_template_2: models.CriteriaTemplate
excl_criteria_template_1: models.CriteriaTemplate
excl_criteria_template_2: models.CriteriaTemplate
excl_criteria_template_with_param: models.CriteriaTemplate
inclusion_type_output: dict
exclusion_type_output: dict
incl_criteria_template_1_output: dict
incl_criteria_template_2_output: dict
excl_criteria_template_1_output: dict
excl_criteria_template_2_output: dict
excl_criteria_template_with_param_output: dict
default_study_criteria_input: dict
default_study_criteria_output: dict
change_description_approve: str


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    global study_uid
    global url_prefix
    global ct_term_inclusion_criteria
    global ct_term_exclusion_criteria
    global incl_criteria_template_1
    global incl_criteria_template_2
    global excl_criteria_template_1
    global excl_criteria_template_2
    global excl_criteria_template_with_param
    global inclusion_type_output
    global exclusion_type_output
    global incl_criteria_template_1_output
    global incl_criteria_template_2_output
    global excl_criteria_template_1_output
    global excl_criteria_template_2_output
    global excl_criteria_template_with_param_output
    global default_study_criteria_input
    global default_study_criteria_output
    global change_description_approve

    """Initialize test data"""
    inject_and_clear_db("studycriteria.api")
    study = inject_base_data()
    study_uid = study.uid
    url_prefix = f"/study/{study_uid}/study-criteria"
    change_description_approve = "Approved version"

    # Create Template Parameter
    parameter_name = "TextValue"
    TestUtils.create_template_parameter(parameter_name)

    # Create CT Terms
    ct_term_inclusion_criteria = TestUtils.create_ct_term(
        sponsorPreferredName="INCLUSION CRITERIA"
    )
    ct_term_exclusion_criteria = TestUtils.create_ct_term(
        sponsorPreferredName="EXCLUSION CRITERIA"
    )

    # Create templates
    incl_criteria_template_1 = TestUtils.create_criteria_template(
        typeUid=ct_term_inclusion_criteria.termUid
    )
    incl_criteria_template_2 = TestUtils.create_criteria_template(
        typeUid=ct_term_inclusion_criteria.termUid
    )
    excl_criteria_template_1 = TestUtils.create_criteria_template(
        typeUid=ct_term_exclusion_criteria.termUid
    )
    excl_criteria_template_2 = TestUtils.create_criteria_template(
        typeUid=ct_term_exclusion_criteria.termUid
    )
    excl_criteria_template_with_param = TestUtils.create_criteria_template(
        name=f"<p>With parameter [{parameter_name}]</p>",
        typeUid=ct_term_exclusion_criteria.termUid,
    )

    # Define default expected outputs
    inclusion_type_output = {
        "termUid": ct_term_inclusion_criteria.termUid,
        "catalogueName": ct_term_inclusion_criteria.catalogueName,
        "codelistUid": ct_term_inclusion_criteria.codelistUid,
        "sponsorPreferredName": ct_term_inclusion_criteria.sponsorPreferredName,
        "sponsorPreferredNameSentenceCase": ct_term_inclusion_criteria.sponsorPreferredNameSentenceCase,
        "order": None,
        "libraryName": ct_term_inclusion_criteria.libraryName,
        "status": "Final",
        "version": "1.0",
        "changeDescription": change_description_approve,
        "possibleActions": ["inactivate", "newVersion"],
    }
    exclusion_type_output = {
        "termUid": ct_term_exclusion_criteria.termUid,
        "catalogueName": ct_term_exclusion_criteria.catalogueName,
        "codelistUid": ct_term_exclusion_criteria.codelistUid,
        "sponsorPreferredName": ct_term_exclusion_criteria.sponsorPreferredName,
        "sponsorPreferredNameSentenceCase": ct_term_exclusion_criteria.sponsorPreferredNameSentenceCase,
        "order": None,
        "libraryName": ct_term_exclusion_criteria.libraryName,
        "status": "Final",
        "version": "1.0",
        "changeDescription": change_description_approve,
        "possibleActions": ["inactivate", "newVersion"],
    }
    incl_criteria_template_1_output = {
        "name": incl_criteria_template_1.name,
        "namePlain": incl_criteria_template_1.namePlain,
        "uid": incl_criteria_template_1.uid,
        "guidanceText": incl_criteria_template_1.guidanceText,
    }
    incl_criteria_template_2_output = {
        "name": incl_criteria_template_2.name,
        "namePlain": incl_criteria_template_2.namePlain,
        "uid": incl_criteria_template_2.uid,
        "guidanceText": incl_criteria_template_2.guidanceText,
    }
    excl_criteria_template_1_output = {
        "name": excl_criteria_template_1.name,
        "namePlain": excl_criteria_template_1.namePlain,
        "uid": excl_criteria_template_1.uid,
        "guidanceText": excl_criteria_template_1.guidanceText,
    }
    excl_criteria_template_2_output = {
        "name": excl_criteria_template_2.name,
        "namePlain": excl_criteria_template_2.namePlain,
        "uid": excl_criteria_template_2.uid,
        "guidanceText": excl_criteria_template_2.guidanceText,
    }
    excl_criteria_template_with_param_output = {
        "name": excl_criteria_template_with_param.name,
        "namePlain": excl_criteria_template_with_param.namePlain,
        "uid": excl_criteria_template_with_param.uid,
        "guidanceText": excl_criteria_template_with_param.guidanceText,
    }
    default_study_criteria_input = {
        "criteriaData": {
            "criteriaTemplateUid": incl_criteria_template_1.uid,
            "libraryName": incl_criteria_template_1.library.name,
            "parameterValues": [],
        }
    }
    default_study_criteria_output = {
        "studyUid": study_uid,
        "keyCriteria": False,
        "order": 1,
        "studyCriteriaUid": "preview",
        "criteriaType": {},
        "criteria": {},
        "latestCriteria": None,
        "acceptedVersion": False,
    }


ROOT_IGNORED_FIELDS = {
    "root['startDate']",
    "root['endDate']",
    "root['userInitials']",
    "root['projectNumber']",
    "root['projectName']",
}
CRITERIA_IGNORED_FIELDS = {
    "root['criteria']['startDate']",
    "root['criteria']['endDate']",
    "root['criteria']['userInitials']",
}
CRITERIA_TYPE_IGNORED_FIELDS = {
    "root['criteriaType']['startDate']",
    "root['criteriaType']['endDate']",
    "root['criteriaType']['userInitials']",
}
CRITERIA_TEMPLATE_IGNORED_FIELDS = {
    "root['criteriaTemplate']['startDate']",
    "root['criteriaTemplate']['endDate']",
    "root['criteriaTemplate']['userInitials']",
    "root['criteriaTemplate']['type']",
    "root['criteriaTemplate']['library']",
    "root['criteriaTemplate']['defaultParameterValues']",
    "root['criteriaTemplate']['possibleActions']",
    "root['criteriaTemplate']['status']",
    "root['criteriaTemplate']['version']",
    "root['criteriaTemplate']['changeDescription']",
}


def test_crud_study_criteria(api_client):
    """Test all endpoints for study-criteria routers.
    This covers all the CRUD operations, including /batch-select and /finalize

    * Preview
    * Create
    * Batch select
    * Reorder
    * Patch key-criteria
    * Get all for all studies
    * Delete
    * Get all with filters
    * Get audit trail for all selections
    * Get audit trail for specific selection
    * Batch select template with parameter
    * Finalize with parameter value
    * Get using specific project name and number filters
    * Get headers for all studies
    * Get headers for a specific study

    """
    # Selection preview
    response = api_client.post(
        url=f"{url_prefix}/create/preview",
        json=default_study_criteria_input,
    )
    res = response.json()

    assert response.status_code == 200
    expected_criteria = default_study_criteria_output
    expected_criteria["criteriaType"] = inclusion_type_output
    expected_criteria["criteria"] = {
        "uid": "preview",
        "name": incl_criteria_template_1.name,
        "namePlain": incl_criteria_template_1.namePlain,
        "status": "Final",
        "version": "1.0",
        "changeDescription": change_description_approve,
        "possibleActions": ["inactivate"],
        "criteriaTemplate": incl_criteria_template_1_output,
        "parameterValues": [],
        "library": {
            "name": incl_criteria_template_1.library.name,
            "isEditable": incl_criteria_template_1.library.isEditable,
        },
        "studyCount": None,
    }
    full_exclude_paths = {
        *ROOT_IGNORED_FIELDS,
        *CRITERIA_IGNORED_FIELDS,
        *CRITERIA_TYPE_IGNORED_FIELDS,
    }
    assert not DeepDiff(res, expected_criteria, exclude_paths=full_exclude_paths)

    # Create selection
    response = api_client.post(
        url=f"{url_prefix}/create",
        json=default_study_criteria_input,
    )
    res = response.json()

    assert response.status_code == 201
    expected_criteria["studyCriteriaUid"] = "StudyCriteria_000001"
    expected_criteria["criteria"]["uid"] = "Criteria_000001"
    assert not DeepDiff(res, expected_criteria, exclude_paths=full_exclude_paths)

    # Test create batch
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteriaTemplateUid": incl_criteria_template_2.uid,
                "libraryName": incl_criteria_template_2.library.name,
            },
            {
                "criteriaTemplateUid": excl_criteria_template_1.uid,
                "libraryName": excl_criteria_template_1.library.name,
            },
            {
                "criteriaTemplateUid": excl_criteria_template_2.uid,
                "libraryName": excl_criteria_template_2.library.name,
            },
        ],
    )
    res = response.json()

    assert response.status_code == 201
    assert len(res) == 3

    expected_incl_criteria_1 = copy.deepcopy(expected_criteria)
    expected_incl_criteria_2 = copy.deepcopy(expected_criteria)
    expected_excl_criteria_1 = copy.deepcopy(expected_criteria)
    expected_excl_criteria_2 = copy.deepcopy(expected_criteria)

    expected_incl_criteria_2["studyCriteriaUid"] = "StudyCriteria_000002"
    expected_incl_criteria_2["order"] = 2
    expected_incl_criteria_2["criteria"]["uid"] = "Criteria_000002"
    expected_incl_criteria_2["criteria"]["name"] = incl_criteria_template_2.name
    expected_incl_criteria_2["criteria"][
        "namePlain"
    ] = incl_criteria_template_2.namePlain
    expected_incl_criteria_2["criteria"][
        "criteriaTemplate"
    ] = incl_criteria_template_2_output

    expected_excl_criteria_1["studyCriteriaUid"] = "StudyCriteria_000003"
    expected_excl_criteria_1["order"] = 1
    expected_excl_criteria_1["criteriaType"] = exclusion_type_output
    expected_excl_criteria_1["criteria"]["uid"] = "Criteria_000003"
    expected_excl_criteria_1["criteria"]["name"] = excl_criteria_template_1.name
    expected_excl_criteria_1["criteria"][
        "namePlain"
    ] = excl_criteria_template_1.namePlain
    expected_excl_criteria_1["criteria"][
        "criteriaTemplate"
    ] = excl_criteria_template_1_output

    expected_excl_criteria_2["studyCriteriaUid"] = "StudyCriteria_000004"
    expected_excl_criteria_2["order"] = 2
    expected_excl_criteria_2["criteriaType"] = exclusion_type_output
    expected_excl_criteria_2["criteria"]["uid"] = "Criteria_000004"
    expected_excl_criteria_2["criteria"]["name"] = excl_criteria_template_2.name
    expected_excl_criteria_2["criteria"][
        "namePlain"
    ] = excl_criteria_template_2.namePlain
    expected_excl_criteria_2["criteria"][
        "criteriaTemplate"
    ] = excl_criteria_template_2_output

    assert not DeepDiff(
        res[0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res[1], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res[2], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # Test reorder
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000001/order",
        json={"new_order": 2},
    )
    res = response.json()

    assert response.status_code == 200
    expected_incl_criteria_1["order"] = 2
    expected_incl_criteria_2["order"] = 1
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test patch study selection keyCriteria
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000001/key-criteria",
        json={"key_criteria": True},
    )
    res = response.json()

    assert response.status_code == 200
    expected_incl_criteria_1["keyCriteria"] = True
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test get specific - with right order
    response = api_client.get(url=f"{url_prefix}/StudyCriteria_000001")
    res = response.json()

    assert response.status_code == 200
    assert not DeepDiff(res, expected_incl_criteria_1, exclude_paths=full_exclude_paths)

    # Test get all - with right orders
    response = api_client.get(url=url_prefix)
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 4
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][1], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][2], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][3], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # Test get all for all studies
    response = api_client.get(url="/study/study-criteria")
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 4
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_2, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][1], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][2], expected_excl_criteria_1, exclude_paths=full_exclude_paths
    )
    assert not DeepDiff(
        res["items"][3], expected_excl_criteria_2, exclude_paths=full_exclude_paths
    )

    # Test delete
    response = api_client.delete(url=f"{url_prefix}/StudyCriteria_000002")
    assert response.status_code == 204

    # Re-test get all - Make sure that the order has been updated after deletion
    # This test also adds a filter on criteria type
    filter_by = {"criteriaType.termUid": {"v": [ct_term_inclusion_criteria.termUid]}}
    response = api_client.get(url=f"{url_prefix}?filters={json.dumps(filter_by)}")
    res = response.json()

    assert response.status_code == 200
    assert len(res["items"]) == 1
    expected_incl_criteria_1["order"] = 1
    assert not DeepDiff(
        res["items"][0], expected_incl_criteria_1, exclude_paths=full_exclude_paths
    )

    # Test history for all selections
    response = api_client.get(url=f"{url_prefix}/audit-trail")
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 9
    incl_criteria_1_entries = [
        i for i in res if i["studyCriteriaUid"] == "StudyCriteria_000001"
    ]
    incl_criteria_1_orders = [i["order"] for i in incl_criteria_1_entries]
    incl_criteria_1_change_types = [i["changeType"] for i in incl_criteria_1_entries]
    incl_criteria_2_entries = [
        i for i in res if i["studyCriteriaUid"] == "StudyCriteria_000002"
    ]
    incl_criteria_2_orders = [i["order"] for i in incl_criteria_2_entries]
    incl_criteria_2_change_types = [i["changeType"] for i in incl_criteria_2_entries]
    assert incl_criteria_1_orders == [1, 2, 2, 1]
    assert incl_criteria_1_change_types == ["Edit", "Edit", "Edit", "Create"]
    assert incl_criteria_2_orders == [1, 1, 2]
    assert incl_criteria_2_change_types == ["Delete", "Edit", "Create"]

    # Test history for specific selection
    response = api_client.get(url=f"{url_prefix}/StudyCriteria_000002/audit-trail")
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 3
    change_types = [i["changeType"] for i in res]
    assert change_types == ["Delete", "Edit", "Create"]

    # Test batch select for template with parameter
    # This study criteria will stay as a template instead of an instance
    # It then needs to be finalized
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteriaTemplateUid": excl_criteria_template_with_param.uid,
                "libraryName": excl_criteria_template_with_param.library.name,
            },
        ],
    )
    res = response.json()

    assert response.status_code == 201
    expected_excl_criteria_with_param = copy.deepcopy(expected_excl_criteria_2)
    expected_excl_criteria_with_param["studyCriteriaUid"] = "StudyCriteria_000005"
    expected_excl_criteria_with_param["order"] = 3
    del expected_excl_criteria_with_param["criteria"]
    del expected_excl_criteria_with_param["latestCriteria"]
    expected_excl_criteria_with_param["latestTemplate"] = None
    # Load the object with values directly from the Template object
    # It needs to be flattened into a dict beforehand though
    expected_excl_criteria_with_param["criteriaTemplate"] = vars(
        excl_criteria_template_with_param
    )
    expected_excl_criteria_with_param["criteriaTemplate"]["parameters"] = [
        {"name": "TextValue"}
    ]
    assert not DeepDiff(
        res[0],
        expected_excl_criteria_with_param,
        exclude_paths={*full_exclude_paths, *CRITERIA_TEMPLATE_IGNORED_FIELDS},
    )

    # Test finalise selection with parameter
    text_value = TestUtils.create_text_value()
    target_parameter_value = {
        "index": 1,
        "name": text_value.name,
        "type": "TextValue",
        "uid": text_value.uid,
    }
    response = api_client.patch(
        url=f"{url_prefix}/StudyCriteria_000005/finalize",
        json={
            "criteriaTemplateUid": excl_criteria_template_with_param.uid,
            "libraryName": excl_criteria_template_with_param.library.name,
            "parameterValues": [
                {
                    "conjunction": "",
                    "position": 1,
                    "value": None,
                    "values": [target_parameter_value],
                }
            ],
        },
    )
    res = response.json()

    assert response.status_code == 200
    expected_criteria_with_param_name = excl_criteria_template_with_param.name.replace(
        "TextValue", text_value.nameSentenceCase
    )
    expected_criteria_with_param_name_plain = (
        expected_criteria_with_param_name.replace("[", "")
        .replace("]", "")
        .replace("<p>", "")
        .replace("</p>", "")
    )
    assert res["studyCriteriaUid"] == "StudyCriteria_000005"
    assert res["order"] == 3
    assert res["criteria"]["uid"] == "Criteria_000005"
    assert res["criteria"]["name"] == expected_criteria_with_param_name
    assert res["criteria"]["namePlain"] == expected_criteria_with_param_name_plain

    # Test get with project name and number filter
    project_name = res["projectName"]
    project_number = res["projectNumber"]
    response = api_client.get(
        url=f"{url_prefix}?projectName={project_name}&projectNumber={project_number}"
    )
    res = response.json()
    assert len(res["items"]) == 4

    # Test /headers endpoint - for all studies
    field_name = "criteria.name"
    search_string = "parameter"
    filter_by = {"criteriaType.termUid": {"v": [ct_term_exclusion_criteria.termUid]}}
    response = api_client.get(
        url=f"/study/study-criteria/headers?filters={json.dumps(filter_by)}&fieldName={field_name}&searchString={search_string}"
    )
    res = response.json()

    assert response.status_code == 200
    assert len(res) == 1

    # Test /headers endpoint - for a specific study
    response = api_client.get(
        url=f"{url_prefix}/headers?filters={json.dumps(filter_by)}&fieldName={field_name}&searchString={search_string}"
    )
    res = response.json()

    assert response.status_code == 200
    assert res == [expected_criteria_with_param_name]


def test_errors(api_client):
    """Test that we get the expected errors when doing something wrong

    * Test that we get a 404 when we reference a non existent template in these endpoints :
    ** Preview
    ** Create
    ** Batch select

    """
    # Test selecting with a non-existent template uid
    dummy_template_uid = "dummy_template_uid"
    expected_response_code = 404
    expected_response_text = (
        f"Criteria template with uid {dummy_template_uid} does not exist"
    )

    # Preview
    dummy_study_criteria_input = copy.deepcopy(default_study_criteria_input)
    dummy_study_criteria_input["criteriaData"][
        "criteriaTemplateUid"
    ] = dummy_template_uid
    response = api_client.post(
        url=f"{url_prefix}/create/preview",
        json=dummy_study_criteria_input,
    )
    res = response.json()

    assert response.status_code == expected_response_code
    assert res["message"] == expected_response_text

    # Creation
    response = api_client.post(
        url=f"{url_prefix}/create",
        json=dummy_study_criteria_input,
    )
    res = response.json()

    assert response.status_code == expected_response_code
    assert res["message"] == expected_response_text

    # Batch selection
    response = api_client.post(
        url=f"{url_prefix}/batch-select",
        json=[
            {
                "criteriaTemplateUid": dummy_template_uid,
                "libraryName": incl_criteria_template_1.library.name,
            },
        ],
    )
    res = response.json()

    assert response.status_code == expected_response_code
    assert res["message"] == expected_response_text
