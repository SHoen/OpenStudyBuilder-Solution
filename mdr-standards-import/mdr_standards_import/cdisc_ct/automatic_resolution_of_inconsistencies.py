# priority list of catalogue names
# if there is an inconsistency between two different catalogues,
# then the catalogue which comes first in this list wins and overrules the other one
from typing import List

from mdr_standards_import.cdisc_ct.entities.resolution import Resolution

# TODO remove this file; see the files inconsistency_resolver.py and entities/resolution.py

# DEFAULT_CATALOGUE_PRIORITY_LIST = [
#     'SDTM CT',
#     'ADaM CT',
#     'CDASH CT',
#     'SEND CT',
#     'PRM CT',
# ]


# def initialize_resolution_config(tx):
#     initialize_catalogue_priorities(tx)
#     initialize_resolutions(tx)


# def initialize_catalogue_priorities(tx):
#     tx.run(
#         """
#         MATCH (prio:CataloguePriorities)
#         WITH prio SKIP 1
#         DETACH DELETE prio
#         """
#     )

#     tx.run(
#         """
#         MERGE (prio:CataloguePriorities)
#         ON CREATE SET
#             prio.catalogue_names=$catalogue_names
#         WITH prio LIMIT 1
#         RETURN prio
#         """,
#         catalogue_names=DEFAULT_CATALOGUE_PRIORITY_LIST
#     )


# def initialize_resolutions(tx):
#     result = tx.run(
#         "MATCH (n:Resolution) RETURN count(n) > 0 AS at_least_one_node_exists").single()
#     at_least_one_node_exists = result.get('at_least_one_node_exists', True)
#     if not at_least_one_node_exists:
#         tx.run(
#             """
#             UNWIND $resolutions AS resolution
#             CREATE (n:Resolution)
#             SET
#                 n.order=resolution.order,
#                 n.action=resolution.action,
#                 n.valid_for_taglines=resolution.valid_for_taglines
#             """,
#             resolutions=DEFAULT_RESOLUTIONS
#         )


# def get_import_node_ids(tx, effective_date: str = None):
#     where_effective_date = ' AND import.effective_date = date($effective_date)' if effective_date else ''
#     return tx.run(
#         """
#         MATCH (import:Import)
#         WHERE (import.automatic_resolution_done IS NULL OR NOT import.automatic_resolution_done)"""
#         + where_effective_date +
#         """
#         RETURN id(import) AS import_id
#         ORDER BY import.effective_date DESC
#         """,
#         effective_date=effective_date
#     ).value()


# def get_resolutions(tx):
#     result = tx.run(
#         """
#         MATCH (resolution:Resolution)
#         RETURN resolution
#         ORDER BY resolution.order
#         //RETURN collect(resolution) AS resolutions
#         """
#     ).data()
#     return Resolution.from_node_records(result)


# def get_catalogue_priorities(tx):
#     result = tx.run(
#         """
#         MATCH (prio:CataloguePriorities)
#         RETURN prio.catalogue_names AS catalogue_names
#         LIMIT 1
#         """
#     ).single()
#     return result.get('catalogue_names', [])


# def resolve_inconsistencies_of_import(tx, import_id: int, resolution: Resolution, catalogue_priorities):
#     condition = "coalesce(concept.concept_id, concept.catalogue_name) IN $concept_ids"
#     where_clause = ""
#     concept_ids=[]
#     if resolution.valid_for_concept_ids and len(resolution.valid_for_concept_ids) > 0:
#         where_clause = f"AND {condition}"
#         concept_ids = resolution.valid_for_concept_ids
#     elif resolution.invalid_for_concept_ids and len(resolution.invalid_for_concept_ids) > 0:
#         where_clause = f"AND NOT {condition}"
#         concept_ids = resolution.invalid_for_concept_ids

#     data = tx.run(
#         """
#         MATCH (import:Import)-[:HAS]->(inconsistency:Inconsistency)-->(concept)
#         WHERE
#             id(import) = $import_id AND
#             inconsistency.tagline IN $taglines
#         """ + where_clause + """
#         RETURN DISTINCT
#             id(inconsistency) AS inconsistency_id,
#             inconsistency.tagline AS tagline
#         """,
#         import_id=import_id,
#         taglines=resolution.valid_for_taglines,
#         concept_ids=concept_ids,
#     ).data()

#     for entry in data:
#         tagline = entry.get('tagline', None)
#         inconsistency_id = entry.get('inconsistency_id', None)
#         print(f"    tagline={tagline}")
#         if tagline == "cannot differentiate code/name":
#             if resolution.action == "separate-term":
#                 # TODO set the user_initials
#                 resolve_inconsistency_for_cannot_differentiate_with_separate_term(tx, inconsistency_id, user_initials='TODO')
#         elif tagline == "":
#             pass
            

# def resolve_inconsistency(tx, inconsistency_id: int, action: str):
#     pass


# def resolve_inconsistency_for_inconsistent_codelist_attributes_with_catalogue_priorities(tx, inconsistency_id: int, catalogue_priorities):
#     tx.run(
#         """
#         MATCH (inconsistency:Inconsistency)-[:AFFECTS_CODELIST]->(codelist)
#             -[:HAS]->(inconsistentAttributes)-[:ARE_DEFINED_IN]->(package)
#         WHERE id(inconsistency) = $inconsistency_id
#         RETURN inconsistency
#         """,
#         inconsistency_id
#     )


# def resolve_inconsistency_for_cannot_differentiate_with_separate_term(tx, inconsistency_id: int, user_initials: str):
#     ignore(tx, inconsistency_id, user_initials)


# def ignore(tx, inconsistency_id: int, user_initials: str):
#     tx.run(
#         """
#         MATCH (inconsistency:Inconsistency)
#         WHERE id(inconsistency) = $inconsistency_id
#         SET
#             inconsistency:ResolvedInconsistency,
#             inconsistency.comment=$comment,
#             inconsistency.user_initials=$user_initials
#         REMOVE inconsistency:Inconsistency
#         """,
#         inconsistency_id=inconsistency_id,
#         user_initials=user_initials,
#         comment='Ignoring the inconsistency and marking it as resolved.',
#     )


# def set_automatic_resolution_flag(tx, import_id: int, flag: bool = True):
#     if flag is None or not flag:
#         tx.run(
#             """
#             MATCH (import:Import) WHERE id(import) = $import_id
#             REMOVE import.automatic_resolution_done
#             """,
#             import_id=import_id
#         )
#     else:
#         tx.run(
#             """
#             MATCH (import:Import) WHERE id(import) = $import_id
#             SET import.automatic_resolution_done = true
#             """,
#             import_id=import_id
#         )


# def automatic_resolution_of_inconsistencies(cdisc_import_neo4j_driver, cdisc_import_db_name: str, effective_date: str = None):
#     pass # TODO
#     # with cdisc_import_neo4j_driver.session(database=cdisc_import_db_name) as session:
#     #     session.write_transaction(initialize_resolution_config)

#     # with cdisc_import_neo4j_driver.session(database=cdisc_import_db_name) as session:
#     #     with session.begin_transaction() as tx:
#     #         import_node_ids = get_import_node_ids(tx)
#     #         resolutions: List[Resolution] = get_resolutions(tx)
#     #         catalogue_priorities = get_catalogue_priorities(tx)
#     #         # print(f"import_node_ids={import_node_ids}")
#     #         # print(f"resolutions={resolutions}")
#     #         # print(f"catalogue_priorities={catalogue_priorities}")
#     #         for import_id in import_node_ids:
#     #             print(f"resolving import_id={import_id}")
#     #             for resolution in resolutions:
#     #                 # print(f"  action={resolution.action}")
#     #                 # print(f"  taglines={resolution.valid_for_taglines}")
#     #                 resolve_inconsistencies_of_import(tx, import_id, resolution, catalogue_priorities)

#     #             # TODO enable this
#     #             # set_automatic_resolution_flag(tx, import_id)
#     #         tx.commit()
