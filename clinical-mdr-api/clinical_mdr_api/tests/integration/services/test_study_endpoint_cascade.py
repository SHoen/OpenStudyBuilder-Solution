import unittest

from neomodel import db

from clinical_mdr_api.domain.templates.endpoint_template import EndpointTemplateAR
from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.domain.templates.timeframe_templates import TimeframeTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
    TemplateVO,
)
from clinical_mdr_api.domain_repositories.models.endpoint import EndpointRoot
from clinical_mdr_api.domain_repositories.models.endpoint_template import (
    EndpointTemplateRoot,
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
from clinical_mdr_api.domain_repositories.templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domain_repositories.templates.timeframe_template_repository import (
    TimeframeTemplateRepository,
)
from clinical_mdr_api.models.endpoint import EndpointCreateInput
from clinical_mdr_api.models.objective import ObjectiveCreateInput
from clinical_mdr_api.models.study_selection import (
    StudySelectionEndpoint,
    StudySelectionEndpointInput,
    StudySelectionObjective,
    StudySelectionObjectiveInput,
)
from clinical_mdr_api.models.template_parameter_multi_select_input import (
    TemplateParameterMultiSelectInput,
)
from clinical_mdr_api.models.timeframe import TimeframeCreateInput
from clinical_mdr_api.services.endpoint_templates import EndpointTemplateService
from clinical_mdr_api.services.endpoints import EndpointService
from clinical_mdr_api.services.objective_templates import ObjectiveTemplateService
from clinical_mdr_api.services.objectives import ObjectiveService
from clinical_mdr_api.services.study_endpoint_selection import (
    StudyEndpointSelectionService,
)
from clinical_mdr_api.services.study_objective_selection import (
    StudyObjectiveSelectionService,
)
from clinical_mdr_api.services.timeframe_templates import TimeframeTemplateService
from clinical_mdr_api.services.timeframes import TimeframeService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
    STARTUP_STUDY_ENDPOINT_CYPHER,
)


class TestStudyEndpointUpversion(unittest.TestCase):
    TPR_LABEL = "ParameterName"
    default_template_name = f"Test [{TPR_LABEL}]"
    default_template_name_plain = f"Test {TPR_LABEL}"
    changed_template_name = f"Changed Test [{TPR_LABEL}]"
    changed_template_name_plain = f"Changed Test {TPR_LABEL}"

    def setUp(self):
        inject_and_clear_db("studyendpointupversion")
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)
        db.cypher_query(STARTUP_STUDY_ENDPOINT_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()
        ObjectiveTemplateRoot.generate_node_uids_if_not_present()
        EndpointRoot.generate_node_uids_if_not_present()
        EndpointTemplateRoot.generate_node_uids_if_not_present()

        lib = Library(name="Library", is_editable=True)
        lib.save()
        self.tpr = TemplateParameter(name=self.TPR_LABEL)
        self.tpr.save()
        self.ttr = TimeframeTemplateRepository()
        self.etr = EndpointTemplateRepository()
        self.otr = ObjectiveTemplateRepository()
        self.objective_service = ObjectiveService()
        self.endpoint_service = EndpointService()
        self.timeframe_service = TimeframeService()
        self.objective_template_service = ObjectiveTemplateService()
        self.timeframe_template_service = TimeframeTemplateService()
        self.endpoint_template_service = EndpointTemplateService()

        self.library = LibraryVO(name="Library", is_editable=True)
        self.tv = TemplateVO(
            name=self.default_template_name,
            name_plain=self.default_template_name_plain,
        )
        self.im = LibraryItemMetadataVO.get_initial_item_metadata(author="Test")
        self.ot_ar = ObjectiveTemplateAR(
            _uid=self.otr.root_class.get_next_free_uid_and_increment_counter(),
            _template=self.tv,
            _library=self.library,
            _item_metadata=self.im,
            _editable_instance=False,
        )
        self.otr.save(self.ot_ar)

        self.ot_ar: ObjectiveTemplateAR = self.otr.find_by_uid_2(
            self.ot_ar.uid, for_update=True
        )
        self.ot_ar.approve(author="TEST")
        self.otr.save(self.ot_ar)

        self.ot_ar: ObjectiveTemplateAR = self.otr.find_by_uid_2(
            self.ot_ar.uid, for_update=True
        )
        self.ot_ar.create_new_version(
            author="TEST", change_description="Change", template=self.tv
        )
        self.otr.save(self.ot_ar)

        self.ot_ar: ObjectiveTemplateAR = self.otr.find_by_uid_2(
            self.ot_ar.uid, for_update=True
        )
        self.ntv = TemplateVO(
            name=self.changed_template_name,
            name_plain=self.changed_template_name_plain,
        )
        self.ot_ar.edit_draft(
            author="TEST", change_description="Change", template=self.ntv
        )
        self.otr.save(self.ot_ar)

        self.et_ar = EndpointTemplateAR(
            _uid=self.etr.root_class.get_next_free_uid_and_increment_counter(),
            _template=self.tv,
            _library=self.library,
            _item_metadata=self.im,
            _editable_instance=False,
        )
        self.etr.save(self.et_ar)

        self.et_ar: EndpointTemplateAR = self.etr.find_by_uid_2(
            self.et_ar.uid, for_update=True
        )
        self.et_ar.approve(author="TEST")
        self.etr.save(self.et_ar)

        self.et_ar: EndpointTemplateAR = self.etr.find_by_uid_2(
            self.et_ar.uid, for_update=True
        )
        self.et_ar.create_new_version(
            author="TEST", change_description="Change", template=self.tv
        )
        self.etr.save(self.et_ar)

        self.et_ar: EndpointTemplateAR = self.etr.find_by_uid_2(
            self.et_ar.uid, for_update=True
        )
        self.ntv = TemplateVO(
            name=self.changed_template_name,
            name_plain=self.changed_template_name_plain,
        )
        self.et_ar.edit_draft(
            author="TEST", change_description="Change", template=self.ntv
        )
        self.etr.save(self.et_ar)

        self.tt_ar = TimeframeTemplateAR(
            _uid=self.ttr.root_class.get_next_free_uid_and_increment_counter(),
            _template=self.tv,
            _library=self.library,
            _item_metadata=self.im,
            _editable_instance=False,
        )
        self.ttr.save(self.tt_ar)

        self.tt_ar: TimeframeTemplateAR = self.ttr.find_by_uid_2(
            self.tt_ar.uid, for_update=True
        )
        self.tt_ar.approve(author="TEST")
        self.ttr.save(self.tt_ar)

        self.tt_ar: TimeframeTemplateAR = self.ttr.find_by_uid_2(
            self.tt_ar.uid, for_update=True
        )
        self.tt_ar.create_new_version(
            author="TEST", change_description="Change", template=self.tv
        )
        self.ttr.save(self.tt_ar)

        self.tt_ar: TimeframeTemplateAR = self.ttr.find_by_uid_2(
            self.tt_ar.uid, for_update=True
        )
        self.ntv = TemplateVO(
            name=self.changed_template_name,
            name_plain=self.changed_template_name_plain,
        )
        self.tt_ar.edit_draft(
            author="TEST", change_description="Change", template=self.ntv
        )
        self.ttr.save(self.tt_ar)

        self.create_template_parameters(count=14)
        self.create_objectives(count=10, approved=True)
        self.create_endpoints(count=10, approved=True)
        self.create_timeframes(count=10, approved=True)
        study_service = StudyObjectiveSelectionService(author="TEST_USER")
        study_selection_objective_input = StudySelectionObjectiveInput(
            objectiveUid="Objective_000010"
        )
        self.selection: StudySelectionObjective = study_service.make_selection(
            "study_root", study_selection_objective_input
        )

    def create_template_parameters(self, label=TPR_LABEL, count=10):
        self.value_roots = []
        self.value_values = []
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

    def create_objectives(self, count=10, approved=False, retired=False):
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
                objectiveTemplateUid=self.ot_ar.uid,
                libraryName="Library",
                parameterValues=[pv],
            )

            print("CREATE", pv)
            item = self.objective_service.create(template)
            if approved:
                self.objective_service.approve(item.uid)
            if retired:
                self.objective_service.inactivate_final(item.uid)

    def create_timeframes(self, count=10, approved=False, retired=False):
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
            template = TimeframeCreateInput(
                timeframeTemplateUid=self.tt_ar.uid,
                libraryName="Library",
                parameterValues=[pv],
            )

            item = self.timeframe_service.create(template)
            if approved:
                self.timeframe_service.approve(item.uid)
            if retired:
                self.timeframe_service.inactivate_final(item.uid)

    def create_endpoints(self, count=10, approved=False, retired=False):
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
            template = EndpointCreateInput(
                endpointTemplateUid=self.et_ar.uid,
                libraryName="Library",
                parameterValues=[pv],
            )
            item = self.endpoint_service.create(template)
            if approved:
                self.endpoint_service.approve(item.uid)
            if retired:
                self.endpoint_service.inactivate_final(item.uid)

    def test__endpoint_upversion__update(self):
        # given

        endpointData = {
            "endpointLevel": None,
            "endpointUid": "Endpoint_000005",
            "endpointUnits": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "studyObjectiveUid": self.selection.studyObjectiveUid,
            "timeframeUid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService(author="TEST_USER")
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpointData)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latestTimeframe)
        self.assertIsNone(endpoint_selection.latestEndpoint)

        self.endpoint_template_service.approve_cascade(self.et_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.studyEndpointUid,
        )

        self.assertNotEqual(
            selection.endpoint.version, selection.latestEndpoint.version
        )

        # when

        response = endpoint_service.update_selection_to_latest_version_of_endpoint(
            "study_root", selection.studyEndpointUid
        )

        self.assertIsNone(response.latestEndpoint)
        # then
        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyEndpointUid
        )
        self.assertIsNone(selection.latestEndpoint)
        self.assertIsNone(selection.latestTimeframe)

    def test__timeframe_upversion__update(self):
        # given
        endpointData = {
            "endpointLevel": None,
            "endpointUid": "Endpoint_000005",
            "endpointUnits": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "studyObjectiveUid": self.selection.studyObjectiveUid,
            "timeframeUid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService(author="TEST_USER")
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpointData)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latestTimeframe)
        self.assertIsNone(endpoint_selection.latestEndpoint)

        self.timeframe_template_service.approve_cascade(self.tt_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.studyEndpointUid,
        )

        self.assertNotEqual(
            selection.timeframe.version, selection.latestTimeframe.version
        )

        # when
        response = endpoint_service.update_selection_to_latest_version_of_timeframe(
            "study_root", selection.studyEndpointUid
        )

        self.assertIsNone(response.latestTimeframe)
        # then
        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyEndpointUid
        )
        self.assertIsNone(selection.latestTimeframe)
        self.assertIsNone(selection.latestEndpoint)

    def test__timeframe_and_endpoint_upversion__update(self):
        # given
        endpointData = {
            "endpointLevel": None,
            "endpointUid": "Endpoint_000005",
            "endpointUnits": {"separator": "string", "units": ["unit 1", "unit 2"]},
            "studyObjectiveUid": self.selection.studyObjectiveUid,
            "timeframeUid": "Timeframe_000005",
        }
        endpoint_service = StudyEndpointSelectionService(author="TEST_USER")
        endpoint_selection_input: StudySelectionEndpointInput = (
            StudySelectionEndpointInput(**endpointData)
        )
        endpoint_selection: StudySelectionEndpoint = endpoint_service.make_selection(
            "study_root", endpoint_selection_input
        )

        self.assertIsNone(endpoint_selection.latestTimeframe)
        self.assertIsNone(endpoint_selection.latestEndpoint)

        self.timeframe_template_service.approve_cascade(self.tt_ar.uid)
        self.endpoint_template_service.approve_cascade(self.et_ar.uid)

        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root",
            study_selection_uid=endpoint_selection.studyEndpointUid,
        )

        self.assertNotEqual(
            selection.timeframe.version, selection.latestTimeframe.version
        )
        self.assertNotEqual(
            selection.endpoint.version, selection.latestEndpoint.version
        )

        # when
        response = endpoint_service.update_selection_to_latest_version_of_timeframe(
            "study_root", selection.studyEndpointUid
        )

        self.assertIsNone(response.latestTimeframe)
        # then
        selection: StudySelectionEndpoint = endpoint_service.get_specific_selection(
            study_uid="study_root", study_selection_uid=selection.studyEndpointUid
        )
        self.assertIsNone(selection.latestTimeframe)
        self.assertIsNotNone(selection.latestEndpoint)
