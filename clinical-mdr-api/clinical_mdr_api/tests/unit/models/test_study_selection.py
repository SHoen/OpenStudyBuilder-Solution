from dataclasses import dataclass

from hypothesis import given, settings
from hypothesis.strategies import (
    composite,
    datetimes,
    from_regex,
    integers,
    lists,
    text,
)

from clinical_mdr_api.domain.project.project import ProjectAR
from clinical_mdr_api.domain.study_selection.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_objective import (
    StudySelectionObjectivesAR,
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.models import Objective, StudySelectionObjective


@composite
def non_empty_text(draw):
    return (
        draw(text(max_size=5))
        + draw(from_regex(r"[^\s]", fullmatch=True))
        + draw(text(max_size=5))
    )


@composite
def study_selection_objectives_values(draw):
    return StudySelectionObjectiveVO.from_input_values(
        objective_uid=draw(non_empty_text()),
        objective_version=draw(non_empty_text()),
        study_selection_uid=draw(non_empty_text()),
        objective_level_uid=None,
        objective_level_order=None,
        start_date=draw(datetimes()),
        user_initials=draw(non_empty_text()),
    )


@composite
def objective_models(draw):
    return Objective(
        uid=draw(non_empty_text()),
        name=draw(non_empty_text()),
        startDate=draw(datetimes()),
        endDate=draw(datetimes()),
        status=draw(non_empty_text()),
        version=draw(non_empty_text()),
        changeDescription=draw(non_empty_text()),
        userInitials=draw(non_empty_text()),
    )


@composite
def study_selection_objectives_aggregates(draw):
    return StudySelectionObjectivesAR.from_repository_values(
        study_uid=draw(non_empty_text()),
        study_objectives_selection=draw(
            lists(study_selection_objectives_values(), min_size=1, max_size=5)
        ),
    )


@composite
def study_selection_endpoints_aggregates_with_given_study_uid_study_objective_uid_and_count(
    draw, study_uid: str, study_objective_uid: str, count: int
):
    return StudySelectionEndpointsAR.from_repository_values(
        study_uid=study_uid,
        study_endpoints_selection=[
            StudySelectionEndpointVO.from_input_values(
                study_selection_uid=draw(non_empty_text()),
                study_objective_uid=study_objective_uid,
                start_date=draw(datetimes()),
                endpoint_uid=draw(non_empty_text()),
                endpoint_version=draw(non_empty_text()),
                endpoint_units=draw(non_empty_text()),
                endpoint_level_uid=draw(non_empty_text()),
                endpoint_sub_level_uid=draw(non_empty_text()),
                endpoint_level_order=0,
                timeframe_uid=draw(non_empty_text()),
                timeframe_version=draw(non_empty_text()),
                unit_separator=draw(non_empty_text()),
                user_initials=draw(non_empty_text()),
            )
            for _ in range(0, count)
        ]
        + [
            StudySelectionEndpointVO.from_input_values(
                study_selection_uid=draw(non_empty_text()),
                study_objective_uid=draw(
                    non_empty_text().filter(lambda _: _ != study_objective_uid)
                ),
                start_date=draw(datetimes()),
                endpoint_uid=draw(non_empty_text()),
                endpoint_version=draw(non_empty_text()),
                endpoint_units=draw(non_empty_text()),
                endpoint_level_uid=draw(non_empty_text()),
                endpoint_sub_level_uid=draw(non_empty_text()),
                endpoint_level_order=0,
                timeframe_uid=draw(non_empty_text()),
                timeframe_version=draw(non_empty_text()),
                unit_separator=draw(non_empty_text()),
                user_initials=draw(non_empty_text()),
            )
            for _ in range(0, draw(integers(min_value=0, max_value=5)))
        ],
    )


@dataclass(frozen=True)
class StudySelectionObjectiveFromStudySelectionObjectivesArAndOrderTestTuple:
    study_selection_objectives_ar: StudySelectionObjectivesAR
    order: int
    objective: Objective
    study_selection_endpoints_ar: StudySelectionEndpointsAR
    expected_endpoint_count: int
    project: ProjectAR


@composite
def study_selection_objective__from_study_selection_objectives_ar_and_order__test_tuples(
    draw,
):
    expected_endpoint_count: int = draw(integers(min_value=0, max_value=5))
    study_selection_objectives_ar: StudySelectionObjectivesAR
    order: int
    project: ProjectAR = ProjectAR(
        _uid="Project_000001",
        _project_number="123",
        _clinical_programme_uid="CP_000001",
        name="Test project",
    )

    study_selection_objectives_ar = draw(study_selection_objectives_aggregates())

    order = draw(
        integers(
            min_value=0,
            max_value=len(study_selection_objectives_ar.study_objectives_selection) - 1,
        )
    )

    objective_model = draw(objective_models())

    study_selection_endpoints_ar = draw(
        study_selection_endpoints_aggregates_with_given_study_uid_study_objective_uid_and_count(
            study_uid=study_selection_objectives_ar.study_uid,
            study_objective_uid=study_selection_objectives_ar.study_objectives_selection[
                order - 1
            ].study_selection_uid,
            count=expected_endpoint_count,
        )
    )

    return StudySelectionObjectiveFromStudySelectionObjectivesArAndOrderTestTuple(
        study_selection_objectives_ar=study_selection_objectives_ar,
        order=order,
        objective=objective_model,
        study_selection_endpoints_ar=study_selection_endpoints_ar,
        expected_endpoint_count=expected_endpoint_count,
        project=project,
    )


@settings(max_examples=20)
@given(
    test_tuple=study_selection_objective__from_study_selection_objectives_ar_and_order__test_tuples()
)
def test__study_selection_objective__from_study_selection_objectives_ar_and_order__results(
    test_tuple: StudySelectionObjectiveFromStudySelectionObjectivesArAndOrderTestTuple,
):
    # when
    result = StudySelectionObjective.from_study_selection_objectives_ar_and_order(
        study_selection_objectives_ar=test_tuple.study_selection_objectives_ar,
        order=test_tuple.order,
        accepted_version=False,
        get_objective_by_uid_callback=lambda _: test_tuple.objective,
        get_objective_by_uid_version_callback=lambda x, y: test_tuple.objective,
        get_ct_term_objective_level=lambda x, y: None,
        get_study_selection_endpoints_ar_by_study_uid_callback=lambda _: test_tuple.study_selection_endpoints_ar,
        find_project_by_study_uid=lambda x: test_tuple.project,
    )

    # then
    assert result.order == test_tuple.order
    assert result.objective == test_tuple.objective
    assert (
        result.studyObjectiveUid
        == test_tuple.study_selection_objectives_ar.study_objectives_selection[
            test_tuple.order - 1
        ].study_selection_uid
    )
    assert (
        result.startDate
        == test_tuple.study_selection_objectives_ar.study_objectives_selection[
            test_tuple.order - 1
        ].start_date
    )
    assert (
        result.objectiveLevel
        == test_tuple.study_selection_objectives_ar.study_objectives_selection[
            test_tuple.order - 1
        ].objective_level_uid
    )
    assert result.studyUid == test_tuple.study_selection_objectives_ar.study_uid
    assert result.endpointCount == test_tuple.expected_endpoint_count
