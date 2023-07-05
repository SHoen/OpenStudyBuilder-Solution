import unittest

from clinical_mdr_api.config import STUDY_ENDPOINT_TP_NAME
from clinical_mdr_api.models import study_selections
from clinical_mdr_api.models.listings.listings_study import (
    RegistryIdentifiersListingModel,
    StudyArmListingModel,
    StudyAttributesListingModel,
    StudyCohortListingModel,
    StudyCriteriaListingModel,
    StudyDesignMatrixListingModel,
    StudyElementListingModel,
    StudyEndpointListingModel,
    StudyEpochListingModel,
    StudyMetadataListingModel,
    StudyObjectiveListingModel,
    StudyPopulationListingModel,
    StudyTypeListingModel,
    StudyVisitListingModel,
)
from clinical_mdr_api.services.listings.listings_study import (
    StudyMetadataListingService,
)
from clinical_mdr_api.services.studies.study import StudyService
from clinical_mdr_api.services.studies.study_epoch import StudyEpochService
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import inject_base_data
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_some_visits,
    create_study_arm,
    create_study_branch_arm,
    create_study_cohort,
    create_study_design_cell,
    create_study_element,
    create_study_epoch_codelists_ret_cat_and_lib,
    generate_description_json_model,
    get_catalogue_name_library_name,
    high_level_study_design_json_model_to_vo,
    input_metadata_in_study,
    registry_identifiers_json_model_to_vo,
    study_intervention_json_model_to_vo,
    study_population_json_model_to_vo,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils


class TestStudyListing(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db("StudyListingTest")
        TestUtils.create_library(name="UCUM", is_editable=True)
        inject_base_data()
        codelist = TestUtils.create_ct_codelist()
        TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
        study_service = StudyService(user="some_user")
        studies = study_service.get_all()
        cls.study_uid = studies.items[0].uid
        cls.study_number = studies.items[
            0
        ].current_metadata.identification_metadata.study_number
        # Inject study metadata
        input_metadata_in_study(cls.study_uid)
        # Create study epochs
        create_study_epoch_codelists_ret_cat_and_lib(use_test_utils=True)
        catalogue_name, library_name = get_catalogue_name_library_name(
            use_test_utils=True
        )
        study_epoch = TestUtils.create_study_epoch(
            study_uid=cls.study_uid, epoch_subtype="EpochSubType_0001"
        )
        study_epoch2 = TestUtils.create_study_epoch(
            study_uid=cls.study_uid, epoch_subtype="EpochSubType_0002"
        )
        # Create study elements
        element_type_codelist = create_codelist(
            "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
        )
        element_type_term = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0001",
            1,
            catalogue_name,
            library_name,
        )
        element_type_term_2 = create_ct_term(
            element_type_codelist.codelist_uid,
            "Element Type",
            "ElementType_0002",
            2,
            catalogue_name,
            library_name,
        )
        study_elements = [
            create_study_element(element_type_term.uid, cls.study_uid),
            create_study_element(element_type_term_2.uid, cls.study_uid),
        ]

        # Create study arms
        codelist = create_codelist(
            name="Arm Type",
            uid="CTCodelist_00009",
            catalogue=catalogue_name,
            library=library_name,
        )
        arm_type = create_ct_term(
            codelist=codelist.codelist_uid,
            name="Arm Type",
            uid="ArmType_0001",
            order=1,
            catalogue_name=catalogue_name,
            library_name=library_name,
        )

        create_study_arm(
            study_uid=cls.study_uid,
            name="Arm_Name_1",
            short_name="Arm_Short_Name_1",
            code="Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )
        create_study_arm(
            study_uid=cls.study_uid,
            name="Arm_Name_2",
            short_name="Arm_Short_Name_2",
            code="Arm_code_2",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup2",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )
        create_study_arm(
            study_uid=cls.study_uid,
            name="Arm_Name_3",
            short_name="Arm_Short_Name_3",
            code="Arm_code_3",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup3",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )

        create_study_arm(
            study_uid=cls.study_uid,
            name="Arm_Name_9",
            short_name="Arm_Short_Name_9",
            code="Arm_code_9",
            description="desc...",
            colour_code="colour...",
            randomization_group="Arm_randomizationGroup9",
            number_of_subjects=100,
            arm_type_uid=arm_type.uid,
        )

        # Create study design cells
        create_study_design_cell(
            study_element_uid=study_elements[0].element_uid,
            study_epoch_uid=study_epoch.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=cls.study_uid,
        )
        create_study_design_cell(
            study_element_uid=study_elements[0].element_uid,
            study_epoch_uid=study_epoch2.uid,
            study_arm_uid="StudyArm_000003",
            study_uid=cls.study_uid,
        )

        create_study_design_cell(
            study_element_uid=study_elements[1].element_uid,
            study_epoch_uid=study_epoch2.uid,
            study_arm_uid="StudyArm_000001",
            study_uid=cls.study_uid,
        )

        create_study_design_cell(
            study_element_uid=study_elements[0].element_uid,
            study_epoch_uid=study_epoch2.uid,
            study_arm_uid="StudyArm_000005",
            study_uid=cls.study_uid,
        )

        # Create study branch arms
        create_study_branch_arm(
            study_uid=cls.study_uid,
            name="Branch_Arm_Name_1",
            short_name="Branch_Arm_Short_Name_1",
            code="Branch_Arm_code_1",
            description="desc...",
            colour_code="colour...",
            randomization_group="Branch_Arm_randomizationGroup",
            number_of_subjects=100,
            arm_uid="StudyArm_000003",
        )

        # Create study cohort
        create_study_cohort(
            study_uid=cls.study_uid,
            name="Cohort_Name_1",
            short_name="Cohort_Short_Name_1",
            code="Cohort_code_1",
            description="desc...",
            colour_code="desc...",
            number_of_subjects=100,
            arm_uids=["StudyArm_000001"],
        )

        # Create study visit
        create_some_visits(
            use_test_utils=True,
            create_epoch_codelist=False,
            study_uid=cls.study_uid,
            epoch1=study_epoch,
            epoch2=study_epoch2,
        )

        # Create CT Terms
        ct_term_inclusion_criteria = TestUtils.create_ct_term(
            sponsor_preferred_name="INCLUSION CRITERIA"
        )
        ct_term_exclusion_criteria = TestUtils.create_ct_term(
            sponsor_preferred_name="EXCLUSION CRITERIA"
        )

        # Create criteria templates
        incl_criteria_template_1 = TestUtils.create_criteria_template(
            type_uid=ct_term_inclusion_criteria.term_uid
        )
        excl_criteria_template_1 = TestUtils.create_criteria_template(
            type_uid=ct_term_exclusion_criteria.term_uid
        )

        # Create study criterias
        TestUtils.create_study_criteria(
            study_uid=cls.study_uid,
            criteria_template_uid=incl_criteria_template_1.uid,
            library_name=incl_criteria_template_1.library.name,
            parameter_terms=[],
        )

        TestUtils.create_study_criteria(
            study_uid=cls.study_uid,
            criteria_template_uid=excl_criteria_template_1.uid,
            library_name=excl_criteria_template_1.library.name,
            parameter_terms=[],
        )

        # Create objective template
        objective_template = TestUtils.create_objective_template()
        TestUtils.create_study_objective(
            study_uid=cls.study_uid,
            objective_template_uid=objective_template.uid,
            parameter_terms=[],
        )

        # Create study objectives
        study_objective = TestUtils.create_study_objective(
            study_uid=cls.study_uid,
            objective_template_uid=objective_template.uid,
            library_name=objective_template.library.name,
            parameter_terms=[],
        )

        # Create endpoint templates
        TestUtils.create_template_parameter(STUDY_ENDPOINT_TP_NAME)
        endpoint_template = TestUtils.create_endpoint_template()

        unit_definitions = [
            TestUtils.create_unit_definition(name="unit1"),
            TestUtils.create_unit_definition(name="unit2"),
        ]
        unit_separator = "and"
        timeframe_template = TestUtils.create_timeframe_template()
        timeframe = TestUtils.create_timeframe(
            timeframe_template_uid=timeframe_template.uid
        )

        # Create study endpoints
        TestUtils.create_study_endpoint(
            study_uid=cls.study_uid,
            endpoint_template_uid=endpoint_template.uid,
            endpoint_units=study_selections.study_selection.EndpointUnitsInput(
                units=[u.uid for u in unit_definitions], separator=unit_separator
            ),
            timeframe_uid=timeframe.uid,
            library_name=endpoint_template.library.name,
        )

        TestUtils.create_study_endpoint(
            study_uid=cls.study_uid,
            endpoint_template_uid=endpoint_template.uid,
            library_name=endpoint_template.library.name,
            timeframe_uid=timeframe.uid,
            study_objective_uid=study_objective.study_objective_uid,
        )

    def test_study_metadata_listing(self):
        self.maxDiff = None
        study_listing_service = StudyMetadataListingService()
        output = study_listing_service.get_study_metadata(self.study_number)
        expected_output = StudyMetadataListingModel(
            study_title=generate_description_json_model(),
            registry_identifiers=RegistryIdentifiersListingModel.from_study_registry_identifiers_vo(
                registry_identifiers_json_model_to_vo(),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
            ),
            study_type=StudyTypeListingModel.from_high_level_study_design_vo(
                high_level_study_design_json_model_to_vo(),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
            ),
            study_attributes=StudyAttributesListingModel.from_study_intervention_vo(
                study_intervention_json_model_to_vo(),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
            ),
            study_population=StudyPopulationListingModel.from_study_population_vo(
                study_population_json_model_to_vo(),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
                find_dictionary_term_by_uid=study_listing_service.dict_term_repo.find_by_uid,
            ),
            study_arms=StudyArmListingModel.from_study_selection_arm_ar(
                study_uid=self.study_uid,
                study_selection_arm_ar=study_listing_service.arm_repo.find_by_study(
                    study_uid=self.study_uid
                ),
                find_simple_term_arm_type_by_term_uid=study_listing_service.ct_attr_repo.find_by_uid,
                find_multiple_connected_branch_arm=study_listing_service.branch_arm_repo.find_by_arm,
            ),
            study_cohorts=StudyCohortListingModel.from_study_selection_cohort_ar(
                study_selection_cohort_ar=study_listing_service.cohort_repo.find_by_study(
                    study_uid=self.study_uid,
                ),
            ),
            study_epochs=StudyEpochListingModel.from_all_study_epochs(
                all_study_epochs=StudyEpochService()
                .get_all_epochs(
                    study_uid=self.study_uid,
                )
                .items,
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
            ),
            study_elements=StudyElementListingModel.from_study_element_ar(
                study_element_ar=study_listing_service.element_repo.find_by_study(
                    study_uid=self.study_uid,
                ),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
            ),
            study_design_matrix=StudyDesignMatrixListingModel.from_all_study_design_cells(
                all_design_cells=study_listing_service.design_cell_repo.find_all_design_cells_by_study(
                    study_uid=self.study_uid,
                ),
            ),
            study_visits=StudyVisitListingModel.from_all_study_visits(
                all_study_visits=study_listing_service.get_all_visits(
                    study_uid=self.study_uid,
                )
            ),
            study_criterias=StudyCriteriaListingModel.from_study_criteria_ar(
                study_criteria_ar=study_listing_service.study_criteria_repo.find_by_study(
                    study_uid=self.study_uid,
                ),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
                find_criteria_by_uid=study_listing_service.criteria_repo.find_by_uid_2,
            ),
            study_objectives=StudyObjectiveListingModel.from_study_objective_ar(
                study_objective_ar=study_listing_service.study_objective_repo.find_by_study(
                    study_uid=self.study_uid,
                ),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
                find_objective_by_uid=study_listing_service.objective_repo.find_by_uid_2,
            ),
            study_endpoints=StudyEndpointListingModel.from_study_endpoint_ar(
                study_endpoint_ar=study_listing_service.study_endpoint_repo.find_by_study(
                    study_uid=self.study_uid,
                ),
                find_term_by_uid=study_listing_service.ct_attr_repo.find_by_uid,
                find_endpoint_by_uid=study_listing_service.endpoint_repo.find_by_uid_2,
                find_timeframe_by_uid=study_listing_service.timeframe_repo.find_by_uid_2,
            ),
        )

        # Check study title
        self.assertEqual(output.study_title, expected_output.study_title)

        # Check study identifiers
        self.assertEqual(
            output.registry_identifiers,
            expected_output.registry_identifiers,
        )
        self.assertCountEqual(
            output.registry_identifiers,
            expected_output.registry_identifiers,
        )

        # Check study type
        self.assertCountEqual(output.study_type, expected_output.study_type)
        self.assertEqual(output.study_type, expected_output.study_type)

        # Check study attributes
        self.assertCountEqual(output.study_attributes, expected_output.study_attributes)
        self.assertEqual(output.study_attributes, expected_output.study_attributes)

        # Check study population
        self.assertCountEqual(output.study_population, expected_output.study_population)
        self.assertEqual(output.study_population, expected_output.study_population)

        # Check study arms
        self.assertCountEqual(output.study_arms, expected_output.study_arms)
        self.assertEqual(output.study_arms, expected_output.study_arms)

        # Check study cohorts
        self.assertCountEqual(output.study_cohorts, expected_output.study_cohorts)
        self.assertEqual(output.study_cohorts, expected_output.study_cohorts)

        # Check study epochs
        self.assertCountEqual(output.study_epochs, expected_output.study_epochs)
        self.assertEqual(output.study_epochs, expected_output.study_epochs)

        # Check study elements
        self.assertCountEqual(output.study_elements, expected_output.study_elements)
        self.assertEqual(output.study_elements, expected_output.study_elements)

        # Check study design matrix
        self.assertCountEqual(
            output.study_design_matrix, expected_output.study_design_matrix
        )
        self.assertEqual(
            output.study_design_matrix, expected_output.study_design_matrix
        )

        # Check study visits
        self.assertCountEqual(output.study_visits, expected_output.study_visits)
        self.assertEqual(output.study_visits, expected_output.study_visits)

        # Check study criterias
        self.assertCountEqual(output.study_criterias, expected_output.study_criterias)
        self.assertEqual(output.study_criterias, expected_output.study_criterias)

        # Check study criterias
        self.assertCountEqual(output.study_objectives, expected_output.study_objectives)
        self.assertEqual(output.study_objectives, expected_output.study_objectives)

        # Check study criterias
        self.assertCountEqual(output.study_endpoints, expected_output.study_endpoints)
        self.assertEqual(output.study_endpoints, expected_output.study_endpoints)
