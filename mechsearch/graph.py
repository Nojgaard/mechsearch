from collections import Counter
from mechsearch.atom_spectrum import AtomSpectrum
from mechsearch.hydrogen_abstraction import abstract_graph, abstract_rule
from mechsearch.rule_canonicalisation import CanonSmilesRule
import mod
from typing import Any, Dict, Iterable, List, Optional, Set


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
