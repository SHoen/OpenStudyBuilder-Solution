import unittest

from neomodel import db

from clinical_mdr_api import exceptions
from clinical_mdr_api.models.compound import Compound
from clinical_mdr_api.models.compound_alias import CompoundAlias
from clinical_mdr_api.models.study_selection import (
    StudyCompoundDosing,
    StudyCompoundDosingInput,
    StudySelectionCompound,
    StudySelectionCompoundInput,
    StudySelectionElement,
    StudySelectionElementCreateInput,
)
from clinical_mdr_api.services.concepts.compound_alias_service import (
    CompoundAliasService,
)
from clinical_mdr_api.services.concepts.compound_service import CompoundService
from clinical_mdr_api.services.study_compound_dosing_selection import (
    StudyCompoundDosingSelectionService,
)
from clinical_mdr_api.services.study_compound_selection import (
    StudyCompoundSelectionService,
)
from clinical_mdr_api.services.study_element_selection import (
    StudyElementSelectionService,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    CREATE_BASE_TEMPLATE_PARAMETER_TREE,
    STARTUP_ACTIVITIES,
    STARTUP_ACTIVITY_GROUPS,
    STARTUP_ACTIVITY_INSTANCES,
    STARTUP_ACTIVITY_INSTANCES_CT_INIT,
    STARTUP_ACTIVITY_SUB_GROUPS,
    STARTUP_CT_TERM,
    STARTUP_NUMERIC_VALUES_WITH_UNITS,
    STARTUP_PROJECTS_CYPHER,
    STARTUP_STUDY_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import STUDY_UID, TestUtils


class TestStudyCompoundsService(unittest.TestCase):
    def setUp(self):
        inject_and_clear_db("study.compounds.service")

        db.cypher_query(STARTUP_CT_TERM)
        db.cypher_query(STARTUP_STUDY_CYPHER)
        db.cypher_query(CREATE_BASE_TEMPLATE_PARAMETER_TREE)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES_CT_INIT)
        db.cypher_query(STARTUP_ACTIVITY_GROUPS)
        db.cypher_query(STARTUP_ACTIVITY_SUB_GROUPS)
        db.cypher_query(STARTUP_ACTIVITIES)
        db.cypher_query(STARTUP_ACTIVITY_INSTANCES)
        db.cypher_query(STARTUP_NUMERIC_VALUES_WITH_UNITS)
        db.cypher_query(STARTUP_PROJECTS_CYPHER)

        super().setUp()

    def test_make_selection(self):
        # Create some library compounds and aliases, and select some of them as study interventions

        compound1: Compound = TestUtils.create_compound(
            name="name-AAA",
            dosageFormUids=["dosage_form_uid1"],
            deliveryDevicesUids=["delivery_device_uid1"],
            dispensersUids=["dispenser_uid1"],
            routeOfAdministrationUids=["route_of_administration_uid1"],
            strengthValuesUids=["NumericValueWithUnit_000001"],
            doseFrequencyUids=["dose_frequency_uid1"],
            doseValuesUids=["NumericValueWithUnit_000001"],
        )
        compoundAlias1a: CompoundAlias = TestUtils.create_compound_alias(
            compoundUid=compound1.uid
        )
        compoundAlias1b: CompoundAlias = TestUtils.create_compound_alias(
            compoundUid=compound1.uid
        )

        compound2: Compound = TestUtils.create_compound(
            name="name-BBB",
            dosageFormUids=["dosage_form_uid1"],
            deliveryDevicesUids=["delivery_device_uid1"],
            dispensersUids=["dispenser_uid1"],
            routeOfAdministrationUids=["route_of_administration_uid1"],
            strengthValuesUids=["NumericValueWithUnit_000001"],
            doseFrequencyUids=["dose_frequency_uid1"],
            doseValuesUids=["NumericValueWithUnit_000001"],
        )
        compoundAlias2a: CompoundAlias = TestUtils.create_compound_alias(
            compoundUid=compound1.uid
        )
        compoundAlias2b: CompoundAlias = TestUtils.create_compound_alias(
            compoundUid=compound1.uid
        )

        CompoundService().approve(compound1.uid)
        CompoundService().approve(compound2.uid)
        CompoundAliasService().approve(compoundAlias1a.uid)
        CompoundAliasService().approve(compoundAlias2a.uid)
        CompoundAliasService().approve(compoundAlias1b.uid)
        CompoundAliasService().approve(compoundAlias2b.uid)

        study_selection_element: StudySelectionElement = StudyElementSelectionService(
            "test"
        ).make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudySelectionElementCreateInput(
                name="Elem1", shortName="el1", elementSubTypeUid="term1"
            ),
        )

        # Make a compound selection with compound alias 'compoundAlias1a'
        study_compound_created1: StudySelectionCompound = (
            TestUtils.create_study_compound(
                compoundAliasUid=compoundAlias1a.uid,
                dosageFormUid="dosage_form_uid1",
                deviceUid="delivery_device_uid1",
                dispensedInUid="dispenser_uid1",
                routeOfAdministrationUid="route_of_administration_uid1",
                strengthValueUid="NumericValueWithUnit_000001",
            )
        )
        assert study_compound_created1.studyCompoundUid == "StudyCompound_000001"

        # Make a compound selection with another compound alias, while keeping all other details the same
        study_compound_created2: StudySelectionCompound = StudyCompoundSelectionService(
            "test"
        ).make_selection(
            study_uid=STUDY_UID,
            selection_create_input=StudySelectionCompoundInput(
                compoundAliasUid=compoundAlias2a.uid,
                dosageFormUid="dosage_form_uid1",
                deviceUid="delivery_device_uid1",
                dispensedInUid="dispenser_uid1",
                routeOfAdministrationUid="route_of_administration_uid1",
                strengthValueUid="NumericValueWithUnit_000001",
            ),
        )
        assert study_compound_created2.studyCompoundUid == "StudyCompound_000003"

        # Try to make a compound selection with the same compound alias 'compoundAlias1a' and all other details
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    dosageFormUid="dosage_form_uid1",
                    deviceUid="delivery_device_uid1",
                    dispensedInUid="dispenser_uid1",
                    routeOfAdministrationUid="route_of_administration_uid1",
                    strengthValueUid="NumericValueWithUnit_000001",
                ),
            )
        msg = (
            "Compound selection with the specified combination of compound, "
            + "pharmaceutical dosage form, strength, route of administration, dispenser and delivery device already exists."
        )
        assert context.exception.msg == msg

        # Make a compound dosing selection with just-created study compound 'study_compound_created1'
        study_compound_dosing_created1: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    studyCompoundUid=study_compound_created1.studyCompoundUid,
                    doseFrequencyUid="dose_frequency_uid1",
                    doseValueUid="NumericValueWithUnit_000001",
                    studyElementUid=study_selection_element.elementUid,
                ),
            )
        )

        assert (
            study_compound_dosing_created1.studyCompoundDosingUid
            == "StudyCompoundDosing_000001"
        )

        # Make a compound dosing selection with another study compound, while keeping all other details the same
        study_compound_dosing_created2: StudyCompoundDosing = (
            StudyCompoundDosingSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    studyCompoundUid=study_compound_created2.studyCompoundUid,
                    doseFrequencyUid="dose_frequency_uid1",
                    doseValueUid="NumericValueWithUnit_000001",
                    studyElementUid=study_selection_element.elementUid,
                ),
            )
        )
        assert (
            study_compound_dosing_created2.studyCompoundDosingUid
            == "StudyCompoundDosing_000002"
        )

        # Try to make a compound dosing selection with the same study compound and all other details
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    studyCompoundUid=study_compound_created1.studyCompoundUid,
                    doseFrequencyUid="dose_frequency_uid1",
                    doseValueUid="NumericValueWithUnit_000001",
                    studyElementUid=study_selection_element.elementUid,
                ),
            )
        msg = "Compound dosing selection with the specified compound, dose value and dose frequency already exists."
        assert context.exception.msg == msg

        # Try to make a compound intervention with invalid selection values for:
        #   - Pharmaceutical dosage form
        #   - Compound strength value
        #   - Route of administration
        #   - Dispenser
        #   - Delivery device
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    dosageFormUid="dosage_form_uidXYZ",
                ),
            )
        msg = (
            "Selected pharmaceutical dosage form is not valid for compound 'name-AAA'."
        )
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    deviceUid="delivery_device_uidXYZ",
                ),
            )
        msg = "Selected delivery device is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    dispensedInUid="dispenser_uidXYZ",
                ),
            )
        msg = "Selected dispenser is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    routeOfAdministrationUid="route_of_administration_uidXYZ",
                ),
            )
        msg = "Selected route of administration is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudySelectionCompoundInput(
                    compoundAliasUid=compoundAlias1a.uid,
                    strengthValueUid="NumericValueWithUnit_00000XYZ",
                ),
            )
        msg = "Selected strength value is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        # Try to make a compound dosing intervention with invalid selection values for:
        #   - dose value
        #   - dose frequency
        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    studyCompoundUid=study_compound_created1.studyCompoundUid,
                    doseValueUid="NumericValueWithUnit_00000XYZ",
                    studyElementUid=study_selection_element.elementUid,
                ),
            )
        msg = "Selected dose value is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg

        with self.assertRaises(exceptions.BusinessLogicException) as context:
            StudyCompoundDosingSelectionService("test").make_selection(
                study_uid=STUDY_UID,
                selection_create_input=StudyCompoundDosingInput(
                    studyCompoundUid=study_compound_created1.studyCompoundUid,
                    doseFrequencyUid="dose_frequency_uidXYZ",
                    studyElementUid=study_selection_element.elementUid,
                ),
            )
        msg = "Selected dose frequency is not valid for compound 'name-AAA'."
        assert context.exception.msg == msg
