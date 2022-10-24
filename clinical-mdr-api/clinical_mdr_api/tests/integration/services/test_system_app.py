def test_get_system_information(app_client):
    response = app_client.get("/system/information")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get(
        "api_version"
    ), "missing api_version property of system information"
    assert payload.get(
        "db_version"
    ), "missing db_version property of system information"
    assert payload.get("build_id"), "missing build_id property of system information"
    assert payload.get("commit_id"), "missing commit_id property of system information"


def test_get_system_healthcheck(app_client):
    response = app_client.get("/system/healthcheck")
    assert response.status_code == 200


def test_get_system_information_build_id(app_client):
    response = app_client.get("/system/information/build-id")
    assert response.status_code == 200
    assert response.text
