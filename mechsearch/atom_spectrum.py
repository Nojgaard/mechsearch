import mod
import re
from typing import Dict, Iterable, List, Union


amino_pattern: re.Pattern = re.compile(
    r"[\s]*Amino[\s]*\([\s]*([a-zA-Z]+)[\+\-]*[\s]*,[\s]*([a-zA-Z]+)[\s]*,[^)]+\)[\s]*")
alias_pattern: re.Pattern = re.compile(r"[\s]*Alias[\s]*\([\s]*([a-zA-Z]+)[\+\-]*[\s]*,[^)]+\)[\s]*")
wildcard_pattern: re.Pattern = re.compile(r"[\s]*\*[\s]*")
atom_label_pattern: re.Pattern = re.compile(r"[\s]*([a-zA-Z]+)[0-9+\-]*[\s]*")


class AtomSpectrum:
    def __init__(self, vertices: Iterable[Union[mod.Graph.Vertex, mod.Rule.LeftGraph.Vertex]]):
        self._element_count: Dict[str, int] = dict()
        self._wildcard_atom_count: int = 0

        for vertex in vertices:
            self._add_vertex(vertex)

    def __eq__(self, other: 'AtomSpectrum') -> bool:
        return self.__le__(other) and self.__ge__(other)

    def __ge__(self, other: 'AtomSpectrum') -> bool:
        return self._compute_wildcard_balance(other)

    def __le__(self, other: 'AtomSpectrum') -> bool:
        return other >= self

    def __gt__(self, other: 'AtomSpectrum') -> bool:
        return not self.__le__(other)

    def __lt__(self, other: 'AtomSpectrum') -> bool:
        return not self.__ge__(other)

    def __add__(self, other: 'AtomSpectrum') -> 'AtomSpectrum':
        result = AtomSpectrum(dict())

        for element, count in self._element_count.items():
            result._add_atom(element, other.element_mass(element))

        for element, count in other._element_count.items():
            result._add_atom(element, other.element_mass(element))

        result._wildcard_atom_count = self._wildcard_atom_count + other._wildcard_atom_count

        return result

    def __str__(self) -> str:
        return f"{self._wildcard_atom_count} wildcards and {self._element_count}"

    def _compute_wildcard_balance(self, other: 'AtomSpectrum') -> bool:
        uncovered_wildcards = other._wildcard_atom_count
        free_wildcards = self._wildcard_atom_count
        for element, count in other._element_count.items():
            if element in self._element_count:
                free_wildcards -= max(0, count - self._element_count[element])
                uncovered_wildcards -= max(0, self._element_count[element] - count)
            else:
                free_wildcards -= count

        return uncovered_wildcards <= 0 <= free_wildcards

    def _add_atom(self, element: str, count: int = 1):
        if element not in self._element_count:
            self._element_count[element] = 0

        self._element_count[element] += count

    def _add_vertex(self, vertex: Union[mod.Graph.Vertex, mod.Rule.LeftGraph.Vertex]):
        amino_match = amino_pattern.match(vertex.stringLabel)
        if amino_match is not None:
            self._add_atom(f"{amino_match.group(2)}_{amino_match.group(1)}")
            return

        alias_match = alias_pattern.match(vertex.stringLabel)
        if alias_match is not None:
            self._add_atom(f"ALIAS_{alias_match.lastgroup}")

        wildcard_match = wildcard_pattern.match(vertex.stringLabel)
        if wildcard_match is not None:
            self._wildcard_atom_count += 1

        atom_label_match = atom_label_pattern.match(vertex.stringLabel)
        if atom_label_match is not None:
            self._add_atom(atom_label_match.lastgroup)

    @staticmethod
    def from_graph(graph: mod.Graph) -> 'AtomSpectrum':
        return AtomSpectrum(graph.vertices)

    @staticmethod
    def from_graphs(graphs: Iterable[mod.Graph]) -> 'AtomSpectrum':
        vertices: List[mod.GraphVertex] = []
        for graph in graphs:
            vertices.extend(graph.vertices)

        return AtomSpectrum(vertices)

    @staticmethod
    def from_rule(rule: mod.Rule) -> 'AtomSpectrum':
        return AtomSpectrum(rule.left.vertices)

    def element_mass(self, element: str):
        if element not in self._element_count:
            return 0

        return self._element_count[element]
