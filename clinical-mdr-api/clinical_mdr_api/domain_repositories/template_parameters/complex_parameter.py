from dataclasses import asdict, dataclass

from neomodel import db


@dataclass
class ParameterConcept:
    name: str
    values: str

    def get_values(self):
        return asdict(self)


class ParameterConceptRepository:
    @staticmethod
    def get_parameter_concept_values(query):
        items, labels = db.cypher_query(query)
        return_values = []
        for row in items:
            return_item = {}
            for key, value in zip(labels, row):
                return_item[key] = value
            return_values.append(return_item)
        return return_values


def parameter_concept_create_factory(name, query):
    values = ParameterConceptRepository.get_parameter_concept_values(query)
    return ParameterConcept(name, values)


class ComplexTemplateParameterRepository:
    def __init__(self):
        tu = parameter_concept_create_factory(
            name="TimeUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "TIME"}) 
            return n.uid as uid, v.name as name, 'TimeUnit' as type
            """,
        )
        au = parameter_concept_create_factory(
            name="AcidityUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "ACIDITY"}) 
            return n.uid as uid, v.name as name, 'AcidityUnit' as type
            """,
        )
        cu = parameter_concept_create_factory(
            name="ConcentrationUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "CONCENTRATION"}) 
            return n.uid as uid, v.name as name, 'ConcentrationUnit' as type
            """,
        )
        self.concepts = [tu, au, cu]

    def find_extended(self):
        values = self.find_all_with_samples()
        for concept in self.concepts:
            values.append(concept.get_values())
        values.sort(key=lambda s: s["name"])
        return values

    def find_all_with_samples(self):
        items, _ = db.cypher_query(
            """
            MATCH (pt:TemplateParameter)
            CALL {
                WITH pt
                MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(ptParents)-[:HAS_VALUE]->(pr)-[:LATEST_FINAL]->(pv)
                WITH  pr, pv,  ptParents
                ORDER BY pv.name ASC
                LIMIT 3
                RETURN collect({uid: pr.uid, name: pv.name, type: ptParents.name}) AS values
            }
            RETURN
                pt.name AS name,
                values
            ORDER BY name
        """
        )
        return_value = [{"name": item[0], "values": item[1]} for item in items]
        return return_value

    def find_values(self, template_parameter_name: str):
        items, _ = db.cypher_query(
            """
            MATCH (pt:TemplateParameter {name: $name})
            CALL {
                WITH pt
                MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(ptParents)-[:HAS_VALUE]->(pr)-[:LATEST_FINAL]->(pv)
                WITH  pr, pv,  ptParents
                ORDER BY pv.name ASC
                RETURN collect({uid: pr.uid, name: pv.name, type: ptParents.name}) AS values
            }
            RETURN
                pt.name AS name,
                values
            ORDER BY name
        """,
            {"name": template_parameter_name},
        )
        if len(items) > 0:
            return items[0][1]
        return []

    def get_parameter_including_values(self, parameter_name: str):
        for item in self.find_extended():
            if item["name"] == parameter_name:
                return item
        return None
