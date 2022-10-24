import os

from neomodel import db
from starlette.testclient import TestClient

from clinical_mdr_api.tests.integration.utils import api
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
)

BASE_SCENARIO_PATH = "clinical_mdr_api/tests/data/scenarios/"


class ActivityTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class ActivityNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_negative.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "time"]


class ActivitySubGroupTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_sub_group.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class ActivitySubGroupTestNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_group_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "time"]


class ActivityGroupTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_group.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class ActivityGroupNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_group_negative.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "time"]


class ActivityInstanceTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_instance.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class ActivityInstanceNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_instance_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "time"]


class NewCategoricFindingTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/categoric_finding.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class NewCategoricFindingNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/categoric_finding_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewNumericFindingTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/numeric_finding.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class NewNumericFindingNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/numeric_finding_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewTextualNumericFindingTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/textual_finding.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class NewTextualFindingNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/textual_finding_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewCompoundDosingTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/compound_dosing.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "specimen"]


class NewCompoundDosingNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/compound_dosing_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials", "specimen"]


class NewEventTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/event.json")]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "specimen"]


class NewEventNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/event_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials", "specimen"]


class NewReminderTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/reminder.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials", "specimen"]


class NewReminderNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/reminder_negative.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials", "specimen"]


class NewSpecialPurposeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/special_purpose.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class NewSpecialPurposeNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/special_purpose_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewLaboratoryActivityTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/laboratory_activity.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]


class NewLaboratoryActivityNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH,
            "activity_sub_types/laboratory_activity_negative.json",
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewRatingScaleNegativeTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(
            BASE_SCENARIO_PATH, "activity_sub_types/rating_scale_negative.json"
        )
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "uid", "time", "userInitials"]


class NewRatingScaleTest(api.APITest):
    TEST_DB_NAME = "activities"

    def setUp(self):
        inject_and_clear_db(self.TEST_DB_NAME)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)

        from clinical_mdr_api import main

        self.test_client = TestClient(main.app)

    SCENARIO_PATHS = [
        os.path.join(BASE_SCENARIO_PATH, "activity_sub_types/rating_scale.json")
    ]

    def ignored_fields(self):
        return ["startDate", "endDate", "userInitials"]
