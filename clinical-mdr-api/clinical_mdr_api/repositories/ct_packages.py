from typing import Sequence

from neomodel import db

CODELIST_DATA_RETRIEVAL_SPECIFIC_QUERY = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[old_versions]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_codelist_root {uid:$codelist_uid})
WITH old_codelist_root, codelist_attr_val, max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[new_versions]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_codelist_root {uid:$codelist_uid}) 
WITH old_items, new_codelist_root, codelist_attr_val, max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS new_items
"""

TERM_DATA_RETRIEVAL_SPECIFIC_QUERY = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_TERM]->
(package_term)-[:CONTAINS_ATTRIBUTES]->(term_attr_val)<-[old_versions]-
(term_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_term_root)<-[:HAS_TERM]-(old_codelist_root {uid:$codelist_uid})
WITH old_term_root, 
    [(codelist_root)-[:HAS_TERM]->(old_term_root) | codelist_root.uid] AS codelists,
    term_attr_val, 
    max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_term_root.uid, {
    value_node:term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_TERM]->
(package_term)-[:CONTAINS_ATTRIBUTES]->(term_attr_val)<-[new_versions]-
(term_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_term_root)<-[:HAS_TERM]-(new_codelist_root {uid:$codelist_uid})
WITH old_items, 
    new_term_root, 
    [(codelist_root)-[:HAS_TERM]->(new_term_root) | codelist_root.uid] AS codelists,
    term_attr_val, 
    max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_term_root.uid, {
    value_node: term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS new_items
"""

TERM_NOT_MODIFIED_CLAUSE_SPECIFIC_QUERY = """
,CASE WHEN old_items_map[common_item] = new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item, 
    'value_node', new_items_map[common_item].value_node,
    'change_date', new_items_map[common_item].change_date,
    'codelists', new_items_map[common_item].codelists
    ])
END AS not_modified
"""

TERM_RETURN_CLAUSE_SPECIFIC_QUERY = """
WITH collect(diff) as items_diffs, added_items, removed_items, collect(not_modified) as not_modified_items
RETURN added_items, removed_items, items_diffs, not_modified_items
"""

CODELIST_DATA_RETRIEVAL = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[old_versions]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_codelist_root)
WITH old_codelist_root, codelist_attr_val, max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_ATTRIBUTES]->
(codelist_attr_val)<-[new_versions]-(codelist_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_codelist_root) 
WITH old_items, new_codelist_root, codelist_attr_val, max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_codelist_root.uid, {
    value_node:codelist_attr_val,
    change_date: latest_date}])) AS new_items
"""
CODELIST_DIFF_CLAUSE = """
CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item, 
    'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
    'change_date', new_items_map[common_item].change_date,
    'is_change_of_codelist', true
    ])
END AS diff
"""
CODELIST_RETURN_CLAUSE = """
WITH collect(diff) as items_diffs, added_items, removed_items, new_items_map
RETURN added_items, removed_items, items_diffs, new_items_map
"""

TERM_DATA_RETRIEVAL = """
MATCH (old_package:CTPackage {name:$old_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_TERM]->
(package_term)-[:CONTAINS_ATTRIBUTES]->(term_attr_val)<-[old_versions]-
(term_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(old_term_root)
WITH old_term_root, 
    [(codelist_root)-[:HAS_TERM]->(old_term_root) | codelist_root.uid] AS codelists,
    term_attr_val, 
    max(old_versions.start_date) AS latest_date
WITH collect(apoc.map.fromValues([old_term_root.uid, {
    value_node:term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS old_items

MATCH (new_package:CTPackage {name:$new_package_name})-[:CONTAINS_CODELIST]->(package_codelist)-[:CONTAINS_TERM]->
(package_term)-[:CONTAINS_ATTRIBUTES]->(term_attr_val)<-[new_versions]-
(term_attr_root)<-[:HAS_ATTRIBUTES_ROOT]-(new_term_root)
WITH old_items, 
    new_term_root, 
    [(codelist_root)-[:HAS_TERM]->(new_term_root) | codelist_root.uid] AS codelists,
    term_attr_val, 
    max(new_versions.start_date) AS latest_date
WITH old_items, collect(apoc.map.fromValues([new_term_root.uid, {
    value_node: term_attr_val,
    codelists: codelists,
    change_date: latest_date}])) AS new_items
"""
TERM_DIFF_CLAUSE = """
CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
apoc.map.fromValues([
    'uid', common_item, 
    'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
    'change_date', new_items_map[common_item].change_date,
    'codelists', new_items_map[common_item].codelists
    ])
END AS diff
"""
TERM_RETURN_CLAUSE = """
WITH collect(diff) as items_diffs, added_items, removed_items
RETURN added_items, removed_items, items_diffs
"""

COMPARISON_PART = """
// From pattern comprehensions we get list of maps, where each map represents data for specific codelist or term.
// The following section merge list of maps coming from pattern comprehensions into one map.
// The created maps store codelist uids or term uids as a keys and attributes values as a map values.
WITH old_items, new_items,
apoc.map.mergeList(old_items) AS old_items_map,
apoc.map.mergeList(new_items) AS new_items_map
// The following section creates arrays with codelist uids or terms uids 
WITH old_items_map, new_items_map,
keys(old_items_map) AS old_items_uids,
keys(new_items_map) AS new_items_uids
// In the following section the comparison of uid arrays is made to identify if given codelist or term:
// was added, deleted, or is not moved in new package
WITH old_items_map, new_items_map, old_items_uids, new_items_uids,
apoc.coll.subtract(new_items_uids, old_items_uids) AS added_items,
apoc.coll.subtract(old_items_uids, new_items_uids) AS removed_items,
apoc.coll.intersection(old_items_uids, new_items_uids) AS common_items
// The following section unwinds list with uids of added items to filter out added items from the map that contains
// all elements from new package
WITH old_items_map, new_items_map, added_items, removed_items, common_items
UNWIND
  CASE WHEN added_items=[] THEN [NULL]
  ELSE added_items
  END AS added_item
WITH old_items_map, new_items_map,
  CASE WHEN added_items <> [] THEN
  collect(apoc.map.merge(apoc.map.fromValues(['uid',added_item]), new_items_map[added_item])) 
  ELSE collect(added_item) 
  END AS added_items, 
removed_items, common_items
// The following section unwinds list with uids of removed items to filter out removed items from the map that contains
// all elements from old package
UNWIND 
  CASE WHEN removed_items=[] THEN [NULL]
  ELSE removed_items
  END as removed_item
WITH old_items_map, new_items_map, added_items, 
  CASE WHEN removed_items <> [] THEN 
  collect(apoc.map.merge(apoc.map.fromValues(['uid', removed_item]), old_items_map[removed_item]))
  ELSE collect(removed_item) END 
  AS removed_items, 
common_items
// The following section unwinds list with uids of items that are present in old package and new package
// to filter out common items from the map that contains all elements from new package.
UNWIND 
  CASE WHEN common_items=[] THEN [NULL]
  ELSE common_items
  END AS common_item
// The following section makes the comparison of nodes that are present in both packages
WITH old_items_map, new_items_map, added_items, removed_items, common_items, common_item,
"""


@db.transaction
def get_ct_packages_codelist_changes(
    old_package_name: str, new_package_name: str, codelist_uid: str
) -> dict:
    query_params = {
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
        "codelist_uid": codelist_uid,
    }

    output = {}
    # codelists query
    complete_codelist_query = " ".join(
        [
            CODELIST_DATA_RETRIEVAL_SPECIFIC_QUERY,
            COMPARISON_PART,
            CODELIST_DIFF_CLAUSE,
            CODELIST_RETURN_CLAUSE,
        ]
    )
    codelist_ret, _ = db.cypher_query(complete_codelist_query, query_params)
    output["new_codelists"] = (
        sorted(codelist_ret[0][0], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["deleted_codelists"] = (
        sorted(codelist_ret[0][1], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["updated_codelists"] = codelist_ret[0][2] if len(codelist_ret) > 0 else []
    all_codelists_in_package = codelist_ret[0][3] if len(codelist_ret) > 0 else {}

    # terms query
    complete_term_query = " ".join(
        [
            TERM_DATA_RETRIEVAL_SPECIFIC_QUERY,
            COMPARISON_PART,
            TERM_DIFF_CLAUSE,
            TERM_NOT_MODIFIED_CLAUSE_SPECIFIC_QUERY,
            TERM_RETURN_CLAUSE_SPECIFIC_QUERY,
        ]
    )
    terms_ret, _ = db.cypher_query(complete_term_query, query_params)
    output["new_terms"] = (
        sorted(terms_ret[0][0], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["deleted_terms"] = (
        sorted(terms_ret[0][1], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["updated_terms"] = (
        sorted(terms_ret[0][2], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["not_modified_terms"] = (
        sorted(terms_ret[0][3], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )

    update_modified_codelists(
        output=output, all_codelists_in_package=all_codelists_in_package
    )
    return output


@db.transaction
def get_ct_packages_changes(old_package_name: str, new_package_name: str) -> dict:
    query_params = {
        "old_package_name": old_package_name,
        "new_package_name": new_package_name,
    }

    output = {}
    # codelists query
    complete_codelist_query = " ".join(
        [
            CODELIST_DATA_RETRIEVAL,
            COMPARISON_PART,
            CODELIST_DIFF_CLAUSE,
            CODELIST_RETURN_CLAUSE,
        ]
    )
    codelist_ret, _ = db.cypher_query(complete_codelist_query, query_params)
    output["new_codelists"] = (
        sorted(codelist_ret[0][0], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["deleted_codelists"] = (
        sorted(codelist_ret[0][1], key=lambda ct_codelist: ct_codelist["change_date"])
        if len(codelist_ret) > 0
        else []
    )
    output["updated_codelists"] = codelist_ret[0][2] if len(codelist_ret) > 0 else []
    all_codelists_in_package = codelist_ret[0][3] if len(codelist_ret) > 0 else {}

    # terms query
    complete_term_query = " ".join(
        [TERM_DATA_RETRIEVAL, COMPARISON_PART, TERM_DIFF_CLAUSE, TERM_RETURN_CLAUSE]
    )
    terms_ret, _ = db.cypher_query(complete_term_query, query_params)
    output["new_terms"] = (
        sorted(terms_ret[0][0], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["deleted_terms"] = (
        sorted(terms_ret[0][1], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )
    output["updated_terms"] = (
        sorted(terms_ret[0][2], key=lambda ct_term: ct_term["change_date"])
        if len(terms_ret) > 0
        else []
    )

    update_modified_codelists(
        output=output, all_codelists_in_package=all_codelists_in_package
    )
    return output


@db.transaction
def get_package_changes_by_year():
    query = """
    MATCH (p1)-[rel:NEXT_PACKAGE]->(p2)
    WITH p2.effective_date.year as year,
    rel.added_codelists as added_codelists, rel.updated_codelists as updated_codelists, rel.deleted_codelists as deleted_codelists,
    rel.added_terms as added_terms, rel.updated_terms as updated_terms, rel.deleted_terms as deleted_terms
    WITH year,
    sum(added_codelists) as added_codelists, sum(updated_codelists) as updated_codelists, sum(deleted_codelists) as deleted_codelists,
    sum(added_terms) as added_terms, sum(updated_terms) as updated_terms, sum(deleted_terms) as deleted_terms
    RETURN year, added_codelists, updated_codelists, deleted_codelists, added_terms, updated_terms, deleted_terms
    """
    yearly_aggregates = db.cypher_query(query)
    output = []
    if len(yearly_aggregates) > 0:
        for aggregate in yearly_aggregates[0]:
            output.append(
                {
                    "year": aggregate[0],
                    "added_codelists": aggregate[1],
                    "updated_codelists": aggregate[2],
                    "deleted_codelists": aggregate[3],
                    "added_terms": aggregate[4],
                    "updated_terms": aggregate[5],
                    "deleted_terms": aggregate[6],
                }
            )
    return output


def update_modified_codelists(output: dict, all_codelists_in_package: Sequence[dict]):
    """
    The following function adds codelists that contains some terms from the
    * new_terms
    * deleted_terms
    * updated_terms
    sections to the 'updated_codelists' section to mark given codelist as updated.
    :param output:
    :param all_codelists_in_package:
    """
    updated_codelist_uids = [
        codelist["uid"] for codelist in output["updated_codelists"]
    ]
    for terms in [
        output["new_terms"],
        output["deleted_terms"],
        output["updated_terms"],
    ]:
        for term in terms:
            for codelist in term["codelists"]:
                # we only want to add a codelist to the 'updated_codelists' column if given codelist
                # is not already there and this codelist is from the package that we are currently comparing
                if (
                    codelist not in updated_codelist_uids
                    and codelist in all_codelists_in_package
                ):
                    # updated_codelists_uids is a helper list to track all uids
                    # of codelists in the package that is being compared
                    updated_codelist_uids.append(codelist)
                    output["updated_codelists"].append(
                        {
                            "uid": codelist,
                            "value_node": all_codelists_in_package[codelist][
                                "value_node"
                            ],
                            "change_date": term["change_date"],
                            "is_change_of_codelist": False,
                        }
                    )
    output["updated_codelists"].sort(key=lambda codelist: codelist["change_date"])
