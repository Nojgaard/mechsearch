from mechsearch.edge_weight import EdgeWeight
from mechsearch.state import State
from mechsearch.state_space import StateSpaceEdge
import mod
from typing import Dict


class CargoEnergyHeuristic(EdgeWeight):
    def __init__(self, model):
        super().__init__()

        self._model = model
        self._energy_cache: Dict[mod.Graph, float] = dict()

    def _estimate_energy(self, graph: mod.Graph) -> float:
        if graph not in self._cache:
            self._cache[graph] = self._model.predict(graph)

        return self._cache[graph]

    def compute_energy(self, state: State) -> float:
        return sum(self._estimate_energy(graph) * count for graph, count in state.graph_multiset.counter.items())


class EnergyBarrier(CargoEnergyHeuristic):
    def __init__(self, model):
        super().__init__(model)

    def compute_weight(self, source_weight: float, edge: StateSpaceEdge) -> float:
        return max(source_weight, self.compute_energy(edge.target.state))


class EnergyDifference(CargoEnergyHeuristic):
    def __init__(self, model):
        super().__init__(model)

    def compute_weight(self, source_weight: float, edge: StateSpaceEdge) -> float:
        energy_difference = self.compute_energy(edge.target.state) - self.compute_energy(edge.source.state)

        return source_weight + energy_difference
