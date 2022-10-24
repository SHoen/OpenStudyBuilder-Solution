from typing import Optional, Tuple, cast

from neomodel import db

from clinical_mdr_api.domain.unit_definition.unit_definition import (
    CTTerm,
    UnitDefinitionAR,
    UnitDefinitionValueVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models._utils import convert_to_datetime
from clinical_mdr_api.domain_repositories.models.concepts import (
    UnitDefinitionRoot,
    UnitDefinitionValue,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import UCUMTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterValueRoot,
)
from clinical_mdr_api.models.unit_definition import UnitDefinitionModel


class UnitDefinitionRepository(ConceptGenericRepository[UnitDefinitionAR]):

    value_class = UnitDefinitionValue
    root_class = UnitDefinitionRoot
    user: str
    return_model = UnitDefinitionModel

    def specific_alias_clause(self) -> str:
        return """
        WITH *,
            concept_value.si_unit as siUnit,
            concept_value.display_unit AS displayUnit,
            concept_value.master_unit as masterUnit,
            concept_value.convertible_unit as convertibleUnit,
            concept_value.us_conventional_unit as usConventionalUnit,
            concept_value.molecular_weight_conv_expon AS molecularWeightConvExpon,
            concept_value.legacy_code AS legacyCode,
            concept_value.conversion_factor_to_master as conversionFactorToMaster,
            concept_value.order as order,
            concept_value.comment as comment,
            [(concept_value)-[:HAS_CT_UNIT]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}] AS ctUnits,
            [(concept_value)-[:HAS_UNIT_SUBSET]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}] AS unitSubsets,
            head([(concept_value)-[:HAS_CT_DIMENSION]->(term_root)-[:HAS_NAME_ROOT]-()-[:LATEST_FINAL]-(value) 
                | {uid:term_root.uid, name: value.name}]) AS unitDimension,
            head([(concept_value)-[:HAS_UCUM_TERM]->(ucum_term_root)-[:LATEST_FINAL]->(value) 
                | {uid:ucum_term_root.uid, name:value.name}]) AS ucum
        """

    def create_query_filter_statement(
        self, library: Optional[str] = None, **kwargs
    ) -> Tuple[str, dict]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("dimension") is not None:
            unit_dimension_name = kwargs.get("dimension")
            filter_by_unit_dimension_name = """
            head([(concept_value)-[:HAS_CT_DIMENSION]->(term_root)-[:HAS_NAME_ROOT]->
            (term_name_root)-[:LATEST_FINAL]->(term_name_value) | 
            term_name_value.name])=$unit_dimension_name"""
            filter_parameters.append(filter_by_unit_dimension_name)
            filter_query_parameters["unit_dimension_name"] = unit_dimension_name
        if kwargs.get("subset") is not None:
            subset_value = kwargs.get("subset")
            filter_by_subset_name = """
            $subset_value IN [(concept_value)-[:HAS_UNIT_SUBSET]->(term_root)-[:HAS_NAME_ROOT]->
            (term_name_root)-[:LATEST_FINAL]->(term_name_value) | term_name_value.name]"""
            filter_parameters.append(filter_by_subset_name)
            filter_query_parameters["subset_value"] = subset_value
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        *,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
    ) -> UnitDefinitionAR:
        ar_root = cast(UnitDefinitionRoot, root)
        ar_value = cast(UnitDefinitionValue, value)

        ct_units = []
        for ct_unit in value.has_ct_unit.all():
            ct_term = CTTerm(
                uid=ct_unit.uid,
                name=ct_unit.has_name_root.get().latest_final.get().name,
            )
            ct_units.append(ct_term)

        unit_subsets = []
        for unit_subset in value.has_unit_subset.all():
            unit_subset_term = CTTerm(
                uid=unit_subset.uid,
                name=unit_subset.has_name_root.get().latest_final.get().name,
            )
            unit_subsets.append(unit_subset_term)

        ct_dimension = ar_value.has_ct_dimension.get_or_none()
        ucum_term = ar_value.has_ucum_term.get_or_none()

        result = UnitDefinitionAR.from_repository_values(
            library=LibraryVO.from_repository_values(
                library_name=library.name, is_editable=library.is_editable
            ),
            uid=ar_root.uid,
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            unit_definition_value=UnitDefinitionValueVO.from_repository_values(
                name=ar_value.name,
                definition=ar_value.definition,
                si_unit=ar_value.si_unit,
                display_unit=ar_value.display_unit,
                master_unit=ar_value.master_unit,
                convertible_unit=ar_value.convertible_unit,
                us_conventional_unit=ar_value.convertible_unit,
                molecular_weight_conv_expon=ar_value.molecular_weight_conv_expon,
                legacy_code=ar_value.legacy_code,
                conversion_factor_to_master=ar_value.conversion_factor_to_master,
                order=ar_value.order,
                comment=ar_value.comment,
                ct_units=ct_units,
                unit_subsets=unit_subsets,
                unit_dimension_uid=ct_dimension.uid if ct_dimension else None,
                ucum_uid=ucum_term.uid if ucum_term else None,
                ucum_name=None,
                unit_dimension_name=None,
                is_template_parameter=self.is_concept_node_a_tp(concept_node=value),
            ),
        )
        return result

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict
    ) -> UnitDefinitionAR:
        major, minor = input_dict.get("version").split(".")

        ct_units = []
        for ct_unit in input_dict.get("ctUnits"):
            ct_units.append(CTTerm(uid=ct_unit.get("uid"), name=ct_unit.get("name")))
        unit_subsets = []
        for unit_subset in input_dict.get("unitSubsets"):
            unit_subsets.append(
                CTTerm(uid=unit_subset.get("uid"), name=unit_subset.get("name"))
            )

        unit_dimension = input_dict.get("unitDimension")
        unit_dimension_uid = unit_dimension.get("uid") if unit_dimension else None
        unit_dimension_name = unit_dimension.get("name") if unit_dimension else None

        ucum = input_dict.get("ucum")
        ucum_uid = ucum.get("uid") if ucum else None
        ucum_name = ucum.get("name") if ucum else None
        return UnitDefinitionAR.from_repository_values(
            uid=input_dict.get("uid"),
            unit_definition_value=UnitDefinitionValueVO.from_repository_values(
                name=input_dict.get("name"),
                definition=input_dict.get("definition"),
                si_unit=input_dict.get("siUnit"),
                display_unit=input_dict.get("displayUnit"),
                master_unit=input_dict.get("masterUnit"),
                convertible_unit=input_dict.get("convertibleUnit"),
                us_conventional_unit=input_dict.get("usConventionalUnit"),
                molecular_weight_conv_expon=input_dict.get("molecularWeightConvExpon"),
                legacy_code=input_dict.get("legacyCode"),
                conversion_factor_to_master=input_dict.get("conversionFactorToMaster"),
                ct_units=ct_units,
                unit_subsets=unit_subsets,
                unit_dimension_uid=unit_dimension_uid,
                ucum_uid=ucum_uid,
                ucum_name=ucum_name,
                unit_dimension_name=unit_dimension_name,
                order=input_dict.get("order"),
                comment=input_dict.get("comment"),
                is_template_parameter=input_dict.get("templateParameter"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("libraryName"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("changeDescription"),
                status=LibraryItemStatus(input_dict.get("status")),
                author=input_dict.get("userInitials"),
                start_date=convert_to_datetime(value=input_dict.get("startDate")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_new_value_node(self, ar: UnitDefinitionAR) -> VersionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.legacy_code = ar.concept_vo.legacy_code
        value_node.convertible_unit = ar.concept_vo.convertible_unit
        value_node.display_unit = ar.concept_vo.display_unit
        value_node.master_unit = ar.concept_vo.master_unit
        value_node.si_unit = ar.concept_vo.si_unit
        value_node.us_conventional_unit = ar.concept_vo.us_conventional_unit
        value_node.molecular_weight_conv_expon = (
            ar.concept_vo.molecular_weight_conv_expon
        )
        value_node.conversion_factor_to_master = (
            ar.concept_vo.conversion_factor_to_master
        )
        value_node.order = ar.concept_vo.order
        value_node.comment = ar.concept_vo.comment
        value_node.save()

        if ar.concept_vo.ucum_uid:
            value_node.has_ucum_term.connect(
                UCUMTermRoot.nodes.get(uid=ar.concept_vo.ucum_uid)
            )
        if ar.concept_vo.unit_dimension_uid:
            value_node.has_ct_dimension.connect(
                CTTermRoot.nodes.get(uid=ar.concept_vo.unit_dimension_uid)
            )

        for ct_unit in ar.concept_vo.ct_units:
            value_node.has_ct_unit.connect(CTTermRoot.nodes.get(uid=ct_unit.uid))
        for unit_subset in ar.concept_vo.unit_subsets:
            value_node.has_unit_subset.connect(
                CTTermRoot.nodes.get(uid=unit_subset.uid)
            )

        return value_node

    def _has_data_changed(
        self, ar: UnitDefinitionAR, value: UnitDefinitionValue
    ) -> bool:

        return value != ar.concept_vo

    def _maintain_parameters(
        self,
        versioned_object: UnitDefinitionAR,
        root: UnitDefinitionRoot,
        value: UnitDefinitionValue,
    ) -> None:

        if versioned_object.concept_vo.is_template_parameter:
            # neomodel can't add custom label to already existing node, we have to manage that by executing cypher query
            # unit definitions should link to the template parameter with the name of the associated unit dimension
            unit_subsets = value.has_unit_subset.all()
            if unit_subsets:
                for unit_subset in unit_subsets:
                    template_parameter_name = (
                        unit_subset.has_name_root.single()
                        .has_latest_value.single()
                        .name
                    )
                    query = """
                        MATCH (template_parameter:TemplateParameter {name:$template_parameter_name})
                        MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                        MERGE (template_parameter)-[:HAS_VALUE]->(concept_root)
                    """
                    db.cypher_query(
                        query,
                        {
                            "uid": versioned_object.uid,
                            "template_parameter_name": template_parameter_name,
                        },
                    )
            query = """
                MATCH (concept_root:ConceptRoot {uid: $uid})-[:LATEST]->(concept_value)
                MATCH (unit:TemplateParameter {name: "Unit"})
                MERGE (unit)-[:HAS_VALUE]->(concept_root)
                SET concept_root:TemplateParameterValueRoot
                SET concept_value:TemplateParameterValue
            """
            db.cypher_query(
                query,
                {
                    "uid": versioned_object.uid,
                },
            )
            TemplateParameterValueRoot.generate_node_uids_if_not_present()

    def master_unit_exists_by_unit_dimension(self, unit_dimension: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{master_unit: true}})
            -[:HAS_CT_DIMENSION]->(term_root:CTTermRoot {{uid: $unit_dimension_uid}})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"unit_dimension_uid": unit_dimension})

        return len(items) > 0

    def exists_by_legacy_code(self, legacy_code: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{legacy_code: $legacy_code}})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"legacy_code": legacy_code})

        return len(items) > 0

    def exists_by_unit_ct_uid(self, unit_ct_uid: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{unit_ct_uid: $unit_ct_uid}})
            RETURN or.uid
        """
        items, _ = db.cypher_query(cypher_query, {"unit_ct_uid": unit_ct_uid})

        return len(items) > 0

    def check_exists_by_name(self, name: str) -> bool:
        cypher_query = f"""
            MATCH (or:{self.root_class.__label__})-[:LATEST]->(ov:{self.value_class.__label__} {{name: $name }})
            RETURN or.uid, ov.name
        """
        items, _ = db.cypher_query(cypher_query, {"name": name})

        return len(items) > 0
