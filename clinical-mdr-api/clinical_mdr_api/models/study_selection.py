import re
from datetime import datetime
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Union

from pydantic import Field, root_validator

from clinical_mdr_api.domain.concepts.simple_concepts.numeric_value_with_unit import (
    NumericValueWithUnitAR,
)
from clinical_mdr_api.domain.study_selection.study_activity_instruction import (
    StudyActivityInstructionVO,
)
from clinical_mdr_api.domain.study_selection.study_activity_schedule import (
    StudyActivityScheduleVO,
)
from clinical_mdr_api.domain.study_selection.study_compound_dosing import (
    StudyCompoundDosingVO,
)
from clinical_mdr_api.domain.study_selection.study_design_cell import StudyDesignCellVO
from clinical_mdr_api.domain.study_selection.study_selection_activity import (
    StudySelectionActivityAR,
)
from clinical_mdr_api.domain.study_selection.study_selection_arm import (
    StudySelectionArmVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_branch_arm import (
    StudySelectionBranchArmVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_cohort import (
    StudySelectionCohortVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_compound import (
    StudySelectionCompoundVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_criteria import (
    StudySelectionCriteriaAR,
)
from clinical_mdr_api.domain.study_selection.study_selection_element import (
    StudySelectionElementVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_endpoint import (
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from clinical_mdr_api.domain.study_selection.study_selection_objective import (
    StudySelectionObjectivesAR,
)
from clinical_mdr_api.domain.unit_definition.unit_definition import UnitDefinitionAR
from clinical_mdr_api.domain_repositories.study_selection.study_compound_dosing_repository import (
    SelectionHistory as StudyCompoundDosingSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_activity_repository import (
    SelectionHistory as StudyActivitySelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_arm_repository import (
    SelectionHistoryArm,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_branch_arm_repository import (
    SelectionHistoryBranchArm,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_cohort_repository import (
    SelectionHistoryCohort,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_compound_repository import (
    StudyCompoundSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_criteria_repository import (
    SelectionHistory as StudyCriteriaSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_element_repository import (
    SelectionHistoryElement,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_endpoint_repository import (
    SelectionHistoryObject as StudyEndpointSelectionHistory,
)
from clinical_mdr_api.domain_repositories.study_selection.study_selection_objective_repository import (
    SelectionHistory as StudyObjectiveSelectionHistory,
)
from clinical_mdr_api.models.activities.activity import Activity
from clinical_mdr_api.models.activity_instruction import ActivityInstructionCreateInput
from clinical_mdr_api.models.compound import Compound
from clinical_mdr_api.models.compound_alias import CompoundAlias
from clinical_mdr_api.models.concept import SimpleNumericValueWithUnit
from clinical_mdr_api.models.criteria import Criteria, CriteriaCreateInput
from clinical_mdr_api.models.criteria_template import CriteriaTemplate
from clinical_mdr_api.models.ct_term import SimpleTermModel
from clinical_mdr_api.models.ct_term_name import CTTermName
from clinical_mdr_api.models.duration import DurationJsonModel
from clinical_mdr_api.models.endpoint import Endpoint, EndpointCreateInput
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.objective import Objective, ObjectiveCreateInput
from clinical_mdr_api.models.timeframe import Timeframe
from clinical_mdr_api.models.utils import BaseModel


class StudySelection(BaseModel):
    studyUid: Optional[str] = Field(
        ...,
        title="studyUid",
        description="The uid of the study",
    )

    order: int = Field(
        ...,
        title="order",
        description="The ordering of the selection",
    )

    projectNumber: Optional[str] = Field(
        None,
        title="projectNumber",
        description="Number property of the project that the study belongs to",
    )

    projectName: Optional[str] = Field(
        None,
        title="projectName",
        description="Name property of the project that the study belongs to",
    )

    @classmethod
    def remove_brackets_from_name_property(cls, object_to_clear):
        """
        Method removes brackets that surround template parameter used in the StudySelection object
        :param object_to_clear:
        :return:
        """
        used_template_parameters = []
        for parameter_value in object_to_clear.parameterValues:
            for value in parameter_value.values:
                used_template_parameters.append(value.name)
        for template_parameter in used_template_parameters:
            object_to_clear.name = re.sub(
                rf"\[?{template_parameter}\]?", template_parameter, object_to_clear.name
            )


"""
    Study objectives
"""


class StudySelectionObjectiveCore(StudySelection):
    studyObjectiveUid: Optional[str] = Field(
        ...,
        title="studyObjectiveUid",
        description="uid for the study objective",
    )

    objectiveLevel: Optional[CTTermName] = Field(
        None,
        title="objectiveLevel",
        description="level defining the objective",
    )

    objective: Optional[Objective] = Field(
        ...,
        title="objective",
        description="the objective selected for the study",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyObjectiveSelectionHistory,
        study_uid: str,
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
    ) -> "StudySelectionObjectiveCore":

        if study_selection_history.objective_level_uid:
            objective_level = get_ct_term_objective_level(
                study_selection_history.objective_level_uid
            )
        else:
            objective_level = None

        return cls(
            studyObjectiveUid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            studyUid=study_uid,
            objectiveLevel=objective_level,
            startDate=study_selection_history.start_date,
            objective=get_objective_by_uid_version_callback(
                study_selection_history.objective_uid,
                study_selection_history.objective_version,
            ),
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
        )


class StudySelectionObjective(StudySelectionObjectiveCore):
    endpointCount: Optional[int] = Field(
        None,
        title="endpointCount",
        description="Number of study endpoints related to given study objective.",
    )

    latestObjective: Optional[Objective] = Field(
        ...,
        title="latestObjective",
        description="Latest version of objective selected for study.",
    )
    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete objective versions",
    )

    @classmethod
    def from_study_selection_objectives_ar_and_order(
        cls,
        study_selection_objectives_ar: StudySelectionObjectivesAR,
        order: int,
        get_objective_by_uid_callback: Callable[[str], Objective],
        get_objective_by_uid_version_callback: Callable[[str], Objective],
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_study_selection_endpoints_ar_by_study_uid_callback: Callable[
            [str], StudySelectionEndpointsAR
        ],
        find_project_by_study_uid: Callable,
        no_brackets: bool = False,
        accepted_version: bool = False,
    ) -> "StudySelectionObjective":

        study_objective_selection = (
            study_selection_objectives_ar.study_objectives_selection
        )
        study_uid = study_selection_objectives_ar.study_uid
        single_study_selection = study_objective_selection[order - 1]
        study_objective_uid = single_study_selection.study_selection_uid
        objective_uid = single_study_selection.objective_uid
        study_selection_endpoints_ar = (
            get_study_selection_endpoints_ar_by_study_uid_callback(study_uid)
        )
        project = find_project_by_study_uid(study_uid)
        assert project is not None

        endpoint_count = sum(
            _.study_objective_uid == study_objective_uid
            for _ in study_selection_endpoints_ar.study_endpoints_selection
        )

        if single_study_selection.objective_level_uid:
            objective_level = get_ct_term_objective_level(
                single_study_selection.objective_level_uid
            )
        else:
            objective_level = None

        assert objective_uid is not None
        latest_objective = get_objective_by_uid_callback(objective_uid)
        if (
            latest_objective
            and latest_objective.version == single_study_selection.objective_version
        ):
            selected_objective = latest_objective
            latest_objective = None
        else:
            selected_objective = get_objective_by_uid_version_callback(
                objective_uid, single_study_selection.objective_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_objective)
            if latest_objective is not None:
                cls.remove_brackets_from_name_property(latest_objective)

        return cls(
            studyObjectiveUid=study_objective_uid,
            order=order,
            acceptedVersion=accepted_version,
            studyUid=study_uid,
            objectiveLevel=objective_level,
            startDate=single_study_selection.start_date,
            latestObjective=latest_objective,
            objective=selected_objective,
            endpointCount=endpoint_count,
            userInitials=single_study_selection.user_initials,
            projectName=project.name,
            projectNumber=project.project_number,
        )


class StudySelectionObjectiveCreateInput(BaseModel):
    objectiveLevelUid: Optional[str] = Field(
        None,
        title="objectiveLevel",
        description="level defining the objective",
    )
    objectiveData: ObjectiveCreateInput = Field(
        ..., title="objectiveData", description="Objective data to create new objective"
    )


class StudySelectionObjectiveInput(BaseModel):
    objectiveUid: str = Field(
        None,
        title="objectiveUid",
        description="Uid of the selected objective",
    )

    objectiveLevelUid: Optional[str] = Field(
        None,
        title="objectiveLevel",
        description="level defining the objective",
    )


class StudySelectionObjectiveNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="Uid of the selected objective",
    )


"""
    Study endpoints
"""


class EndpointUnits(BaseModel):
    units: Optional[List[str]] = Field(
        ...,
        title="units",
        description="the endpoint units selected for the study endpoint",
    )

    separator: Optional[str] = Field(
        None,
        title="separator",
        description="the endpoint units selected for the study endpoint",
    )


class StudySelectionEndpoint(StudySelection):
    studyEndpointUid: Optional[str] = Field(
        ...,
        title="studyEndpointUid",
        description="uid for the study endpoint",
    )

    studyObjective: Optional[StudySelectionObjective] = Field(
        None,
        title="studyObjectiveUid",
        description="uid for the study objective which the study endpoints connects to",
    )

    endpointLevel: Optional[CTTermName] = Field(
        None,
        title="endpointLevel",
        description="level defining the endpoint",
    )

    endpointSubLevel: Optional[CTTermName] = Field(
        None,
        title="endpointSubLevel",
        description="sub level defining the endpoint",
    )
    endpointUnits: Optional[EndpointUnits] = Field(
        None,
        title="endpointUnits",
        description="the endpoint units selected for the study endpoint",
    )

    endpoint: Optional[Endpoint] = Field(
        None,
        title="endpoint",
        description="the endpoint selected for the study",
    )

    timeframe: Optional[Timeframe] = Field(
        None,
        title="timeframe",
        description="the timeframe selected for the study",
    )

    latestEndpoint: Optional[Endpoint] = Field(
        None,
        title="latestEndpoint",
        description="Latest version of the endpoint selected for the study (if available else none)",
    )

    latestTimeframe: Optional[Timeframe] = Field(
        None,
        title="latestTimeframe",
        description="Latest version of the timeframe selected for the study (if available else none)",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )
    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete endpoint and timeframe versions",
    )

    @classmethod
    def from_study_selection_endpoint(
        cls,
        study_selection: StudySelectionEndpointVO,
        study_uid: str,
        order: int,
        get_endpoint_by_uid_and_version: Callable[[str], Endpoint],
        get_latest_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid_and_version: Callable[[str], Timeframe],
        get_latest_timeframe: Callable[[str], Timeframe],
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
        no_brackets: bool = False,
    ) -> "StudySelectionEndpoint":

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        if study_selection.endpoint_uid is None:
            end_model = None
            latest_end_model = None
        else:
            end_model = get_endpoint_by_uid_and_version(
                study_selection.endpoint_uid, study_selection.endpoint_version
            )
            latest_end_model = get_latest_endpoint_by_uid(study_selection.endpoint_uid)
            if end_model.version == latest_end_model.version:
                latest_end_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=end_model)
                if latest_end_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_end_model
                    )
        if study_selection.timeframe_uid is None:
            time_model = None
            latest_time_model = None
        else:
            time_model = get_timeframe_by_uid_and_version(
                study_selection.timeframe_uid, study_selection.timeframe_version
            )
            latest_time_model = get_latest_timeframe(study_selection.timeframe_uid)
            if time_model.version == latest_time_model.version:
                latest_time_model = None
            if no_brackets:
                cls.remove_brackets_from_name_property(object_to_clear=time_model)
                if latest_time_model is not None:
                    cls.remove_brackets_from_name_property(
                        object_to_clear=latest_time_model
                    )
        if study_selection.study_objective_uid is None:
            study_obj_model = None
        else:
            study_obj_model = get_study_objective_by_uid(
                study_uid, study_selection.study_objective_uid, no_brackets=no_brackets
            )
            if no_brackets:
                cls.remove_brackets_from_name_property(
                    object_to_clear=study_obj_model.objective
                )
        if study_selection.endpoint_level_uid:
            endpoint_level = get_ct_term_objective_level(
                study_selection.endpoint_level_uid
            )
        else:
            endpoint_level = None
        if study_selection.endpoint_sub_level_uid:
            endpoint_sub_level = get_ct_term_objective_level(
                study_selection.endpoint_sub_level_uid
            )
        else:
            endpoint_sub_level = None
        return StudySelectionEndpoint(
            studyObjective=study_obj_model,
            studyUid=study_uid,
            order=order,
            acceptedVersion=accepted_version,
            studyEndpointUid=study_selection.study_selection_uid,
            endpointUnits=EndpointUnits(
                units=study_selection.endpoint_units,
                separator=study_selection.unit_separator,
            ),
            endpointLevel=endpoint_level,
            endpointSubLevel=endpoint_sub_level,
            startDate=study_selection.start_date,
            endpoint=end_model,
            latestEndpoint=latest_end_model,
            timeframe=time_model,
            latestTimeframe=latest_time_model,
            userInitials=study_selection.user_initials,
            projectName=project.name,
            projectNumber=project.project_number,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyEndpointSelectionHistory,
        study_uid: str,
        get_endpoint_by_uid: Callable[[str], Endpoint],
        get_timeframe_by_uid: Callable[[str], Timeframe],
        get_ct_term_objective_level: Callable[[str], CTTermName],
        get_study_objective_by_uid: Callable[[str], StudySelectionObjective],
    ) -> "StudySelectionEndpoint":
        if study_selection_history.endpoint_uid:
            endpoint = get_endpoint_by_uid(
                study_selection_history.endpoint_uid,
                study_selection_history.endpoint_version,
            )
        else:
            endpoint = None
        if study_selection_history.timeframe_uid:
            timeframe = get_timeframe_by_uid(
                study_selection_history.timeframe_uid,
                study_selection_history.timeframe_version,
            )
        else:
            timeframe = None
        if study_selection_history.study_objective_uid:
            study_objective = get_study_objective_by_uid(
                study_uid, study_selection_history.study_objective_uid
            )
        else:
            study_objective = None
        if study_selection_history.endpoint_level:
            endpoint_level = get_ct_term_objective_level(
                study_selection_history.endpoint_level
            )
        else:
            endpoint_level = None
        if study_selection_history.endpoint_sub_level:
            endpoint_sub_level = get_ct_term_objective_level(
                study_selection_history.endpoint_sub_level
            )
        else:
            endpoint_sub_level = None
        return cls(
            studyUid=study_uid,
            studyEndpointUid=study_selection_history.study_selection_uid,
            studyObjective=study_objective,
            endpointLevel=endpoint_level,
            endpointSubLevel=endpoint_sub_level,
            endpointUnits=EndpointUnits(
                units=study_selection_history.endpoint_units,
                separator=study_selection_history.unit_separator,
            ),
            endpoint=endpoint,
            timeframe=timeframe,
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            order=study_selection_history.order,
        )


class StudySelectionEndpointCreateInput(BaseModel):
    studyObjectiveUid: Optional[str] = Field(
        None,
        title="studyObjectiveUid",
        description="uid for a study objective to connect with",
    )
    endpointLevelUid: Optional[str] = Field(
        None,
        title="endpoint level",
        description="level defining the endpoint",
    )
    endpointSubLevelUid: Optional[str] = Field(
        None,
        title="endpoint sub level",
        description="sub level defining the endpoint",
    )
    endpointData: EndpointCreateInput = Field(
        ..., title="endpointData", description="endpoint data to create new endpoint"
    )
    endpointUnits: Optional[EndpointUnits] = Field(
        None,
        title="endpointUnits",
        description="hold the units used in the study endpoint",
    )
    timeframeUid: Optional[str] = Field(
        None,
        title="timeframeUid",
        description="uid for a timeframe",
    )


class StudySelectionEndpointInput(BaseModel):
    studyObjectiveUid: Optional[str] = Field(
        None,
        title="studyObjectiveUid",
        description="uid for a study objective to connect with",
    )

    endpointUid: Optional[str] = Field(
        None,
        title="endpointUid",
        description="uid for a study objective to connect with",
    )

    endpointLevelUid: Optional[str] = Field(
        None,
        title="endpoint level",
        description="level for the endpoint",
    )
    endpointSubLevelUid: Optional[str] = Field(
        None,
        title="endpoint sub level",
        description="sub level for the endpoint",
    )
    timeframeUid: Optional[str] = Field(
        None,
        title="timeframeUid",
        description="uid for a timeframe",
    )

    endpointUnits: Optional[EndpointUnits] = Field(
        None,
        title="endpointUnits",
        description="hold the units used in the study endpoint",
    )


class StudySelectionEndpointNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="Uid of the selected endpoint",
    )


"""
    Study compounds
"""


class StudySelectionCompound(StudySelection):
    @classmethod
    def from_study_compound_ar(
        cls,
        study_uid: str,
        selection: StudySelectionCompoundVO,
        order: int,
        compound_model: Optional[Compound],
        compound_alias_model: Optional[CompoundAlias],
        find_simple_term_model_name_by_term_uid: Callable,
        find_project_by_study_uid: Callable,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_numeric_value_by_uid: Callable[[str], Optional[NumericValueWithUnitAR]],
    ):
        project = find_project_by_study_uid(study_uid)
        return cls(
            order=order,
            studyUid=study_uid,
            studyCompoundUid=selection.study_selection_uid,
            compound=compound_model,
            compoundAlias=compound_alias_model,
            typeOfTreatment=find_simple_term_model_name_by_term_uid(
                selection.type_of_treatment_uid
            ),
            routeOfAdministration=find_simple_term_model_name_by_term_uid(
                selection.route_of_administration_uid
            ),
            strengthValue=SimpleNumericValueWithUnit.from_concept_uid(
                uid=selection.strength_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dosageForm=find_simple_term_model_name_by_term_uid(
                selection.dosage_form_uid
            ),
            dispensedIn=find_simple_term_model_name_by_term_uid(
                selection.dispensed_in_uid
            ),
            device=find_simple_term_model_name_by_term_uid(selection.device_uid),
            formulation=find_simple_term_model_name_by_term_uid(
                selection.formulation_uid
            ),
            otherInfo=selection.other_info,
            reasonForMissingNullValue=find_simple_term_model_name_by_term_uid(
                selection.reason_for_missing_value_uid
            ),
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            projectName=project.name,
            projectNumber=project.project_number,
            studyCompoundDosingCount=selection.study_compound_dosing_count,
        )

    studyCompoundUid: Optional[str] = Field(
        ...,
        title="studyCompoundUid",
        description="uid for the study compound",
        source="uid",
    )

    compound: Optional[Compound] = Field(
        None, title="compound", description="the connected compound model"
    )

    compoundAlias: Optional[CompoundAlias] = Field(
        None,
        title="compoundAlias",
        description="the connected compound alias",
    )

    typeOfTreatment: Optional[SimpleTermModel] = Field(
        None,
        title="typeOfTreatment",
        description="type of treatment uid defined for the selection",
    )

    routeOfAdministration: Optional[SimpleTermModel] = Field(
        None,
        title="routeOfAdministration",
        description="route of administration defined for the study selection",
    )

    strengthValue: Optional[SimpleNumericValueWithUnit] = Field(
        None,
        title="strength",
        description="compound strength defined for the study selection",
    )

    dosageForm: Optional[SimpleTermModel] = Field(
        None,
        title="dosageForm",
        description="dosage form defined for the study selection",
    )

    dispensedIn: Optional[SimpleTermModel] = Field(
        None,
        title="dispensedIn",
        description="dispense method defined for the study selection",
    )

    device: Optional[SimpleTermModel] = Field(
        None,
        title="device",
        description="device used for the compound in the study selection",
    )

    formulation: Optional[SimpleTermModel] = Field(
        None,
        title="formulation",
        description="formulation defined for the study selection",
    )

    otherInfo: Optional[str] = Field(
        None,
        title="otherInfo",
        description="any other information logged regarding the study compound",
    )

    reasonForMissingNullValue: Optional[SimpleTermModel] = Field(
        None,
        title="reasonForMissingNullValue",
        description="Reason why no compound is used in the study selection, e.g. exploratory study",
    )

    studyCompoundDosingCount: Optional[int] = Field(
        None, description="Number of compound dosing linked to Study Compound"
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="End date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundSelectionHistory,
        study_uid: str,
        get_compound_by_uid: Callable[[str], Compound],
        get_compound_alias_by_uid: Callable[[str], CompoundAlias],
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_numeric_value_by_uid: Callable[[str], Optional[NumericValueWithUnitAR]],
    ) -> "StudySelectionCompound":
        if study_selection_history.compound_uid:
            compound = get_compound_by_uid(study_selection_history.compound_uid)
        else:
            compound = None
        if study_selection_history.compound_alias_uid:
            compound_alias = get_compound_alias_by_uid(
                study_selection_history.compound_alias_uid
            )
        else:
            compound_alias = None
        return cls(
            studyCompoundUid=study_selection_history.study_selection_uid,
            order=study_selection_history.order,
            studyUid=study_uid,
            typeOfTreatment=find_simple_term_model_name_by_term_uid(
                study_selection_history.type_of_treatment_uid
            ),
            routeOfAdministration=find_simple_term_model_name_by_term_uid(
                study_selection_history.route_of_administration_uid
            ),
            strengthValue=SimpleNumericValueWithUnit.from_concept_uid(
                uid=study_selection_history.strength_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            dosageForm=find_simple_term_model_name_by_term_uid(
                study_selection_history.dosage_form_uid
            ),
            dispensedIn=find_simple_term_model_name_by_term_uid(
                study_selection_history.dispensed_in_uid
            ),
            device=find_simple_term_model_name_by_term_uid(
                study_selection_history.device_uid
            ),
            formulation=find_simple_term_model_name_by_term_uid(
                study_selection_history.formulation_uid
            ),
            otherInfo=study_selection_history.other_info,
            reasonForMissingNullValue=find_simple_term_model_name_by_term_uid(
                study_selection_history.reason_for_missing_value_uid
            ),
            startDate=study_selection_history.start_date,
            compound=compound,
            compoundAlias=compound_alias,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
        )


class StudySelectionCompoundInput(BaseModel):

    compoundAliasUid: Optional[str] = Field(
        None,
        title="compoundAliasUid",
        description="uid for the library compound alias",
    )

    typeOfTreatmentUid: Optional[str] = Field(
        None,
        title="typeOfTreatmentUid",
        description="type of treatment defined for the selection",
    )

    routeOfAdministrationUid: Optional[str] = Field(
        None,
        title="routeOfAdministrationUid",
        description="route of administration defined for the study selection",
    )

    strengthValueUid: Optional[str] = Field(
        None,
        title="strengthValueUid",
        description="compound strength defined for the study selection",
    )

    dosageFormUid: Optional[str] = Field(
        None,
        title="dosageFormUid",
        description="dosage form defined for the study selection",
    )

    dispensedInUid: Optional[str] = Field(
        None,
        title="dispensedInUid",
        description="dispense method defined for the study selection",
    )

    deviceUid: Optional[str] = Field(
        None,
        title="deviceUid",
        description="device used for the compound in the study selection",
    )

    formulationUid: Optional[str] = Field(
        None,
        title="formulationUid",
        description="formulation defined for the study selection",
    )

    otherInfo: Optional[str] = Field(
        None,
        title="otherInfo",
        description="any other information logged regarding the study compound",
    )

    reasonForMissingNullValueUid: Optional[str] = Field(
        None,
        title="reasonForMissingNullValueUid",
        description="Reason why no compound is used in the study selection, e.g. exploratory study",
    )


class StudySelectionCompoundNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order selected for the study compound",
    )


"""
    Study criteria
"""


class StudySelectionCriteriaCore(StudySelection):
    studyCriteriaUid: Optional[str] = Field(
        ...,
        title="studyCriteriaUid",
        description="uid for the study criteria",
    )

    criteriaType: Optional[CTTermName] = Field(
        None,
        title="criteriaType",
        description="Type of criteria",
    )

    criteria: Optional[Criteria] = Field(
        None,
        title="criteria",
        description="the criteria selected for the study",
    )

    criteriaTemplate: Optional[CriteriaTemplate] = Field(
        None,
        title="criteriaTemplate",
        description="the criteria template selected for the study",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )
    keyCriteria: Optional[bool] = Field(False, title="keyCriteria", description="")

    @classmethod
    def from_study_selection_template_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
    ) -> "StudySelectionCriteriaCore":

        return cls(
            studyCriteriaUid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            studyUid=study_uid,
            startDate=study_selection_history.start_date,
            criteriaTemplate=get_criteria_template_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
            keyCriteria=study_selection_history.key_criteria,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCriteriaSelectionHistory,
        study_uid: str,
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
    ) -> "StudySelectionCriteriaCore":

        return cls(
            studyCriteriaUid=study_selection_history.study_selection_uid,
            order=study_selection_history.criteria_type_order,
            studyUid=study_uid,
            startDate=study_selection_history.start_date,
            criteria=get_criteria_by_uid_version_callback(
                study_selection_history.syntax_object_uid,
                study_selection_history.syntax_object_version,
            ),
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
            keyCriteria=study_selection_history.key_criteria,
        )


class StudySelectionCriteria(StudySelectionCriteriaCore):
    latestCriteria: Optional[Criteria] = Field(
        None,
        title="latestCriteria",
        description="Latest version of criteria selected for study.",
    )
    latestTemplate: Optional[CriteriaTemplate] = Field(
        None,
        title="latestTemplate",
        description="Latest version of criteria template selected for study.",
    )
    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete criteria versions",
    )

    @classmethod
    def from_study_selection_criteria_template_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_template_by_uid_callback: Callable[[str], CriteriaTemplate],
        get_criteria_template_by_uid_version_callback: Callable[
            [str], CriteriaTemplate
        ],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        accepted_version: bool = False,
    ) -> "StudySelectionCriteria":
        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_template_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(criteria_type_uid)

        assert criteria_template_uid is not None
        latest_criteria_template = get_criteria_template_by_uid_callback(
            criteria_template_uid
        )
        if (
            latest_criteria_template
            and latest_criteria_template.version
            == single_study_selection.syntax_object_version
        ):
            selected_criteria_template = latest_criteria_template
            latest_criteria_template = None
        else:
            selected_criteria_template = get_criteria_template_by_uid_version_callback(
                criteria_template_uid, single_study_selection.syntax_object_version
            )

        return cls(
            studyCriteriaUid=study_criteria_uid,
            criteriaType=criteria_type,
            order=criteria_type_order,
            acceptedVersion=accepted_version,
            studyUid=study_uid,
            startDate=single_study_selection.start_date,
            latestTemplate=latest_criteria_template,
            criteriaTemplate=selected_criteria_template,
            userInitials=single_study_selection.user_initials,
            projectName=project.name,
            projectNumber=project.project_number,
            keyCriteria=single_study_selection.key_criteria,
        )

    @classmethod
    def from_study_selection_criteria_ar_and_order(
        cls,
        study_selection_criteria_ar: StudySelectionCriteriaAR,
        criteria_type_uid: str,
        criteria_type_order: int,
        get_criteria_by_uid_callback: Callable[[str], Criteria],
        get_criteria_by_uid_version_callback: Callable[[str], Criteria],
        get_ct_term_criteria_type: Callable[[str], CTTermName],
        find_project_by_study_uid: Callable,
        no_brackets: bool = False,
        accepted_version: bool = False,
    ) -> "StudySelectionCriteria":

        study_uid = study_selection_criteria_ar.study_uid

        project = find_project_by_study_uid(study_uid)
        assert project is not None

        # Filter criteria list on criteria type before selecting with order property
        study_criteria_selection_with_type = [
            x
            for x in study_selection_criteria_ar.study_criteria_selection
            if x.criteria_type_uid == criteria_type_uid
        ]
        single_study_selection = study_criteria_selection_with_type[
            criteria_type_order - 1
        ]
        study_criteria_uid = single_study_selection.study_selection_uid
        criteria_uid = single_study_selection.syntax_object_uid

        criteria_type = get_ct_term_criteria_type(criteria_type_uid)

        assert criteria_uid is not None
        latest_criteria = get_criteria_by_uid_callback(criteria_uid)
        if (
            latest_criteria
            and latest_criteria.version == single_study_selection.syntax_object_version
        ):
            selected_criteria = latest_criteria
            latest_criteria = None
        else:
            selected_criteria = get_criteria_by_uid_version_callback(
                criteria_uid, single_study_selection.syntax_object_version
            )
        if no_brackets:
            cls.remove_brackets_from_name_property(selected_criteria)
            if latest_criteria is not None:
                cls.remove_brackets_from_name_property(latest_criteria)

        return cls(
            studyCriteriaUid=study_criteria_uid,
            criteriaType=criteria_type,
            order=criteria_type_order,
            acceptedVersion=accepted_version,
            studyUid=study_uid,
            startDate=single_study_selection.start_date,
            latestCriteria=latest_criteria,
            criteria=selected_criteria,
            userInitials=single_study_selection.user_initials,
            projectName=project.name,
            projectNumber=project.project_number,
            keyCriteria=single_study_selection.key_criteria,
        )


class StudySelectionCriteriaCreateInput(BaseModel):
    criteriaData: CriteriaCreateInput = Field(
        ..., title="criteriaData", description="Criteria data to create new criteria"
    )


class StudySelectionCriteriaTemplateSelectInput(BaseModel):
    criteriaTemplateUid: str = Field(
        ...,
        title="criteriaTemplateUid",
        description="The unique id of the criteria template that is to be selected.",
    )
    libraryName: str = Field(
        None,
        title="libraryName",
        description="If specified: The name of the library to which the criteria will be linked. The following rules apply: \n"
        "* The library needs to be present, it will not be created with this request. The *[GET] /libraries* criteria can help. And \n"
        "* The library needs to allow the creation: The 'isEditable' property of the library needs to be true. \n\n"
        "If not specified: The library of the criteria template will be used.",
    )


class StudySelectionCriteriaNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="New value to set for the order property of the selection",
    )


class StudySelectionCriteriaKeyCriteria(BaseModel):
    key_criteria: bool = Field(
        ...,
        title="key_criteria",
        description="New value to set for the key_criteria property of the selection",
    )


#
# Study Activity
#


class CommonStudyActivity(BaseModel):
    showActivityGroupInProtocolFlowchart: Optional[bool] = Field(
        None,
        title="showActivityGroupInProtocolFlowchart",
        description="show activity group in protocol flow chart",
    )

    showActivitySubGroupInProtocolFlowchart: Optional[bool] = Field(
        None,
        title="showActivitySubGroupInProtocolFlowchart",
        description="show activity sub group in protocol flow chart",
    )

    showActivityInProtocolFlowchart: Optional[bool] = Field(
        None,
        title="showActivityInProtocolFlowchart",
        description="show activity in protocol flow chart",
    )


class StudySelectionActivityCore(CommonStudyActivity, StudySelection):
    studyActivityUid: Optional[str] = Field(
        ...,
        title="studyActivityUid",
        description="uid for the study activity",
        source="uid",
    )

    activity: Optional[Activity] = Field(
        ...,
        title="activity",
        description="the activity selected for the study",
    )

    flowchartGroup: Optional[CTTermName] = Field(
        None,
        title="flowchartGroup",
        description="flow chart group linked to this study activity",
    )

    note: Optional[str] = Field(
        None, title="note", description="Foot note to display in flowchart"
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )

    userInitials: Optional[str] = Field(
        ...,
        title="userInitials",
        description="User initials for the version",
        source="has_after.user_initials",
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyActivitySelectionHistory,
        study_uid: str,
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        get_activity_by_uid_version_callback: Callable[[str], Activity],
    ) -> "StudySelectionActivityCore":

        return cls(
            studyActivityUid=study_selection_history.study_selection_uid,
            order=study_selection_history.activity_order,
            showActivityGroupInProtocolFlowchart=study_selection_history.show_activity_group_in_protocol_flowchart,
            showActivitySubGroupInProtocolFlowchart=study_selection_history.show_activity_subgroup_in_protocol_flowchart,
            showActivityInProtocolFlowchart=study_selection_history.show_activity_in_protocol_flowchart,
            note=study_selection_history.note,
            studyUid=study_uid,
            flowchartGroup=get_ct_term_flowchart_group(
                study_selection_history.flowchart_group_uid
            ),
            startDate=study_selection_history.start_date,
            activity=get_activity_by_uid_version_callback(
                study_selection_history.activity_uid,
                study_selection_history.activity_version,
            ),
            endDate=study_selection_history.end_date,
            # status=study_selection_history.status,  FIXME
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
        )


class StudySelectionActivity(StudySelectionActivityCore):
    class Config:
        orm_mode = True

    latestActivity: Optional[Activity] = Field(
        None,
        title="latestActivity",
        description="Latest version of activity selected for study.",
    )
    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete activity versions",
    )

    @classmethod
    def from_study_selection_activity_ar_and_order(
        cls,
        study_selection_activity_ar: StudySelectionActivityAR,
        activity_order: int,
        get_activity_by_uid_callback: Callable[[str], Activity],
        get_activity_by_uid_version_callback: Callable[[str], Activity],
        get_ct_term_flowchart_group: Callable[[str], CTTermName],
        accepted_version: bool = False,
    ) -> "StudySelectionActivity":

        study_activity_selection = study_selection_activity_ar.study_objects_selection
        study_uid = study_selection_activity_ar.study_uid
        single_study_selection = study_activity_selection[activity_order - 1]
        study_activity_uid = single_study_selection.study_selection_uid
        activity_uid = single_study_selection.activity_uid

        flowchart_group = get_ct_term_flowchart_group(
            single_study_selection.flowchart_group_uid
        )

        assert activity_uid is not None
        latest_activity = get_activity_by_uid_callback(activity_uid)
        if (
            latest_activity
            and latest_activity.version == single_study_selection.activity_version
        ):
            selected_activity = latest_activity
            latest_activity = None
        else:
            selected_activity = get_activity_by_uid_version_callback(
                activity_uid, single_study_selection.activity_version
            )

        return cls(
            studyActivityUid=study_activity_uid,
            activity=selected_activity,
            latestActivity=latest_activity,
            order=activity_order,
            flowchartGroup=flowchart_group,
            showActivityGroupInProtocolFlowchart=single_study_selection.show_activity_group_in_protocol_flowchart,
            showActivitySubGroupInProtocolFlowchart=single_study_selection.show_activity_subgroup_in_protocol_flowchart,
            showActivityInProtocolFlowchart=single_study_selection.show_activity_in_protocol_flowchart,
            note=single_study_selection.note,
            acceptedVersion=accepted_version,
            studyUid=study_uid,
            startDate=single_study_selection.start_date,
            userInitials=single_study_selection.user_initials,
        )


class StudySelectionActivityCreateInput(BaseModel):
    flowchartGroupUid: str = Field(
        title="flowchartGroupUid",
        description="flowchart CT term uid",
    )
    activityUid: str = Field(title="activityUid", description="activity uid")
    activityInstanceUid: Optional[str] = Field(
        None, title="activityInstanceUid", description="activity instance uid"
    )


class StudySelectionActivityInput(CommonStudyActivity):
    flowchartGroupUid: Optional[str] = Field(
        title="flowchartGroupUid",
        description="flowchart CT term uid",
    )

    note: Optional[str] = Field(
        None, title="note", description="Foot note to display in flowchart"
    )


class StudySelectionActivityNewOrder(BaseModel):
    new_order: int = Field(
        ...,
        title="new_order",
        description="new order selected for the study activity",
    )


class StudySelectionActivityBatchUpdateInput(BaseModel):
    studyActivityUid: str = Field(
        ...,
        title="studyActivityUid",
        description="UID of the Study Activity to update",
    )
    content: StudySelectionActivityInput


class StudySelectionActivityBatchDeleteInput(BaseModel):
    studyActivityUid: str = Field(
        ...,
        title="studyActivityUid",
        description="UID of the study activity to delete",
    )


class StudySelectionActivityBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: Union[
        StudySelectionActivityBatchUpdateInput,
        StudySelectionActivityCreateInput,
        StudySelectionActivityBatchDeleteInput,
    ]


class StudySelectionActivityBatchOutput(BaseModel):
    responseCode: int = Field(
        ...,
        title="responseCode",
        description="The HTTP response code related to input operation",
    )
    content: Union[StudySelectionActivity, None, BatchErrorResponse]


#
# Study Activity Schedule
#


class StudyActivitySchedule(BaseModel):
    class Config:
        orm_mode = True

    studyUid: str = Field(
        ...,
        title="studyUid",
        description="The uid of the study",
        source="study_value.study_root.uid",
    )

    studyActivityScheduleUid: Optional[str] = Field(
        ...,
        title="studyActivityScheduleUid",
        description="uid for the study activity schedule",
        source="uid",
    )

    studyActivityUid: str = Field(
        title="studyActivityUid",
        description="The related study activity UID",
        source="study_activity.uid",
    )

    studyActivityName: Optional[str] = Field(
        title="studyActivityName",
        description="The related study activity name",
        source="study_activity.has_selected_activity.name",
    )

    studyVisitUid: str = Field(
        title="studyVisitUid",
        description="The related study visit UID",
        source="study_visit.uid",
    )

    studyVisitName: Optional[str] = Field(
        title="studyVisitName",
        description="The related study visit name",
        source="study_visit.has_visit_name.has_latest_value.name",
    )

    note: Optional[str] = Field(
        None, title="note", description="Foot note to display in flowchart"
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )

    userInitials: Optional[str] = Field(
        ...,
        title="userInitials",
        description="User initials for the version",
        source="has_after.user_initials",
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    @classmethod
    def from_vo(cls, schedule_vo: StudyActivityScheduleVO) -> "StudyActivitySchedule":
        return cls(
            studyActivityScheduleUid=schedule_vo.uid,
            studyUid=schedule_vo.study_uid,
            studyActivityUid=schedule_vo.study_activity_uid,
            studyActivityName=schedule_vo.study_activity_name,
            studyVisitUid=schedule_vo.study_visit_uid,
            studyVisitName=schedule_vo.study_visit_name,
            note=schedule_vo.note,
            startDate=schedule_vo.start_date,
            userInitials=schedule_vo.user_initials,
        )


class StudyActivityScheduleHistory(BaseModel):
    studyUid: str = Field(
        ...,
        title="studyUid",
        description="The uid of the study",
    )

    studyActivityScheduleUid: str = Field(
        ...,
        title="studyActivityScheduleUid",
        description="uid for the study activity schedule",
    )

    studyActivityUid: str = Field(
        ...,
        title="studyActivityUid",
        description="uid for the study activity",
    )

    studyVisitUid: str = Field(
        ...,
        title="studyVisitUid",
        description="uid for the study visit",
    )

    note: Optional[str] = Field(
        None, title="note", description="Foot note to display in flowchart"
    )

    modified: Optional[datetime] = Field(
        None, title="modified", description="Date of last modification"
    )


class StudyActivityScheduleCreateInput(BaseModel):

    studyActivityUid: str = Field(
        ..., title="studyActivityUid", description="The related study activity uid"
    )

    studyVisitUid: str = Field(
        ..., title="studyVisitUid", description="The related study visit uid"
    )

    note: Optional[str] = Field(None, title="note", description="A note")


class StudyActivityScheduleDeleteInput(BaseModel):
    uid: str = Field(
        ..., title="uid", description="UID of the study activity schedule to delete"
    )


class StudyActivityScheduleBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: Union[StudyActivityScheduleCreateInput, StudyActivityScheduleDeleteInput]


class StudyActivityScheduleBatchOutput(BaseModel):
    responseCode: int = Field(
        ...,
        title="responseCode",
        description="The HTTP response code related to input operation",
    )
    content: Union[StudyActivitySchedule, None, BatchErrorResponse]


"""
    Study design cells
"""


class StudyDesignCell(BaseModel):
    class Config:
        orm_mode = True

    studyUid: str = Field(
        ...,
        title="studyUid",
        description="The uid of the study",
        source="study_value.study_root.uid",
    )

    designCellUid: Optional[str] = Field(
        ..., title="designCellUid", description="uid for the study cell", source="uid"
    )

    studyArmUid: Optional[str] = Field(
        None,
        title="studyArmUid",
        description="the uid of the related study arm",
        source="study_arm.uid",
    )

    studyArmName: Optional[str] = Field(
        None,
        title="studyArmName",
        description="the name of the related study arm",
        source="study_arm.name",
    )

    studyBranchArmUid: Optional[str] = Field(
        None,
        title="studyBranchArmUid",
        description="the uid of the related study branch arm",
        source="study_branch_arm.uid",
    )

    studyBranchArmName: Optional[str] = Field(
        None,
        title="studyBranchArmName",
        description="the name of the related study branch arm",
        source="study_branch_arm.name",
    )

    studyEpochUid: str = Field(
        ...,
        title="studyEpochUid",
        description="the uid of the related study epoch",
        source="study_epoch.uid",
    )

    studyEpochName: str = Field(
        ...,
        title="studyEpochName",
        description="the name of the related study epoch",
        source="study_epoch.has_epoch.has_name_root.has_latest_value.name",
    )

    studyElementUid: str = Field(
        ...,
        title="studyElementUid",
        description="the uid of the related study element",
        source="study_element.uid",
    )

    studyElementName: str = Field(
        ...,
        title="studyElementName",
        description="the name of the related study element",
        source="study_element.name",
    )

    transitionRule: Optional[str] = Field(
        ...,
        title="transitionRule",
        description="transition rule for the cell",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )

    userInitials: Optional[str] = Field(
        ...,
        title="userInitials",
        description="User initials for the version",
        source="has_after.user_initials",
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    order: Optional[int] = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )

    @classmethod
    def from_vo(cls, design_cell_vo: StudyDesignCellVO) -> "StudyDesignCell":
        return cls(
            designCellUid=design_cell_vo.uid,
            studyUid=design_cell_vo.study_uid,
            studyArmUid=design_cell_vo.study_arm_uid,
            studyArmName=design_cell_vo.study_arm_name,
            studyBranchArmUid=design_cell_vo.study_branch_arm_uid,
            studyBranchArmName=design_cell_vo.study_branch_arm_name,
            studyEpochUid=design_cell_vo.study_epoch_uid,
            studyEpochName=design_cell_vo.study_epoch_name,
            studyElementUid=design_cell_vo.study_element_uid,
            studyElementName=design_cell_vo.study_element_name,
            transitionRule=design_cell_vo.transition_rule,
            startDate=design_cell_vo.start_date,
            userInitials=design_cell_vo.user_initials,
            order=design_cell_vo.order,
        )


class StudyDesignCellHistory(BaseModel):
    studyUid: str = Field(..., title="studyUid", description="The uid of the study")

    studyDesignCellUid: str = Field(
        ..., title="studyDesignCellUid", description="uid for the study design cell"
    )

    studyArmUid: Optional[str] = Field(
        None, title="studyArmUid", description="the uid of the related study arm"
    )

    studyBranchArmUid: Optional[str] = Field(
        None,
        title="studyBranchArmUid",
        description="the uid of the related study branch arm",
    )

    studyEpochUid: str = Field(
        ..., title="studyEpochUid", description="the uid of the related study epoch"
    )

    studyElementUid: str = Field(
        None,
        title="studyElementUid",
        description="the uid of the related study element",
    )

    transitionRule: str = Field(
        None, title="transitionRule", description="transition rule for the cell"
    )

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    modified: Optional[datetime] = Field(
        None, title="modified", description="Date of last modification"
    )

    order: Optional[int] = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )


class StudyDesignCellVersion(StudyDesignCellHistory):
    changes: Dict


class StudyDesignCellCreateInput(BaseModel):
    studyArmUid: Optional[str] = Field(
        None, title="studyArmUid", description="the uid of the related study arm"
    )

    studyBranchArmUid: Optional[str] = Field(
        None,
        title="studyBranchArmUid",
        description="the uid of the related study branch arm",
    )

    studyEpochUid: str = Field(
        ..., title="studyEpochUid", description="the uid of the related study epoch"
    )

    studyElementUid: str = Field(
        ..., title="studyElementUid", description="the uid of the related study element"
    )

    transitionRule: Optional[str] = Field(
        None,
        title="transitionRule",
        description="Optionally, a transition rule for the cell",
    )

    order: Optional[int] = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )


class StudyDesignCellEditInput(BaseModel):
    studyDesignCellUid: str = Field(
        ..., title="studyDesignCellUid", description="uid for the study design cell"
    )
    studyArmUid: Optional[str] = Field(
        None, title="studyArmUid", description="the uid of the related study arm"
    )
    studyBranchArmUid: Optional[str] = Field(
        None,
        title="studyBranchArmUid",
        description="the uid of the related study branch arm",
    )
    studyElementUid: Optional[str] = Field(
        None,
        title="studyElementUid",
        description="the uid of the related study element",
    )
    order: Optional[int] = Field(
        None,
        title="order",
        description="The ordering of the selection",
    )
    transitionRule: Optional[str] = Field(
        None,
        title="transitionRule",
        description="transition rule for the cell",
    )


class StudyDesignCellDeleteInput(BaseModel):
    uid: str = Field(
        ..., title="uid", description="UID of the study design cell to delete"
    )


class StudyDesignCellBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: Union[
        StudyDesignCellCreateInput, StudyDesignCellDeleteInput, StudyDesignCellEditInput
    ]


class StudyDesignCellBatchOutput(BaseModel):
    responseCode: int = Field(
        ...,
        title="responseCode",
        description="The HTTP response code related to input operation",
    )
    content: Union[StudyDesignCell, None, BatchErrorResponse]


"""
    Study brancharms without ArmRoot
"""


class StudySelectionBranchArmWithoutStudyArm(StudySelection):
    branchArmUid: Optional[str] = Field(
        ...,
        title="studyBranchArmUid",
        description="uid for the study BranchArm",
    )

    name: str = Field(
        ...,
        title="studyBranchArmName",
        description="name for the study Brancharm",
    )

    shortName: str = Field(
        ...,
        title="studyBranchArmShortName",
        description="short name for the study Brancharm",
    )

    code: Optional[str] = Field(
        ...,
        title="studyBranchArmCode",
        description="code for the study Brancharm",
    )

    description: Optional[str] = Field(
        ...,
        title="studyBranchArmDescription",
        description="description for the study Brancharm",
    )

    colourCode: Optional[str] = Field(
        ...,
        title="studyBranchArmcolourCode",
        description="colourCode for the study Brancharm",
    )

    randomizationGroup: Optional[str] = Field(
        ...,
        title="studyBranchArmRandomizationGroup",
        description="randomization group for the study Brancharm",
    )

    numberOfSubjects: Optional[int] = Field(
        ...,
        title="studyBranchArmNumberOfSubjects",
        description="number of subjects for the study Brancharm",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete endpoint and timeframe versions",
    )

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
    ):
        return cls(
            studyUid=study_uid,
            branchArmUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            colourCode=selection.colour_code,
            order=order,
            randomizationGroup=selection.randomization_group,
            numberOfSubjects=selection.number_of_subjects,
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )


"""
    Study arms
"""


class StudySelectionArm(StudySelection):
    armUid: Optional[str] = Field(
        ...,
        title="studyArmUid",
        description="uid for the study arm",
    )

    name: str = Field(
        ...,
        title="studyArmName",
        description="name for the study arm",
    )

    shortName: str = Field(
        ...,
        title="studyArmShortName",
        description="short name for the study arm",
    )

    code: Optional[str] = Field(
        ...,
        title="studyArmCode",
        description="code for the study arm",
    )

    description: Optional[str] = Field(
        ...,
        title="studyArmDescription",
        description="description for the study arm",
    )

    armColour: Optional[str] = Field(
        ...,
        title="studyArmColour",
        description="colour for the study arm",
    )

    randomizationGroup: Optional[str] = Field(
        ...,
        title="studyArmRandomizationGroup",
        description="randomization group for the study arm",
    )

    numberOfSubjects: Optional[int] = Field(
        ...,
        title="studyArmNumberOfSubjects",
        description="number of subjects for the study arm",
    )

    armType: Optional[CTTermName] = Field(
        ..., title="studyArmType", description="type for the study arm"
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete endpoint and timeframe versions",
    )

    @classmethod
    def from_study_selection_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
    ):
        if selection.arm_type_uid:
            armTypeCallBack = find_simple_term_arm_type_by_term_uid(
                selection.arm_type_uid
            )
        else:
            armTypeCallBack = None

        return cls(
            studyUid=study_uid,
            armUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            armColour=selection.arm_colour,
            order=order,
            randomizationGroup=selection.randomization_group,
            numberOfSubjects=selection.number_of_subjects,
            armType=armTypeCallBack,
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryArm,
        study_uid: str,
        get_ct_term_arm_type: Callable[[str], CTTermName],
    ) -> "StudySelectionArm":

        if study_selection_history.arm_type:
            armTypeCallBack = get_ct_term_arm_type(study_selection_history.arm_type)
        else:
            armTypeCallBack = None

        return cls(
            studyUid=study_uid,
            order=study_selection_history.order,
            armUid=study_selection_history.study_selection_uid,
            name=study_selection_history.arm_name,
            shortName=study_selection_history.arm_short_name,
            code=study_selection_history.arm_code,
            description=study_selection_history.arm_description,
            armColour=study_selection_history.arm_colour,
            randomizationGroup=study_selection_history.arm_randomization_group,
            numberOfSubjects=study_selection_history.arm_number_of_subjects,
            armType=armTypeCallBack,
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            acceptedVersion=study_selection_history.accepted_version,
        )


class StudySelectionArmWithConnectedBranchArms(StudySelectionArm):

    armConnectedBranchArms: Optional[
        Sequence[StudySelectionBranchArmWithoutStudyArm]
    ] = Field(
        None,
        title="studyBranchArms",
        description="lsit of study branch arms connected to arm",
    )

    @classmethod
    def from_study_selection_arm_ar__order__connected_branch_arms(
        cls,
        study_uid: str,
        selection: StudySelectionArmVO,
        order: int,
        find_simple_term_arm_type_by_term_uid: Callable,
        find_multiple_connected_branch_arm: Callable,
    ):
        if selection.arm_type_uid:
            armTypeCallBack = find_simple_term_arm_type_by_term_uid(
                selection.arm_type_uid
            )
        else:
            armTypeCallBack = None

        return cls(
            studyUid=study_uid,
            armUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            armColour=selection.arm_colour,
            order=order,
            randomizationGroup=selection.randomization_group,
            numberOfSubjects=selection.number_of_subjects,
            armType=armTypeCallBack,
            armConnectedBranchArms=find_multiple_connected_branch_arm(
                study_uid=study_uid,
                study_arm_uid=selection.study_selection_uid,
                user_initials=selection.user_initials,
            ),
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )


class StudySelectionArmCreateInput(BaseModel):

    name: str = Field(
        None,
        title="studyArmName",
        description="name for the study arm",
    )

    shortName: str = Field(
        None,
        title="studyArmShortName",
        description="short name for the study arm",
    )

    code: Optional[str] = Field(
        None,
        title="studyArmCode",
        description="code for the study arm",
    )

    description: Optional[str] = Field(
        None,
        title="studyDescription",
        description="description for the study arm",
    )

    armColour: Optional[str] = Field(
        None,
        title="studyArmColour",
        description="colour for the study arm",
    )

    randomizationGroup: Optional[str] = Field(
        None,
        title="studyArmRandomizationGroup",
        description="randomization group for the study arm",
    )

    numberOfSubjects: Optional[int] = Field(
        None,
        title="studyArmNumberOfSubjects",
        description="number of subjects for the study arm",
    )

    armTypeUid: Optional[str] = Field(
        None,
        title="studyArmTypeUid",
        description="uid for the study arm",
    )


class StudySelectionArmInput(StudySelectionArmCreateInput):

    armUid: str = Field(
        None,
        title="studyArmUid",
        description="uid for the study arm",
    )


class StudySelectionArmNewOrder(BaseModel):

    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected arm",
    )


class StudySelectionArmVersion(StudySelectionArm):
    changes: Dict


# Study Activity Instructions


class StudyActivityInstruction(BaseModel):
    class Config:
        orm_mode = True

    studyActivityInstructionUid: Optional[str] = Field(
        ...,
        title="studyActivityInstructionUid",
        description="uid for the study activity instruction",
        source="uid",
    )

    studyUid: str = Field(
        ...,
        title="studyUid",
        description="The uid of the study",
        source="study_value.study_root.uid",
    )

    studyActivityUid: Optional[str] = Field(
        ...,
        title="studyActivityUid",
        description="uid for the study activity",
        source="study_activity.uid",
    )

    activityInstructionUid: str = Field(
        title="activityInstructionUid",
        description="The related activity instruction UID",
        source="activity_instruction_value.activity_instruction_root.uid",
    )

    activityInstructionName: str = Field(
        title="activityInstructionName",
        description="The related activity instruction name",
        source="activity_instruction_value.name",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
        source="has_after.date",
    )

    userInitials: Optional[str] = Field(
        ...,
        title="userInitials",
        description="User initials for the version",
        source="has_after.user_initials",
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    @classmethod
    def from_vo(
        cls, instruction_vo: StudyActivityInstructionVO
    ) -> "StudyActivityInstruction":
        return cls(
            studyActivityInstructionUid=instruction_vo.uid,
            studyUid=instruction_vo.study_uid,
            studyActivityUid=instruction_vo.study_activity_uid,
            activityInstructionName=instruction_vo.activity_instruction_name,
            activityInstructionUid=instruction_vo.activity_instruction_uid,
            startDate=instruction_vo.start_date,
            userInitials=instruction_vo.user_initials,
        )


class StudyActivityInstructionCreateInput(BaseModel):
    activityInstructionData: Optional[ActivityInstructionCreateInput] = Field(
        None,
        title="activityInstructionData",
        description="Data to create new activity instruction",
    )

    activityInstructionUid: Optional[str] = Field(
        None,
        title="activityInstructionUid",
        description="The uid of an existing activity instruction",
    )

    studyActivityUid: str = Field(
        ..., title="studyActivityUid", description="uid for the study activity"
    )

    @root_validator(pre=False)
    @classmethod
    def check_required_fields(cls, values):
        data, uid = values.get("activityInstructionData"), values.get(
            "activityInstructionUid"
        )
        if not data and not uid:
            raise ValueError(
                "You must provide activityInstructionData or activityInstructionUid"
            )
        return values


class StudyActivityInstructionDeleteInput(BaseModel):
    studyActivityInstructionUid: Optional[str] = Field(
        ...,
        title="studyActivityInstructionUid",
        description="uid for the study activity instruction",
        source="uid",
    )


class StudyActivityInstructionBatchInput(BaseModel):
    method: str = Field(
        ..., title="method", description="HTTP method corresponding to operation type"
    )
    content: Union[
        StudyActivityInstructionCreateInput, StudyActivityInstructionDeleteInput
    ]


class StudyActivityInstructionBatchOutput(BaseModel):
    responseCode: int = Field(
        ...,
        title="responseCode",
        description="The HTTP response code related to input operation",
    )
    content: Union[StudyActivityInstruction, None, BatchErrorResponse]


"""
    Study elements
"""


class StudySelectionElement(StudySelection):
    elementUid: Optional[str] = Field(
        ...,
        title="studyElementUid",
        description="uid for the study element",
    )

    name: Optional[str] = Field(
        ...,
        title="studyElementName",
        description="name for the study element",
    )

    shortName: Optional[str] = Field(
        ...,
        title="studyElementShortName",
        description="short name for the study element",
    )

    code: Optional[str] = Field(
        ...,
        title="studyElementCode",
        description="code for the study element",
    )

    description: Optional[str] = Field(
        ...,
        title="studyElementDescription",
        description="description for the study element",
    )

    plannedDuration: Optional[DurationJsonModel] = Field(
        ...,
        title="studyElementPlannedDuration",
        description="planned_duration for the study element",
    )

    startRule: Optional[str] = Field(
        ...,
        title="studyElementStartRule",
        description="start_rule for the study element",
    )

    endRule: Optional[str] = Field(
        ...,
        title="studyElementEndRule",
        description="end_rule for the study element",
    )

    elementColour: Optional[str] = Field(
        ...,
        title="studyElementelementColour",
        description="elementColour for the study element",
    )

    elementSubType: Optional[CTTermName] = Field(
        ..., title="studyElementSubType", description="subtype for the study element"
    )

    studyCompoundDosingCount: Optional[int] = Field(
        None, description="Number of compound dosing linked to Study Element"
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete endpoint and timeframe versions",
    )

    @classmethod
    def from_study_selection_element_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionElementVO,
        order: int,
        find_simple_term_element_subtype_by_term_uid: Callable,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> "StudySelectionElement":
        return cls(
            studyUid=study_uid,
            elementUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            plannedDuration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            startRule=selection.start_rule,
            endRule=selection.end_rule,
            elementColour=selection.element_colour,
            order=order,
            elementSubType=find_simple_term_element_subtype_by_term_uid(
                selection.element_subtype_uid
            ),
            studyCompoundDosingCount=selection.study_compound_dosing_count,
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryElement,
        study_uid: str,
        get_ct_term_element_subtype: Callable[[str], CTTermName],
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> "StudySelectionElement":
        return cls(
            studyUid=study_uid,
            order=study_selection_history.order,
            elementUid=study_selection_history.study_selection_uid,
            name=study_selection_history.element_name,
            shortName=study_selection_history.element_short_name,
            code=study_selection_history.element_code,
            description=study_selection_history.element_description,
            plannedDuration=(
                DurationJsonModel.from_duration_object(
                    duration=study_selection_history.element_planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if study_selection_history.element_planned_duration is not None
                else None
            ),
            startRule=study_selection_history.element_start_rule,
            endRule=study_selection_history.element_end_rule,
            elementColour=study_selection_history.element_colour,
            elementSubType=get_ct_term_element_subtype(
                study_selection_history.element_subtype
            ),
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            acceptedVersion=study_selection_history.accepted_version,
        )


class StudySelectionElementCreateInput(BaseModel):

    name: str = Field(
        None,
        title="studyElementName",
        description="name for the study element",
    )

    shortName: str = Field(
        None,
        title="studyElementShortName",
        description="short name for the study element",
    )

    code: Optional[str] = Field(
        None,
        title="studyElementCode",
        description="code for the study element",
    )

    description: Optional[str] = Field(
        None,
        title="studyDescription",
        description="description for the study element",
    )

    plannedDuration: Optional[DurationJsonModel] = Field(
        None,
        title="studyElementPlannedDuration",
        description="planned_duration for the study element",
    )

    startRule: Optional[str] = Field(
        None,
        title="studyElementStartRule",
        description="start_rule for the study element",
    )

    endRule: Optional[str] = Field(
        None,
        title="studyElementEndRule",
        description="end_rule for the study element",
    )

    elementColour: Optional[str] = Field(
        None,
        title="studyelementColour",
        description="element_colour for the study element",
    )

    elementSubTypeUid: str = Field(
        None,
        title="studyElementSubTypeUid",
        description="uid for the study element",
    )


class StudySelectionElementInput(StudySelectionElementCreateInput):

    elementUid: str = Field(
        None,
        title="studyElementUid",
        description="uid for the study element",
    )

    @classmethod
    def from_study_selection_element(
        cls,
        selection: StudySelectionElementVO,
        find_all_study_time_units: Callable[[str], Iterable[UnitDefinitionAR]],
    ) -> "StudySelectionElementInput":
        return cls(
            elementUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            plannedDuration=(
                DurationJsonModel.from_duration_object(
                    duration=selection.planned_duration,
                    find_all_study_time_units=find_all_study_time_units,
                )
                if selection.planned_duration is not None
                else None
            ),
            startRule=selection.start_rule,
            endRule=selection.end_rule,
            elementColour=selection.element_colour,
            elementSubTypeUid=selection.element_subtype_uid,
        )


class StudyElementTypes(BaseModel):
    type: str = Field(..., title="Type uid", description="Element type uid")
    type_name: str = Field(..., title="Type name", description="Element type name")
    subtype: str = Field(..., title="Subtype", description="Element subtype uid")
    subtype_name: str = Field(
        ..., title="Subtype name", description="Element subtype name"
    )


class StudySelectionElementNewOrder(BaseModel):

    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected element",
    )


class StudySelectionElementVersion(StudySelectionElement):
    changes: Dict


"""
    Study brancharms adding Arm Root parameter
"""


class StudySelectionBranchArm(StudySelectionBranchArmWithoutStudyArm):

    armRoot: StudySelectionArm = Field(
        ..., title="studyArmRoot", description="Root for the study branch arm"
    )

    @classmethod
    def from_study_selection_branch_arm_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionBranchArmVO,
        order: int,
        find_simple_term_branch_arm_root_by_term_uid: Callable,
    ):
        return cls(
            studyUid=study_uid,
            branchArmUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            colourCode=selection.colour_code,
            order=order,
            randomizationGroup=selection.randomization_group,
            numberOfSubjects=selection.number_of_subjects,
            armRoot=find_simple_term_branch_arm_root_by_term_uid(
                study_uid, selection.arm_root_uid
            ),
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
        find_simple_term_branch_arm_root_by_term_uid: Callable[[str], CTTermName],
    ) -> "StudySelectionBranchArm":
        return cls(
            studyUid=study_uid,
            order=study_selection_history.order,
            branchArmUid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            shortName=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colourCode=study_selection_history.branch_arm_colour_code,
            randomizationGroup=study_selection_history.branch_arm_randomization_group,
            numberOfSubjects=study_selection_history.branch_arm_number_of_subjects,
            armRoot=find_simple_term_branch_arm_root_by_term_uid(
                study_uid, study_selection_history.arm_root
            ),
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            acceptedVersion=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmHistory(StudySelectionBranchArmWithoutStudyArm):
    """
    Class created to describe Study BranchArm History, it specifies the ArmRootUid instead of ArmRoot to handle non longer existent Arms
    """

    armRootUid: str = Field(
        ..., title="studyArmRootUid", description="Uid Root for the study branch arm"
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryBranchArm,
        study_uid: str,
    ) -> "StudySelectionBranchArmHistory":
        return cls(
            studyUid=study_uid,
            order=study_selection_history.order,
            branchArmUid=study_selection_history.study_selection_uid,
            name=study_selection_history.branch_arm_name,
            shortName=study_selection_history.branch_arm_short_name,
            code=study_selection_history.branch_arm_code,
            description=study_selection_history.branch_arm_description,
            colourCode=study_selection_history.branch_arm_colour_code,
            randomizationGroup=study_selection_history.branch_arm_randomization_group,
            numberOfSubjects=study_selection_history.branch_arm_number_of_subjects,
            armRootUid=study_selection_history.arm_root,
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            acceptedVersion=study_selection_history.accepted_version,
        )


class StudySelectionBranchArmCreateInput(BaseModel):

    name: str = Field(
        None,
        title="studyBranchArmName",
        description="name for the study Brancharm",
    )

    shortName: str = Field(
        None,
        title="studyBranchArmShortName",
        description="short name for the study Brancharm",
    )

    code: Optional[str] = Field(
        None,
        title="studyBranchArmCode",
        description="code for the study Brancharm",
    )

    description: Optional[str] = Field(
        None,
        title="studyDescription",
        description="description for the study Brancharm",
    )

    colourCode: Optional[str] = Field(
        None,
        title="studycolourCode",
        description="colourCode for the study Brancharm",
    )

    randomizationGroup: Optional[str] = Field(
        None,
        title="studyBranchArmRandomizationGroup",
        description="randomization group for the study Brancharm",
    )

    numberOfSubjects: Optional[int] = Field(
        None,
        title="studyBranchArmNumberOfSubjects",
        description="number of subjects for the study Brancharm",
    )

    armUid: str = Field(
        None,
        title="studyArmtUid",
        description="uid for the study arm",
    )


class StudySelectionBranchArmEditInput(StudySelectionBranchArmCreateInput):

    branchArmUid: str = Field(
        None,
        title="studyBranchArmUid",
        description="uid for the study branch arm",
    )


class StudySelectionBranchArmNewOrder(BaseModel):

    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected branch arm",
    )


class StudySelectionBranchArmVersion(StudySelectionBranchArmHistory):
    changes: Dict


"""
    Study cohorts
"""


class StudySelectionCohortWithoutArmBranArmRoots(StudySelection):
    cohortUid: Optional[str] = Field(
        ...,
        title="studyCohortUid",
        description="uid for the study Cohort",
    )

    name: str = Field(
        ...,
        title="studyCohortName",
        description="name for the study Cohort",
    )

    shortName: str = Field(
        ...,
        title="studyCohortShortName",
        description="short name for the study Cohort",
    )

    code: Optional[str] = Field(
        None,
        title="studyCohortCode",
        description="code for the study Cohort",
    )

    description: Optional[str] = Field(
        ...,
        title="studyCohortDescription",
        description="description for the study Cohort",
    )

    colourCode: Optional[str] = Field(
        ...,
        title="studyCohortColourCode",
        description="colour code for the study Cohort",
    )

    numberOfSubjects: Optional[int] = Field(
        ...,
        title="studyCohortNumberOfSubjects",
        description="number of subjects for the study Cohort",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )

    status: Optional[str] = Field(None, title="status", description="Change status")

    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    acceptedVersion: Optional[bool] = Field(
        None,
        title="Accepted Version",
        description="Denotes if user accepted obsolete endpoint and timeframe versions",
    )


class StudySelectionCohort(StudySelectionCohortWithoutArmBranArmRoots):

    branchArmRoots: Optional[Sequence[StudySelectionBranchArm]] = Field(
        None,
        title="studyBranchArmRoots",
        description="Branch Arm Roots for the study Cohort",
    )

    armRoots: Optional[Sequence[StudySelectionArm]] = Field(
        None, title="studyArmRoots", description="ArmRoots for the study Cohort"
    )

    @classmethod
    def from_study_selection_cohort_ar_and_order(
        cls,
        study_uid: str,
        selection: StudySelectionCohortVO,
        order: int,
        find_arm_root_by_uid: Callable = None,
        find_branch_arm_root_cohort_by_uid: Union[Callable, None] = None,
    ):

        """
        Factory method
        :param study_uid
        :param selection
        :param order
        :param find_project_by_study_uid
        :param find_arm_root_by_uid
        :param find_branch_arm_root_cohort_by_uid
        :return:
        """
        if selection.branch_arm_root_uids:
            branchArmRoots = [
                find_branch_arm_root_cohort_by_uid(study_uid, branch_arm_root_uid)
                for branch_arm_root_uid in selection.branch_arm_root_uids
            ]
        else:
            branchArmRoots = None

        if selection.arm_root_uids:
            armRoots = [
                find_arm_root_by_uid(study_uid, arm_root_uid)
                for arm_root_uid in selection.arm_root_uids
            ]
        else:
            armRoots = None

        return cls(
            studyUid=study_uid,
            cohortUid=selection.study_selection_uid,
            name=selection.name,
            shortName=selection.short_name,
            code=selection.code,
            description=selection.description,
            order=order,
            colourCode=selection.colour_code,
            numberOfSubjects=selection.number_of_subjects,
            branchArmRoots=branchArmRoots,
            armRoots=armRoots,
            startDate=selection.start_date,
            userInitials=selection.user_initials,
            endDate=selection.end_date,
            status=selection.status,
            changeType=selection.change_type,
            acceptedVersion=selection.accepted_version,
        )


class StudySelectionCohortHistory(StudySelectionCohortWithoutArmBranArmRoots):

    branchArmRootsUids: Optional[Sequence[str]] = Field(
        None,
        title="studyBranchArmRootsUids",
        description="Branch Arm Roots Uids for the study Cohort",
    )

    armRootsUids: Optional[Sequence[str]] = Field(
        None,
        title="studyArmRootsUids",
        description="ArmRoots Uids for the study Cohort",
    )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: SelectionHistoryCohort,
        study_uid: str,
    ) -> "StudySelectionCohortHistory":

        if study_selection_history.branch_arm_roots:
            branchArmRootsUids = study_selection_history.branch_arm_roots
        else:
            branchArmRootsUids = None

        if study_selection_history.arm_roots:
            armRootsUids = study_selection_history.arm_roots
        else:
            armRootsUids = None

        return cls(
            studyUid=study_uid,
            order=study_selection_history.order,
            cohortUid=study_selection_history.study_selection_uid,
            name=study_selection_history.cohort_name,
            shortName=study_selection_history.cohort_short_name,
            code=study_selection_history.cohort_code,
            description=study_selection_history.cohort_description,
            colourCode=study_selection_history.cohort_colour_code,
            numberOfSubjects=study_selection_history.cohort_number_of_subjects,
            branchArmRootsUids=branchArmRootsUids,
            armRootsUids=armRootsUids,
            startDate=study_selection_history.start_date,
            userInitials=study_selection_history.user_initials,
            endDate=study_selection_history.end_date,
            status=study_selection_history.status,
            changeType=study_selection_history.change_type,
            acceptedVersion=study_selection_history.accepted_version,
        )


class StudySelectionCohortCreateInput(BaseModel):

    name: str = Field(
        None,
        title="studyCohortName",
        description="name for the study Cohort",
    )

    shortName: str = Field(
        None,
        title="studyCohortShortName",
        description="short name for the study Cohort",
    )

    code: Optional[str] = Field(
        None,
        title="studyCohortCode",
        description="code for the study Cohort",
    )

    description: Optional[str] = Field(
        None,
        title="studyDescription",
        description="description for the study Cohort",
    )

    colourCode: Optional[str] = Field(
        None,
        title="studyCohortColourCode",
        description="colour code for the study Cohort",
    )

    numberOfSubjects: Optional[int] = Field(
        None,
        title="studyCohortNumberOfSubjects",
        description="number of subjects for the study Cohort",
    )

    branchArmUids: Optional[Sequence[str]] = Field(
        None,
        title="studybranchArmUid",
        description="uid for the study branch arm",
    )

    armUids: Optional[Sequence[str]] = Field(
        None,
        title="studyArmtUid",
        description="uid for the study arm",
    )


class StudySelectionCohortEditInput(StudySelectionCohortCreateInput):

    cohortUid: str = Field(
        None,
        title="studyCohortUid",
        description="uid for the study Cohort",
    )


class StudySelectionCohortNewOrder(BaseModel):

    new_order: int = Field(
        ...,
        title="new_order",
        description="new order of the selected Cohort",
    )


class StudySelectionCohortVersion(StudySelectionCohortHistory):
    changes: Dict


#
# Study compound dosing
#


class StudyCompoundDosing(StudySelection):

    studyCompoundDosingUid: Optional[str] = Field(
        ...,
        title="studyCompoundDosingUid",
        description="uid for the study compound dosing",
    )

    studyCompound: StudySelectionCompound = Field(
        ..., title="studyCompound", description="The related study compound"
    )

    studyElement: StudySelectionElement = Field(
        ..., title="studyElement", description="The related study element"
    )

    doseValue: Optional[SimpleNumericValueWithUnit] = Field(
        None,
        title="dose",
        description="compound dose defined for the study selection",
    )

    doseFrequency: Optional[SimpleTermModel] = Field(
        None,
        title="doseFrequency",
        description="dose frequency defined for the study selection",
    )

    startDate: Optional[datetime] = Field(
        ...,
        title="startDate",
        description="The most recent point in time when the study selection was edited."
        "The format is ISO 8601 in UTC±0, e.g.: '2020-10-31T16:00:00+00:00' for October 31, 2020 at 6pm in UTC+2 timezone.",
    )

    userInitials: Optional[str] = Field(
        ..., title="userInitials", description="User initials for the version"
    )

    endDate: Optional[datetime] = Field(
        None, title="endDate", description="Start date for the version"
    )
    changeType: Optional[str] = Field(
        None, title="changeType", description="Type of last change for the version"
    )

    @classmethod
    def from_vo(
        cls,
        compound_dosing_vo: StudyCompoundDosingVO,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_numeric_value_by_uid: Callable[[str], Optional[NumericValueWithUnitAR]],
    ) -> "StudyCompoundDosing":
        return cls(
            order=order,
            studyCompoundDosingUid=compound_dosing_vo.study_selection_uid,
            studyUid=compound_dosing_vo.study_uid,
            studyCompound=study_compound_model,
            studyElement=study_element_model,
            doseValue=SimpleNumericValueWithUnit.from_concept_uid(
                uid=compound_dosing_vo.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            doseFrequency=find_simple_term_model_name_by_term_uid(
                compound_dosing_vo.dose_frequency_uid
            ),
            startDate=compound_dosing_vo.start_date,
            userInitials=compound_dosing_vo.user_initials,
        )

    @classmethod
    def from_study_selection_history(
        cls,
        study_selection_history: StudyCompoundDosingSelectionHistory,
        study_uid: str,
        order: int,
        study_compound_model: StudySelectionCompound,
        study_element_model: StudySelectionElement,
        find_simple_term_model_name_by_term_uid: Callable,
        find_unit_by_uid: Callable[[str], Optional[UnitDefinitionAR]],
        find_numeric_value_by_uid: Callable[[str], Optional[NumericValueWithUnitAR]],
    ) -> "StudyCompoundDosing":
        return cls(
            studyCompoundDosingUid=study_selection_history.study_selection_uid,
            studyUid=study_uid,
            order=order,
            studyCompound=study_compound_model,
            studyElement=study_element_model,
            doseValue=SimpleNumericValueWithUnit.from_concept_uid(
                uid=study_selection_history.dose_value_uid,
                find_unit_by_uid=find_unit_by_uid,
                find_numeric_value_by_uid=find_numeric_value_by_uid,
            ),
            doseFrequency=find_simple_term_model_name_by_term_uid(
                study_selection_history.dose_frequency_uid
            ),
            startDate=study_selection_history.start_date,
            endDate=study_selection_history.end_date,
            changeType=study_selection_history.change_type,
            userInitials=study_selection_history.user_initials,
        )


class StudyCompoundDosingInput(BaseModel):

    studyCompoundUid: str = Field(
        ..., title="studyCompoundUid", description="The related study compound uid"
    )

    studyElementUid: str = Field(
        ..., title="studyElementUid", description="The related study element uid"
    )

    doseValueUid: Optional[str] = Field(
        None,
        title="doseValueUid",
        description="compound dose defined for the study selection",
    )

    doseFrequencyUid: Optional[str] = Field(
        None,
        title="doseFrequencyUid",
        description="dose frequency defined for the study selection",
    )
