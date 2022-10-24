from typing import Optional

from neomodel import db

from clinical_mdr_api.domain.controlled_terminology.ct_term_name import (
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_get_all_query_utils import (
    create_term_name_aggregate_instances_from_cypher_result,
)
from clinical_mdr_api.domain_repositories.controlled_terminology.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CodelistTermRelationship,
    CTTermNameRoot,
    CTTermNameValue,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)


class CTTermNameRepository(CTTermGenericRepository[CTTermNameAR]):
    root_class = CTTermNameRoot
    value_class = CTTermNameValue
    relationship_from_root = "has_name_root"

    def term_specific_exists_by_name(self, term_name: str) -> bool:
        query = """
            MATCH (term_ver_root:CTTermNameRoot)-[:LATEST]->(term_ver_value:CTTermNameValue {name: $term_name})
            RETURN term_ver_value
            """
        result, _ = db.cypher_query(query, {"term_name": term_name})
        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict
    ) -> CTTermNameAR:
        return create_term_name_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=False
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTTermNameRoot,
        library: Optional[Library],
        relationship: VersionRelationship,
        value: CTTermNameValue,
    ) -> CTTermNameAR:
        ct_term_root_node = root.has_root.single()
        ct_codelist_root_node = ct_term_root_node.has_term.single()
        has_term_relationship: CodelistTermRelationship = (
            ct_codelist_root_node.has_term.relationship(ct_term_root_node)
        )

        return CTTermNameAR.from_repository_values(
            uid=ct_term_root_node.uid,
            ct_term_name_vo=CTTermNameVO.from_repository_values(
                codelist_uid=ct_codelist_root_node.uid,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                order=has_term_relationship.order,
                catalogue_name=ct_codelist_root_node.has_codelist.single().name,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(self, ar: CTTermNameAR, value: VersionValue) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: CTTermNameRoot, ar: CTTermNameAR
    ) -> CTTermNameValue:
        for itm in root.has_version.filter(
            name=ar.ct_term_vo.name, name_sentence_case=ar.ct_term_vo.name_sentence_case
        ):
            return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired
        new_value = self.value_class(
            name=ar.ct_term_vo.name, name_sentence_case=ar.ct_term_vo.name_sentence_case
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTTermNameAR, value: VersionValue):
        return (
            ar.ct_term_vo.name != value.name
            or ar.ct_term_vo.name_sentence_case != value.name_sentence_case
        )

    def _create(self, item: CTTermNameAR) -> CTTermNameAR:
        """
        Creates new CTTermNameAR, checks possibility based on library setting, then creates database representation,
        Creates CTTermNameRoot and CTTermNameValue database objects,
        recreates AR based on created database model and returns created AR.
        Saving into database is necessary due to uid creation process that require saving object to database.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(
            name=item.ct_term_vo.name,
            name_sentence_case=item.ct_term_vo.name_sentence_case,
        )
        self._db_save_node(root)

        (root, value, _, _, _,) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        ct_term_root_node = CTTermRoot.nodes.get_or_none(uid=item.uid)
        ct_term_root_node.has_name_root.connect(root)
        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        """
        Method maintains TemplateParameterValueRoot and TemplateParameterValue labels when saving CTTermNameAR.
        :param versioned_object:
        :param root:
        :param value:
        :return None:
        """

        maintain_order_query = """
        MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[has_term:HAS_TERM]->
            (term_root:CTTermRoot {uid:$term_uid})
        CALL apoc.do.case([
        
            // CTTermRoot was just created and order is not set yet  
            has_term.order IS NULL,
            'SET has_term.order = $order',
            
            // order was changed, HAS_TERM relationship has to be updated
            has_term.order <> $order,
            'CREATE (codelist_root)-[had_term:HAD_TERM]->(term_root)
            SET had_term.start_date=has_term.start_date
            SET had_term.end_date=datetime()
            SET had_term.user_initials=$user_initials
            SET had_term.order=has_term.order
            DELETE has_term
            CREATE (codelist_root)-[new_has_term:HAS_TERM]->(term_root)
            SET new_has_term.start_date=datetime()
            SET new_has_term.end_date=NULL
            SET new_has_term.user_initials=$user_initials
            SET new_has_term.order=$order'
        ], 
        '',
        {
            has_term: has_term, 
            order: $order,
            codelist_root: codelist_root,
            term_root: term_root,
            user_initials: $user_initials
        })
        YIELD value
        RETURN value            
        """
        db.cypher_query(
            maintain_order_query,
            {
                "codelist_uid": versioned_object.ct_term_vo.codelist_uid,
                "term_uid": versioned_object.uid,
                "order": versioned_object.ct_term_vo.order,
                "user_initials": versioned_object.item_metadata.user_initials,
            },
        )

        maintain_template_parameter_query = """
            MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->
                (codelist_ver_value:TemplateParameter)
            WITH codelist_root, codelist_ver_value
            MATCH (term_root:CTTermRoot {uid: $term_uid})-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
            MERGE (codelist_ver_value)-[hv:HAS_VALUE]->(term_ver_root)
            SET term_ver_root:TemplateParameterValueRoot
            SET term_ver_value:TemplateParameterValue
        """
        db.cypher_query(
            maintain_template_parameter_query,
            {
                "codelist_uid": versioned_object.ct_term_vo.codelist_uid,
                "term_uid": versioned_object.uid,
            },
        )
        TemplateParameterValueRoot.generate_node_uids_if_not_present()

    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        return False
