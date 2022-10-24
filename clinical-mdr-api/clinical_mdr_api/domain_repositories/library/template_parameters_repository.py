from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import Conjunction
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterValueRoot,
)


class TemplateParameterRepository:
    def _get_values_for_parameter(self, parameter: TemplateParameter):
        all_values = parameter.has_value.all()
        data = []
        value: TemplateParameterValueRoot
        for value in all_values:
            latest = value.has_latest_final.single()
            if latest is not None:
                data.append({"name": latest.name, "uid": value.uid})
        return data

    def parameter_name_exists(self, parameter_name: str) -> bool:
        return TemplateParameter.nodes.get_or_none(name=parameter_name) is not None

    def is_parameter_value_uid_valid_for_parameter_name(
        self,
        *,
        parameter_name: str,
        parameter_value_uid: str,
    ) -> bool:
        return TemplateParameterValueRoot.check_value_exists(
            parameter_name, parameter_value_uid
        )

    def close(self) -> None:
        pass

    def get_conjunction_or_create_if_not_exists(self, conjunction_str: str):
        result = Conjunction.nodes.get_or_none(string=conjunction_str)
        if result is None:
            conjunction = Conjunction(string=conjunction_str)
            conjunction.save()
        else:
            conjunction = result
        return conjunction

    def get_parameter_including_values(self, template_parameter_name: str):
        cypher_query = """
ramete
            MATCH (pt:TemplateParameter {name: $name})
            WITH pt
            CALL {
                WITH pt
                MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(ptParents)-[:HAS_VALUE]->(pr)-[:LATEST_FINAL]->(pv)
                WITH  pr, pv,  ptParents
                ORDER BY pv.name ASC
                RETURN collect({uid: pr.uid, name: pv.name, type: ptParents.name }) AS values
            }
            RETURN
                pt.name AS name,
                values
            """
        dataset, _ = db.cypher_query(cypher_query, {"name": template_parameter_name})
        data = [dict(name=item[0], values=item[1]) for item in dataset]
        if len(data) > 0:
            return data[0]
        return None
