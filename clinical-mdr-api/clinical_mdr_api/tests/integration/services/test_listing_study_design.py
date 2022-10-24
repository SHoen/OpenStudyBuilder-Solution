import unittest

from neomodel import db

from clinical_mdr_api.models.listings_sdtm import (
    StudyArmListing,
    StudyElementListing,
    StudySummaryListing,
    StudyVisitListing,
)
from clinical_mdr_api.models.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.listings_sdtm import (
    SDTMListingsService as ListingsService,
)
from clinical_mdr_api.services.listings_study import StudyListingService
from clinical_mdr_api.services.study import StudyService
from clinical_mdr_api.services.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    get_codelist_with_term_cypher,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    add_parent_ctTerm,
    create_codelist,
    create_ct_term,
    create_library_data,
    create_some_visits,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_element_with_planned_duration,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    generate_study_root,
    get_catalogue_name_library_name,
    input_metadata_in_study,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils


class TestTVListing(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("SDTMTVListingTest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        create_library_data()
        generate_study_root()
        create_some_visits()

    def test_tv_listing(self):
        listing_service: ListingsService = ListingsService()
        output = listing_service.list_tv(study_uid="study_root").items
        expected_output = [
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=100,
                VISIT="VISIT 1",
                VISITDY=1,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=200,
                VISIT="VISIT 2",
                VISITDY=11,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=300,
                VISIT="VISIT 3",
                VISITDY=13,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=400,
                VISIT="VISIT 4",
                VISITDY=31,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=410,
                VISIT="VISIT 4",
                VISITDY=32,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
            StudyVisitListing(
                STUDYID="SOME_ID-0",
                DOMAIN="TV",
                VISITNUM=500,
                VISIT="VISIT 5",
                VISITDY=36,
                ARMCD=None,
                ARM=None,
                TVSTRL="STARTRULE",
                TVENRL="ENDRULE",
            ),
        ]
        self.assertCountEqual(output, expected_output)
        self.assertListEqual(output, expected_output)


class TestTAListing(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("SDTMTAListingTest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        self.study = generate_study_root()
        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")
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

        codelist = create_codelist(
            name="Arm Type",
            uid="CTCodelist_00004",
            catalogue=catalogue_name,
            library=library_name,
        )
        armType = create_ct_term(
            codelist=codelist.codelistUid,
            name="Arm Type",
            uid="ArmType_0001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_1",
            shortName="Arm_Short_Name_1",
            code="Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_2",
            shortName="Arm_Short_Name_2",
            code="Arm_code_2",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup2",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_3",
            shortName="Arm_Short_Name_3",
            code="Arm_code_3",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup3",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )

        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_9",
            shortName="Arm_Short_Name_9",
            code="Arm_code_9",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup9",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )

        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )

        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[1].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000001",
            study_uid=self.study.uid,
        )

        self.branch_arm = create_study_branch_arm(
            study_uid=self.study.uid,
            name="Branch_Arm_Name_1",
            shortName="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Branch_Arm_randomizationGroup",
            numberOfSubjects=100,
            armUid="StudyArm_000003",
        )
        self.branch_arm = patch_study_branch_arm(
            branch_arm_uid=self.branch_arm.branchArmUid, study_uid=self.study.uid
        )

        self.design_cell3 = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000005",
            study_uid=self.study.uid,
        )

        self.cohort = create_study_cohort(
            study_uid=self.study.uid,
            name="Cohort_Name_1",
            shortName="Cohort_Short_Name_1",
            code="Cohort_code_1",
            description="desc...",
            colourCode="desc...",
            numberOfSubjects=100,
            armUids=["StudyArm_000001"],
        )
        # edit an epoch to track if the relationships have been updated
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(self.study_epoch2.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            studyUid=epoch.studyUid,
            startRule=start_rule,
            endRule=end_rule,
            changeDescription="rules change",
        )
        self.study_epoch3 = epoch_service.edit(
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

    def test_ta_listing(self):
        listing_service: ListingsService = ListingsService()
        output = listing_service.list_ta(study_uid="study_root").items
        expected_output = [
            # 1
            StudyArmListing(
                ARM="Arm_Name_1",
                ARMCD="Arm_code_1",
                DOMAIN="TA",
                ELEMENT="Element_Name_1",
                EPOCH="Epoch Subtype 2",
                ETCD="2",
                STUDYID="SOME_ID-0",
                TABRANCH=None,
                TAETORD="2",
                TATRANS=None,
            ),
            # 2
            StudyArmListing(
                ARM="Arm_Name_2",
                ARMCD="Arm_code_2-Branch_Arm_code_1",
                DOMAIN="TA",
                ELEMENT="Element_Name_1",
                EPOCH="Epoch Subtype 1",
                ETCD="1",
                STUDYID="SOME_ID-0",
                TABRANCH="Branch_Arm_Name_1_edit",
                TAETORD="1",
                TATRANS=None,
            ),
            # 3
            StudyArmListing(
                ARM="Arm_Name_2",
                ARMCD="Arm_code_2-Branch_Arm_code_1",
                DOMAIN="TA",
                ELEMENT="Element_Name_1",
                EPOCH="Epoch Subtype 2",
                ETCD="1",
                STUDYID="SOME_ID-0",
                TABRANCH="Branch_Arm_Name_1_edit",
                TAETORD="2",
                TATRANS=None,
            ),
            # 4
            StudyArmListing(
                ARM="Arm_Name_3",
                ARMCD="Arm_code_3",
                DOMAIN="TA",
                ELEMENT="Element_Name_1",
                EPOCH="Epoch Subtype 2",
                ETCD="1",
                STUDYID="SOME_ID-0",
                TABRANCH=None,
                TAETORD="2",
                TATRANS=None,
            ),
        ]

        self.assertCountEqual(output, expected_output)
        self.assertListEqual(output, expected_output)


class TestStudyListing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db("StudyListingTest")
        inject_base_data()

        study_service = StudyService(user="some_user")
        studies = study_service.get_all()
        cls.study_uid = studies.items[0].uid
        cls.study_number = studies.items[0].studyNumber
        input_metadata_in_study(cls.study_uid)

    def test_registry_identifiers_listing(self):
        study_service = StudyService(user="some_user")
        service_response = study_service.get_by_uid(
            uid=self.study_uid,
            fields="currentMetadata.identificationMetadata",
        )
        study_listing_service = StudyListingService()
        output = study_listing_service.get_registry_identifiers(self.study_number)
        expected_output = (
            service_response.currentMetadata.identificationMetadata.registryIdentifiers
        )
        self.assertCountEqual(output, expected_output)
        self.assertEqual(output, expected_output)

    def test_high_level_study_design_listing(self):
        study_service = StudyService(user="some_user")
        service_response = study_service.get_by_uid(
            uid=self.study_uid,
            fields="currentMetadata.highLevelStudyDesign",
        )
        study_listing_service = StudyListingService()
        output = study_listing_service.get_study_type(self.study_number)
        expected_output = service_response.currentMetadata.highLevelStudyDesign
        self.assertCountEqual(output, expected_output)
        self.assertEqual(output, expected_output)

    def test_study_population_listing(self):
        study_service = StudyService(user="some_user")
        service_response = study_service.get_by_uid(
            uid=self.study_uid,
            fields="currentMetadata.studyPopulation",
        )
        study_listing_service = StudyListingService()
        output = study_listing_service.get_study_population(self.study_number)
        expected_output = service_response.currentMetadata.studyPopulation
        self.assertCountEqual(output, expected_output)
        self.assertEqual(output, expected_output)


class TestTEListing(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("SDTMTEListingTest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        self.study = generate_study_root()
        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")

        element_type_term_uid1 = "ElementTypeTermUid_1"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="No Treatment",
                codelist_name="Element Type",
                codelist_uid="ElementTypeCodelistUid",
                term_uid=element_type_term_uid1,
            )
        )

        element_subtype_term_uid1 = "ElementSubTypeTermUid_1"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="Screening",
                codelist_name="Element Sub Type",
                codelist_uid="ElementSubTypeCodelistUid",
                term_uid=element_subtype_term_uid1,
            )
        )
        add_parent_ctTerm(element_subtype_term_uid1, element_type_term_uid1)

        element_subtype_term_uid2 = "ElementSubTypeTermUid_2"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="Wash-out",
                codelist_name="Element Sub Type",
                codelist_uid="ElementSubTypeCodelistUid",
                term_uid=element_subtype_term_uid2,
            )
        )
        add_parent_ctTerm(element_subtype_term_uid2, element_type_term_uid1)

        catalogue_name = "catalogue"
        library_name = "Sponsor"
        codelist = create_codelist(
            name="time",
            uid="C66781",
            catalogue=catalogue_name,
            library=library_name,
        )
        ct_term_uid = "hours001"
        hour_term = create_ct_term(
            codelist=codelist.codelistUid,
            name="hours",
            uid=ct_term_uid,
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        subset_codelist = create_codelist(
            name="Unit Subset",
            uid="UnitSubsetCuid",
            catalogue=catalogue_name,
            library=library_name,
        )
        study_time_subset = create_ct_term(
            codelist=subset_codelist.codelistUid,
            name="Study Time",
            uid="StudyTimeSuid",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        unit_def = TestUtils.create_unit_definition(
            name="hours",
            libraryName="Sponsor",
            ctUnits=[hour_term.uid],
            unitSubsets=[study_time_subset.uid],
        )

        self.study_elements = [
            create_study_element_with_planned_duration(
                element_type_term_uid1, self.study.uid, unit_definition_uid=unit_def.uid
            ),
            create_study_element_with_planned_duration(
                element_type_term_uid1, self.study.uid, unit_definition_uid=unit_def.uid
            ),
        ]

    def test_te_listing(self):
        listing_service: ListingsService = ListingsService()
        output = listing_service.list_te(study_uid="study_root").items
        expected_output = [
            StudyElementListing(
                DOMAIN="TE",
                ELEMENT="Element_Name_1",
                ETCD="1",
                STUDYID="SOME_ID-0",
                TEDUR="P70H",
                TEENRL="stop_rule",
                TESTRL="start_rule",
            ),
            # 1
            StudyElementListing(
                DOMAIN="TE",
                ELEMENT="Element_Name_1",
                ETCD="2",
                STUDYID="SOME_ID-0",
                TEDUR="P70H",
                TEENRL="stop_rule",
                TESTRL="start_rule",
            ),
        ]
        print(output)
        self.assertCountEqual(output, expected_output)
        self.assertListEqual(output, expected_output)


class TestTSListing(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("SDTMTSListingTest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        self.study = generate_study_root()
        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")
        self.study_epoch2 = create_study_epoch("EpochSubType_0001")
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

        codelist = create_codelist(
            name="Arm Type",
            uid="CTCodelist_00004",
            catalogue=catalogue_name,
            library=library_name,
        )
        armType = create_ct_term(
            codelist=codelist.codelistUid,
            name="Arm Type",
            uid="ArmType_0001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_1",
            shortName="Arm_Short_Name_1",
            code="Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_2",
            shortName="Arm_Short_Name_2",
            code="Arm_code_2",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup2",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )
        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_3",
            shortName="Arm_Short_Name_3",
            code="Arm_code_3",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup3",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )

        self.arm = create_study_arm(
            study_uid=self.study.uid,
            name="Arm_Name_9",
            shortName="Arm_Short_Name_9",
            code="Arm_code_9",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Arm_randomizationGroup9",
            numberOfSubjects=100,
            armTypeUid=armType.uid,
        )

        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )

        self.design_cell2 = create_study_design_cell(
            study_element_uid=self.study_elements[1].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000001",
            study_uid=self.study.uid,
        )

        self.branch_arm = create_study_branch_arm(
            study_uid=self.study.uid,
            name="Branch_Arm_Name_1",
            shortName="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Branch_Arm_randomizationGroup",
            numberOfSubjects=100,
            armUid="StudyArm_000003",
        )
        self.branch_arm = patch_study_branch_arm(
            branch_arm_uid=self.branch_arm.branchArmUid, study_uid=self.study.uid
        )

        self.design_cell3 = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000005",
            study_uid=self.study.uid,
        )

        self.cohort = create_study_cohort(
            study_uid=self.study.uid,
            name="Cohort_Name_1",
            shortName="Cohort_Short_Name_1",
            code="Cohort_code_1",
            description="desc...",
            colourCode="desc...",
            numberOfSubjects=100,
            armUids=["StudyArm_000001"],
        )
        # edit an epoch to track if the relationships have been updated
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(self.study_epoch2.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            studyUid=epoch.studyUid,
            startRule=start_rule,
            endRule=end_rule,
            changeDescription="rules change",
        )
        self.study_epoch3 = epoch_service.edit(
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        codelist = create_codelist(
            name="Trial Summary Parameter Test Code",
            uid="C66738",
            catalogue=catalogue_name,
            library=library_name,
        )

        armType = create_ct_term(
            codelist=codelist.codelistUid,
            name="C98771",
            uid="C98771_NARMS",
            code_submission_value="NARMS",
            name_submission_value="Planned Number of Arms",
            preferred_term="Planned Number of Arms",
            definition="The planned number of intervention groups.",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

        codelist = create_codelist(
            name="Trial Summary Parameter Test Name",
            uid="C67152",
            catalogue=catalogue_name,
            library=library_name,
        )

        armType = create_ct_term(
            codelist=codelist.codelistUid,
            name="C126063",
            uid="C126063_NCOHORT",
            code_submission_value="NCOHORT",
            name_submission_value="Number of Groups/Cohorts",
            preferred_term="Number of Groups or Cohorts",
            definition="The number of groups or cohorts that are part of the study.",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

    def test_ts_listing(self):
        listing_service: ListingsService = ListingsService()
        output = listing_service.list_ts(study_uid="study_root").items
        expected_output = [
            StudySummaryListing(
                DOMAIN="TS",
                STUDYID="some_id-0",
                TSPARM="Planned Number of Arms",
                TSPARMCD="NARMS",
                TSVAL="3",
                TSVALCD="",
                TSVALNF="",
                TSVCDREF="",
                TSVCDVER="",
            ),
            # 1
            StudySummaryListing(
                DOMAIN="TS",
                STUDYID="some_id-0",
                TSPARM="Number of Groups/Cohorts",
                TSPARMCD="NCOHORT",
                TSVAL="1",
                TSVALCD="",
                TSVALNF="",
                TSVCDREF="",
                TSVCDVER="",
            ),
        ]
        self.assertCountEqual(output, expected_output)
        self.assertListEqual(output, expected_output)
