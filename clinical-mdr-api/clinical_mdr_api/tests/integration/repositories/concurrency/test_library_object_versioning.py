import unittest
from typing import Sequence

from neomodel import db

from clinical_mdr_api.domain._utils import strip_html
from clinical_mdr_api.domain.library.object import (
    ParameterValueEntryVO,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domain.library.objectives import ObjectiveAR
from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryVO,
    TemplateVO,
    VersioningException,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class ObjectiveRepositoryConcurrencyTest(unittest.TestCase):
    """
    Tests whether concurrency checks are in place when library objects change state.
    It checks that performing two versioning operations at the same time ensures that no invalid
    operations take place, given the object state.

    Note: these tests are only performed for objectives, as endpoints and timeframes use the same repository implementation.
    """

    _repos = MetaRepository()

    library_name = "Sponsor"
    user_initials = "TEST"
    template_name = "Example Template"
    parameter_values: Sequence[ParameterValueEntryVO] = []

    # These are set as part of the test for [Objective, Endpoint, Timeframe]
    template_uid = None
    object_uid = None
    object_ar = None
    template_repository = None
    object_repository = None

    parameterized_template_vo_to_edit: ParametrizedTemplateVO

    INIT_TEST_DATA = """
    CREATE (l:Library{name: 'Sponsor', is_editable: true});
    """

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db("concurrency.versioning")

    def set_up_base_graph_for_objectives(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(self.INIT_TEST_DATA)
        self.template_uid = "ObjectiveTemplate_000002"
        self.object_uid = "Objective_000001"
        self.template_repository = self._repos.objective_template_repository
        self.object_repository = self._repos.objective_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name,
            template_name_plain=strip_html(self.template_name),
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=(lambda _: True)
        )
        objective_template_ar = ObjectiveTemplateAR.from_input_values(
            author=self.user_initials,
            template=template_vo,
            library=library_vo,
            template_value_exists_callback=(lambda _: False),
            generate_uid_callback=(lambda: self.template_uid),
            editable_instance=False,
        )
        # Create template
        with db.transaction:
            self.template_repository.save(objective_template_ar)
        # Approve template
        with db.transaction:
            objective_template_ar = self.template_repository.find_by_uid_2(
                self.template_uid, for_update=True
            )
            objective_template_ar.approve(author=self.user_initials)
            self.template_repository.save(objective_template_ar)
        parameterized_template_vo = (
            ParametrizedTemplateVO.from_name_and_parameter_values(
                name=self.template_name,
                template_uid=self.template_uid,
                parameter_values=self.parameter_values,
            )
        )
        self.parameterized_template_vo_to_edit = (
            ParametrizedTemplateVO.from_name_and_parameter_values(
                name=f"{self.template_name} to edit",
                template_uid=self.template_uid,
                parameter_values=self.parameter_values,
            )
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=(lambda _: True)
        )
        self.object_ar = ObjectiveAR.from_input_values(
            author=self.user_initials,
            template=parameterized_template_vo,
            library=library_vo,
        )
        self.object_repository.save(self.object_ar)

    def test_soft_delete_objective_aborted_on_approval(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.approve_object_without_save,
                concurrent_operation=self.soft_delete_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("Object has been accepted", str(message.exception))

    def test_approve_objective_aborted_on_soft_delete(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.soft_delete_object_with_save,
                concurrent_operation=self.approve_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Object labels were changed - likely the object was deleted in a concurrent transaction.",
            str(message.exception),
        )

    def test_edit_objective_aborted_on_approval(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.approve_object_without_save,
                concurrent_operation=self.edit_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("The object is not in draft status.", str(message.exception))

    def test_edit_objective_aborted_on_soft_delete(self):
        self.set_up_base_graph_for_objectives()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.soft_delete_object_with_save,
                concurrent_operation=self.edit_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Object labels were changed - likely the object was deleted in a concurrent transaction.",
            str(message.exception),
        )

    def test_inactivate_aborted_on_new_version(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.new_version_without_save,
                concurrent_operation=self.inactivate_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("Cannot retire draft version.", str(message.exception))

    def test_new_version_aborted_on_inactivate(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.inactivate_object_without_save,
                concurrent_operation=self.new_version_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual("Cannot create new Draft version", str(message.exception))

    def test_new_version_aborted_on_reactivate(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with db.transaction:
            self.inactivate_object_with_save()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.reactivate_object_without_save,
                concurrent_operation=self.new_version_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Only RETIRED version can be reactivated.", str(message.exception)
        )

    def test_reactivate_aborted_on_new_version(self):
        self.set_up_base_graph_for_objectives()
        with db.transaction:
            self.approve_object_with_save()
        with db.transaction:
            self.inactivate_object_with_save()
        with self.assertRaises(VersioningException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.new_version_without_save,
                concurrent_operation=self.reactivate_object_with_save,
                main_operation_after=self.save_object,
            )
        self.assertEqual(
            "Only RETIRED version can be reactivated.", str(message.exception)
        )

    """
    Helper functions to be used by the locking validator:
    """

    def approve_object_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.approve(author=self.user_initials, change_description="APPROVED!")
        self.object_ar = object_ar

    def approve_object_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.approve(author=self.user_initials, change_description="APPROVED!")
        self.object_repository.save(object_ar)

    def soft_delete_object_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.soft_delete()
        self.object_ar = object_ar

    def soft_delete_object_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.soft_delete()
        self.object_repository.save(object_ar)

    def edit_object_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.edit_draft(
            author=self.user_initials,
            change_description="Edited",
            template=self.parameterized_template_vo_to_edit,
        )
        self.object_ar = object_ar

    def edit_object_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.edit_draft(
            author=self.user_initials,
            change_description="Edited",
            template=self.parameterized_template_vo_to_edit,
        )
        self.object_repository.save(self.object_ar)

    def inactivate_object_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.inactivate(
            author=self.user_initials, change_description="Inactivated"
        )
        self.object_ar = object_ar

    def inactivate_object_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.inactivate(
            author=self.user_initials, change_description="Inactivated"
        )
        self.object_repository.save(self.object_ar)

    def new_version_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar._create_new_version(
            author=self.user_initials, change_description="New Draft"
        )
        self.object_ar = object_ar

    def new_version_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar._create_new_version(
            author=self.user_initials, change_description="New Draft"
        )
        self.object_repository.save(self.object_ar)

    def reactivate_object_without_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.reactivate(
            author=self.user_initials, change_description="Reactivated"
        )
        self.object_ar = object_ar

    def reactivate_object_with_save(self):
        object_ar = self.object_repository.find_by_uid_2(
            self.object_uid, for_update=True
        )
        object_ar.reactivate(
            author=self.user_initials, change_description="Reactivated"
        )
        self.object_repository.save(self.object_ar)

    def save_object(self):
        self.object_repository.save(self.object_ar)
