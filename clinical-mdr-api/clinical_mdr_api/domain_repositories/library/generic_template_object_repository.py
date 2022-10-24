import abc
from datetime import datetime
from typing import Iterable, TypeVar

from neomodel import db

from clinical_mdr_api.domain.library.object import (
    ParametrizedTemplateARBase,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domain.library.parameter_value import (
    ComplexParameterValue,
    NumericParameterValueVO,
    SimpleParameterValueVO,
)
from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    NumericValue,
    NumericValueRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Conjunction,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    ParameterTemplateRoot,
    TemplateParameterComplexRoot,
    TemplateParameterComplexValue,
    TemplateParameterValueRoot,
)
from clinical_mdr_api.exceptions import NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType", bound=ParametrizedTemplateARBase)

"""
TODO - this entire class is REALLY underdocumented and does things weirdly. For a generic class, we should really do better.
It is also very inefficient, which is a real issue as we use it everywhere.
"""


class GenericTemplateBasedObjectRepository(
    LibraryItemRepositoryImplBase[_AggregateRootType], abc.ABC
):
    template_class: type

    def find_item_uids_by_template_uid(self, template_uid: str) -> Iterable[str]:
        # this is implementation moved from GenericTemplateRepository
        # TODO: @Piotr K. for me it seems not right (since template class does not have 'has_template" relationship manager
        template_root: VersionRoot = self.template_class.nodes.get_or_none(
            uid=template_uid
        )
        items = template_root.has_template.all()
        return [it.uid for it in items]

    def _maintain_complex_parameter(
        self,
        parameter_config: ComplexParameterValue,
    ):
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

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:

        value.name = versioned_object.name
        value.save()
        value.has_parameters.disconnect_all()
        value.has_conjunction.disconnect_all()
        params = versioned_object.get_parameters()
        for position, parameter_config in enumerate(params):
            if isinstance(parameter_config, ComplexParameterValue):
                root_id = self._maintain_complex_parameter(
                    parameter_config=parameter_config
                )
                cypher_query = f"""
                    MATCH (ov), (pt:TemplateParameterValueRoot)
                    WHERE ID(ov) = $value_id and ID(pt) = $root_id
                    CREATE (ov)-[r:{value.PARAMETERS_LABEL} {{position: $position, index: $index}}]->(pt)
                    """
                db.cypher_query(
                    cypher_query,
                    {
                        "root_id": root_id,
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
                        conjunction, {"position": position + 1}
                    )
                for index, value_config in enumerate(parameter_config.parameters):
                    self._add_value_parameter_relation(
                        value, value_config.uid, position + 1, index + 1
                    )
        template = self.template_class.nodes.get(uid=versioned_object.template_uid)

        # If the template is retired, we can't instantiate objects from it
        root.has_template.connect(template)

        # Double check that we actually performed a valid connection to the template that isn't retired.
        # this needs to be done after connecting, as there might be concurrent transactions retiring the template.
        if template.latest_retired.get_or_none() is not None:
            raise ValueError(
                root.uid + " cannot be added to " + template.uid + ", as it is retired."
            )

    def _add_value_parameter_relation(
        self, value: VersionValue, parameter_uid: str, position: int, index: int
    ):
        # ov is any of EndpointValue ObjectiveValue and TimeframeValue

        cypher_query = f"""
            MATCH (ov), (pt:TemplateParameterValueRoot {{uid: $parameter_uid}})
            WHERE ID(ov) = $value_id
            CREATE (ov)-[r:{value.PARAMETERS_LABEL} {{position: $position, index: $index}}]->(pt)
            """
        db.cypher_query(
            cypher_query,
            {
                "parameter_uid": parameter_uid,
                "position": position,
                "index": index,
                "value_id": value.id,
            },
        )

    def find_by(self, name: str) -> _AggregateRootType:
        values: Iterable[VersionValue] = self.value_class.nodes.filter(name=name)
        if len(values) > 0:
            root_uid = values[0].get_root_uid_by_latest()
            item: _AggregateRootType = self.find_by_uid_2(uid=root_uid)
            return item
        raise NotFoundException(
            "Not Found - The object with the specified 'name' wasn't found."
        )

    def _read_additional_data(self, root: VersionRoot, value: VersionValue) -> object:
        name = value.name
        template = root.has_template.single()
        template_name = template.has_latest_value.single().name
        data = {
            "_name": name,
            "_parameter_values": self._get_template_parameters(root, value),
            "_template_name": template_name,
            "_template_uid": template.uid,
        }
        return data

    def _get_database_parameters(self, root: VersionRoot, value: VersionValue):
        cypher_query = f"""
        MATCH  (param:TemplateParameter)<-[u:OT_USES_PARAMETER|ET_USES_PARAMETER|TT_USES_PARAMETER|CT_USES_PARAMETER|AT_USES_PARAMETER]-
              ()-[:HAS_OBJECTIVE|HAS_ENDPOINT|HAS_TIMEFRAME|HAS_CRITERIA|HAS_ACTIVITY_DESCRIPTION]->
              (vt:{root.__label__})-[:LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED|HAS_VERSION]->
              (vv:{value.__label__})
        WHERE vt.uid=$root_uid AND vv.name=$value_name
        WITH vv, param.name as parameter, u.position as position
        OPTIONAL MATCH (vv)-[rel:OV_USES_VALUE|EV_USES_VALUE|TV_USES_VALUE|CT_USES_VALUE|AT_USES_VALUE]->(tpvr:TemplateParameterValueRoot)
           WITH head([(tpvr)-[:LATEST_FINAL]->(tpv) | tpv]) as tpv,
                head([(tpvr)<-[:HAS_VALUE]-(tp) | tp]) as tp,
                rel as rel,
                position,
                parameter,
                tpvr as tpvr
        OPTIONAL MATCH (tpvv: ParameterTemplateValue)<-[:LATEST_FINAL]-(td: ParameterTemplateRoot)-[:HAS_COMPLEX_VALUE]->(tpvr)
        WHERE tpv iS NOT NULL AND tp is NOT NULL
        
        WITH  position, parameter, collect(DISTINCT {{position: rel.position, index: rel.index, parameter_name: tp.name, parameter_value: tpv.name, parameter_uid: tpvr.uid,  definition: td.uid, template: tpvv.template_string }}) as data
        RETURN  position, parameter, [row in data where row.position = position | row] as parametervalues
        """

        results, _ = db.cypher_query(
            cypher_query, params={"root_uid": root.uid, "value_name": value.name}
        )

        parameter_values = self._parse_parameter_values(instance_parameters=results)
        return parameter_values[0] if len(parameter_values) > 0 else []

    def _get_template_parameters(self, root, value):
        cypher_query = f"""
        MATCH  (param:TemplateParameter)<-[u:OT_USES_PARAMETER|ET_USES_PARAMETER|TT_USES_PARAMETER|CT_USES_PARAMETER|AT_USES_PARAMETER]-
              ()-[:HAS_OBJECTIVE|HAS_ENDPOINT|HAS_TIMEFRAME|HAS_CRITERIA|HAS_ACTIVITY_DESCRIPTION]->
              (vt:{root.__label__})-[:LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED|HAS_VERSION]->
              (vv:{value.__label__})
        WHERE vt.uid=$root_uid AND vv.name=$value_name
        WITH vv, param.name as parameter, u.position as position
        OPTIONAL MATCH (vv)-[rel:OV_USES_VALUE|EV_USES_VALUE|TV_USES_VALUE|CT_USES_VALUE|AT_USES_VALUE]->(tpvr:TemplateParameterValueRoot)
        CALL apoc.when(
            tpvr IS NOT NULL AND tpvr:StudyEndpoint,
            "MATCH (:StudyValue)-->(tpvr)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
            OPTIONAL MATCH (tpvr)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL
            {{
                WITH tpvr
                OPTIONAL MATCH (tpvr)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(udv:UnitDefinitionValue)
                WITH rel, udv, tpvr ORDER BY rel.index
                WITH collect(udv.name_sentence_case) as unit_names, tpvr
                OPTIONAL MATCH (tpvr)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                WITH unit_names, co
                RETURN apoc.text.join(unit_names, ' ' + coalesce(co.string, '') + ' ') AS unit
            }}
            RETURN ev.name + coalesce(' ' + unit, '') + coalesce(' ' + tv.name, '') AS tpv",
            "WITH head([(tpvr)-[:LATEST_FINAL]->(tpv) | tpv]) AS tpv
            CALL apoc.case(
                [
                    tpv.name_sentence_case IS NOT NULL, 'RETURN tpv.name_sentence_case AS name',
                    tpv.name_sentence_case IS NULL, 'RETURN tpv.name AS name'
                ],
                '',
                {{ tpv:tpv }})
            YIELD value
            RETURN value.name AS tpv
            ",
            {{tpvr:tpvr}})
            YIELD value
           WITH vv,
                head([(tpvr)<-[:HAS_VALUE]-(tp) | tp]) as tp,
                rel,
                position,
                parameter,
                tpvr,
                value.tpv AS tpv
        OPTIONAL MATCH (tpvv: ParameterTemplateValue)<-[:LATEST_FINAL]-(td: ParameterTemplateRoot)-[:HAS_COMPLEX_VALUE]->(tpvr)
        WHERE tpv iS NOT NULL AND tp is NOT NULL
        
        WITH vv, position, parameter, collect(DISTINCT {{set_number: 0, position: rel.position, index: rel.index, parameter_name: tp.name, parameter_value: tpv, parameter_uid: tpvr.uid,  definition: td.uid, template: tpvv.template_string }}) as data
        OPTIONAL MATCH (vv)-[con_rel:HAS_CONJUNCTION]->(con:Conjunction)
        WHERE con_rel.position=position
        WITH position, parameter, data, coalesce(con.string, "") AS conjunction
        RETURN position, parameter, [row in data where row.position = position | row] as parametervalues, conjunction
        """

        results, _ = db.cypher_query(
            cypher_query, params={"root_uid": root.uid, "value_name": value.name}
        )

        parameter_values = self._parse_parameter_values(instance_parameters=results)
        return parameter_values[0] if len(parameter_values) > 0 else []

    def _from_repository_values(self, value):
        pv = SimpleParameterValueVO.from_repository_values(
            uid=value["parameter_uid"], value=value["parameter_value"]
        )
        return pv

    def _get_template(
        self, root: VersionRoot, value: VersionValue, date_before: datetime
    ) -> ParametrizedTemplateVO:
        parameter_values = self._get_template_parameters(root, value)
        template_object: VersionRoot = root.has_template.get()
        if date_before is None:
            template_value_object: VersionValue = template_object.latest_final.get()
        else:
            template_value_object: VersionValue = template_object.get_final_before(
                date_before
            )
            if template_value_object is None:
                template_value_object: VersionValue = (
                    template_object.get_retired_before(date_before)
                )

        template = ParametrizedTemplateVO(
            template_name=template_value_object.name,
            template_uid=template_object.uid,
            parameter_values=parameter_values,
        )
        return template

    def check_usage_count(self, uid: str) -> bool:
        return False
