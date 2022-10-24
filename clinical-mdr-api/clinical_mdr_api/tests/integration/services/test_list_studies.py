import unittest

from neomodel import db

from clinical_mdr_api import models
from clinical_mdr_api.domain_repositories.models.endpoint import (
    EndpointRoot,
    EndpointValue,
)
from clinical_mdr_api.domain_repositories.models.objective import (
    ObjectiveRoot,
    ObjectiveValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.services.endpoints import EndpointService
from clinical_mdr_api.services.objectives import ObjectiveService
from clinical_mdr_api.services.study import StudyService
from clinical_mdr_api.services.study_activity_instruction import (
    StudyActivityInstructionService,
)
from clinical_mdr_api.services.study_activity_selection import (
    StudyActivitySelectionService,
)
from clinical_mdr_api.services.study_criteria_selection import (
    StudyCriteriaSelectionService,
)
from clinical_mdr_api.tests.integration.utils import data_library
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class TestListStudiesForObjectiveAndEndpoint(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("liststudiestest")
        db.cypher_query(data_library.STARTUP_STUDY_LIST_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()

    def test__list_objectives_studies(self):
        objective_service = ObjectiveService()
        studies = objective_service.get_referencing_studies(
            "Objective_000001", node_type=ObjectiveValue
        )

        assert len(studies) == 1

    def test__list_endpoints_studies(self):
        endpoint_service = EndpointService()
        studies = endpoint_service.get_referencing_studies(
            "Endpoint_000001", node_type=EndpointValue
        )

        assert len(studies) == 1


class TestListStudies(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("liststudiestest2")
        db.cypher_query(data_library.STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(data_library.STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(data_library.STARTUP_ACTIVITIES)
        db.cypher_query(
            data_library.get_codelist_with_term_cypher("EFFICACY", "Flowchart Group")
        )
        db.cypher_query(data_library.STARTUP_CRITERIA)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()

        # Create a study activity
        StudyActivitySelectionService("AZNG").make_selection(
            "study_root",
            models.StudySelectionActivityCreateInput(
                flowchartGroupUid="term_root_final", activityUid="activity_root1"
            ),
        )

        # Create a criteria template
        db.cypher_query(
            """
MATCH (incl:CTTermRoot {uid: "C25532"})
MATCH (library:Library {name: "Sponsor"})
MERGE (incl)<-[:HAS_TYPE]-(ctr1:CriteriaTemplateRoot {uid: "incl_criteria_1"})
-[relt:LATEST_FINAL]->(ctv1:CriteriaTemplateValue {name : "incl_criteria_1", name_plain : "incl_criteria_1"})
MERGE (ctr1)-[:LATEST]->(ctv1)
set relt.change_description="Approved version"
set relt.start_date= datetime()
set relt.status = "Final"
set relt.user_initials = "TODO Initials"
set relt.version = "1.0"
MERGE (library)-[:CONTAINS_CRITERIA_TEMPLATE]->(ctr1)
"""
        )

        # Create a study criteria
        StudyCriteriaSelectionService("AZNG").make_selection_create_criteria(
            "study_root",
            models.study_selection.StudySelectionCriteriaCreateInput(
                criteriaData=models.criteria.CriteriaCreateInput(
                    criteriaTemplateUid="incl_criteria_1",
                    libraryName="Sponsor",
                    parameterValues=[],
                )
            ),
        )

        # Create an Activity Description Template
        db.cypher_query(
            """
MATCH (lib:Library {name: "Sponsor"})
MERGE (adt:ActivityDescriptionTemplateRoot {uid: "ActivityDescriptionTemplate_000001"})
-[relt:LATEST_FINAL]->(adtv:ActivityDescriptionTemplateValue {name : "activity_description_1", name_plain : "activity_description_1"})
MERGE (lib)-[:CONTAINS_ACTIVITY_DESCRIPTION_TEMPLATE]->(adt)
set relt.change_description="Approved version"
set relt.start_date= datetime()
set relt.status = "Final"
set relt.user_initials = "TODO Initials"
set relt.version = "1.0"
"""
        )

        # Create a study activity instruction
        StudyActivityInstructionService("AZNG").create(
            "study_root",
            models.StudyActivityInstructionCreateInput(
                activityInstructionData=models.ActivityInstructionCreateInput(
                    activityInstructionTemplateUid="ActivityDescriptionTemplate_000001",
                    parameterValues=[],
                    libraryName="Sponsor",
                ),
                studyActivityUid="StudyActivity_000001",
            ),
        )

        # Let's create an empty study
        db.cypher_query(
            """
MERGE (sr:StudyRoot {uid: "study_root2"})-[:LATEST]->(sv:StudyValue{study_id_prefix: "some_id2", study_number:"1"})
MERGE (sr)-[hv:HAS_VERSION]->(sv)
MERGE (sr)-[ld:LATEST_DRAFT]->(sv)
set hv.status = "DRAFT"
set hv.start_date = datetime()
set hv.user_initials = "AZNG"
set ld = hv
WITH sv
MATCH (p:Project {uid: "Project_000001"})
MERGE (p)-[:HAS_FIELD]->(sf:StudyField:StudyProjectField)<-[:HAS_PROJECT]-(sv)
"""
        )

        self.study_service = StudyService()

    def test_filter_by_study_objective(self):
        result = self.study_service.get_all(has_study_objective=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_endpoint(self):
        result = self.study_service.get_all(has_study_endpoint=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_activity(self):
        result = self.study_service.get_all(has_study_activity=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_criteria(self):
        result = self.study_service.get_all(has_study_criteria=True)
        self.assertEqual(len(result.items), 1)

    def test_filter_by_study_activity_instruction(self):
        result = self.study_service.get_all(has_study_activity_instruction=True)
        self.assertEqual(len(result.items), 1)
