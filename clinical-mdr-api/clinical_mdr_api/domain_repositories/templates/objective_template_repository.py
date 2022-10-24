from typing import Optional

from neomodel import db

from clinical_mdr_api.domain.templates.objective_template import ObjectiveTemplateAR
from clinical_mdr_api.domain.versioned_object_aggregate import (
    InstantiationCountsVO,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.generic_template_repository import (
    GenericTemplateRepository,  # type: ignore
)
from clinical_mdr_api.domain_repositories.models.generic import (  # type: ignore
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.objective_template import (  # type: ignore
    ObjectiveTemplateRoot,
    ObjectiveTemplateValue,
)


class ObjectiveTemplateRepository(GenericTemplateRepository[ObjectiveTemplateAR]):
    root_class = ObjectiveTemplateRoot
    value_class = ObjectiveTemplateValue

    def check_exists_by_name_in_study(self, name: str, study_uid: str) -> bool:
        query = """
            MATCH (study_root:StudyRoot{uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_OBJECTIVE]->(:StudyObjective)-
            [:HAS_SELECTED_OBJECTIVE]->(:ObjectiveValue)<-[:LATEST]-(or:ObjectiveRoot)<-[:HAS_OBJECTIVE]-(:ObjectiveTemplateRoot)-[:LATEST]->(otv:ObjectiveTemplateValue {name:$name})
            RETURN or
            """
        result, _ = db.cypher_query(query, {"study_uid": study_uid, "name": name})

        return len(result) > 0 and len(result[0]) > 0

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: ObjectiveTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ObjectiveTemplateValue,
        study_count: Optional[int] = None,
        counts: InstantiationCountsVO = None
    ) -> ObjectiveTemplateAR:

        return ObjectiveTemplateAR.from_repository_values(
            uid=root.uid,
            editable_instance=root.editable_instance,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self._get_template(value),
            confirmatory_testing=root.confirmatory_testing,
            study_count=study_count,
            counts=counts,
        )

    def _create(self, item: ObjectiveTemplateAR) -> ObjectiveTemplateAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Set confirmatory_testing property
        * Attaching root node to indication nodes
        * Attaching root node to category nodes
        """
        item = super()._create(item)
        root = self.root_class.nodes.get(uid=item.uid)

        root.confirmatory_testing = item.confirmatory_testing
        self._db_save_node(root)

        if item.indications:
            for indication in item.indications:
                indication = self._get_indication(indication.uid)
                root.has_indication.connect(indication)
        if item.categories:
            for category in item.categories:
                category = self._get_category(category[0].uid)
                root.has_category.connect(category)

        return item

    def patch_confirmatory_testing(
        self, uid: str, confirmatory_testing: Optional[bool] = None
    ) -> None:
        root = self.root_class.nodes.get(uid=uid)
        if confirmatory_testing is None and root.confirmatory_testing is not None:
            root.confirmatory_testing = None
        elif confirmatory_testing is not None:
            root.confirmatory_testing = confirmatory_testing

        self._db_save_node(root)
