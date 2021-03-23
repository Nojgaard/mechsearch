import mod
import re
from typing import Dict, List, Optional, Set


hydrogen_pattern = re.compile("H")
element_pattern = re.compile("^[\s]*[a-zA-Z]+")


expected_bond_counts: Dict[str, int] = {"C": 4, "O": 2, "N": 3, "S": 2, "P": 5}


class Vertex:
    def __init__(self, original_vertex: mod.Graph.Vertex):
        self._original: mod.Graph.Vertex = original_vertex
        self._hydrogen_count: int = 0

    def __str__(self):
        label = f"HydAbs({self._original.stringLabel}, {self._hydrogen_count})"
        return f"node [ id {self._original.id} label \"{label}\" ]"

    def add_hydrogen(self):
        self._hydrogen_count += 0


class RuleVertex:
    def __init__(self, original_vertex: mod.Rule.Vertex):
        self._original: mod.Rule.Vertex = original_vertex
        self._left_hydrogen_count: int = 0
        self._right_hydrogen_count: int = 0
        self._left_bound_electrons: float = 0
        self._right_bound_electrons: float = 0

    def _label_vertex(self, label: str, hydrogen_count: int, bound_electrons: float) -> str:
        element = element_pattern.match(label).group(0)
        local_charge = 0
        if label.endswith("+"):
            local_charge = 1
        elif label.endswith("-"):
            local_charge = -1

        hydrogen_string = str(hydrogen_count)
        if element not in expected_bond_counts or bound_electrons < (expected_bond_counts[element] + local_charge):
            hydrogen_string = "*"

        label = f"HydAbs({label}, {hydrogen_string})"
        return f"node [ id {self._original.id} label \"{label}\" ]"

    def left_string(self) -> str:
        if self._original.left.stringLabel != self._original.right.stringLabel or\
                self._left_bound_electrons != self._right_bound_electrons:
            return self._label_vertex(self._original.left.stringLabel, self._left_hydrogen_count,
                                      self._left_bound_electrons)

        return ""

    def right_string(self) -> str:
        if self._original.left.stringLabel != self._original.right.stringLabel or\
                self._left_bound_electrons != self._right_bound_electrons:
            return self._label_vertex(self._original.right.stringLabel, self._right_hydrogen_count,
                                      self._right_bound_electrons)

        return ""

    def context_string(self) -> str:
        if self._original.left.stringLabel != self._original.right.stringLabel or\
                self._left_bound_electrons != self._right_bound_electrons:
            return ""

        return self._label_vertex(self._original.left.stringLabel, self._left_hydrogen_count,
                                  self._left_bound_electrons)

    def add_hydrogen(self):
        self.add_left_hydrogen()
        self.add_right_hydrogen()

    def add_left_hydrogen(self):
        self._left_hydrogen_count += 1
        self._left_bound_electrons += 1

    def add_right_hydrogen(self):
        self._right_hydrogen_count += 1
        self._right_bound_electrons += 1

    def record_edge(self, edge: mod.Rule.Edge):
        if edge.left:
            self.record_left_edge(edge.left)
        if edge.right:
            self.record_right_edge(edge.right)

    def record_left_edge(self, edge: mod.Rule.LeftGraph.Edge):
        if edge.bondType == mod.BondType.Single:
            self._left_bound_electrons += 1
        elif edge.bondType == mod.BondType.Double:
            self._left_bound_electrons += 2
        elif edge.bondType == mod.BondType.Triple:
            self._left_bound_electrons += 3
        elif edge.bondType == mod.BondType.Aromatic:
            self._left_bound_electrons += 1.5

    def record_right_edge(self, edge: mod.Rule.RightGraph.Edge):
        if edge.bondType == mod.BondType.Single:
            self._right_bound_electrons += 1
        elif edge.bondType == mod.BondType.Double:
            self._right_bound_electrons += 2
        elif edge.bondType == mod.BondType.Triple:
            self._right_bound_electrons += 3
        elif edge.bondType == mod.BondType.Aromatic:
            self._right_bound_electrons += 1.5


def abstract_graph(graph: mod.Graph) -> mod.Graph:
    new_nodes: Dict[mod.Graph.Vertex, Vertex] = {}
    preserved_edges: List[mod.Graph.Edge] = list()

    for edge in graph.edges:
        preserved_nodes: Set[mod.Graph.Vertex] = set()
        hydrogenated_node: Optional[mod.Graph.Vertex] = None

        if hydrogen_pattern.match(edge.source.stringLabel):
            preserved_nodes.add(edge.target)
            hydrogenated_node = edge.target
        elif hydrogen_pattern.match(edge.target.stringLabel):
            preserved_nodes.add(edge.source)
            hydrogenated_node = edge.source
        else:
            preserved_nodes |= {edge.source, edge.target}
            preserved_edges.append(edge)

        for node in preserved_nodes:
            if node not in new_nodes:
                new_nodes[node] = Vertex(node)

        if hydrogenated_node is not None:
            new_nodes[hydrogenated_node].add_hydrogen()

    gml: str = f"graph [ " + " ".join(str(vertex) for vertex in new_nodes.values()) + " " +\
               " ".join(f"edge [ source {edge.source.id} target {edge.target.id} label \"{edge.stringLabel}\" ]" for
                        edge in preserved_edges) + " ]"
    return mod.graphGMLString(gml, add=False)


def abstract_rule(rule: mod.Rule) -> mod.Rule:
    new_nodes: Dict[mod.Rule.Vertex, RuleVertex] = dict()
    preserved_edges: List[mod.Rule.Edge] = list()

    for edge in rule.edges:
        preserved_nodes: Set[mod.Rule.Vertex] = set()
        hydrogen_node: Optional[mod.Rule.Vertex] = None

        if hydrogen_pattern.match(edge.source.left.stringLabel):
            preserved_nodes.add(edge.target)
            hydrogen_node = edge.source
        elif hydrogen_pattern.match(edge.target.left.stringLabel):
            preserved_nodes.add(edge.source)
            hydrogen_node = edge.target
        else:
            preserved_nodes |= {edge.source, edge.target}
            preserved_edges.append(edge)

        for node in preserved_nodes:
            if node not in new_nodes:
                new_nodes[node] = RuleVertex(node)

        if hydrogen_node is not None:
            other_node = next(node for node in {edge.source, edge.target} if node != hydrogen_node)
            if edge.left:
                if edge.right:
                    new_nodes[other_node].add_hydrogen()
                else:
                    new_nodes[other_node].add_left_hydrogen()
            else:
                new_nodes[other_node].add_right_hydrogen()
        else:
            for node in preserved_nodes:
                new_nodes[node].record_edge(edge)

    left_edges = list(edge.left for edge in preserved_edges if edge.left and
                      (not edge.right or edge.left.bondType != edge.right.bondType))
    context_edges = list(edge.left for edge in preserved_edges if edge.left and edge.right and
                         edge.left.bondType == edge.right.bondType)
    right_edges = list(edge.right for edge in preserved_edges if edge.right and
                       (not edge.left or edge.left.bondType != edge.right.bondType))

    left_gml: str = f"left [ " + " ".join(vertex.left_string() for vertex in new_nodes.values()) + " " +\
                    " ".join(f"edge [ source {edge.source.id} target {edge.target.id} label \"{edge.stringLabel}\" ]"
                             for edge in left_edges) + " ]"
    context_gml: str = f"context [ " + " ".join(vertex.context_string() for vertex in new_nodes.values()) + " " +\
                       " ".join(f"edge [ source {edge.source.id} target {edge.target.id} label \"{edge.stringLabel}\" ]"
                                for edge in context_edges) + " ]"
    right_gml: str = f"right [ " + " ".join(vertex.right_string() for vertex in new_nodes.values()) + " " +\
                     " ".join(f"edge [ source {edge.source.id} target {edge.target.id} label \"{edge.stringLabel}\" ]"
                              for edge in right_edges) + " ]"

    gml: str = "rule [ " + " ".join([left_gml, context_gml, right_gml]) + " ]"
    return mod.ruleGMLString(gml, add=False)

