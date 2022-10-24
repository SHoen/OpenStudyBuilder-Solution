import abc
from typing import Dict, List, Optional, Sequence, TypeVar

from neomodel import db

from clinical_mdr_api.config import (
    STUDY_DAY_NAME,
    STUDY_DURATION_DAYS_NAME,
    STUDY_DURATION_WEEKS_NAME,
    STUDY_ENDPOINT_TP_NAME,
    STUDY_TIMEPOINT_NAME,
    STUDY_VISIT_NAME,
    STUDY_VISIT_TIMEREF_NAME,
    STUDY_VISIT_TYPE_NAME,
    STUDY_WEEK_NAME,
)
from clinical_mdr_api.domain._utils import strip_html
from clinical_mdr_api.domain.library.parameter_value import (
    ComplexParameterValue,
    NumericParameterValueVO,
    ParameterValueEntryVO,
)
from clinical_mdr_api.domain.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    TemplateVO,
)
from clinical_mdr_api.domain_repositories.generic_repository import EntityNotFoundError
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValue,
    NumericValueRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import Conjunction, VersionRoot
from clinical_mdr_api.domain_repositories.models.syntax_template import (
    SyntaxTemplateValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    ParameterTemplateRoot,
    TemplateParameter,
    TemplateParameterComplexRoot,
    TemplateParameterComplexValue,
    TemplateParameterValueRoot,
)

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)

RETRIEVED_READ_ONLY_MARK = object()


class GenericTemplateRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType], abc.ABC
):
    def _get_template(self, value: SyntaxTemplateValue) -> TemplateVO:
        return TemplateVO(
            name=value.name,
            name_plain=value.name_plain,
            guidance_text=value.guidance_text,
        )

    def _get_or_create_value(
        self, root: VersionRoot, ar: _AggregateRootType
    ) -> SyntaxTemplateValue:

        for itm in root.has_version.filter(
            name=ar.name, guidance_text=ar.guidance_text
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
            name=ar.name, guidance_text=ar.guidance_text, name_plain=strip_html(ar.name)
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(
        self, ar: _AggregateRootType, value: SyntaxTemplateValue
    ) -> bool:
        base_comparison = (
            ar.name != value.name or ar.guidance_text != value.guidance_text
        )
        return base_comparison

    def patch_indications(self, uid: str, indication_uids: Sequence[str]) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_indication.disconnect_all()
        for indication in indication_uids:
            indication = self._get_indication(indication)
            root.has_indication.connect(indication)

    def patch_categories(self, uid: str, category_uids: Sequence[str]) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_category.disconnect_all()
        for category in category_uids:
            category = self._get_category(category)
            root.has_category.connect(category)

    def patch_sub_categories(self, uid: str, sub_category_uids: Sequence[str]) -> None:
        root = self.root_class.nodes.get(uid=uid)
        root.has_sub_category.disconnect_all()
        for sub_category in sub_category_uids:
            sub_category = self._get_category(sub_category)
            root.has_sub_category.connect(sub_category)

    def patch_default_parameter_values(
        self,
        versioned_object: _AggregateRootType,
        parameters: Sequence[ParameterValueEntryVO],
        set_number: Optional[int] = None,
    ):
        (
            _,
            template_value,
            _,
            _,
        ) = versioned_object.repository_closure_data

        # If set_number isn't provided, auto determine the set number
        if set_number is None:
            cypher_query = f"""MATCH (t)-[rel:{template_value.PARAMETERS_LABEL}]->()
            WHERE id(t)=$id
            RETURN coalesce(max(rel.set_number), 0) AS max_set_number
            """
            result, _ = db.cypher_query(cypher_query, {"id": template_value.id})
            set_number = result[0][0] + 1
        else:
            # If the template already has a default value set with this number, first disconnect the parameters
            value_set = template_value.has_parameters.match(set_number=set_number).all()
            for param in value_set:
                self._db_remove_relationship(template_value.has_parameters, param)
        # Then, create the set of parameters
        self._create_default_parameter_value_set(
            value=template_value, parameters=parameters, set_number=set_number
        )

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: SyntaxTemplateValue,
    ) -> None:
        root.has_parameters.disconnect_all()
        for index, parameter_name in enumerate(
            versioned_object.template_value.parameter_names
        ):
            parameter = TemplateParameter.nodes.get_or_none(name=parameter_name)
            if parameter is not None:
                # root.has_parameters.connect(parameter, {"position": index + 1})
                cypher_query = f"""
                    MATCH (tr:{self.root_class.__label__}) WHERE ID(tr)=$id
                    WITH tr
                    MATCH (tp:TemplateParameter {{name: $parameter_name}})
                    WITH tr, tp
                    CREATE (tr)-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(tp)
                    SET uses_parameter.position=$position
                    """
                db.cypher_query(
                    cypher_query,
                    {
                        "id": root.id,
                        "parameter_name": parameter_name,
                        "position": index + 1,
                    },
                )
            else:
                raise EntityNotFoundError(
                    f"Cannot find parameter named {parameter_name}"
                )

        if (
            hasattr(versioned_object.template_value, "default_parameter_values")
            and versioned_object.template_value.default_parameter_values is not None
        ):
            # Then, create the relationships to the TemplateParameterValue nodes, as default values
            value.has_parameters.disconnect_all()
            value.has_conjunction.disconnect_all()

            self._create_default_parameter_value_set(
                value=value,
                parameters=versioned_object.template_value.default_parameter_values,
            )

    def _create_default_parameter_value_set(
        self,
        value: SyntaxTemplateValue,
        parameters: Sequence[ParameterValueEntryVO],
        set_number: Optional[int] = 0,
    ) -> None:

        for position, parameter_config in enumerate(parameters):
            if isinstance(parameter_config, ComplexParameterValue):
                root_id = self._maintain_complex_parameter(parameter_config)
                cypher_query = f"""
                    MATCH (tv), (pt:TemplateParameterValueRoot)
                    WHERE ID(tv) = $value_id AND ID(pt) = $root_id
                    CREATE (tv)-[r:{value.PARAMETERS_LABEL} {{set_number: $set_number, position: $position, index: $index}}]->(pt)
                    """
                db.cypher_query(
                    cypher_query,
                    {
                        "root_id": root_id,
                        "set_number": set_number,
                        "position": position,
                        "index": 1,
                        "value_id": value.id,
                    },
                )
            else:
                conjunction_string: str = parameter_config.conjunction
                if len(conjunction_string) != 0:
                    result = Conjunction.nodes.get_or_none(string=conjunction_string)
                    if result is None:
                        conjunction = Conjunction(string=conjunction_string)
                        conjunction.save()
                    else:
                        conjunction = result
                    value.has_conjunction.connect(
                        conjunction,
                        {"set_number": set_number, "position": position + 1},
                    )
                for index, value_config in enumerate(parameter_config.parameters):
                    self._add_value_parameter_relation(
                        value=value,
                        parameter_uid=value_config.uid,
                        set_number=set_number,
                        position=position + 1,
                        index=index + 1,
                    )

    def _maintain_complex_parameter(self, parameter_config: ComplexParameterValue):
        complex_value = TemplateParameterComplexValue.nodes.get_or_none(
            name=parameter_config.value
        )
        if complex_value is None:
            root: TemplateParameterComplexRoot = TemplateParameterComplexRoot(
                is_active_parameter=True
            )
            root.save()
            complex_value = TemplateParameterComplexValue(name=parameter_config.value)
            complex_value.save()
            root.latest_final.connect(complex_value)
            root.has_latest_value.connect(complex_value)
            parameter_root = ParameterTemplateRoot.get(uid=parameter_config.uid)
            root.has_complex_value.connect(parameter_root)
            template_root = ParameterTemplateRoot.nodes.get(uid=parameter_config.uid)
            tp = template_root.has_definition.get()
            root.has_value.connect(tp)
        else:
            root_uid = complex_value.get_root_uid_by_latest()
            root = TemplateParameterComplexRoot.nodes.get(uid=root_uid)
        for i, param in enumerate(parameter_config.parameters):
            param_uid = param.uid
            if isinstance(param, NumericParameterValueVO):
                v = NumericValue.nodes.get_or_none(name=param.value)
                if not v:
                    r = NumericValueRoot(uid="NumericValue_" + str(param.value))
                    r.save()
                    v = NumericValue(name=param.value)
                    v.save()
                    r.latest_final.connect(v, {})
                    r.has_latest_value.connect(v)
                    r = r.uid
                else:
                    r = v.get_root_uid_by_latest()
                param_uid = r
            tpvr = TemplateParameterValueRoot.nodes.get(uid=param_uid)
            complex_value.uses_parameter.connect(tpvr, {"position": i + 1})
        return root.id

    def _add_value_parameter_relation(
        self,
        value: SyntaxTemplateValue,
        parameter_uid: str,
        position: int,
        index: int,
        set_number: Optional[int],
    ):
        set_number_sub_clause = (
            "set_number: $set_number, " if set_number is not None else ""
        )
        cypher_query = f"""
            MATCH (tv), (pt:TemplateParameterValueRoot {{uid: $parameter_uid}})
            WHERE ID(tv) = $value_id
            CREATE (tv)-[r:{value.PARAMETERS_LABEL} {{{set_number_sub_clause}position: $position, index: $index}}]->(pt)
            """
        db.cypher_query(
            cypher_query,
            {
                "parameter_uid": parameter_uid,
                "set_number": set_number,
                "position": position,
                "index": index,
                "value_id": value.id,
            },
        )

    def get_parameters_including_values(
        self,
        template_uid: str,
        study_uid: Optional[str] = None,
        include_study_endpoints: Optional[bool] = False,
    ):
        cypher_query = f"""
            MATCH (otr:{self.root_class.__label__} {{uid: $uid}})-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(pt)
            WHERE NOT pt.name=$name
            OPTIONAL MATCH (pt)-[:HAS_DEFINITION]->(tpd:ParameterTemplateRoot)-
                [:LATEST_FINAL]->(tpv:ParameterTemplateValue)
            WITH uses_parameter, pt, tpd, tpv
            ORDER BY
                uses_parameter.position ASC
            CALL {{
                WITH pt
                OPTIONAL MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(ptParents)-[:HAS_VALUE]->(pr)-[:LATEST_FINAL]->(pv)
                WITH  pr, pv,  ptParents
                CALL apoc.case(
                 [
                   pv.name_sentence_case IS NOT NULL, 'RETURN pv.name_sentence_case AS name',
                   pv.name_sentence_case IS NULL, 'RETURN pv.name AS name'
                 ],
                 '',
                 {{ pv:pv }})
                 yield value
                WITH pr, ptParents, value.name as value
                ORDER BY value ASC
                RETURN collect({{uid: pr.uid, name: value, type: ptParents.name}}) AS values
            }}
            RETURN
                pt.name AS name, tpd.uid as definition, tpv.template_string as template,
                values
            """
        dataset, _ = db.cypher_query(
            cypher_query, {"uid": template_uid, "name": STUDY_ENDPOINT_TP_NAME}
        )
        data = [
            dict(name=item[0], definition=item[1], template=item[2], values=item[3])
            for item in dataset
        ]

        if study_uid:
            data = self.subset_parameters_to_specific_study(
                data=data, study_uid=study_uid
            )

        # StudyEndpoint parameters need to be treated separately
        if include_study_endpoints is True:
            cypher_query = f"""
                MATCH (:{self.root_class.__label__} {{uid: $uid}})-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(pt)
                WHERE pt.name=$pt_name
                WITH uses_parameter, pt
                ORDER BY
                    uses_parameter.position ASC
                CALL {{
                    WITH pt
                    MATCH (pt)-[:HAS_VALUE]->(pr)<-[:HAS_STUDY_ENDPOINT]-(:StudyValue)<-[:LATEST]-(sr:StudyRoot)
                    WHERE sr.uid=$study_uid
                    MATCH (pr)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
                    OPTIONAL MATCH (pr)-[:HAS_SELECTED_TIMEFRAME]->(tv)
                    CALL
                    {{
                        WITH pr
                        OPTIONAL MATCH (pr)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(udv:UnitDefinitionValue)
                        WITH rel, udv, pr ORDER BY rel.index
                        WITH collect(udv.name_sentence_case) as unit_names, pr
                        OPTIONAL MATCH (pr)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                        WITH unit_names, co
                        RETURN apoc.text.join(unit_names, " " + coalesce(co.string, "") + " ") AS unit
                    }}
                    WITH pr.uid AS puid, ev.name + coalesce(" " + unit, "") + coalesce(" " + tv.name, "") AS pname
                    ORDER BY pname ASC
                    RETURN collect({{uid: puid, name: pname, type: $pt_name}}) AS values
                }}

                RETURN
                    pt.name AS name, null as definition, null as template,
                    values
                """
            dataset, _ = db.cypher_query(
                cypher_query,
                {
                    "uid": template_uid,
                    "study_uid": study_uid,
                    "pt_name": STUDY_ENDPOINT_TP_NAME,
                },
            )
            data += [
                dict(name=item[0], definition=item[1], template=item[2], values=item[3])
                for item in dataset
            ]

        return data

    def get_default_parameter_values(
        self, template_uid: str
    ) -> Dict[int, Sequence[ParameterValueEntryVO]]:
        cypher_query = f"""
        MATCH  (param:TemplateParameter)<-[u:OT_USES_PARAMETER|ET_USES_PARAMETER|TT_USES_PARAMETER|CT_USES_PARAMETER|AT_USES_PARAMETER]-
          (tr:{self.root_class.__label__})-[:LATEST]->(tv)
        WHERE tr.uid=$root_uid
        WITH tv, param.name as parameter, u.position as position
        OPTIONAL MATCH (tv)-[rel:USES_DEFAULT_VALUE]->(tpvr:TemplateParameterValueRoot)
        WITH tv,
            head([(tpvr)-[:LATEST_FINAL]->(tpv) | tpv]) as tpv,
            head([(tpvr)<-[:HAS_VALUE]-(tp) | tp]) as tp,
            rel as rel,
            position,
            parameter,
            tpvr as tpvr
        OPTIONAL MATCH (tpvv: ParameterTemplateValue)<-[:LATEST_FINAL]-(td: ParameterTemplateRoot)-[:HAS_COMPLEX_VALUE]->(tpvr)
        WHERE tpv iS NOT NULL AND tp is NOT NULL
        
        WITH DISTINCT coalesce(rel.set_number, 0) AS set_number, tv, position, parameter, collect(DISTINCT {{set_number: coalesce(rel.set_number, 0), position: rel.position, index: rel.index, parameter_name: tp.name, parameter_value: tpv.name, parameter_uid: tpvr.uid,  definition: td.uid, template: tpvv.template_string }}) as data
        OPTIONAL MATCH (tv)-[con_rel:HAS_CONJUNCTION]->(con:Conjunction)
        WHERE con_rel.position=position AND con_rel.set_number=set_number
        WITH position, parameter, data, coalesce(con.string, "") AS conjunction
        RETURN DISTINCT position, parameter, [row in data where row.position = position | row] as parametervalues, conjunction
        """

        results, _ = db.cypher_query(cypher_query, params={"root_uid": template_uid})

        default_parameter_values = self._parse_parameter_values(
            instance_parameters=results
        )
        return default_parameter_values

    def simple_concept_template(self, rel_type: str):
        query_to_subset = f"""
            MATCH (:StudyRoot {{uid:$uid}})-[:LATEST]->(:StudyValue)
            -[:HAS_STUDY_VISIT]->(:StudyVisit {{is_deleted:false}})-[:{rel_type}]->(:SimpleConceptRoot)
            -[:LATEST_FINAL]->(simple_concept_value:SimpleConceptValue)
            return simple_concept_value.name
            """
        return query_to_subset

    def ct_term_template(self, rel_type: str):
        query_to_subset = f"""
        MATCH (:StudyRoot {{uid:$uid}})-[:LATEST]->(:StudyValue)
        -[:HAS_STUDY_VISIT]->(:StudyVisit {{is_deleted:false}})-[:{rel_type}]->(:CTTermRoot)
        -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(term_name_value:CTTermNameValue)
        return term_name_value.name
        """
        return query_to_subset

    def subset_time_point_reference(self):
        query_to_subset = """
            MATCH (:StudyRoot {uid:$uid})-[:LATEST]->(:StudyValue)
            -[:HAS_STUDY_VISIT]->(:StudyVisit {is_deleted:false})-[:HAS_TIMEPOINT]->(:SimpleConceptRoot)
            -[:LATEST_FINAL]->(simple_concept_value:SimpleConceptValue)-[:HAS_TIME_REFERENCE]->(:CTTermRoot)
            -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(term_name_value:CTTermNameValue)
            return term_name_value.name
            """
        return query_to_subset

    def subset_parameters_to_specific_study(self, data: List, study_uid: str):

        for parameter in data:
            query_to_subset = None
            param_name = parameter["name"]
            if parameter["name"] == STUDY_VISIT_TYPE_NAME:
                query_to_subset = self.ct_term_template(rel_type="HAS_VISIT_TYPE")
            elif parameter["name"] == STUDY_VISIT_TIMEREF_NAME:
                query_to_subset = self.subset_time_point_reference()
            elif parameter["name"] == STUDY_VISIT_NAME:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_VISIT_NAME"
                )
            elif parameter["name"] == STUDY_DAY_NAME:
                query_to_subset = self.simple_concept_template(rel_type="HAS_STUDY_DAY")
            elif parameter["name"] == STUDY_DURATION_DAYS_NAME:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_DURATION_DAYS"
                )
            elif parameter["name"] == STUDY_WEEK_NAME:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_WEEK"
                )
            elif parameter["name"] == STUDY_DURATION_WEEKS_NAME:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_DURATION_WEEKS"
                )
            elif parameter["name"] == STUDY_TIMEPOINT_NAME:
                query_to_subset = self.simple_concept_template(rel_type="HAS_TIMEPOINT")
            if query_to_subset:
                template_parameters_subset, _ = db.cypher_query(
                    query_to_subset, {"uid": study_uid}
                )
                flat_template_parameters = self.flatten_neomodel_output(
                    output=template_parameters_subset
                )
                self.subset_value_list_for_given_tp(
                    data=data,
                    param_name=param_name,
                    subset_list=flat_template_parameters,
                )
        return data

    def flatten_neomodel_output(self, output: List):
        flatted_output = []
        if len(output) > 0:
            for value in output:
                flatted_output.append(value[0].lower())
        return flatted_output

    def subset_value_list_for_given_tp(
        self, data: List, param_name: str, subset_list: List
    ):
        for template_param_value in data:
            if template_param_value["name"] == param_name:
                template_param_value["values"] = [
                    item
                    for item in template_param_value["values"]
                    if item["name"].lower() in subset_list
                ]

    def is_template_instance_editable(self, uid: str) -> bool:
        return self.root_class.nodes.get(uid=uid).editable_instance

    @abc.abstractmethod
    def check_exists_by_name_in_study(self, name: str, study_uid: str) -> bool:
        raise NotImplementedError()
