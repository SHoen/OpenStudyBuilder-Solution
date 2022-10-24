import unittest

from neomodel import db

from clinical_mdr_api.domain.study_selection.study_epoch import StudyEpochVO, TimelineAR
from clinical_mdr_api.domain.study_selection.study_visit import StudyVisitVO
from clinical_mdr_api.exceptions import ValidationException
from clinical_mdr_api.models import StudyVisit
from clinical_mdr_api.models.study_epoch import StudyEpochEditInput
from clinical_mdr_api.models.study_visit import (
    StudyVisitCreateInput,
    StudyVisitEditInput,
)
from clinical_mdr_api.services.study_epoch import StudyEpochService
from clinical_mdr_api.services.study_visit import StudyVisitService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_library_data,
    create_study_epoch,
    create_study_visit_codelists,
    create_visit_with_update,
    generate_study_root,
    get_unit_uid_by_name,
    preview_visit_with_update,
    update_visit_with_update,
)


class TestStudyVisitManagement(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("studiesvisitstest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        create_library_data()

        self.study = generate_study_root()
        create_study_visit_codelists()

        self.epoch1 = create_study_epoch("EpochSubType_0001")
        self.epoch2 = create_study_epoch("EpochSubType_0002")
        self.epoch3 = create_study_epoch("EpochSubType_0003")
        self.DAYUID = get_unit_uid_by_name("day")

    def test__list__visits_studies(self):
        inputs = dict(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.order, 1)
        self.assertEqual(preview.visit_number, 1)
        self.assertEqual(preview.unique_visit_number, 100)

        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=12,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=10,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        inputs = dict(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0004",
            timeReferenceUid="VisitSubType_0001",
            timeValue=20,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.order, 4)
        self.assertEqual(preview.visit_number, 4)
        self.assertEqual(preview.unique_visit_number, 400)

        v3 = create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0004",
            timeReferenceUid="VisitSubType_0001",
            timeValue=20,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        self.assertEqual(v3.unique_visit_number, preview.unique_visit_number)
        v4 = create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0002",
            timeReferenceUid="VisitSubType_0001",
            timeValue=30,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0001",
            visitSubLabelReference=None,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        v5 = create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0002",
            timeValue=31,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0002",
            visitSubLabelReference=v4.uid,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )
        visit_service: StudyVisitService = StudyVisitService()
        visits = visit_service.get_all_visits(self.study.uid)
        self.assertEqual(len(visits.items), 6)

        v3new: StudyVisit = visit_service.find_by_uid(v3.uid)
        self.assertEqual(v3new.order, 4)
        self.assertEqual(v3new.visit_number, 4)
        self.assertEqual(v3new.unique_visit_number, 400)

        self.assertEqual(v3new.studyDayNumber, 21)
        self.assertEqual(v3new.minVisitWindowValue, -1)
        self.assertEqual(v3new.maxVisitWindowValue, 1)

        v5new: StudyVisit = visit_service.find_by_uid(v4.uid)
        self.assertEqual(v5new.order, 5)
        self.assertEqual(v5new.visit_number, 5)
        print("V%sub", v5new)
        self.assertEqual(v5new.unique_visit_number, 500)

        v6new: StudyVisit = visit_service.find_by_uid(v5.uid)
        self.assertEqual(v6new.order, 5)
        self.assertEqual(v5new.visit_number, 5)
        print("V%sub", v6new)
        self.assertEqual(v6new.unique_visit_number, 510)

        references = visit_service.get_all_references(self.study.uid)
        self.assertEqual(len(references), 2)
        visit: StudyVisit = references[0]
        self.assertEqual(visit.visitTypeName, "BASELINE")
        visit: StudyVisit = references[1]
        self.assertEqual(visit.visitTypeName, "BASELINE2")

        inputs = dict(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0002",
            timeValue=40,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0003",
            visitSubLabelReference=v4.uid,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )
        preview = preview_visit_with_update(self.study.uid, **inputs)
        print("PREVIEW", preview)
        self.assertEqual(preview.unique_visit_number, 520)

        epoch_service: StudyEpochService = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        epoch1 = epochs[0]
        epoch2 = epochs[1]
        study_epochs = epoch_service.repo.find_all_epochs_by_study(self.study.uid)

        epoch = epoch_service.find_by_uid(epoch1.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            studyUid=epoch.studyUid,
            startRule=start_rule,
            endRule=end_rule,
            changeDescription="rules change",
        )
        epoch_service.edit(
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )

        visit_repo = epoch_service._repos.study_visit_repository
        study_visits = visit_repo.find_all_visits_by_study_uid(self.study.uid)
        timeline = TimelineAR(self.study.uid, _visits=study_visits)
        epochs = timeline.collect_visits_to_epochs(study_epochs)
        visit_vo: StudyVisitVO
        epoch_vo: StudyEpochVO
        for visit_vo in timeline.ordered_study_visits:
            print(
                "VIS",
                visit_vo.uid,
                visit_vo.study_day_number,
                visit_vo.get_unified_window(),
            )
            self.assertEqual(
                visit_vo.get_unified_window(),
                (visit_vo.study_day_number - 1, visit_vo.study_day_number + 1),
            )

        for v in study_visits:
            if v.uid == v3.uid:
                visit3_vo: StudyVisitVO = v
                self.assertEqual(visit3_vo.study_day_number, 21)
                self.assertEqual(visit3_vo.study_week_number, 3)
        for epoch_vo in study_epochs:
            print(
                "EPOCH", epoch_vo.uid, epoch_vo.get_start_day(), epoch_vo.get_end_day()
            )
        print("EPOCH 1", epoch1)
        print("EPOCH 2", epoch2)
        self.assertEqual(epoch1.startDay, 1)
        self.assertEqual(epoch1.endDay, 31)
        self.assertEqual(epoch2.startDay, epoch1.endDay)
        self.assertEqual(epoch2.endDay, 62)

        v3update = update_visit_with_update(
            v3new.uid,
            uid=v3new.uid,
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0004",
            timeReferenceUid="VisitSubType_0001",
            timeValue=25,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        self.assertEqual(v3update.studyDayNumber, 26)

    def test__create__props_are_correctly_saved(self):
        visit_service = StudyVisitService()

        input_values = dict(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            visitContactModeUid="VisitContactMode_0002",
            maxVisitWindowValue=10,
            minVisitWindowValue=0,
            showVisit=True,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
            epochAllocationUid="EpochAllocation_0002",
        )
        visit = create_visit_with_update(**input_values)
        visit_after_create = visit_service.find_by_uid(uid=visit.uid)
        self.assertEqual(
            visit_after_create.visitContactModeUid, input_values["visitContactModeUid"]
        )
        self.assertEqual(
            visit_after_create.maxVisitWindowValue, input_values["maxVisitWindowValue"]
        )
        self.assertEqual(
            visit_after_create.minVisitWindowValue, input_values["minVisitWindowValue"]
        )
        self.assertEqual(visit_after_create.timeUnitUid, input_values["timeUnitUid"])
        self.assertEqual(visit_after_create.timeValue, input_values["timeValue"])
        self.assertEqual(visit_after_create.show_visit, input_values["showVisit"])
        self.assertEqual(
            visit_after_create.timeReferenceUid, input_values["timeReferenceUid"]
        )
        self.assertEqual(visit_after_create.visitTypeUid, input_values["visitTypeUid"])
        self.assertEqual(
            visit_after_create.epochAllocationUid, input_values["epochAllocationUid"]
        )

    def test__edit_visit_successfully_handled(self):
        visit_service = StudyVisitService()
        visit = create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
            epochAllocationUid="EpochAllocation_0001",
        )

        edit_input = dict(
            uid=visit.uid,
            studyEpochUid=visit.study_epoch_uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=7,
            timeUnitUid=self.DAYUID,
            visitContactModeUid="VisitContactMode_0002",
            maxVisitWindowValue=10,
            minVisitWindowValue=0,
            visitWindowUnitUid=visit.visitWindowUnitUid,
            showVisit=True,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
            epochAllocationUid="EpochAllocation_0002",
        )
        visit_service.edit(
            study_uid=visit.studyUid,
            study_visit_uid=visit.uid,
            study_visit_input=StudyVisitEditInput(**edit_input),
        )
        visit_after_update = visit_service.find_by_uid(uid=visit.uid)
        self.assertEqual(
            visit_after_update.visitContactModeUid, edit_input["visitContactModeUid"]
        )
        self.assertEqual(
            visit_after_update.maxVisitWindowValue, edit_input["maxVisitWindowValue"]
        )
        self.assertEqual(
            visit_after_update.minVisitWindowValue, edit_input["minVisitWindowValue"]
        )
        self.assertEqual(visit_after_update.timeUnitUid, edit_input["timeUnitUid"])
        self.assertEqual(visit_after_update.timeValue, edit_input["timeValue"])
        self.assertEqual(visit_after_update.show_visit, edit_input["showVisit"])
        self.assertEqual(
            visit_after_update.timeReferenceUid, edit_input["timeReferenceUid"]
        )
        self.assertEqual(visit_after_update.visitTypeUid, edit_input["visitTypeUid"])
        self.assertEqual(
            visit_after_update.epochAllocationUid, edit_input["epochAllocationUid"]
        )

    def test__version_visits(self):
        visit_service = StudyVisitService()
        visit = create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
            epochAllocationUid="EpochAllocation_0001",
        )

        edit_input = dict(
            uid=visit.uid,
            studyEpochUid=visit.study_epoch_uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=7,
            timeUnitUid=self.DAYUID,
            visitContactModeUid="VisitContactMode_0002",
            maxVisitWindowValue=10,
            minVisitWindowValue=0,
            visitWindowUnitUid=visit.visitWindowUnitUid,
            showVisit=True,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
            epochAllocationUid="EpochAllocation_0002",
        )
        visit_service.edit(
            study_uid=visit.studyUid,
            study_visit_uid=visit.uid,
            study_visit_input=StudyVisitEditInput(**edit_input),
        )
        visit_after_update = visit_service.find_by_uid(uid=visit.uid)
        self.assertEqual(
            visit_after_update.visitContactModeUid, edit_input["visitContactModeUid"]
        )
        self.assertEqual(
            visit_after_update.maxVisitWindowValue, edit_input["maxVisitWindowValue"]
        )
        self.assertEqual(
            visit_after_update.minVisitWindowValue, edit_input["minVisitWindowValue"]
        )
        self.assertEqual(visit_after_update.timeUnitUid, edit_input["timeUnitUid"])
        self.assertEqual(visit_after_update.timeValue, edit_input["timeValue"])
        self.assertEqual(visit_after_update.show_visit, edit_input["showVisit"])
        self.assertEqual(
            visit_after_update.timeReferenceUid, edit_input["timeReferenceUid"]
        )
        self.assertEqual(visit_after_update.visitTypeUid, edit_input["visitTypeUid"])
        self.assertEqual(
            visit_after_update.epochAllocationUid, edit_input["epochAllocationUid"]
        )

        visit_service.audit_trail(
            visit_uid=visit.uid,
            study_uid=visit.studyUid,
        )

        time_value = 30
        create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0002",
            timeReferenceUid="VisitSubType_0001",
            timeValue=time_value,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0001",
            visitSubLabelReference=None,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        visits_versions = visit_service.audit_trail_all_visits(
            study_uid=visit.studyUid,
        )

        current_visit = visits_versions[0]
        previous_visit = visits_versions[1]
        current_visit_2 = visits_versions[2]
        self.assertEqual(
            current_visit.visitContactModeUid, edit_input["visitContactModeUid"]
        )
        self.assertEqual(
            current_visit.maxVisitWindowValue, edit_input["maxVisitWindowValue"]
        )
        self.assertEqual(
            current_visit.minVisitWindowValue, edit_input["minVisitWindowValue"]
        )
        self.assertEqual(current_visit.timeUnitUid, edit_input["timeUnitUid"])
        self.assertEqual(current_visit.timeValue, edit_input["timeValue"])
        self.assertEqual(current_visit.show_visit, edit_input["showVisit"])
        self.assertEqual(current_visit.timeReferenceUid, edit_input["timeReferenceUid"])
        self.assertEqual(current_visit.visitTypeUid, edit_input["visitTypeUid"])
        self.assertEqual(
            current_visit.epochAllocationUid, edit_input["epochAllocationUid"]
        )
        self.assertEqual(current_visit.uid, previous_visit.uid)
        self.assertGreater(current_visit.startDate, previous_visit.startDate)
        self.assertEqual(previous_visit.changes, {})
        self.assertEqual(current_visit_2.changes, {})

    def test__create_subvisits_uvn__reordered_successfully(self):
        visit_service = StudyVisitService()
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        time_value = 30
        first_visit_in_seq_of_subvisits = create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0002",
            timeReferenceUid="VisitSubType_0001",
            timeValue=time_value,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0001",
            visitSubLabelReference=None,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        sub_visit_uvn = 200
        # we add so many subvists as there is a logic of
        # recalculating subvists unique-visit-numbers when we exceed allowed limits
        for i in range(1, 21):
            create_visit_with_update(
                studyEpochUid=self.epoch2.uid,
                visitTypeUid="VisitType_0003",
                timeReferenceUid="VisitSubType_0005",
                timeValue=time_value + i,
                timeUnitUid=self.DAYUID,
                visitSubLabelCodelistUid="VisitSubLabel_0002",
                visitSubLabelReference=first_visit_in_seq_of_subvisits.uid,
                isGlobalAnchorVisit=False,
                visitClass="SINGLE_VISIT",
                visitSubclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
            )
            # check unique visit numbers before recalculation
            if i == 9:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visitSubclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.studyDayNumber - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 10
                    )
            # check unique visit numbers after first recalculation
            if i == 10:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visitSubclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.studyDayNumber - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 5
                    )
            # check unique visit numbers after second recalculation
            if i == 20:
                all_visits = visit_service.get_all_visits(
                    study_uid=self.study.uid
                ).items
                for sub_idx, sub_visit in enumerate(all_visits[1:]):
                    if (
                        sub_visit.visitSubclass
                        == "ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV"
                    ):
                        self.assertEqual(
                            sub_visit.studyDayNumber - 1,
                            time_value + time_value + sub_idx,
                        )
                    self.assertEqual(
                        sub_visit.unique_visit_number, sub_visit_uvn + sub_idx * 1
                    )
        create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0005",
            timeValue=-1,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0002",
            visitSubLabelReference=first_visit_in_seq_of_subvisits.uid,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ADDITIONAL_SUBVISIT_IN_A_GROUP_OF_SUBV",
        )

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        all_visits = [visit for visit in all_visits if visit.visit_number == 2]

        self.assertEqual(all_visits[0].unique_visit_number, sub_visit_uvn)
        self.assertEqual(all_visits[0].studyDayNumber - 1, time_value - 1)
        self.assertEqual(all_visits[1].unique_visit_number, sub_visit_uvn + 1)
        self.assertEqual(all_visits[1].studyDayNumber - 1, time_value)

    def test__get_global_anchor_visit(self):
        visit_service = StudyVisitService()

        global_anchor_visit = visit_service.get_global_anchor_visit(
            study_uid=self.study.uid
        )
        self.assertIsNone(global_anchor_visit)

        vis = create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        global_anchor_visit = visit_service.get_global_anchor_visit(
            study_uid=self.study.uid
        )
        self.assertEqual(global_anchor_visit.uid, vis.uid)
        self.assertEqual(global_anchor_visit.visitName, vis.visitName)
        self.assertEqual(global_anchor_visit.visitTypeName, vis.visitTypeName)

    def test__get_anchor_visits_in_a_group_of_subvisits(self):
        visit_service = StudyVisitService()

        anchor_visits = visit_service.get_anchor_visits_in_a_group_of_subvisits(
            study_uid=self.study.uid
        )
        self.assertEqual(anchor_visits, [])

        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        anchor_visit = create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0002",
            timeReferenceUid="VisitSubType_0001",
            timeValue=30,
            timeUnitUid=self.DAYUID,
            visitSubLabelCodelistUid="VisitSubLabel_0001",
            visitSubLabelReference=None,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="ANCHOR_VISIT_IN_GROUP_OF_SUBV",
        )
        anchor_visits = visit_service.get_anchor_visits_in_a_group_of_subvisits(
            study_uid=self.study.uid
        )
        self.assertEqual(len(anchor_visits), 1)
        self.assertEqual(anchor_visit.uid, anchor_visits[0].uid)
        self.assertEqual(anchor_visit.visitName, anchor_visits[0].visitName)
        self.assertEqual(anchor_visit.visitTypeName, anchor_visits[0].visitTypeName)

    def test__epochs_durations_are_calculated_properly_when_having_empty_epoch(self):

        epoch_service = StudyEpochService()

        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch3.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=10,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch3.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=30,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )

        study_epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(study_epochs), 3)
        self.assertEqual(study_epochs[0].startDay, 1)
        self.assertEqual(study_epochs[0].duration, 0)
        self.assertEqual(study_epochs[0].endDay, 1)
        self.assertEqual(study_epochs[1].startDay, 1)
        self.assertEqual(study_epochs[1].duration, 10)
        self.assertEqual(study_epochs[1].endDay, 11)
        self.assertEqual(study_epochs[2].startDay, 11)
        self.assertEqual(study_epochs[2].duration, 20)
        self.assertEqual(study_epochs[2].endDay, 31)

    def test__epochs_durations_are_calculated_properly_when_having_last_epoch_with_one_visit(
        self,
    ):

        epoch_service = StudyEpochService()

        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=10,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=30,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch2.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=40,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch3.uid,
            visitTypeUid="VisitType_0003",
            timeReferenceUid="VisitSubType_0001",
            timeValue=50,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        study_epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(study_epochs), 3)
        self.assertEqual(study_epochs[0].startDay, 1)
        self.assertEqual(study_epochs[0].duration, 30)
        self.assertEqual(study_epochs[0].endDay, 31)
        self.assertEqual(study_epochs[1].startDay, 31)
        self.assertEqual(study_epochs[1].duration, 20)
        self.assertEqual(study_epochs[1].endDay, 51)
        self.assertEqual(study_epochs[2].startDay, 51)
        self.assertEqual(study_epochs[2].duration, 7)
        self.assertEqual(study_epochs[2].endDay, 58)

    def test__create_visit_with_duplicated_timing__error_raised(self):
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        with self.assertRaises(ValidationException):
            create_visit_with_update(
                studyEpochUid=self.epoch1.uid,
                visitTypeUid="VisitType_0001",
                timeReferenceUid="VisitSubType_0001",
                timeValue=0,
                timeUnitUid=self.DAYUID,
                isGlobalAnchorVisit=True,
                visitClass="SINGLE_VISIT",
                visitSubclass="SINGLE_VISIT",
            )

    def test__create_unscheduled_visit_without_time_data__no_error_is_raised(self):

        visit_service: StudyVisitService = StudyVisitService()
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0001",
            timeReferenceUid="VisitSubType_0001",
            timeValue=0,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=True,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        create_visit_with_update(
            studyEpochUid=self.epoch1.uid,
            visitTypeUid="VisitType_0002",
            timeReferenceUid="VisitSubType_0001",
            timeValue=10,
            timeUnitUid=self.DAYUID,
            isGlobalAnchorVisit=False,
            visitClass="SINGLE_VISIT",
            visitSubclass="SINGLE_VISIT",
        )
        non_visit_input = {
            "studyEpochUid": self.epoch1.uid,
            "consecutiveVisitGroup": "",
            "showVisit": True,
            "description": "description",
            "startRule": "startRule",
            "endRule": "endRule",
            "note": "note",
            "visitContactModeUid": "VisitContactMode_0001",
            "visitTypeUid": "VisitType_0003",
            "isGlobalAnchorVisit": False,
            "visitClass": "NON_VISIT",
        }
        visit_input = StudyVisitCreateInput(**non_visit_input)
        visit_service.create(study_uid=self.study.uid, study_visit_input=visit_input)

        all_visits = visit_service.get_all_visits(study_uid=self.study.uid).items

        self.assertEqual(len(all_visits), 3)
        self.assertEqual(all_visits[0].timeValue, 0)
        self.assertEqual(all_visits[1].timeValue, 10)
        self.assertEqual(all_visits[2].timeValue, None)
        self.assertEqual(all_visits[2].timeReferenceUid, None)
        self.assertEqual(all_visits[2].timeReferenceName, None)
        self.assertEqual(all_visits[2].visit_number, 29500)
        self.assertEqual(all_visits[2].minVisitWindowValue, -9999)
        self.assertEqual(all_visits[2].maxVisitWindowValue, 9999)
