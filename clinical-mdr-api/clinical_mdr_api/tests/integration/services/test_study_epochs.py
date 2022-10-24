import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.models.study_epoch import (
    StudyEpoch,
    StudyEpochCreateInput,
    StudyEpochEditInput,
)
from clinical_mdr_api.services.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
)


class TestStudyEpochManagement(unittest.TestCase):
    TPR_LABEL = "ParameterName"

    def setUp(self):
        inject_and_clear_db("studiesepochstest")
        db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
        db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

        # Generate UIDs
        StudyRoot.generate_node_uids_if_not_present()
        self.study = StudyRoot.nodes.all()[0]
        create_study_epoch_codelists_ret_cat_and_lib()

    def test__list_epoch_studies(self):

        epoch_service = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 0

    def test__create_study_epoch(self):
        epoch_service = StudyEpochService()
        study_epoch_create_input = StudyEpochCreateInput(
            studyUid="study_root",
            startRule="startRule",
            endRule="endRule",
            description="test_description",
            epochSubType="EpochSubType_0001",
            duration=0,
            durationUnit="durationUnit",
            order="1",
            colorHash="#1100FF",
        )
        StudyEpochService().create(
            "study_root", study_epoch_input=study_epoch_create_input
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 1

    def test__create_study_epoch_with_not_unique_epoch_sub_type__not_raises_ForbiddenError(
        self,
    ):
        epoch_sub_type_uid = "EpochSubType_0001"
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)

        epoch_service = StudyEpochService()
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 2)

    def test__create_study_epoch_with_not_unique_epoch_sub_type__epoch_names_are_properly_assigned(
        self,
    ):
        epoch_service = StudyEpochService()

        first_epoch_sub_type_name = "Epoch Subtype1"
        first_epoch_sub_type_uid = "EpochSubType_0002"

        create_study_epoch(epoch_sub_type_uid=first_epoch_sub_type_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].epochName, first_epoch_sub_type_name)
        self.assertEqual(epochs[0].order, 1)

        epoch_sub_type_uid = "EpochSubType_0001"
        epoch_sub_type_name = "Epoch Subtype"

        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 2)
        self.assertEqual(epochs[0].epochName, first_epoch_sub_type_name)
        self.assertEqual(epochs[0].order, 1)
        self.assertEqual(epochs[1].epochName, epoch_sub_type_name)
        self.assertEqual(epochs[1].order, 2)

        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)

        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 3)
        self.assertEqual(epochs[0].epochName, first_epoch_sub_type_name)
        self.assertEqual(epochs[0].order, 1)
        self.assertEqual(epochs[1].epochName, epoch_sub_type_name + " 1")
        self.assertEqual(epochs[1].order, 2)
        self.assertEqual(epochs[2].epochName, epoch_sub_type_name + " 2")
        self.assertEqual(epochs[2].order, 3)

    def test__create_study_epoch_no_unit__created(self):
        epoch_service = StudyEpochService()
        study_epoch_create_input = StudyEpochCreateInput(
            studyUid="study_root",
            startRule="startRule",
            endRule="endRule",
            description="test_description",
            epochSubType="EpochSubType_0001",
            duration=0,
            colorHash="#1100FF",
        )
        StudyEpochService().create(
            "study_root", study_epoch_input=study_epoch_create_input
        )
        epochs = epoch_service.get_all_epochs(self.study.uid).items

        assert len(epochs) == 1

    def test__reorder_epochs(self):
        epoch_service = StudyEpochService()
        ep_epoch_sub_type_uid = "EpochSubType_0001"
        ep_epoch_sub_type_name = "Epoch Subtype"
        ep1: StudyEpoch = create_study_epoch(ep_epoch_sub_type_uid)
        ep2 = create_study_epoch(ep_epoch_sub_type_uid)
        ep3 = create_study_epoch(ep_epoch_sub_type_uid)

        ep1 = epoch_service.find_by_uid(ep1.uid)
        ep2 = epoch_service.find_by_uid(ep2.uid)
        ep3 = epoch_service.find_by_uid(ep3.uid)

        self.assertEqual(ep1.order, 1)
        self.assertEqual(ep1.epochName, ep_epoch_sub_type_name + " 1")
        self.assertEqual(ep2.order, 2)
        self.assertEqual(ep2.epochName, ep_epoch_sub_type_name + " 2")
        self.assertEqual(ep3.order, 3)
        self.assertEqual(ep3.epochName, ep_epoch_sub_type_name + " 3")

        epoch_service.reorder(ep3.uid, 0)

        ep_after1 = epoch_service.find_by_uid(ep1.uid)
        ep_after2 = epoch_service.find_by_uid(ep2.uid)
        ep_after3 = epoch_service.find_by_uid(ep3.uid)

        self.assertEqual(ep_after1.order, 2)
        self.assertEqual(ep_after1.epochName, ep_epoch_sub_type_name + " 2")
        self.assertEqual(ep_after2.order, 3)
        self.assertEqual(ep_after2.epochName, ep_epoch_sub_type_name + " 3")
        self.assertEqual(ep_after3.order, 1)
        self.assertEqual(ep_after3.epochName, ep_epoch_sub_type_name + " 1")

        epoch_service.reorder(ep1.uid, 2)

        ep_after1 = epoch_service.find_by_uid(ep1.uid)
        ep_after2 = epoch_service.find_by_uid(ep2.uid)
        ep_after3 = epoch_service.find_by_uid(ep3.uid)

        self.assertEqual(ep_after1.order, 3)
        self.assertEqual(ep_after1.epochName, ep_epoch_sub_type_name + " 3")
        self.assertEqual(ep_after2.order, 2)
        self.assertEqual(ep_after2.epochName, ep_epoch_sub_type_name + " 2")
        self.assertEqual(ep_after3.order, 1)
        self.assertEqual(ep_after3.epochName, ep_epoch_sub_type_name + " 1")

        epoch_sub_type_uid2 = "EpochSubType_0002"
        epoch_sub_type_name2 = "Epoch Subtype1"
        epoch_sub_type_uid3 = "EpochSubType_0003"
        epoch_sub_type_name3 = "Epoch Subtype2"
        epoch_subtype_2 = create_study_epoch(epoch_sub_type_uid2)
        epoch_subtype_3 = create_study_epoch(epoch_sub_type_uid3)
        ep2 = epoch_service.find_by_uid(epoch_subtype_2.uid)
        self.assertEqual(ep2.order, 4)
        self.assertEqual(ep2.epochName, epoch_sub_type_name2)
        ep3 = epoch_service.find_by_uid(epoch_subtype_3.uid)
        self.assertEqual(ep3.order, 5)
        self.assertEqual(ep3.epochName, epoch_sub_type_name3)
        epoch_service.reorder(ep3.uid, 3)
        ep2 = epoch_service.find_by_uid(epoch_subtype_2.uid)
        self.assertEqual(ep2.order, 5)
        self.assertEqual(ep2.epochName, epoch_sub_type_name2)
        ep3 = epoch_service.find_by_uid(epoch_subtype_3.uid)
        self.assertEqual(ep3.order, 4)
        self.assertEqual(ep3.epochName, epoch_sub_type_name3)

    def test__create_study_epoch_with_not_unique_epoch_sub_type__new_epoch_is_being_created(
        self,
    ):
        epoch_service = StudyEpochService()

        epoch_sub_type_uid = "EpochSubType_0001"
        epoch_sub_type_name = "Epoch Subtype"
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].epochName, epoch_sub_type_name)

        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)

        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 4)
        self.assertEqual(epochs[0].epochName, epoch_sub_type_name + " 1")
        self.assertEqual(epochs[1].epochName, epoch_sub_type_name + " 2")
        self.assertEqual(epochs[2].epochName, epoch_sub_type_name + " 3")
        self.assertEqual(epochs[3].epochName, epoch_sub_type_name + " 4")

    def test__preview_study_epoch_should_not_bump_epoch_counter(
        self,
    ):
        epoch_service = StudyEpochService()

        epoch_sub_type_uid = "EpochSubType_0001"
        epoch_sub_type_name = "Epoch Subtype"
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].epochName, epoch_sub_type_name)

        preview_input = StudyEpochCreateInput(
            studyUid="study_root",
            startRule="startRule",
            endRule="endRule",
            description="test_description",
            epochSubType=epoch_sub_type_uid,
            colorHash="#1100FF",
        )
        epoch_service.preview(study_uid=self.study.uid, study_epoch_input=preview_input)

        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].epochName, epoch_sub_type_name)

    def test__edit_epoch_color(self):
        epoch: StudyEpoch = create_study_epoch("EpochSubType_0001")

        epoch_service = StudyEpochService()

        epoch = epoch_service.find_by_uid(epoch.uid)
        start_rule = "New start rule"
        end_rule = "New end rule"
        edit_input = StudyEpochEditInput(
            studyUid=epoch.studyUid,
            startRule=start_rule,
            endRule=end_rule,
            changeDescription="rules change",
        )
        edited_epoch = epoch_service.edit(
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        edited_epoch = epoch_service.find_by_uid(edited_epoch.uid)
        self.assertEqual(edited_epoch.startRule, start_rule)
        self.assertEqual(edited_epoch.endRule, end_rule)
        # verify that properties not sent in the payload were not overridden
        self.assertEqual(edited_epoch.epochSubType, epoch.epochSubType)
        self.assertEqual(edited_epoch.epochType, epoch.epochType)
        self.assertEqual(edited_epoch.duration, epoch.duration)
        self.assertEqual(edited_epoch.colorHash, epoch.colorHash)
        self.assertEqual(edited_epoch.order, epoch.order)
        self.assertEqual(edited_epoch.uid, epoch.uid)

        edit_input = StudyEpochEditInput(
            studyUid=epoch.studyUid,
            colorHash="#FFFFFF",
            changeDescription="color change",
        )
        edited_epoch = epoch_service.edit(
            study_epoch_uid=epoch.uid,
            study_epoch_input=edit_input,
        )
        epoch = epoch_service.find_by_uid(edited_epoch.uid)
        self.assertEqual(epoch.colorHash, "#FFFFFF")

    def test__get_versions(self):
        epoch: StudyEpoch = create_study_epoch(epoch_sub_type_uid="EpochSubType_0001")
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(epoch.uid)
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
        epoch_versions = epoch_service.audit_trail(
            epoch_uid=epoch.uid, study_uid=epoch.studyUid
        )

        current_epoch = epoch_versions[0]
        previous_epoch = epoch_versions[1]
        self.assertEqual(current_epoch.changes["startRule"], True)
        self.assertEqual(current_epoch.startRule, start_rule)
        self.assertEqual(current_epoch.changes["endRule"], True)
        self.assertEqual(current_epoch.endRule, end_rule)
        self.assertEqual(previous_epoch.changes, {})

        # test all versions
        epoch: StudyEpoch = create_study_epoch(epoch_sub_type_uid="EpochSubType_0002")
        epoch_service = StudyEpochService()
        epoch = epoch_service.find_by_uid(epoch.uid)
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
        epoch_versions = epoch_service.audit_trail_all_epochs(
            study_uid=epoch.studyUid,
        )

        current_epoch = epoch_versions[0]
        previous_epoch = epoch_versions[1]
        current_epoch_2 = epoch_versions[2]
        previous_epoch_2 = epoch_versions[3]
        self.assertEqual(current_epoch.changes["startRule"], True)
        self.assertEqual(current_epoch.startRule, start_rule)
        self.assertEqual(current_epoch.changes["endRule"], True)
        self.assertEqual(current_epoch.endRule, end_rule)
        self.assertEqual(previous_epoch.changes, {})

        self.assertEqual(current_epoch_2.changes["startRule"], True)
        self.assertEqual(current_epoch_2.startRule, start_rule)
        self.assertEqual(current_epoch_2.changes["endRule"], True)
        self.assertEqual(current_epoch_2.endRule, end_rule)
        self.assertEqual(previous_epoch_2.changes, {})

    def test__delete_study_epoch__epochs_are_recalculated(self):
        epoch_service = StudyEpochService()

        first_epoch_sub_type_name = "Epoch Subtype1"
        first_epoch_sub_type_uid = "EpochSubType_0002"

        create_study_epoch(epoch_sub_type_uid=first_epoch_sub_type_uid)
        epochs = epoch_service.get_all_epochs(self.study.uid).items
        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0].epochName, first_epoch_sub_type_name)
        self.assertEqual(epochs[0].order, 1)

        epoch_sub_type_uid = "EpochSubType_0001"
        epoch_sub_type_name = "Epoch Subtype"
        epoch1 = create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        epoch2 = create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
        epoch3 = create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)

        ep1 = epoch_service.find_by_uid(epoch1.uid)
        ep2 = epoch_service.find_by_uid(epoch2.uid)
        ep3 = epoch_service.find_by_uid(epoch3.uid)

        self.assertEqual(ep1.epochName, epoch_sub_type_name + " 1")
        self.assertEqual(ep1.order, 2)
        self.assertEqual(ep2.epochName, epoch_sub_type_name + " 2")
        self.assertEqual(ep2.order, 3)
        self.assertEqual(ep3.epochName, epoch_sub_type_name + " 3")
        self.assertEqual(ep3.order, 4)

        epoch_service.delete(study_uid=ep1.studyUid, study_epoch_uid=ep1.uid)

        ep1 = epoch_service.find_by_uid(epoch2.uid)
        ep2 = epoch_service.find_by_uid(epoch3.uid)

        self.assertEqual(ep1.epochName, epoch_sub_type_name + " 1")
        self.assertEqual(ep1.order, 2)
        self.assertEqual(ep2.epochName, epoch_sub_type_name + " 2")
        self.assertEqual(ep2.order, 3)

        epoch_service.delete(study_uid=ep1.studyUid, study_epoch_uid=ep1.uid)
        ep1 = epoch_service.find_by_uid(ep2.uid)
        self.assertEqual(ep1.epochName, epoch_sub_type_name)
        self.assertEqual(ep1.order, 2)

    def test__duplicated_supplemental_epoch_created__value_error_is_raised(self):
        epoch_sub_type_uid = "Basic_uid"
        create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)

        with self.assertRaises(ValueError):
            create_study_epoch(epoch_sub_type_uid=epoch_sub_type_uid)
