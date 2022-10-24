import unittest

from neomodel import db

from clinical_mdr_api import exceptions, models
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.services.study_design_cell import StudyDesignCellService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)


class StudyDesignCellTestCase(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studydesigncelltest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        # Create a study
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]

        # Create an epoch
        catalogue_name, library_name = get_catalogue_name_library_name()
        create_study_epoch_codelists_ret_cat_and_lib()
        self.study_epoch = create_study_epoch("EpochSubType_0001")

        # Create a study arm
        arm_type_codelist = create_codelist(
            "Arm Type", "CTCodelist_ArmType", catalogue_name, library_name
        )
        arm_type_term = create_ct_term(
            arm_type_codelist.codelistUid,
            "Arm Type",
            "ArmType_0001",
            1,
            catalogue_name,
            library_name,
        )
        self.study_arms = [
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_1",
                shortName="Arm_Short_Name_1",
                code="Arm_code_1",
                description="desc...",
                colourCode="colour...",
                randomizationGroup="Randomization_Group_1",
                numberOfSubjects=1,
                armTypeUid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_2",
                shortName="Arm_Short_Name_2",
                code="Arm_code_2",
                description="desc...",
                colourCode="colour...",
                randomizationGroup="Randomization_Group_2",
                numberOfSubjects=1,
                armTypeUid=arm_type_term.uid,
            ),
            create_study_arm(
                study_uid=self.study.uid,
                name="Arm_Name_3",
                shortName="Arm_Short_Name_3",
                code="Arm_code_3",
                description="desc...",
                colourCode="colour...",
                randomizationGroup="Randomization_Group_3",
                numberOfSubjects=3,
                armTypeUid=arm_type_term.uid,
            ),
        ]

        # Create a study element
        element_type_codelist = create_codelist(
            "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
        )
        element_type_term = create_ct_term(
            element_type_codelist.codelistUid,
            "Element Type",
            "ElementType_0001",
            1,
            catalogue_name,
            library_name,
        )
        element_type_term_2 = create_ct_term(
            element_type_codelist.codelistUid,
            "Element Type",
            "ElementType_0002",
            2,
            catalogue_name,
            library_name,
        )
        self.study_elements = [
            create_study_element(element_type_term.uid, self.study.uid),
            create_study_element(element_type_term_2.uid, self.study.uid),
        ]

        # Create a study branch arm
        self.study_branch_arms = [
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_1",
                shortName="BranchArm_Short_Name_1",
                code="BranchArm_code_1",
                description="desc...",
                colourCode="desc...",
                randomizationGroup="Randomization_Group_1",
                numberOfSubjects=1,
                armUid=self.study_arms[0].armUid,
            ),
            create_study_branch_arm(
                self.study.uid,
                name="BranchArm_Name_2",
                shortName="BranchArm_Short_Name_2",
                code="BranchArm_code_2",
                description="desc...",
                colourCode="desc...",
                randomizationGroup="BranchArm_Randomization_Group_2",
                numberOfSubjects=1,
                armUid=self.study_arms[1].armUid,
            ),
        ]

    def test_create_patch_delete_design_cell(self):
        service = StudyDesignCellService("test")
        # Check if the BusinessLogicException is raised when a StudyDesignCell is assigned to an Arm that has StudyBranchArm assigned to it.
        with self.assertRaises(exceptions.BusinessLogicException):
            # Create a design cell -- Arm Specified
            design_cell = service.create(
                self.study.uid,
                models.StudyDesignCellCreateInput(
                    studyArmUid=self.study_arms[0].armUid,
                    studyEpochUid=self.study_epoch.uid,
                    studyElementUid=self.study_elements[0].elementUid,
                    transitionRule="Transition_Rule_2",
                ),
            )

        # Create a design cell -- Arm Specified
        design_cell = service.create(
            self.study.uid,
            models.StudyDesignCellCreateInput(
                studyArmUid=self.study_arms[2].armUid,
                studyEpochUid=self.study_epoch.uid,
                studyElementUid=self.study_elements[0].elementUid,
                transitionRule="Transition_Rule_2",
            ),
        )

        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 1

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid,
                studyArmUid=self.study_arms[2].armUid,
                studyElementUid=self.study_elements[1].elementUid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyElementUid == self.study_elements[1].elementUid
        assert design_cell.studyArmUid == self.study_arms[2].armUid

        # Patch a design cell - switching between study arm and study branch arm
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid,
                studyBranchArmUid=self.study_branch_arms[0].branchArmUid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyArmUid is None
        assert design_cell.studyBranchArmUid == self.study_branch_arms[0].branchArmUid

        # Patch a design cell - patch on study branch arm
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid,
                studyBranchArmUid=self.study_branch_arms[1].branchArmUid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyArmUid is None
        assert design_cell.studyBranchArmUid == self.study_branch_arms[1].branchArmUid

        # Create a design cell -- Branch Specified
        design_cell = service.create(
            self.study.uid,
            models.StudyDesignCellCreateInput(
                studyBranchArmUid=self.study_branch_arms[0].branchArmUid,
                studyEpochUid=self.study_epoch.uid,
                studyElementUid=self.study_elements[0].elementUid,
                transitionRule="Transition_Rule_1",
            ),
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 2

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid,
                studyBranchArmUid=self.study_branch_arms[1].branchArmUid,
                studyElementUid=self.study_elements[1].elementUid,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyArmUid is None
        assert design_cell.studyBranchArmUid == self.study_branch_arms[1].branchArmUid

        # Patch a design cell - switching between study branch arm and study arm
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid,
                studyArmUid=self.study_arms[2].armUid,
                studyBranchArmUid=None,
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyElementUid == self.study_elements[1].elementUid
        assert design_cell.studyArmUid == self.study_arms[2].armUid
        assert design_cell.studyBranchArmUid is None

        # Patch a design cell - patch on study arm and study element
        # Will return a 204 no content
        designCellUid = design_cells[0].designCellUid
        service.patch(
            self.study.uid,
            models.StudyDesignCellEditInput(
                studyDesignCellUid=designCellUid, studyArmUid=self.study_arms[2].armUid
            ),
        )
        # Get the updated design cell
        # This will also test the get specific design cell
        design_cell = service.get_specific_design_cell(self.study.uid, designCellUid)
        assert design_cell.studyArmUid == self.study_arms[2].armUid
        assert design_cell.studyBranchArmUid is None

        # Delete a design cell
        service.delete(self.study.uid, designCellUid)
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 1

    def test_batch_operations(self):
        service = StudyDesignCellService("test")

        # create
        service.handle_batch_operations(
            self.study.uid,
            [
                models.StudyDesignCellBatchInput(
                    method="POST",
                    content=models.StudyDesignCellCreateInput(
                        studyArmUid=self.study_arms[2].armUid,
                        studyEpochUid=self.study_epoch.uid,
                        studyElementUid=self.study_elements[0].elementUid,
                        transitionRule="Transition_Rule_1",
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="POST",
                    content=models.StudyDesignCellCreateInput(
                        studyArmUid=self.study_arms[2].armUid,
                        studyEpochUid=self.study_epoch.uid,
                        studyElementUid=self.study_elements[1].elementUid,
                        transitionRule="Transition_Rule_2",
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="POST",
                    content=models.StudyDesignCellCreateInput(
                        studyBranchArmUid=self.study_branch_arms[0].branchArmUid,
                        studyEpochUid=self.study_epoch.uid,
                        studyElementUid=self.study_elements[0].elementUid,
                        transitionRule="Transition_Rule_3",
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="POST",
                    content=models.StudyDesignCellCreateInput(
                        studyBranchArmUid=self.study_branch_arms[1].branchArmUid,
                        studyEpochUid=self.study_epoch.uid,
                        studyElementUid=self.study_elements[1].elementUid,
                        transitionRule="Transition_Rule_4",
                    ),
                ),
            ],
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 4

        # patch
        design_cells = service.get_all_design_cells(self.study.uid)
        service.handle_batch_operations(
            self.study.uid,
            [
                models.StudyDesignCellBatchInput(
                    method="PATCH",
                    content=models.StudyDesignCellEditInput(
                        studyDesignCellUid=design_cells[0].designCellUid,
                        studyElementUid=self.study_elements[1].elementUid,
                        studyArmUid=self.study_arms[2].armUid,
                        studyBranchArmUid=None,
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="PATCH",
                    content=models.StudyDesignCellEditInput(
                        studyDesignCellUid=design_cells[1].designCellUid,
                        studyElementUid=self.study_elements[0].elementUid,
                        studyBranchArmUid=self.study_branch_arms[0].branchArmUid,
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="PATCH",
                    content=models.StudyDesignCellEditInput(
                        studyDesignCellUid=design_cells[2].designCellUid,
                        studyBranchArmUid=self.study_branch_arms[1].branchArmUid,
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="PATCH",
                    content=models.StudyDesignCellEditInput(
                        studyDesignCellUid=design_cells[3].designCellUid,
                        studyArmUid=self.study_arms[2].armUid,
                    ),
                ),
            ],
        )
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[0].designCellUid
        )
        assert design_cell.studyElementUid == self.study_elements[1].elementUid
        assert design_cell.studyArmUid == self.study_arms[2].armUid
        assert design_cell.studyBranchArmUid is None
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[1].designCellUid
        )
        assert design_cell.studyElementUid == self.study_elements[0].elementUid
        assert design_cell.studyArmUid is None
        assert design_cell.studyBranchArmUid == self.study_branch_arms[0].branchArmUid
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[2].designCellUid
        )
        assert design_cell.studyArmUid is None
        assert design_cell.studyBranchArmUid == self.study_branch_arms[1].branchArmUid
        design_cell = service.get_specific_design_cell(
            self.study.uid, design_cells[3].designCellUid
        )
        assert design_cell.studyArmUid == self.study_arms[2].armUid
        assert design_cell.studyBranchArmUid is None

        # delete
        design_cells = service.get_all_design_cells(self.study.uid)
        service.handle_batch_operations(
            self.study.uid,
            [
                models.StudyDesignCellBatchInput(
                    method="DELETE",
                    content=models.StudyDesignCellDeleteInput(
                        uid=design_cells[0].designCellUid
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="DELETE",
                    content=models.StudyDesignCellDeleteInput(
                        uid=design_cells[1].designCellUid
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="DELETE",
                    content=models.StudyDesignCellDeleteInput(
                        uid=design_cells[2].designCellUid
                    ),
                ),
                models.StudyDesignCellBatchInput(
                    method="DELETE",
                    content=models.StudyDesignCellDeleteInput(
                        uid=design_cells[3].designCellUid
                    ),
                ),
            ],
        )
        design_cells = service.get_all_design_cells(self.study.uid)
        assert len(design_cells) == 0
