import datetime

import pytest

from clinical_mdr_api.models import (
    CTTermName,
    Endpoint,
    Objective,
    StudySelectionEndpoint,
    StudySelectionObjective,
    Timeframe,
)
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.study_selection import EndpointUnits
from clinical_mdr_api.models.unit_definition import UnitDefinitionModel
from clinical_mdr_api.services.study_objectives import StudyObjectivesService

USER_INITIALS = "unknown-user"
STUDY_UID = "Study_000001"

DATETIME_799 = datetime.datetime(2022, 9, 14, 15, 43, 32, 610799)
DATETIME_811 = datetime.datetime(2022, 9, 14, 15, 43, 32, 561811)
DATETIME_874 = datetime.datetime(2022, 9, 14, 15, 28, 16, 236874)
DATETIME_668 = datetime.datetime(2022, 9, 14, 15, 41, 34, 287668)

TERM_PRIMARY = CTTermName(
    termUid="CTTerm_000053",
    sponsorPreferredName="Primary",
    sponsorPreferredNameSentenceCase="primary",
)
TERM_PRI_OBJ = CTTermName(
    termUid="C85826_OBJPRIM",
    sponsorPreferredName="Primary Objective",
    sponsorPreferredNameSentenceCase="primary objective",
    order=1,
)
TERM_PRI_END = CTTermName(
    termUid="C98772_OUTMSPRI",
    sponsorPreferredName="Primary Endpoint",
    sponsorPreferredNameSentenceCase="primary endpoint",
)
TERM_SEC_END = CTTermName(
    termUid="C98781_OUTMSSEC",
    sponsorPreferredName="Secondary Endpoint",
    sponsorPreferredNameSentenceCase="secondary endpoint",
)

TIMEFRAME_1 = Timeframe(
    uid="Timeframe_000001",
    name="<p>Time Frame: through study completion, an average of 2 year</p>",
    namePlain="Time Frame: through study completion, an average of 2 year",
)
TIMEFRAME_2 = Timeframe(
    uid="Timeframe_000002",
    name="test 25-Hydroxyvitamin D",
    namePlain="test 25-Hydroxyvitamin D",
)

ENDPOINT_4 = Endpoint(
    uid="Endpoint_000004",
    name="<p>Disease control rate of Actrapid + Empagliflozin cohort</p>",
    namePlain="Disease control rate of Actrapid + Empagliflozin cohort",
)
ENDPOINT_3 = Endpoint(
    uid="Endpoint_000003",
    name="<p>Mean Change from Baseline in 25-Hydroxyvitamin D</p>",
    namePlain="Mean Change from Baseline in 25-Hydroxyvitamin D",
)

ENDPOINT_UNITS_ = EndpointUnits(units=[], separator=None)
ENDPOINT_UNITS_2 = EndpointUnits(units=["UnitDefinition_000002"], separator=None)
ENDPOINT_UNITS_6 = EndpointUnits(units=["UnitDefinition_000006"], separator=None)

OBJECTIVE_3 = Objective(
    uid="Objective_000003",
    name="To compare the effect of Actrapid relative to BYETTA on 25-Hydroxyvitamin D",
    namePlain="To compare the effect of Actrapid relative to BYETTA on 25-Hydroxyvitamin D",
)

STUDY_OBJECTIVE_3 = StudySelectionObjective(
    studyUid=STUDY_UID,
    order=1,
    studyObjectiveUid="StudyObjective_000003",
    objectiveLevel=TERM_PRI_OBJ,
    objective=OBJECTIVE_3,
    startDate=DATETIME_874,
    userInitials=USER_INITIALS,
    latestObjective=None,
)

STUDY_OBJECTIVES = (STUDY_OBJECTIVE_3,)

STUDY_ENDPOINT_1 = StudySelectionEndpoint(
    studyUid=STUDY_UID,
    order=3,
    studyEndpointUid="StudyEndpoint_000001",
    studyObjective=None,
    endpointLevel=None,
    endpointSubLevel=None,
    endpointUnits=ENDPOINT_UNITS_,
    endpoint=None,
    timeframe=None,
    startDate=DATETIME_799,
    userInitials=USER_INITIALS,
)
STUDY_ENDPOINT_20 = StudySelectionEndpoint(
    studyUid=STUDY_UID,
    order=2,
    studyEndpointUid="StudyEndpoint_000020",
    studyObjective=STUDY_OBJECTIVE_3,
    endpointLevel=TERM_SEC_END,
    endpointSubLevel=None,
    endpointUnits=ENDPOINT_UNITS_6,
    endpoint=ENDPOINT_4,
    timeframe=TIMEFRAME_2,
    startDate=DATETIME_811,
    userInitials=USER_INITIALS,
)
STUDY_ENDPOINT_17 = StudySelectionEndpoint(
    studyUid=STUDY_UID,
    order=1,
    studyEndpointUid="StudyEndpoint_000017",
    studyObjective=STUDY_OBJECTIVE_3,
    endpointLevel=TERM_PRI_END,
    endpointSubLevel=TERM_PRIMARY,
    endpointUnits=ENDPOINT_UNITS_2,
    endpoint=ENDPOINT_3,
    timeframe=TIMEFRAME_1,
    startDate=DATETIME_668,
    userInitials=USER_INITIALS,
)

STUDY_ENDPOINTS = (
    STUDY_ENDPOINT_1,
    STUDY_ENDPOINT_20,
    STUDY_ENDPOINT_17,
)

UNIT_ATTRS = dict(
    startDate=DATETIME_799,
    status="Final",
    version="1.0",
    userInitials=USER_INITIALS,
    changeDescription="Approved version",
    libraryName="Sponsor",
    convertibleUnit=True,
    displayUnit=True,
    masterUnit=True,
    usConventionalUnit=True,
    unitSubsets=[],
    templateParameter=False,
)

UNITS = {
    "UnitDefinition_000002": UnitDefinitionModel(
        uid="UnitDefinition_000002",
        name="beats/min",
        siUnit=False,
        ctUnits=[SimpleTermModel(termUid="C49673_beats/min", name="beats/min")],
        **UNIT_ATTRS,
    ),
    "UnitDefinition_000006": UnitDefinitionModel(
        uid="UnitDefinition_000006",
        name="kg/m^2",
        siUnit=True,
        ctUnits=[
            SimpleTermModel(termUid="C49671_kg/m2", name="Kilogram per Square Meter")
        ],
        **UNIT_ATTRS,
    ),
}

STANDARD_TREE = {
    "C85826_OBJPRIM": (
        TERM_PRI_OBJ,
        {
            "StudyObjective_000003": (
                STUDY_OBJECTIVE_3,
                {
                    "C98781_OUTMSSEC": (
                        TERM_SEC_END,
                        {"StudyEndpoint_000020": STUDY_ENDPOINT_20},
                    ),
                    "CTTerm_000053": (
                        TERM_PRIMARY,
                        {"StudyEndpoint_000017": STUDY_ENDPOINT_17},
                    ),
                },
            )
        },
    )
}

CONDENSED_TREE = {
    "C85826_OBJPRIM": (
        TERM_PRI_OBJ,
        {"StudyObjective_000003": STUDY_OBJECTIVE_3},
        {
            "CTTerm_000053": (
                TERM_PRIMARY,
                {"StudyEndpoint_000017": STUDY_ENDPOINT_17},
            ),
            "C98781_OUTMSSEC": (
                TERM_SEC_END,
                {"StudyEndpoint_000020": STUDY_ENDPOINT_20},
            ),
        },
    )
}


# pylint: disable=redefined-outer-name
@pytest.fixture(scope="module")
def study_objectives_service():
    service = StudyObjectivesService(USER_INITIALS)
    setattr(service, "_units", UNITS)
    return service


def test_build_standard_tree(study_objectives_service):
    tree = study_objectives_service._build_tree(STUDY_ENDPOINTS)
    assert tree == STANDARD_TREE


def test_build_condensed_tree(study_objectives_service):
    tree = study_objectives_service._build_condensed_tree(STUDY_ENDPOINTS)
    assert tree == CONDENSED_TREE


def test_build_condensed_html(study_objectives_service):
    doc = study_objectives_service._build_condensed_html(CONDENSED_TREE)

    # Check that document is HTML and has table data (not only headers)
    assert "</body>" in doc, "document has no </body>"
    assert "</td>" in doc, "document has no </td>"

    # Search for objective text in document
    for objective in STUDY_OBJECTIVES:
        assert (
            objective.objectiveLevel.sponsorPreferredName in doc
        ), f'objective level "{objective.objectiveLevel.sponsorPreferredName}" was not found in document'
        assert (
            objective.objective.namePlain in doc
        ), f'objective "{objective.objective.namePlain}" was not found in document'

    assert_patterns_in_document(doc)


def test_build_condensed_docx(study_objectives_service):
    docx = study_objectives_service._build_condensed_docx(CONDENSED_TREE).document

    assert len(docx.tables) == 1, "expected exactly 1 table in DOCX document"

    table = docx.tables[0]
    assert len(table.columns) == 2, "expected 2 columns of table"
    assert len(table.rows) == 2, "expected 2 rows of table"

    # extract all text from the table
    doc = "\n".join([cell.text for row in table.rows for cell in row.cells])

    assert_patterns_in_document(doc)


def test_build_standard_docx(study_objectives_service):
    docx = study_objectives_service._build_standard_docx(STANDARD_TREE).document

    assert len(docx.tables) == 1, "expected exactly 1 table in DOCX document"

    table = docx.tables[0]
    assert len(table.columns) == 4, "expected 4 columns of table"
    assert len(table.rows) == 6, "expected 6 rows of table"

    # extract all text from the table
    doc = "\n".join([cell.text for row in table.rows for cell in row.cells])

    assert_patterns_in_document(doc)


def assert_patterns_in_document(doc: str):
    # Search for objective text in document
    for objective in STUDY_OBJECTIVES:
        assert (
            objective.objectiveLevel.sponsorPreferredName in doc
        ), f'objective level "{objective.objectiveLevel.sponsorPreferredName}" was not found in document'
        assert (
            objective.objective.namePlain in doc
        ), f'objective "{objective.objective.namePlain}" was not found in document'

    # Search for endpoints text in document
    for endpoint in STUDY_ENDPOINTS:
        if not endpoint.endpoint:
            continue
        if endpoint.endpointSubLevel:
            assert (
                endpoint.endpointSubLevel.sponsorPreferredName in doc
            ), f'endpoint sub-level "{endpoint.endpointSubLevel.sponsorPreferredName}" was not found in document'
        elif endpoint.endpointLevel:
            assert (
                endpoint.endpointLevel.sponsorPreferredName in doc
            ), f'endpoint level "{endpoint.endpointLevel.sponsorPreferredName}" was not found in document'
        assert endpoint.endpoint.namePlain in doc
