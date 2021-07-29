from collections import Counter
from mechsearch.atom_spectrum import AtomSpectrum
from mechsearch.hydrogen_abstraction import abstract_graph, abstract_rule
from mechsearch.rule_canonicalisation import CanonSmilesRule
import mod
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union


class Graph:
    def __init__(self, graph: mod.Graph, functional_groups: Optional[Dict['Graph', int]] = None):
        self._original: mod.Graph = graph
        self._abstracted: Optional[mod.Graph] = None

        self._atom_spectrum: Optional[AtomSpectrum] = None

        self._functional_groups: Dict[Graph, int] = dict(functional_groups) if functional_groups is not None else {}

    def __eq__(self, other: 'Graph') -> bool:
        return self.id == other.id

    def __ne__(self, other: 'Graph') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name

    @property
    def graph(self) -> mod.Graph:
        return self._original

    @property
    def id(self) -> int:
        return self.graph.id

    @property
    def name(self) -> str:
        return self.graph.name

    @property
    def number_of_vertices(self) -> int:
        return self.graph.numVertices

    @property
    def abstract_graph(self) -> mod.Graph:
        if self._abstracted is None:
            self._abstracted = abstract_graph(self.graph)

        return self._abstracted

    @property
    def atom_spectrum(self) -> AtomSpectrum:
        if self._atom_spectrum is None:
            self._atom_spectrum = AtomSpectrum.from_graph(self.graph)

        return self._atom_spectrum

    @property
    def functional_groups(self) -> Dict['Graph', int]:
        return dict(self._functional_groups)

    def print(self, printer: mod.GraphPrinter):
        self.graph.print(printer)


class GraphMultiset:
    def __init__(self, graphs: Optional[Dict[Graph, int]] = None):
        self._counter: Counter = Counter(graphs) if graphs is not None else {}
        self._graphs: List[Graph] = sorted(self.counter.elements(), key=lambda graph: graph.id)

        self._key = tuple(self.graphs)
        self._hash = hash(self._key)

        self._atom_spectrum: Optional[AtomSpectrum] = None

    def __eq__(self, other: 'GraphMultiset') -> bool:
        return self._key == other._key

    def __ne__(self, other: 'GraphMultiset') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return self._hash

    def __add__(self, other: 'GraphMultiset') -> 'GraphMultiset':
        return GraphMultiset(self.counter + other.counter)

    def __sub__(self, other: 'GraphMultiset') -> 'GraphMultiset':
        return GraphMultiset(self.counter - other.counter)

    def __len__(self) -> int:
        return len(self.graphs)

    def __str__(self) -> str:
        return ", ".join(f"{graph}: {count}" for graph, count in self.counter.items())

    @property
    def counter(self) -> Counter:
        return Counter(self._counter)

    @property
    def graphs(self) -> List[Graph]:
        return self._graphs

    @staticmethod
    def from_graph_iterable(graphs: Iterable[Graph]) -> 'GraphMultiset':
        return GraphMultiset(Counter(graphs))

    @staticmethod
    def from_dg_vertices(vertices: mod.DGVertexRange) -> 'GraphMultiset':
        return GraphMultiset.from_graph_iterable(Graph(vertex.graph) for vertex in vertices)

    @property
    def atom_spectrum(self) -> AtomSpectrum:
        if self._atom_spectrum is None:
            self._atom_spectrum = AtomSpectrum.from_graphs(graph.graph for graph in self.graphs)

        return self._atom_spectrum

    def sub_multisets(self, maximum_size: Optional[int] = None) -> Iterable['GraphMultiset']:
        if maximum_size is None:
            maximum_size = len(self)

        sub_counts = [[]]
        for graph, count in self.counter.items():
            new_sub_counts = []
            for sub_count in sub_counts:
                new_sub_counts.extend(sub_count + [num] for num in range(min(count, maximum_size - sum(sub_count)) + 1))

            sub_counts = new_sub_counts

        for sub_counts in sub_counts:
            yield GraphMultiset({key: count for key, count in zip(self.counter, sub_counts) if count > 0})


class Step:
    def __init__(self, entry: int, mechanism: int, number: int, components: Optional[List[str]] = None):
        self._entry: int = entry
        self._mechanism: int = mechanism
        self._number: int = number

        self._components: Set[str] = set(components) if components is not None else set()

    def __str__(self) -> str:
        return f"{self.entry}-{self.mechanism}-{self.number}"

    @property
    def entry(self) -> int:
        return self._entry

    @property
    def mechanism(self) -> int:
        return self._mechanism

    @property
    def number(self) -> int:
        return self._number

    @property
    def components(self) -> Set[str]:
        return set(self._components)

    @staticmethod
    def deserialise(json_object: Dict[str, Any]) -> 'Step':
        return Step(json_object["entry"], json_object["proposal"], json_object["step"],
                    json_object["components"] if "components" in json_object else None)

    def serialise(self) -> Dict[str, Any]:
        return {"entry": self.entry, "proposal": self.mechanism, "step": self.number,
                "components": list(self.components)}


class Rule:
    def __init__(self, rule: mod.Rule, steps: List[Step] = None, left_functional_groups: Dict[Graph, int] = None,
                 right_functional_groups: Dict[Graph, int] = None):
        self._original: mod.Rule = rule
        self._abstracted: Optional[mod.Rule] = None
        self._inverse: Optional[mod.Rule] = None

        # self._left_multiset: GraphMultiset = left_multiset
        # self._right_multiset: GraphMultiset = right_multiset

        self._steps: List[Step] = list(steps) if steps is not None else []

        self._left_functional_groups: Dict[Graph, int] = dict(left_functional_groups) if\
            left_functional_groups is not None else {}
        self._right_functional_groups: Dict[Graph, int] = dict(right_functional_groups) if\
            right_functional_groups is not None else {}

        self._canonical_smiles: Optional[CanonSmilesRule] = None

        self._atom_spectrum: Optional[AtomSpectrum] = None

    def __eq__(self, other: 'Rule') -> bool:
        return self.canonical_smiles == other.canonical_smiles

    def __ne__(self, other: 'Rule') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.canonical_smiles)

    @property
    def rule(self) -> mod.Rule:
        return self._original

    @property
    def name(self) -> str:
        return self.rule.name

    @property
    def number_of_vertices(self) -> int:
        return self.rule.numVertices

    @property
    def canonical_smiles(self) -> CanonSmilesRule:
        if self._canonical_smiles is None:
            self._canonical_smiles = CanonSmilesRule(self.rule)

        return self._canonical_smiles

    @property
    def abstract_rule(self) -> mod.Rule:
        if self._abstracted is None:
            self._abstracted = abstract_rule(self.rule)

        return self._abstracted

    @property
    def inverse_rule(self) -> mod.Rule:
        if self._inverse is None:
            self._inverse = Rule(self._original.makeInverse() if self._original.numVertices > 0 else self._original)
            self._inverse._inverse = self

        return self._inverse

    # @property
    # def left_multiset(self) -> GraphMultiset:
    #     return self._left_multiset
    #
    # @property
    # def right_multiset(self) -> GraphMultiset:
    #     return self._right_multiset

    @property
    def steps(self) -> List[Step]:
        return list(self._steps)

    @property
    def left_functional_groups(self) -> Dict[Graph, int]:
        return dict(self._left_functional_groups)

    @property
    def right_functional_groups(self) -> Dict[Graph, int]:
        return dict(self._right_functional_groups)

    @property
    def atom_spectrum(self) -> AtomSpectrum:
        if self._atom_spectrum is None:
            self._atom_spectrum = AtomSpectrum.from_rule(self.rule)

        return self._atom_spectrum

    def serialise(self) -> Dict[str, Any]:
        return {"name": self.name, "gml": self.rule.getGMLString(),
                "steps": list(step.serialise() for step in self.steps)}

    def print(self, printer: mod.GraphPrinter):
        return self.rule.print(printer)


class FilteredRule:
    def __init__(self, rule: mod.Rule):
        self._rule: mod.Rule = rule

        self._used_vertices: Set[mod.RuleVertex] = set()
        self._used_edges: Dict[Tuple[mod.RuleVertex, mod.RuleVertex], mod.RuleEdge] = {}

        self._protected_vertices: Set[mod.RuleVertex] = set()

        self._relabels: Dict[Union[mod.RuleLeftGraphVertex, mod.RuleContextGraphVertex], str] = {}

    @property
    def rule(self) -> mod.Rule:
        return self._rule

    @property
    def used_vertices(self) -> Set[mod.RuleVertex]:
        return set(self._used_vertices)

    @property
    def used_edges(self) -> Dict[Tuple[mod.RuleVertex, mod.RuleVertex], mod.RuleEdge]:
        return dict(self._used_edges)

    def add_all(self):
        for vertex in self.rule.vertices:
            self.add_vertex(vertex)

        for edge in self.rule.edges:
            self.add_edge(edge)

        # for ve in list(self.rule.vertices) + list(self.rule.edges):
        #     self.add(ve)

    def add_vertex(self, vertex: mod.RuleVertex, protected: bool = False, left_label: str = None,
                   right_label: str = None):
        self._used_vertices.add(vertex)

        if protected:
            self._protected_vertices.add(vertex)

        if left_label is not None:
            assert(not vertex.left.isNull())
            assert(vertex.left not in self._relabels)
            self._relabels[vertex.left] = left_label

        if right_label is not None:
            assert(not vertex.right.isNull())
            assert(vertex.right not in self._relabels)
            self._relabels[vertex.right] = right_label

    def add_edge(self, edge: mod.RuleEdge, protected: bool = False):
        self._used_edges[_edge_to_tuple(edge)] = edge

        self.add_vertex(edge.source, protected)
        self.add_vertex(edge.target, protected)

    # def add(self, ve: Union[mod.RuleVertex, mod.RuleEdge]):
    #     if isinstance(ve, mod.RuleVertex):
    #         self.add_vertex(ve)
    #     elif isinstance(ve, mod.RuleEdge):
    #         self.add_edge(ve)
    #     else:
    #         assert(False and "must be RuleVertex or RuleEdge")

    def remove_vertex(self, vertex: mod.RuleVertex):
        if not self.has_vertex(vertex) or vertex in self._protected_vertices:
            return

        self._used_vertices.remove(vertex)
        for e in vertex.incidentEdges:
            self.remove_edge(e)

    def remove_edge(self, edge: mod.RuleEdge):
        if not self.has_edge(edge) or\
                (edge.source in self._protected_vertices and edge.target in self._protected_vertices):
            return

        del self._used_edges[_edge_to_tuple(edge)]

    def remove(self, ve: Union[mod.RuleVertex, mod.RuleEdge]):
        if isinstance(ve, mod.RuleVertex):
            self.remove_vertex(ve)
        elif isinstance(ve, mod.RuleEdge):
            self.remove_edge(ve)
        else:
            assert (False and "must be RuleVertex or RuleEdge")

    def has_vertex(self, vertex: mod.RuleVertex):
        return vertex in self.used_vertices

    def has_edge(self, e: mod.RuleEdge):
        endpoints = tuple(sorted([e.source, e.target]))
        return endpoints in self.used_edges

    def to_mod_rule(self):
        mod.ruleGMLString(self.to_gml(), add=False)

    def to_gml(self, name: str = None, unlabelled_vertices: Optional[Set[mod.RuleLeftGraphVertex]] = None):
        if name is None:
            name = self.rule.name
        left = Container()
        context = Container()
        right = Container()

        for v in self.used_vertices:
            if v.left.isNull():
                right.vertices.append(v.right)
            elif v.right.isNull():
                left.vertices.append(v.right)
            elif v.left.stringLabel != v.right.stringLabel:
                left.vertices.append(v.left)
                right.vertices.append(v.right)
            else:
                context.vertices.append(v.left)

        for e in self.used_edges.values():
            if e.left.isNull():
                right.edges.append(e.right)
            elif e.right.isNull():
                left.edges.append(e.left)
            elif e.left.stringLabel != e.right.stringLabel:
                left.edges.append(e.left)
                right.edges.append(e.right)
            else:
                context.edges.append(e.left)

        out = [f'rule [ ruleID "{name}"']
        rule_sections = (('left', left), ('context', context), ('right', right))
        for name, container in rule_sections:
            out.append(f'{name} [')
            for u in container.vertices:
                label: str = u.stringLabel
                if name == "context" and unlabelled_vertices is not None and u in unlabelled_vertices:
                    label = "*"
                if u in self._relabels:
                    label = self._relabels[u]

                out.append(f'node [ id {u.id} label "{label}" ]')

            for u in container.edges:
                src, tar = u.source, u.target
                out.append(f'edge [ source {src.id} target {tar.id} label "{u.stringLabel}" ]')
            out.append(']')
        out.append(']')
        return '\n'.join(out)


class Container:
    def __init__(self):
        self.vertices = []
        self.edges = []


def _edge_to_tuple(edge: mod.RuleEdge) -> Tuple[mod.RuleVertex, mod.RuleVertex]:
    if edge.target.id < edge.source.id:
        return edge.target, edge.source

    return edge.source, edge.target


def add_reaction_center(rule: FilteredRule, verbosity: int = 0) -> FilteredRule:
    if verbosity:
        print(f"\tAdding reaction center for rule {rule.rule}")

    for vertex in rule.rule.vertices:
        if vertex.left.stringLabel != vertex.right.stringLabel:
            rule.add_vertex(vertex, True)

    for edge in rule.rule.edges:
        if edge.left.isNull() or edge.right.isNull() or edge.left.stringLabel != edge.right.stringLabel:
            rule.add_edge(edge, True)

    for edge in rule.rule.edges:
        if edge.source in rule.used_vertices and edge.target in rule.used_vertices:
            rule.add_edge(edge)

    return rule
