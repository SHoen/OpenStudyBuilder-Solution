# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments
import copy
import logging
from typing import List

import pytest
from _pytest.fixtures import FixtureRequest

from clinical_mdr_api import models
from clinical_mdr_api.config import STUDY_ENDPOINT_TP_NAME
from clinical_mdr_api.models import study_selection
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.template_parameter_value import (
    IndexedTemplateParameterValue,
)
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService
from clinical_mdr_api.services.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import (
    inject_and_clear_db,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

AUTHOR = "TEST"

log = logging.getLogger(__name__)

# Global variables shared between fixtures and tests
study_uid: str
unit_definitions: List[models.UnitDefinitionModel]
unit_separator: str
timeframe: models.Timeframe
study_endpoint: models.StudySelectionEndpoint
study_endpoint_2: models.StudySelectionEndpoint


@pytest.fixture(scope="function")
def study_objective_service():
    return StudyObjectiveSelectionService(AUTHOR)


@pytest.fixture(scope="function")
def objective_template_service():
    return ObjectiveTemplateService(AUTHOR)


@pytest.fixture(scope="module")
def test_data(request: FixtureRequest):
    """Fixture creates, initializes and yields a test database, then destroys it at teardown"""

    log.debug("%s() fixture: creating database", request.fixturename)
    db_name = "services.studyendpointsparam"
    db = inject_and_clear_db(db_name)

    log.debug("%s() fixture: initializing database", request.fixturename)

    global study_uid
    global unit_definitions
    global unit_separator
    global timeframe
    global study_endpoint
    global study_endpoint_2

    study = inject_base_data()
    study_uid = study.uid
    db.cypher_query(data_library.STARTUP_PARAMETERS_CYPHER)

    endpoint_template = TestUtils.create_endpoint_template()
    unit_definitions = [
        TestUtils.create_unit_definition(name="unit1"),
        TestUtils.create_unit_definition(name="unit2"),
    ]
    unit_separator = "and"
    timeframe_template = TestUtils.create_timeframe_template()
    timeframe = TestUtils.create_timeframe(timeframeTemplateUid=timeframe_template.uid)
    study_endpoint = TestUtils.create_study_endpoint(
        study_uid=study_uid,
        endpointTemplateUid=endpoint_template.uid,
        endpointUnits=study_selection.EndpointUnits(
            units=[u.uid for u in unit_definitions], separator=unit_separator
        ),
        timeframeUid=timeframe.uid,
    )

    study_2 = TestUtils.create_study()
    endpoint_template_2 = TestUtils.create_endpoint_template()
    study_endpoint_2 = TestUtils.create_study_endpoint(
        study_uid=study_2.uid, endpointTemplateUid=endpoint_template_2.uid
    )

    log.debug("%s() fixture: setup complete", request.fixturename)
    yield db

    log.debug("%s() fixture: teardown: deleting database", request.fixturename)
    db.cypher_query("CREATE OR REPLACE DATABASE $db", {"db": db_name})


def test_crud(test_data, study_objective_service, objective_template_service):
    """
    Test StudyObjective using a StudyEndpoint
    You can only pick StudyEndpoints that belong to the same study as the study objective.
    So we should probably make a test to check that when we list the available parameters,
    we only get endpoints of the same study.
    """
    # Create
    objective_template = TestUtils.create_objective_template(
        name=f"Test objective template with [{STUDY_ENDPOINT_TP_NAME}] parameter"
    )
    parameter_value_dict = {
        "index": 1,
        "type": STUDY_ENDPOINT_TP_NAME,
        "uid": study_endpoint.studyEndpointUid,
        "name": study_endpoint.endpoint.name,
    }
    study_objective = TestUtils.create_study_objective(
        study_uid=study_uid,
        objectiveTemplateUid=objective_template.uid,
        parameterValues=[
            TemplateParameterMultiSelectInput(
                values=[IndexedTemplateParameterValue(**parameter_value_dict)]
            )
        ],
    )

    expected_study_endpoint_name = f"{study_endpoint.endpoint.name} {f' {unit_separator} '.join([u.name for u in unit_definitions])} {timeframe.name}"
    expected_return_parameter_value_dict = copy.deepcopy(parameter_value_dict)
    expected_return_parameter_value_dict["name"] = expected_study_endpoint_name
    assert (
        study_objective.objective.name
        == f"Test objective template with [{expected_study_endpoint_name}] parameter"
    )
    assert (
        study_objective.objective.parameterValues[0].values[0]
        == expected_return_parameter_value_dict
    )
    log.info("Study objective successfully created")

    # Read
    created_study_objective = study_objective_service.get_specific_selection(
        study_uid=study_uid, study_selection_uid=study_objective.studyObjectiveUid
    )
    assert (
        created_study_objective.objective.name
        == f"Test objective template with [{expected_study_endpoint_name}] parameter"
    )
    assert (
        study_objective.objective.parameterValues[0].values[0]
        == expected_return_parameter_value_dict
    )
    log.info("Study objective successfully returned")

    # Check list of available StudyEndpoint parameters
    available_parameters = objective_template_service.get_parameters(
        uid=objective_template.uid, study_uid=study_uid, include_study_endpoints=True
    )
    assert len(available_parameters) == 1
    assert available_parameters[0].values[0].uid == study_endpoint.studyEndpointUid
    log.info("List of available StudyEndpoint parameter values is correct")

    # Try selecting a StudyEndpoint from another study as parameter
    parameter_value_dict["uid"] = study_endpoint_2.studyEndpointUid
    with pytest.raises(ValueError) as e_info:
        _ = TestUtils.create_study_objective(
            study_uid=study_uid,
            objectiveTemplateUid=objective_template.uid,
            parameterValues=[
                TemplateParameterMultiSelectInput(
                    values=[IndexedTemplateParameterValue(**parameter_value_dict)]
                )
            ],
        )
    log.info(e_info)
