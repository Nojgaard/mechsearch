from mechsearch.graph import GraphMultiset, Graph
import mod
from typing import Dict, Optional
from numpy import ndarray


class State:
    def __init__(self, graph_multiset: GraphMultiset):
        self._graph_multiset: GraphMultiset = graph_multiset

        self._key: int = hash(self._graph_multiset)

    def __eq__(self, other: 'State') -> bool:
        return self._graph_multiset == other._graph_multiset

    def __ne__(self, other: 'State') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.key)

    def __str__(self) -> str:
        return f"State {str(self._graph_multiset)}"

    def to_json(self):
        return {g.name: i for g, i in self._graph_multiset.counter.items()}

    @staticmethod
    def from_json(jState: Dict[str, int], name2graph: Dict[str, mod.Graph]):
        graphs = {Graph(name2graph[name]): count for name, count in jState.items()}
        return State(GraphMultiset(graphs))

    @property
    def key(self) -> int:
        return self._key

    @property
    def graph_multiset(self) -> GraphMultiset:
        return self._graph_multiset

    def fire(self, dg_edge: mod.DGHyperEdge, inverse: bool = False) -> Optional['State']:
        counter = self._graph_multiset.counter
        sources = dg_edge.sources
        targets = dg_edge.targets
        #sources = GraphMultiset.from_dg_vertices(dg_edge.sources)
        #targets = GraphMultiset.from_dg_vertices(dg_edge.targets)
        if inverse:
            sources, targets = targets, sources
        #new_multiset = self._graph_multiset - sources + targets
        for v in sources:
            counter[Graph(v.graph)] -= 1
        for v in targets:
            counter[Graph(v.graph)] += 1

        return State(GraphMultiset(counter))


class StateWithDistance(State):
    def __init__(self, graph_multiset: GraphMultiset, distance_matrix: ndarray,
                 atom_id_map: Dict[mod.GraphVertex, int]):
        super().__init__(graph_multiset)

        self._distance_matrix: ndarray = distance_matrix
        self._atom_id_map: Dict[mod.GraphVertex, int] = dict(atom_id_map)

    def _compute_maximum_distance(self, rule: mod.Rule, morphism: mod.AtomMapEvaluateVertexMap):
        maximum_distance = 0
        for edge in rule.edges:
            if edge.left.isNull() and not edge.right.isNull():
                source, target = morphism(edge.source)[0], morphism(edge.target)[0]
                if source not in self._atom_id_map or target not in self._atom_id_map:
                    continue
                source_id = self._atom_id_map[source]
                target_id = self._atom_id_map[target]
                maximum_distance = max(maximum_distance, self._distance_matrix[source_id][target_id])

        return maximum_distance

    def fire(self, dg_transition: mod.DGHyperEdge, inverse: bool = False) -> Optional['StateWithDistance']:
        simple_state: State = super().fire(dg_transition, inverse)
        new_state: StateWithDistance = StateWithDistance(simple_state.graph_multiset,
                                                         self._distance_matrix, self._atom_id_map)

        distances = mod.atomMapEvaluate(dg_transition, self._compute_maximum_distance)
        if min(distances) > 3:
            return None

        return new_state
