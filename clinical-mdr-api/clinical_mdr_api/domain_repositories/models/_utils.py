import datetime
import math
import re
from collections import defaultdict
from typing import Sequence

import neo4j
from neomodel import match, match_q, properties, relationship_manager
from neomodel.core import db
from opencensus.trace import execution_context


def convert_to_tz_aware_datetime(value: datetime.datetime):
    # Function created to properly adjust timezone part in Python datetime
    # TODO: this is to be removed - we need to start time
    # zone aware datetimes. astimezone returns date with UTC tz
    return value.astimezone()


def convert_to_datetime(value: neo4j.time.DateTime):
    # Function created to properly represent the DateTime from database as Python datetime
    # Workaround for improper default rounding in to_native method

    dt: datetime.datetime = value.to_native()
    if hasattr(dt, "second"):
        subseconds, _ = math.modf(value.second)
        # Subseconds are between 0.0 and 0.999 999 999
        # thats why to get microseconds it is needed to multiply by 1000000
        microseconds: int = round(subseconds * 1000000)
        # TODO: this is to be removed - we need to start time
        # zone aware datetimes.
        return dt.replace(microsecond=microseconds).replace(tzinfo=None)
    return dt


def format_generic_header_values(values: Sequence):
    if len(values) > 0 and isinstance(values[0], neo4j.time.DateTime):
        return [convert_to_datetime(_val) for _val in values]
    return values


def process_filter_args(cls, kwargs):
    """
    loop through properties in filter parameters check they match class definition
    deflate them and convert into something easy to generate cypher from
    """

    output = {}

    for key, value in kwargs.items():
        current_class = cls
        prop = ""
        leaf_prop = None
        operator = "="
        for part in key.split("__"):
            defined_props = current_class.defined_properties(rels=True)
            if part in defined_props:
                if isinstance(
                    defined_props[part], relationship_manager.RelationshipDefinition
                ):
                    defined_props[part]._lookup_node_class()
                    current_class = defined_props[part].definition["node_class"]
                if prop:
                    prop += "__"
                prop += part
            elif part in match.OPERATOR_TABLE:
                operator = match.OPERATOR_TABLE[part]
                continue
            else:
                raise ValueError(f"No such property {part} on {cls.__name__}")
            leaf_prop = part

        property_obj = getattr(current_class, leaf_prop)

        if isinstance(property_obj, properties.AliasProperty):
            prop = property_obj.aliased_to()
            deflated_value = getattr(cls, prop).deflate(value)
        else:
            # handle special operators
            if operator == match._SPECIAL_OPERATOR_IN:
                if not isinstance(value, tuple) and not isinstance(value, list):
                    raise ValueError(
                        f"Value must be a tuple or list for IN operation {key}={value}"
                    )
                deflated_value = [property_obj.deflate(v) for v in value]
            elif operator == match._SPECIAL_OPERATOR_ISNULL:
                if not isinstance(value, bool):
                    raise ValueError(
                        f"Value must be a bool for isnull operation on {key}"
                    )
                operator = "IS NULL" if value else "IS NOT NULL"
                deflated_value = None
            elif operator in match._REGEX_OPERATOR_TABLE.values():
                deflated_value = property_obj.deflate(value)
                if not isinstance(deflated_value, str):
                    raise ValueError(f"Must be a string value for {key}")
                if operator in match._STRING_REGEX_OPERATOR_TABLE.values():
                    deflated_value = re.escape(deflated_value)
                deflated_value = operator.format(deflated_value)
                operator = match._SPECIAL_OPERATOR_REGEX
            else:
                deflated_value = property_obj.deflate(value)

        # FIXME
        # map property to correct property name in the database
        # db_property = cls.defined_properties(rels=False)[prop].db_property or prop
        db_property = prop

        output[db_property] = (operator, deflated_value)

    return output


# pylint: disable=unused-argument
def _rel_helper(
    lhs,
    rhs,
    ident=None,
    relation_type=None,
    direction=None,
    relation_properties=None,
    **kwargs,
):
    """
    Generate a relationship matching string, with specified parameters.
    Examples:
    relation_direction = OUTGOING: (lhs)-[relation_ident:relation_type]->(rhs)
    relation_direction = INCOMING: (lhs)<-[relation_ident:relation_type]-(rhs)
    relation_direction = EITHER: (lhs)-[relation_ident:relation_type]-(rhs)
    :param lhs: The left hand statement.
    :type lhs: str
    :param rhs: The right hand statement.
    :type rhs: str
    :param ident: A specific identity to name the relationship, or None.
    :type ident: str
    :param relation_type: None for all direct rels, * for all of any length, or a name of an explicit rel.
    :type relation_type: str
    :param direction: None or EITHER for all OUTGOING,INCOMING,EITHER. Otherwise OUTGOING or INCOMING.
    :param relation_properties: dictionary of relationship properties to match
    :returns: string
    """

    if direction == match.OUTGOING:
        stmt = "-{0}->"
    elif direction == match.INCOMING:
        stmt = "<-{0}-"
    else:
        stmt = "-{0}-"

    rel_props = ""

    if relation_properties:
        key_val_pairs = ", ".join(
            [f"{key}: {value}" for key, value in relation_properties.items()]
        )
        rel_props = f"{{{key_val_pairs}}}"

    # direct, relation_type=None is unspecified, relation_type
    if relation_type is None:
        stmt = stmt.format("")
    # all("*" wildcard) relation_type
    elif relation_type == "*":
        stmt = stmt.format("[*]")
    else:
        # explicit relation_type
        stmt = stmt.format(f"[{ident if ident else ''}:`{relation_type}`{rel_props}]")

    # Make sure not to add parenthesis when they are already present
    # (was not part of the original function)
    if lhs[-1] != ")":
        lhs = f"({lhs})"
    if rhs[-1] != ")":
        rhs = f"({rhs})"
    return f"{lhs}{stmt}{rhs}"


class CustomQueryBuilder(match.QueryBuilder):
    def __init__(self, node_set):
        super().__init__(node_set=node_set)
        self._ast["optional match"] = []
        self.node_counter = defaultdict(int)

    def build_ast(self):
        # This is where we deal with required additional relations to
        # fetch, it is not part of the original method.
        self._ast["relation_tree_map"] = {}
        for rel_name in self.node_set._relations_to_fetch:
            self.build_traversal_from_path(rel_name, self.node_set.source)
        for rel_name in self.node_set._optional_relations_to_fetch:
            self.build_traversal_from_path(
                rel_name, self.node_set.source, optional_traversal=True
            )

        self.build_source(self.node_set)

        if hasattr(self.node_set, "skip"):
            self._ast["skip"] = self.node_set.skip
        if hasattr(self.node_set, "limit"):
            self._ast["limit"] = self.node_set.limit

        return self

    def _add_to_return_set(self, name):
        if "return_set" not in self._ast:
            self._ast["return_set"] = []
        if name not in self._ast["return_set"] and name != self._ast.get("return"):
            self._ast["return_set"].append(name)

    def build_traversal_from_path(
        self,
        path: str,
        source_class,
        include_nodes_in_return=True,
        optional_traversal=False,
    ):
        src_class = source_class
        stmt = ""
        relation_tree_map = self._ast["relation_tree_map"]
        for part in path.split("__"):
            relationship = getattr(src_class, part)

            # build source
            if "node_class" not in relationship.definition:
                relationship._lookup_node_class()
            rhs_label = relationship.definition["node_class"].__label__

            rel_reference = f"{relationship.definition['node_class']}_{part}"
            self.node_counter[rel_reference] += 1
            rhs_name = f"{rhs_label.lower()}_{part}_{self.node_counter[rel_reference]}"
            rhs_ident = f"{rhs_name}:{rhs_label}"
            if include_nodes_in_return:
                self._add_to_return_set(rhs_name)

            if not stmt:
                lhs_label = src_class.__label__
                lhs_name = lhs_label.lower()
                lhs_ident = f"{lhs_name}:{lhs_label}"
                if include_nodes_in_return:
                    self._add_to_return_set(lhs_name)
                # FIXME: find something cleaner
                # We remove the item generated by build_label() to avoid a useless MATCH statement
                if f"({lhs_ident}" in self._ast["match"]:
                    self._ast["match"].remove(f"({lhs_ident}")
            else:
                lhs_ident = stmt
            if part not in relation_tree_map:
                relation_tree_map[part] = {
                    "target": relationship.definition["node_class"],
                    "children": {},
                    "variable_name": rhs_name,
                }

            # FIXME: is it useful?
            # self._ast['result_class'] = relationship.definition['node_class']

            rel_ident = self.create_ident()
            stmt = _rel_helper(
                lhs=lhs_ident,
                rhs=rhs_ident,
                ident=rel_ident,
                direction=relationship.definition["direction"],
                relation_type=relationship.definition["relation_type"],
            )
            src_class = relationship.definition["node_class"]
            relation_tree_map = relation_tree_map[part]["children"]
        if not optional_traversal:
            self._ast["match"].append(stmt)
        else:
            self._ast["optional match"].append(stmt)
        return rhs_name

    def build_query(self):
        query = ""

        if "lookup" in self._ast:
            query += self._ast["lookup"]

        # Instead of using only one MATCH statement for every relation
        # to follow, we use one MATCH per relation (to avoid cartesian
        # product issues...). This part will need some refinement!
        query += " MATCH "
        query += " MATCH ".join(i for i in self._ast["match"])

        if "where" in self._ast and self._ast["where"]:
            query += " WHERE "
            query += " AND ".join(self._ast["where"])

        if len(self._ast["optional match"]) > 0:
            query += " OPTIONAL MATCH "
            query += " OPTIONAL MATCH ".join(i for i in self._ast["optional match"])

        if "with" in self._ast and self._ast["with"]:
            query += " WITH "
            query += self._ast["with"]

        query += " RETURN "
        # FIXME: replace all by return_set
        if "return" in self._ast:
            query += self._ast["return"]
        if "return_set" in self._ast:
            if "return" in self._ast:
                query += ", "
            query += ", ".join(self._ast["return_set"])

        if "order_by" in self._ast and self._ast["order_by"]:
            query += " ORDER BY "
            query += ", ".join(self._ast["order_by"])

        if "skip" in self._ast:
            query += f" SKIP {self._ast['skip']:d}"

        if "limit" in self._ast:
            query += f" LIMIT {self._ast['limit']:d}"

        return query

    def build_label(self, ident, cls):
        """
        match nodes by a label
        """
        ident_w_label = ident + ":" + cls.__label__
        if "return_set" not in self._ast or ident not in self._ast["return_set"]:
            self._ast["match"].append(f"({ident_w_label})")
            self._ast["return"] = ident
            self._ast["result_class"] = cls
        return ident

    def _build_filter_statements(self, ident, filters, target, source_class):
        for prop, op_and_val in filters.items():
            if "__" in prop:
                path, prop = prop.rsplit("__", 1)
                ident = self.build_traversal_from_path(
                    path, source_class, include_nodes_in_return=True
                )
            op, val = op_and_val
            if op in match._UNARY_OPERATORS:
                # unary operators do not have a parameter
                statement = f"{ident}.{prop} {op}"
            else:
                place_holder = self._register_place_holder(ident + "_" + prop)
                statement = f"{ident}.{prop} {op} ${place_holder}"
                self._query_params[place_holder] = val
            target.append(statement)

    def _parse_q_filters(self, ident, q, source_class):
        target = []
        for child in q.children:
            if isinstance(child, match_q.QBase):
                q_childs = self._parse_q_filters(ident, child, source_class)
                if child.connector == match_q.Q.OR:
                    q_childs = "(" + q_childs + ")"
                target.append(q_childs)
            else:
                kwargs = {child[0]: child[1]}
                filters = process_filter_args(source_class, kwargs)
                self._build_filter_statements(ident, filters, target, source_class)
        ret = f" {q.connector} ".join(target)
        if q.negated:
            ret = f"NOT ({ret})"
        return ret

    def _execute(self, lazy=False, dict_output=False):
        """
        Overidde of the original method.
        Mostly a copy/paste except we change the results format.
        """
        if lazy:
            # inject id = into ast
            self._ast["return"] = f"id({self._ast['return']})"
        query = self.build_query()

        tracer = execution_context.get_opencensus_tracer()
        with tracer.span("neomodel.query") as span:
            span.add_attribute("cypher.query", query)
            span.add_attribute("cypher.params", self._query_params)

            results, prop_names = db.cypher_query(
                query, self._query_params, resolve_objects=True
            )

        if dict_output:
            result_dict = []
            for item in results:
                result_dict.append(dict(zip(prop_names, item)))
            return result_dict
        if results and len(results[0]) == 1:
            return [n[0] for n in results]
        return results


class CustomNodeSet(match.NodeSet):

    query_cls = CustomQueryBuilder

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._relations_to_fetch = []
        self._optional_relations_to_fetch = []

    def all(self, lazy=False, dict_output=False):
        """
        Return all nodes belonging to the set
        :param lazy: False by default, specify True to get nodes with id only without the parameters.
        :param dict_output: False by default, specify True to get nodes with the corresponding query variable names
        :return: list of nodes
        :rtype: list
        """
        return self.query_cls(self).build_ast()._execute(lazy, dict_output=dict_output)

    def fetch_relations(self, *relation_names):
        """Custom method to specify a set of extra relations to return."""
        self._relations_to_fetch = relation_names
        return self

    def fetch_optional_relations(self, *relation_names):
        """Custom method to specify a set of extra optional relations to return."""
        self._optional_relations_to_fetch = relation_names
        return self

    def _to_relation_tree(self, root_node, other_nodes, relation_tree_map):
        """Recursive method to build root_node's relation tree from relation_tree_map."""
        root_node._relations = {}
        for name, relation_def in relation_tree_map.items():
            for var_name, node in other_nodes.items():
                if var_name == relation_def["variable_name"] and node is not None:
                    root_node._relations[name] = self._to_relation_tree(
                        node, other_nodes, relation_def["children"]
                    )
        return root_node

    def to_relation_trees(self):
        """Convert every result contained in this node set to a relation tree.

        By default, we receive results from neomodel as a list of
        nodes without the hierarchy. This method tries to rebuild this
        hierarchy without overidding anything in the node, that's why
        we use a dedicated property to store node's relations.

        NOTE: there is still an issue with this method, it won't work
        properly if two nodes of the same type are returned because it
        will mix them. This is mostly because we don't have a simple
        way to identify which node corresponds to which relation...

        """
        results = []
        qbuilder = self.query_cls(self).build_ast()
        all_nodes = qbuilder._execute(dict_output=True)
        other_nodes = {}
        root_node = None
        relation_tree_map = qbuilder._ast["relation_tree_map"]
        for result_dict in all_nodes:
            for name, node in result_dict.items():
                if node.__class__ is self.source:
                    root_node = node
                else:
                    other_nodes[name] = node
            results.append(
                self._to_relation_tree(root_node, other_nodes, relation_tree_map)
            )
        return results


def classproperty(f) -> CustomNodeSet:
    class cpf:
        def __init__(self, getter):
            self.getter = getter

        def __get__(self, obj, class_type):
            return self.getter(class_type)

    return cpf(f)
