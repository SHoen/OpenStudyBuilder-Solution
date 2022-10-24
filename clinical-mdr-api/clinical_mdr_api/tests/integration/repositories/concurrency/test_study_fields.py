import unittest
from typing import Optional

from neomodel import db

from clinical_mdr_api.domain.controlled_terminology.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domain.study_definition_aggregate.root import StudyDefinitionAR
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domain_repositories.study_definition.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definition.study_title.study_title_repository import (
    StudyTitleRepository,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_STUDY_FIELD_CYPHER,
    inject_base_data,
)


class StudyFieldsConcurrencyTest(unittest.TestCase):
    """
    Tests the following case:
    - The study (and selected nodes) are NOT locked when creating/modifying/deleting a new study field.
    """

    _repos = MetaRepository()

    library_name = "Sponsor"
    user_initials = "TEST"

    studies_repository: StudyDefinitionRepository
    study_title_repository: StudyTitleRepository
    ct_term_attributes_repository: CTTermAttributesRepository
    ct_term_names_repository: CTTermNameRepository

    ct_term_attributes_ar: CTTermAttributesAR
    ct_term_name_ar: CTTermNameAR
    study_ar: Optional[StudyDefinitionAR]

    @classmethod
    def setUpClass(cls):
        inject_and_clear_db("concurrency.studyfields")
        inject_base_data()

    def set_up_base_graph_for_studies(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(STARTUP_STUDY_FIELD_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
        db.cypher_query("CREATE CONSTRAINT ON (n:CTTermRoot) ASSERT n.uid IS UNIQUE;")

        self.study_title_repository = self._repos.study_title_repository
        self.studies_repository = self._repos.study_definition_repository
        self.ct_term_attributes_repository = self._repos.ct_term_attributes_repository
        self.ct_term_names_repository = self._repos.ct_term_name_repository

        codelist_uid = "editable_cr"

        with db.transaction:
            study_ar = StudyDefinitionAR.from_initial_values(
                generate_uid_callback=lambda: "Study_000001",
                initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                    project_number="456",
                    study_acronym="STUDY_ACR",
                    study_number="123",
                    registry_identifiers=RegistryIdentifiersVO.from_input_values(
                        ct_gov_id="CT_GOV_ID",
                        eudract_id="EUDRACT_ID",
                        universal_trial_number_UTN="UTN",
                        japanese_trial_registry_id_JAPIC="JAPIC",
                        investigational_new_drug_application_number_IND="IND",
                        ct_gov_id_null_value_code=None,
                        eudract_id_null_value_code=None,
                        universal_trial_number_UTN_null_value_code=None,
                        japanese_trial_registry_id_JAPIC_null_value_code=None,
                        investigational_new_drug_application_number_IND_null_value_code=None,
                    ),
                ),
                project_exists_callback=(lambda _: True),
                study_title_exists_callback=(lambda _, study_number: False),
                study_short_title_exists_callback=(lambda _, study_number: False),
                study_number_exists_callback=(lambda _: False),
            )

            self.studies_repository.save(study_ar)
        # add study title term
        with db.transaction:
            library_name = "Sponsor"
            library_vo = LibraryVO.from_repository_values(
                library_name=library_name, is_editable=True
            )

            ct_term_attributes_vo = CTTermAttributesVO.from_repository_values(
                codelist_uid=codelist_uid,
                catalogue_name="SDTM CT",
                concept_id=None,
                code_submission_value="code_submission_value",
                name_submission_value="name_submission_value",
                preferred_term="preferred_term",
                definition="definition",
            )

            self.ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                generate_uid_callback=lambda: "C49802",
                ct_term_attributes_vo=ct_term_attributes_vo,
                library=library_vo,
                author="TODO Initials",
            )
            self.ct_term_attributes_repository.save(self.ct_term_attributes_ar)

        with db.transaction:
            ct_term_attributes_ar = self.ct_term_attributes_repository.find_by_uid(
                "C49802", for_update=True
            )
            ct_term_attributes_ar.approve(author="TODO Initials")
            self.ct_term_attributes_repository.save(ct_term_attributes_ar)

        with db.transaction:
            ct_term_name_vo = CTTermNameVO.from_repository_values(
                codelist_uid=codelist_uid,
                catalogue_name="SDTM CT",
                name="StudyTitle",
                name_sentence_case="study_title",
                order=1,
            )

            self.ct_term_name_ar = CTTermNameAR.from_input_values(
                generate_uid_callback=lambda: "C49802",
                ct_term_name_vo=ct_term_name_vo,
                library=library_vo,
                author="TODO Initials",
            )

            self.ct_term_names_repository.save(self.ct_term_name_ar)

    def test_add_study_field_not_waiting_for_ct_term_approval(self):
        """
        The intended functionality is that adding study fields does not need concurrency checks,
        we confirm no shared locks are grabbed.
        """
        self.set_up_base_graph_for_studies()
        with self.assertRaises(AssertionError) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.add_study_field_without_save,
                concurrent_operation=self.approve_and_save_ct_term_name,
                main_operation_after=self.save_study_ar,
            )
        self.assertEqual(
            "The thread for approve_and_save_ct_term_name has completed. No shared "
            "locks were grabbed by the main transaction, and concurrent updates may create an invalid state in the graph.",
            str(message.exception),
        )

    def approve_and_save_ct_term_name(self):
        ct_term_name_ar = self.ct_term_names_repository.find_by_uid(
            "C49802", for_update=True
        )
        ct_term_name_ar.approve(author="TODO Initials")
        self.ct_term_names_repository.save(ct_term_name_ar)

    def add_study_field_without_save(self):
        self.study_ar = self.studies_repository.find_by_uid(
            "Study_000001", for_update=True
        )
        study_description = StudyDescriptionVO.from_input_values(
            study_title="my title", study_short_title="my short title"
        )
        self.study_ar.edit_metadata(
            new_study_description=study_description,
            study_title_exists_callback=lambda _, study_number: False,
            study_short_title_exists_callback=lambda _, study_number: False,
        )

    def save_study_ar(self):
        self.studies_repository.save(self.study_ar)
