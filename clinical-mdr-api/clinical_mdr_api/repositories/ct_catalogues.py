from datetime import datetime
from enum import Enum
from typing import Optional

from neomodel import db


class CatalogueComparisonType(Enum):
    """
    Enum for Type of the catalogue comparison
    """

    ATTRIBUTES_COMPARISON = "attributes"
    SPONSOR_COMPARISON = "sponsor"


@db.transaction
def get_ct_catalogues_changes(
    library_name: Optional[str],
    catalogue_name: Optional[str],
    comparison_type: CatalogueComparisonType,
    start_datetime: datetime,
    end_datetime=datetime,
) -> dict:

    filter_parameters = []
    if library_name is not None:
        filter_by_library_name = """
            $library_name=head([(library:Library)-[:{LIBRARY_CT_REL}]->({CT_OBJECT}) | library.name])"""
        filter_parameters.append(filter_by_library_name)
    if catalogue_name is not None:
        filter_by_catalogue_name = """
            $catalogue_name IN [(catalogue:CTCatalogue)-[:HAS_CODELIST]->(codelist_root) | catalogue.name]"""
        filter_parameters.append(filter_by_catalogue_name)
    filter_statements = (
        "AND " + " AND ".join(filter_parameters) if len(filter_parameters) > 0 else ""
    )
    codelist_filter_statements = filter_statements.format(
        LIBRARY_CT_REL="CONTAINS_CODELIST", CT_OBJECT="codelist_root"
    )
    term_filter_statements = filter_statements.format(
        LIBRARY_CT_REL="CONTAINS_TERM", CT_OBJECT="term_root"
    )

    if comparison_type == CatalogueComparisonType.ATTRIBUTES_COMPARISON:
        relationship_type = "HAS_ATTRIBUTES_ROOT"
    elif comparison_type == CatalogueComparisonType.SPONSOR_COMPARISON:
        relationship_type = "HAS_NAME_ROOT"

    codelist_data_retrieval = f"""
    MATCH (codelist_root:CTCodelistRoot)-[:{relationship_type}]->
        (old_codelist_ver_root)-[old_versions]->(old_codelist_ver_value)
    WHERE old_versions.start_date < datetime($start_datetime)
    {codelist_filter_statements}
    WITH codelist_root, old_versions, old_codelist_ver_value
    ORDER BY old_versions.start_date DESC
    WITH codelist_root, 
        collect(old_codelist_ver_value)[0] AS old_codelist_ver_value, 
        collect(old_versions.start_date)[0] AS latest_date, 
        collect(old_versions) AS old_versions_collection
    WITH codelist_root, 
         old_codelist_ver_value, 
         latest_date, 
         head([x IN old_versions_collection WHERE x.start_date = latest_date | x ]) AS latest_version
    WITH collect(apoc.map.fromValues([codelist_root.uid, {{value_node:old_codelist_ver_value, change_date: latest_date}}])) AS old_items
    
    MATCH (codelist_root:CTCodelistRoot)-[:{relationship_type}]->
        (new_codelist_ver_root)-[new_versions]->(new_codelist_ver_value)
    WHERE new_versions.start_date < datetime($end_datetime)
    {codelist_filter_statements}
    WITH old_items, codelist_root, new_versions, new_codelist_ver_value
    ORDER BY new_versions.start_date DESC
    WITH old_items,
        codelist_root, 
        collect(new_codelist_ver_value)[0] AS new_codelist_ver_value, 
        collect(new_versions.start_date)[0] AS latest_date, 
        collect(new_versions) AS new_versions_collection
    WITH old_items, 
         codelist_root, 
         new_codelist_ver_value, 
         latest_date, head([x IN new_versions_collection WHERE x.start_date = latest_date | x ]) AS latest_version
    WITH old_items, 
    collect(apoc.map.fromValues([codelist_root.uid, {{value_node:new_codelist_ver_value, change_date: latest_date}}])) AS new_items
    """

    codelist_diff_clause = """
    CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
    apoc.map.fromValues([
        'uid', common_item, 
        'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
        'change_date', new_items_map[common_item].change_date,
        'is_change_of_codelist', true
        ])
    END AS diff
    """
    codelist_return_clause = """
    WITH collect(diff) as items_diffs, added_items, removed_items, new_items_map
    RETURN added_items, removed_items, items_diffs, new_items_map
    """

    term_data_retrieval = f"""
    MATCH (codelist_root:CTCodelistRoot)-[:HAS_TERM]->(term_root)-[:{relationship_type}]->
    (old_term_ver_root)-[old_versions]->(old_term_ver_value)
    WHERE old_versions.start_date < datetime($start_datetime)
    {term_filter_statements}
    WITH term_root, old_versions, old_term_ver_value
    ORDER BY old_versions.start_date DESC
    WITH term_root, 
    collect(old_term_ver_value)[0] AS old_term_ver_value, 
    collect(old_versions.start_date)[0] AS latest_date, 
    collect(old_versions) AS old_versions_collection
    WITH term_root, 
         old_term_ver_value, 
         latest_date, 
         head([x IN old_versions_collection WHERE x.start_date = latest_date | x ]) AS latest_version
    WITH collect(apoc.map.fromValues([term_root.uid, {{value_node:old_term_ver_value, codelists:[
        (term_root)<-[:HAS_TERM]-(codelist_root) | codelist_root.uid], change_date: latest_date}}])) AS old_items

    MATCH (codelist_root:CTCodelistRoot)-[:HAS_TERM]->(term_root)-[:{relationship_type}]->
    (new_term_ver_root)-[new_versions]->(new_term_ver_value)
    WHERE new_versions.start_date < datetime($end_datetime)
    {term_filter_statements}
    WITH old_items, term_root, new_versions, new_term_ver_value
    ORDER BY new_versions.start_date DESC
    WITH old_items,
        term_root,
        collect(new_term_ver_value)[0] AS new_term_ver_value, 
        collect(new_versions.start_date)[0] AS latest_date, 
        collect(new_versions) AS new_versions_collection
    WITH old_items,
         term_root, 
         new_term_ver_value, 
         latest_date, 
         head([x IN new_versions_collection WHERE x.start_date = latest_date | x ]) AS latest_version
    WITH old_items, 
    collect(apoc.map.fromValues([term_root.uid, {{value_node:new_term_ver_value, codelists:[
        (term_root)<-[:HAS_TERM]-(codelist_root) | codelist_root.uid], change_date: latest_date}}])) AS new_items
    """
    term_diff_clause = """
    CASE WHEN old_items_map[common_item] <> new_items_map[common_item] THEN
    apoc.map.fromValues([
        'uid', common_item, 
        'value_node', apoc.diff.nodes(old_items_map[common_item].value_node, new_items_map[common_item].value_node),
        'change_date', new_items_map[common_item].change_date,
        'codelists', new_items_map[common_item].codelists
        ])
    END AS diff
    """
    term_return_clause = """
    WITH collect(diff) as items_diffs, added_items, removed_items
    RETURN added_items, removed_items, items_diffs
    """

    comparison_part = """
    // From data retrieval part we get list of maps, where each map represents data for specific codelist or term.
    // The following section merge list of maps coming from data retrieval part into one map.
    // The created maps store codelist uids or term uids as a keys and attributes values as a map values.
    WITH old_items, new_items,
    apoc.map.mergeList(old_items) AS old_items_map,
    apoc.map.mergeList(new_items) AS new_items_map
    // The following section creates arrays with codelist uids or terms uids 
    WITH old_items_map, new_items_map,
    keys(old_items_map) AS old_items_uids,
    keys(new_items_map) AS new_items_uids
    // In the following section the comparison of uid arrays is made to identify if given codelist or term:
    // was added, deleted, or is not moved in new catalogue
    WITH old_items_map, new_items_map, old_items_uids, new_items_uids,
    apoc.coll.subtract(new_items_uids, old_items_uids) AS added_items,
    apoc.coll.subtract(old_items_uids, new_items_uids) AS removed_items,
    apoc.coll.intersection(old_items_uids, new_items_uids) AS common_items
    // The following section unwinds list with uids of added items to filter out added items from the map that contains
    // all elements from new catalogue
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
    // all elements from old catalogue
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
    // The following section unwinds list with uids of items that are present in old catalogue and new catalogue
    // to filter out common items from the map that contains all elements from new catalogue.
    UNWIND 
      CASE WHEN common_items=[] THEN [NULL]
      ELSE common_items
      END AS common_item
    // The following section makes the comparison of nodes that are present in both catalogues
    WITH old_items_map, new_items_map, added_items, removed_items, common_items, common_item,
    """
    query_params = {
        "library_name": library_name,
        "catalogue_name": catalogue_name,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    }

    output = {}
    # codelist query
    complete_codelist_query = " ".join(
        [
            codelist_data_retrieval,
            comparison_part,
            codelist_diff_clause,
            codelist_return_clause,
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
        [term_data_retrieval, comparison_part, term_diff_clause, term_return_clause]
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

    # The following section adds codelists that contains some terms from the
    # * new_terms
    # * deleted_terms
    # * updated_terms
    # columns to the 'updated_codelists' column to mark given codelist as updated.
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

    return output
