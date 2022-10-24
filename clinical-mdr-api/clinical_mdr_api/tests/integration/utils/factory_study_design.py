from clinical_mdr_api.models.study_selection import (
    DurationJsonModel,
    StudyDesignCellCreateInput,
    StudySelectionArmCreateInput,
    StudySelectionBranchArmCreateInput,
    StudySelectionBranchArmEditInput,
    StudySelectionCohortCreateInput,
    StudySelectionElementCreateInput,
)
from clinical_mdr_api.models.unit_definition import UnitDefinitionSimpleModel
from clinical_mdr_api.services.ct_term import CTTermService
from clinical_mdr_api.services.study_arm_selection import StudyArmSelectionService
from clinical_mdr_api.services.study_branch_arm_selection import (
    StudyBranchArmSelectionService,
)
from clinical_mdr_api.services.study_cohort_selection import StudyCohortSelectionService
from clinical_mdr_api.services.study_design_cell import StudyDesignCellService
from clinical_mdr_api.services.study_element_selection import (
    StudyElementSelectionService,
)


def create_study_element(element_sub_type_uid: str, study_uid: str):
    study_selection_element_create_input = StudySelectionElementCreateInput(
        name="Element_Name_1",
        shortName="Element_Short_Name_1",
        code="Element_code_1",
        description="desc...",
        elementSubTypeUid=element_sub_type_uid,
    )
    item = StudyElementSelectionService(author="test").make_selection(
        study_uid, selection_create_input=study_selection_element_create_input
    )
    return item


def add_parent_ctTerm(element_subtype_term_uid1, element_type_term_uid1):
    CTTermService().add_parent(
        term_uid=element_subtype_term_uid1,
        parent_uid=element_type_term_uid1,
        relationship_type="type",
    )


def create_study_element_with_planned_duration(
    element_sub_type_uid: str, study_uid: str, unit_definition_uid: str
):

    study_selection_element_create_input = StudySelectionElementCreateInput(
        name="Element_Name_1",
        shortName="Element_Short_Name_1",
        code="Element_code_1",
        description="desc...",
        startRule="start_rule",
        endRule="stop_rule",
        plannedDuration=DurationJsonModel(
            durationValue=70,
            durationUnitCode=UnitDefinitionSimpleModel(uid=unit_definition_uid),
        ),
        elementSubTypeUid=element_sub_type_uid,
    )
    item = StudyElementSelectionService(author="test").make_selection(
        study_uid, selection_create_input=study_selection_element_create_input
    )
    return item


def create_study_arm(
    study_uid: str,
    name,
    shortName,
    code,
    description,
    colourCode,
    randomizationGroup,
    numberOfSubjects,
    armTypeUid,
):
    study_selection_arm_create_input = StudySelectionArmCreateInput(
        name=name,
        shortName=shortName,
        code=code,
        description=description,
        colourCode=colourCode,
        randomizationGroup=randomizationGroup,
        numberOfSubjects=numberOfSubjects,
        armTypeUid=armTypeUid,
    )
    item = StudyArmSelectionService(author="test").make_selection(
        study_uid, selection_create_input=study_selection_arm_create_input
    )
    return item


def create_study_branch_arm(
    study_uid: str,
    name,
    shortName,
    code,
    description,
    colourCode,
    randomizationGroup,
    numberOfSubjects,
    armUid,
):
    study_selection_branch_arm_create_input = StudySelectionBranchArmCreateInput(
        name=name,
        shortName=shortName,
        code=code,
        description=description,
        colourCode=colourCode,
        randomizationGroup=randomizationGroup,
        numberOfSubjects=numberOfSubjects,
        armUid=armUid,
    )
    item = StudyBranchArmSelectionService(author="test").make_selection(
        study_uid, selection_create_input=study_selection_branch_arm_create_input
    )
    return item


def patch_study_branch_arm(branch_arm_uid: str, study_uid: str):
    study_selection_branch_arm_edit_input = StudySelectionBranchArmEditInput(
        branchArmUid=branch_arm_uid,
        name="Branch_Arm_Name_1_edit",
    )
    item = StudyBranchArmSelectionService(author="test").patch_selection(
        study_uid=study_uid,
        selection_update_input=study_selection_branch_arm_edit_input,
    )
    return item


def create_study_cohort(
    study_uid: str,
    name,
    shortName,
    code,
    description,
    colourCode,
    numberOfSubjects,
    armUids,
):
    study_selection_cohort_create_input = StudySelectionCohortCreateInput(
        name=name,
        shortName=shortName,
        code=code,
        description=description,
        colourCode=colourCode,
        numberOfSubjects=numberOfSubjects,
        armUids=armUids,
    )
    item = StudyCohortSelectionService(author="test").make_selection(
        study_uid, selection_create_input=study_selection_cohort_create_input
    )
    return item


def create_study_design_cell(
    study_element_uid: str,
    study_arm_uid: str,
    study_epoch_uid: str,
    study_uid: str,
):
    study_design_cell_create_input = StudyDesignCellCreateInput(
        studyArmUid=study_arm_uid,
        studyEpochUid=study_epoch_uid,
        studyElementUid=study_element_uid,
        transitionRule="Transition_Rule_1",
    )
    # Create a design cell -- Arm Specified
    item = StudyDesignCellService(author="test").create(
        study_uid=study_uid, design_cell_input=study_design_cell_create_input
    )
    return item
