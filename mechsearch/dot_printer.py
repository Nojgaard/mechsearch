import mod
import os
from typing import Optional, Set


class DotNode:
    def __init__(self, id: str, label: Optional[str] = None, shape: str = "circle"):
        self._id: str = id

        self._label: str = label
        if label is None:
            self._label = id

        self._shape: str = shape

    def __eq__(self, other: 'DotNode') -> bool:
        return self.id == other.id

    def __ne__(self, other: 'DotNode') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return f"{self.id} [label=\"{self.label}\" shape={self.shape}];"

    @property
    def id(self) -> str:
        return self._id

    def get_label(self) -> str:
        return self._label

    def set_label(self, label: str):
        self._label = label

    def get_shape(self) -> str:
        return self._shape

    def set_shape(self, shape: str):
        self._shape = shape

    label = property(get_label, set_label)
    shape = property(get_shape, set_shape)


class DotEdge:
    def __init__(self, source: str, target: str, label: Optional[str] = None):
        self._source: str = source
        self._target: str = target

        self._label: Optional[str] = label

    def __eq__(self, other: 'DotEdge') -> bool:
        return self.source == other.source and self.target == other.target

    def __ne__(self, other: 'DotEdge') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return 19 * hash(self.source) + 31 * hash(self.target)

    def __str__(self) -> str:
        return f"{self.source} -> {self.target}{self._label_box};"

    @property
    def source(self) -> str:
        return self._source

    @property
    def target(self) -> str:
        return self._target

    @property
    def _label_box(self) -> str:
        if self._label is None:
            return ""
        else:
            return f" [label=\"{self._label}\"]"


class DotGraph:
    def __init__(self):
        self._nodes: Set[DotNode] = set()
        self._edges: Set[DotEdge] = set()

    def add_node(self, node: DotNode):
        self._nodes.add(node)

    def add_nodes(self, nodes: Set[DotNode]):
        self._nodes |= nodes

    def add_edge(self, edge: DotEdge):
        self._edges.add(edge)

    def add_edges(self, edges: Set[DotEdge]):
        self._edges |= edges

    def print(self, name: str):
        prefix = mod.makeUniqueFilePrefix()
        file_name = prefix + name.replace(' ', '_')

        with open(file_name + ".dot", "w") as file:
            file.write("digraph {\n")

            for node in self._nodes:
                file.write(f"\t{node}\n")
            for edge in self._edges:
                file.write(f"\t{edge}\n")

            file.write("}\n")

        os.system(f"dot -Tpdf {file_name}.dot > {file_name}.pdf")

        with open(f"{file_name}.tex", "w") as f:
            f.write(r"\begin{center}" + "\n")
            f.write(r"\includegraphics[width=\textwidth]{./" + file_name + ".pdf}" + "\n")
            f.write(r"\end{center}" + "\n")
        mod.post(f"summaryInput {file_name}.tex")
