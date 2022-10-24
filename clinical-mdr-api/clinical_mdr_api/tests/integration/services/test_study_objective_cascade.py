import unittest

from neomodel import db

from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    TemplateVO,
)
from clinical_mdr_api.domain_repositories.models.generic import Library
from clinical_mdr_api.domain_repositories.models.objective import ObjectiveRoot
from clinical_mdr_api.domain_repositories.models.objective_template import (
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterValue,
    TemplateParameterValueRoot,
)
from clinical_mdr_api.domain_repositories.templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.models.objective import ObjectiveCreateInput
from clinical_mdr_api.models.study_selection import (
    StudySelectionObjective,
    StudySelectionObjectiveInput,
)
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService
from clinical_mdr_api.services.objectives import ObjectiveService
from clinical_mdr_api.services.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    STARTUP_STUDY_OBJECTIVE_CYPHER,
)


class TestStudyObjectiveUpversion(unittest.TestCase):
    TPR_LABEL = "ParameterName"
    value_roots: list = []
    value_values: list = []

    def setUp(self):
        inject_and_clear_db("studyobjectiveselectionupversion")
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_STUDY_OBJECTIVE_CYPHER)
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()

        lib = Library(name="Library", is_editable=True)
        lib.save()
        self.tpr = TemplateParameter(name=self.TPR_LABEL)
        self.tpr.save()
        self.tfr = ObjectiveTemplateRepository()
        self.objective_service = ObjectiveService()
        self.objective_template_service = ObjectiveTemplateService()

        self.library = LibraryVO(name="Library", is_editable=True)
        self.tv = TemplateVO(
            name=f"Test [{self.TPR_LABEL}]",
            name_plain=f"Test {self.TPR_LABEL}",
        )
        self.im = LibraryItemMetadataVO.get_initial_item_metadata(author="Test")
        self.ar = ObjectiveTemplateAR(
            _uid=self.tfr.root_class.get_next_free_uid_and_increment_counter(),
            _template=self.tv,
            _library=self.library,
            _item_metadata=self.im,
            _editable_instance=False,
        )
        self.tfr.save(self.ar)

        self.ar: ObjectiveTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ar.approve(author="TEST")
        self.tfr.save(self.ar)

        self.ar: ObjectiveTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ar.create_new_version(
            author="TEST", change_description="Change", template=self.tv
        )
        self.tfr.save(self.ar)

        self.ar: ObjectiveTemplateAR = self.tfr.find_by_uid_2(
            self.ar.uid, for_update=True
        )
        self.ntv = TemplateVO(
            name=f"Changed Test [{self.TPR_LABEL}]",
            name_plain=f"Changed Test {self.TPR_LABEL}",
        )
        self.ar.edit_draft(
            author="TEST", change_description="Change", template=self.ntv
        )
        self.tfr.save(self.ar)

    def create_template_parameters(self, label=TPR_LABEL, count=1000):
        for i in range(count):
            vr = TemplateParameterValueRoot(uid=label + "uid__" + str(i))
            vr.save()
            vv = TemplateParameterValue(name=label + "__" + str(i))
            vv.save()
            vr.has_value.connect(self.tpr)
            vr.latest_final.connect(vv)
        for vr in self.tpr.has_value.all():
            self.value_roots.append(vr)
            vv = vr.latest_final.single()
            self.value_values.append(vv)

    def create_objectives(self, count=100, approved=False, retired=False):
        for i in range(count):
            pv = TemplateParameterMultiSelectInput(
                templateParameter=self.TPR_LABEL,
                conjunction="",
                values=[
                    {
                        "position": 1,
                        "index": 1,
                        "name": self.value_values[i].name,
                        "type": self.TPR_LABEL,
                        "uid": self.value_roots[i].uid,
                    }
                ],
            )
            template = ObjectiveCreateInput(
                objectiveTemplateUid=self.ar.uid,
                libraryName="Library",
                parameterValues=[pv],
            )

            item = self.objective_service.create(template)
            if approved:
                self.objective_service.approve(item.uid)
            if retired:
                self.objective_service.inactivate_final(item.uid)

    def test__upversion__update(self):
        # given
        self.create_template_parameters(count=14)
        self.create_objectives(count=10, approved=True)
        study_service = StudyObjectiveSelectionService(author="TEST_USER")
        study_selection_objective_input = StudySelectionObjectiveInput(
            objectiveUid="Objective_000010"
        )
        selection: StudySelectionObjective = study_service.make_selection(
            "study_root", study_selection_objective_input
        )

        self.assertIsNone(selection.latestObjective)

        self.objective_template_service.approve_cascade(self.ar.uid)

        selection: StudySelectionObjective = study_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyObjectiveUid
        )

        self.assertNotEqual(
            selection.objective.version, selection.latestObjective.version
        )
        # when

        response = study_service.update_selection_to_latest_version(
            "study_root", selection.studyObjectiveUid
        )

        self.assertIsNone(response.latestObjective)
        # then
        selection: StudySelectionObjective = study_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyObjectiveUid
        )
        self.assertIsNone(selection.latestObjective)

    def test__upversion_retired__update(self):
        # given
        self.create_template_parameters(count=14)
        self.create_objectives(count=10, approved=True)
        study_service = StudyObjectiveSelectionService(author="TEST_USER")
        study_selection_objective_input = StudySelectionObjectiveInput(
            objectiveUid="Objective_000010"
        )
        selection: StudySelectionObjective = study_service.make_selection(
            "study_root", study_selection_objective_input
        )

        self.assertIsNone(selection.latestObjective)

        self.objective_template_service.approve_cascade(self.ar.uid)
        self.objective_service.inactivate_final("Objective_000010")

        # when
        selection: StudySelectionObjective = study_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyObjectiveUid
        )
        # then
        self.assertNotEqual(
            selection.objective.version, selection.latestObjective.version
        )
        self.assertEqual(selection.latestObjective.status, "Retired")

        self.objective_service.reactivate_retired("Objective_000010")

        selection: StudySelectionObjective = study_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyObjectiveUid
        )

        self.assertNotEqual(
            selection.objective.version, selection.latestObjective.version
        )
