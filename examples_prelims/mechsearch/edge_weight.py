from mechsearch.state_space import StateSpaceEdge
from typing import Dict, Tuple


class EdgeWeight:
    def __init__(self):
        self._cache: Dict[Tuple[float, StateSpaceEdge], float] = dict()

    def __call__(self, source_weight: float, edge: StateSpaceEdge) -> float:
        if (source_weight, edge) not in self._cache:
            self._cache[(source_weight, edge)] = self.compute_weight(source_weight, edge)

        return self._cache[(source_weight, edge)]

    def compute_weight(self, source_weight: float, edge: StateSpaceEdge) -> float:
        pass


class ConstantEdgeWeight(EdgeWeight):
    def __init__(self):
        super().__init__()

    def compute_weight(self, source_weight: float, edge: StateSpaceEdge) -> float:
        return source_weight + 1
