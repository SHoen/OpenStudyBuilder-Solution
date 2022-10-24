import unittest

from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.services.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.factory_activity import (
    create_study_activity,
)


class StudyActivitySelectionTestCase(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("studyactivitiescheduletest.selection")
        db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITIES)
        db.cypher_query(
            data_library.get_codelist_with_term_cypher("EFFICACY", "Flowchart Group")
        )
        db.cypher_query(data_library.STARTUP_STUDY_ACTIVITY_CYPHER)

    def test_batch_operations(self):
        service = StudyActivitySelectionService("test")
        service.handle_batch_operations(
            "study_root",
            [
                models.StudySelectionActivityBatchInput(
                    method="POST",
                    content=models.StudySelectionActivityCreateInput(
                        flowchartGroupUid="term_root_final",
                        activityUid="activity_root1",
                    ),
                ),
                models.StudySelectionActivityBatchInput(
                    method="POST",
                    content=models.StudySelectionActivityCreateInput(
                        flowchartGroupUid="term_root_final",
                        activityUid="activity_root2",
                    ),
                ),
            ],
        )

        study_activities = service.get_all_selection("study_root").items
        assert len(study_activities) == 2

        service.handle_batch_operations(
            "study_root",
            [
                models.StudySelectionActivityBatchInput(
                    method="PATCH",
                    content=models.StudySelectionActivityBatchUpdateInput(
                        studyActivityUid=study_activities[0].studyActivityUid,
                        content=models.StudySelectionActivityInput(
                            note="Test note", showActivityInProtocolFlowchart=True
                        ),
                    ),
                ),
                models.StudySelectionActivityBatchInput(
                    method="DELETE",
                    content=models.StudySelectionActivityBatchDeleteInput(
                        studyActivityUid=study_activities[1].studyActivityUid
                    ),
                ),
            ],
        )

        sa1 = service.get_specific_selection(
            "study_root", study_activities[0].studyActivityUid
        )
        assert sa1.showActivityInProtocolFlowchart is True

        study_activities = service.get_all_selection("study_root").items
        assert len(study_activities) == 1

    def test_make_seleciton_duplicated_activity(self):
        create_study_activity("study_root", activity_uid="activity_root1")
        with self.assertRaises(ValidationException):
            create_study_activity("study_root", activity_uid="activity_root1")
