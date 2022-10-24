import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.domain_repositories.models.endpoint import EndpointRoot
from clinical_mdr_api.domain_repositories.models.endpoint_template import (
    EndpointTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.objective import ObjectiveRoot
from clinical_mdr_api.domain_repositories.models.objective_template import (
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.timeframe import TimeframeRoot
from clinical_mdr_api.domain_repositories.models.timeframe_template import (
    TimeframeTemplateRoot,
)
from clinical_mdr_api.models.study_epoch import StudyEpochEditInput
from clinical_mdr_api.services.ct_term import CTTermService
from clinical_mdr_api.services.libraries import create as create_library
from clinical_mdr_api.services.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_STUDY_ACTIVITY_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    STARTUP_STUDY_BRANCH_ARM_CYPHER,
    STARTUP_STUDY_COMPOUND_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
    get_codelist_with_term_cypher,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
    patch_study_branch_arm,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"
initialize_ct_data_map = {
    "TypeOfTreatment": ["CTTerm_000001"],
    "RouteOfAdministration": ["CTTerm_000002"],
    "DosageForm": ["CTTerm_000003"],
    "DispensedIn": ["CTTerm_000004"],
    "Device": ["CTTerm_000005"],
    "Formulation": ["CTTerm_000006"],
    "ReasonForMissingNullValue": ["CTTerm_000007"],
}


class StudyObjectivesTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_objective.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid", "userInitials"]

    def preprocess_expected_response(self, resp_item, actual_response, url):
        """
        Preprocessing is needed as the order returned for the full audit trail of the study selection is depending on the uuid generated,
        as these are random we cannot know up front which is supposed to be listed first.
        """
        if "/study/study_root/study-objectives/audit-trail/" == url:
            actual_responses_items = []
            for item in actual_response:
                actual_responses_items.append(item["studyObjectiveUid"])
            uids = {}
            for item in set(actual_responses_items):
                uids[item] = actual_responses_items.count(item)
            first_uid = actual_response[0]["studyObjectiveUid"]
            if uids[first_uid] == 2:
                return resp_item
            resp_item["result"] = resp_item["result"][3:5].extend(
                resp_item["result"][0:3]
            )
            return resp_item
        return resp_item


class StudyObjectivesNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_objective_negative.json")
    ]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "userInitials",
            "time",
            "studyEndpointUid",
            "uid",
        ]


class StudyEndpointsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointTemplateRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()
        TimeframeTemplateRoot.generate_node_uids_if_not_present()
        TimeframeRoot.generate_node_uids_if_not_present()
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_endpoint.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyEndpointsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_endpoint_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid"]


def initialize_ct_from_data_map():
    for _, value in initialize_ct_data_map.items():
        if isinstance(value, list):
            for val in value:
                db.cypher_query(
                    """MATCH (l:Library {name:"CDISC", is_editable:false}), (codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
                CREATE (l)-[:CONTAINS_TERM]->(a:CTTermRoot {uid: $val})-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot{uid: $val})
                -[:LATEST]->(term_ver_value:CTTermNameValue {name_sentence_case: $val, name: $val})
                CREATE (term_ver_root)-[:LATEST_FINAL{version:1.0,status:"Final",change_description:"test",
                user_initials:"test",start_date:datetime()}]->(term_ver_value)
                CREATE (a)<-[:HAS_TERM]-(codelist)
                """,
                    {"val": val},
                )
        else:
            db.cypher_query(
                """MATCH (l:Library {name:"CDISC", is_editable:false}), (codelist:CTCodelistRoot {uid:"CTCodelist_000001"})
                CREATE (l)-[:CONTAINS_TERM]->(a:CTTermRoot {uid: $val})-[:HAS_NAME_ROOT]->(term_ver_root:CTTermNameRoot{uid: $val})
                -[:LATEST]->(term_ver_value:CTTermNameValue {name_sentence_case: $val, name: $val})
                CREATE (term_ver_root)-[:LATEST_FINAL{version:1.0,status:"Final",change_description:"test",
                user_initials:"test",start_date:datetime()}]->(term_ver_value)
                CREATE (a)<-[:HAS_TERM]-(codelist)""",
                {"val": value},
            )


class StudyCompoundsTest(api.APITest):
    TEST_DB_NAME = "studyselection"
    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_compound.json")]

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        initialize_ct_from_data_map()
        db.cypher_query(STARTUP_STUDY_COMPOUND_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "nncId",
            "UNII",
            "PClass",
            "changeDescription",
            "userInitials",
        ]


class StudyCompoundsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        initialize_ct_from_data_map()
        db.cypher_query(STARTUP_STUDY_COMPOUND_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_compound_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "modifiedDate", "time", "uid"]


class StudyActivityTest(api.APITest):
    TEST_DB_NAME = "studyselection"
    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_activities.json")
    ]

    def setUp(self):
        super().setUp()
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(
            get_codelist_with_term_cypher(
                "EFFICACY", "Flowchart Group", term_uid="term_efficacy_uid"
            )
        )
        db.cypher_query(STARTUP_STUDY_ACTIVITY_CYPHER)

    def ignored_fields(self):
        return ["startDate", "endDate", "time", "uid", "userInitials"]


class StudyArmsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_arms.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyElementsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        # create library
        create_library("Sponsor", True)
        # create catalogue
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

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
        CTTermService().add_parent(
            term_uid=element_subtype_term_uid1,
            parent_uid=element_type_term_uid1,
            relationship_type="type",
        )

        element_subtype_term_uid2 = "ElementSubTypeTermUid_2"
        db.cypher_query(
            get_codelist_with_term_cypher(
                name="Wash-out",
                codelist_name="Element Sub Type",
                codelist_uid="ElementSubTypeCodelistUid",
                term_uid=element_subtype_term_uid2,
            )
        )

        CTTermService().add_parent(
            term_uid=element_subtype_term_uid2,
            parent_uid=element_type_term_uid1,
            relationship_type="type",
        )

        catalogue_name = "catalogue"
        library_name = "Sponsor"
        codelist = create_codelist(
            name="time",
            uid="C66781",
            catalogue=catalogue_name,
            library=library_name,
        )
        hour_term = create_ct_term(
            codelist=codelist.codelistUid,
            name="hours",
            uid="hours001",
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
        week_term = create_ct_term(
            codelist=codelist.codelistUid,
            name="weeks",
            uid="weeks001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )
        TestUtils.create_unit_definition(
            name="hours",
            libraryName="Sponsor",
            ctUnits=[hour_term.uid],
            unitSubsets=[study_time_subset.uid],
        )
        TestUtils.create_unit_definition(
            name="weeks",
            libraryName="Sponsor",
            ctUnits=[week_term.uid],
            unitSubsets=[study_time_subset.uid],
        )

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_elements.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyBranchArmsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
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
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        self.design_cell = create_study_design_cell(
            study_element_uid=self.study_elements[0].elementUid,
            study_epoch_uid=self.study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=self.study.uid,
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_branch_arms.json")
    ]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyBranchArmsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_branch_arms_negative.json")
    ]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyCohortsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        self.studyUid = "study_root"
        self.armUid1 = "StudyArm_000001"
        self.branch_arm = create_study_branch_arm(
            study_uid=self.studyUid,
            name="Branch_Arm_Name_1",
            shortName="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Branch_Arm_randomizationGroup",
            numberOfSubjects=100,
            armUid=self.armUid1,
        )
        self.branch_arm = create_study_branch_arm(
            study_uid=self.studyUid,
            name="Branch_Arm_Name_2",
            shortName="Branch_Arm_Short_Name_2",
            code="Branch_Arm_code_2",
            description="desc...",
            colourCode="colour...2",
            randomizationGroup="Branch_Arm_randomizationGroup2",
            numberOfSubjects=20,
            armUid=self.armUid1,
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_selection_cohorts.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyCohortsNegativeTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)

        self.studyUid = "study_root"
        self.armUid1 = "StudyArm_000001"

        self.cohorts = [
            create_study_cohort(
                study_uid=self.studyUid,
                name="Cohort_Name_1",
                shortName="Cohort_Short_Name_1",
                code="Cohort_code_1",
                description="desc...",
                colourCode="desc...",
                numberOfSubjects=100,
                armUids=[self.armUid1],
            ),
            create_study_cohort(
                study_uid=self.studyUid,
                name="Cohort_Name_2",
                shortName="Cohort_Short_Name_2",
                code="Cohort_code_2",
                description="desc...",
                colourCode="desc...",
                numberOfSubjects=100,
                armUids=[self.armUid1],
            ),
        ]
        self.branch_arm = create_study_branch_arm(
            study_uid=self.studyUid,
            name="Branch_Arm_Name_1",
            shortName="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colourCode="colour...",
            randomizationGroup="Branch_Arm_randomizationGroup",
            numberOfSubjects=100,
            armUid=self.armUid1,
        )
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_cohorts_negative.json")
    ]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyDesignCellsTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)

        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]

        # Create an epoch
        create_study_epoch_codelists_ret_cat_and_lib()
        catalogue_name, library_name = get_catalogue_name_library_name()
        self.study_epoch = create_study_epoch("EpochSubType_0001")

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

        db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
        db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
        db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "study_selection_design_cells.json")
    ]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "modified",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]


class StudyDesignJointTest(api.APITest):
    TEST_DB_NAME = "studyselection"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
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

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "study_design_joint.json")]

    def ignored_fields(self):
        return [
            "startDate",
            "endDate",
            "modifiedDate",
            "modified",
            "time",
            "uid",
            "userInitials",
            "codelistUid",
        ]
