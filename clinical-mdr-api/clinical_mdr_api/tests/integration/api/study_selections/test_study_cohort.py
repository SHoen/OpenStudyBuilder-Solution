"""
Tests for /studies/{uid}/study-cohorts endpoints
"""

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import logging

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.main import app
from clinical_mdr_api.models.study_selections.study import Study
from clinical_mdr_api.models.study_selections.study_selection import StudySelectionArm
from clinical_mdr_api.tests.integration.utils.api import (
    drop_db,
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study: Study
study_arm: StudySelectionArm


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    """Initialize test data"""
    db_name = "studycohortapi"
    inject_and_clear_db(db_name)
    inject_base_data()
    global study
    study = TestUtils.create_study()
    global study_arm
    study_arm = TestUtils.create_study_arm(
        study_uid=study.uid,
        name="test_arm",
        short_name="test_arm",
    )

    yield

    drop_db(db_name)


def test_cohort_modify_actions_on_locked_study(api_client):
    response = api_client.post(
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_1",
            "short_name": "Cohort_Short_Name_1",
            "code": "Cohort_code_1",
        },
    )
    res = response.json()
    assert response.status_code == 201

    # get all cohorts
    response = api_client.get(
        f"/studies/{study.uid}/study-cohort/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    old_res = res
    cohort_uid = res[0]["cohort_uid"]

    # update study title to be able to lock it
    response = api_client.patch(
        f"/studies/{study.uid}",
        json={"current_metadata": {"study_description": {"study_title": "new title"}}},
    )
    assert response.status_code == 200

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert response.status_code == 201

    response = api_client.post(
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_2",
            "short_name": "Cohort_Short_Name_2",
            "code": "Cohort_code_2",
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."
    # edit cohort
    response = api_client.patch(
        f"/studies/{study.uid}/study-cohorts/{cohort_uid}",
        json={
            "name": "New_cohort_Name_1",
        },
    )
    res = response.json()
    assert response.status_code == 400
    assert res["message"] == f"Study with specified uid '{study.uid}' is locked."

    # get all history when was locked
    response = api_client.get(
        f"/studies/{study.uid}/study-cohort/audit-trail/",
    )
    res = response.json()
    assert response.status_code == 200
    assert old_res == res

    # test cannot delete
    response = api_client.delete(f"/studies/{study.uid}/study-cohorts/{cohort_uid}")
    assert response.status_code == 400
    assert (
        response.json()["message"]
        == f"Study with specified uid '{study.uid}' is locked."
    )


def test_study_cohort_study_value_version(api_client):
    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    response = api_client.post(
        f"/studies/{study.uid}/study-branch-arms",
        json={
            "name": "BranchArm_Name_1",
            "short_name": "BranchArm_Short_Name_1",
            "code": "BranchArm_code_1",
            "description": "desc...",
            "colour_code": "desc...",
            "randomization_group": "Randomization_Group_1",
            "number_of_subjects": 1,
            "arm_uid": study_arm.arm_uid,
        },
    )
    res = response.json()
    assert response.status_code == 201
    branch_arm = res

    response = api_client.post(
        f"/studies/{study.uid}/study-cohorts",
        json={
            "name": "Cohort_Name_2",
            "short_name": "Cohort_Short_Name_2",
            "code": "Cohort_code_2",
            "arm_uids": [
                study_arm.arm_uid,
            ],
            "branch_arm_uids": [
                branch_arm["branch_arm_uid"],
            ],
        },
    )
    res = response.json()
    assert response.status_code == 201
    cohort = res

    before_unlock_arms = api_client.get(f"/studies/{study.uid}/study-arms").json()
    before_unlock_branch_arms = api_client.get(
        f"/studies/{study.uid}/study-branch-arms"
    ).json()
    before_unlock_cohorts = api_client.get(f"/studies/{study.uid}/study-cohorts").json()

    # Lock
    response = api_client.post(
        f"/studies/{study.uid}/locks",
        json={"change_description": "Lock 1"},
    )
    assert response.status_code == 201
    # Unlock -- Study remain unlocked
    response = api_client.delete(f"/studies/{study.uid}/locks")
    assert response.status_code == 200

    # edit arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-arms/{study_arm.arm_uid}",
        json={
            "name": "New_Arm_Name_1",
        },
    )
    res = response.json()
    assert response.status_code == 200

    # edit branch arm
    response = api_client.patch(
        f"/studies/{study.uid}/study-branch-arms/{branch_arm['branch_arm_uid']}",
        json={
            "name": "New_Branch_Arm_Name_1",
        },
    )
    res = response.json()
    assert response.status_code == 200

    # edit cohort
    response = api_client.patch(
        f"/studies/{study.uid}/study-cohorts/{cohort['cohort_uid']}",
        json={
            "name": "New_cohort_Name_2",
        },
    )
    res = response.json()
    assert response.status_code == 200

    # get all
    assert (
        before_unlock_arms
        == api_client.get(
            f"/studies/{study.uid}/study-arms?study_value_version=2"
        ).json()
    )
    assert (
        before_unlock_branch_arms
        == api_client.get(
            f"/studies/{study.uid}/study-branch-arms?study_value_version=2"
        ).json()
    )
    assert (
        before_unlock_cohorts
        == api_client.get(
            f"/studies/{study.uid}/study-cohorts?study_value_version=2"
        ).json()
    )


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
def test_get_study_cohorts_csv_xml_excel(api_client, export_format):
    url = f"/studies/{study.uid}/study-cohorts"
    TestUtils.verify_exported_data_format(api_client, export_format, url)
