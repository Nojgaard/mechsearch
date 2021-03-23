from collections import Counter
from mechsearch.dg_expander2 import DGExpander2
from mechsearch.graph import Graph, GraphMultiset
from mechsearch.grammar import Grammar
import mod
import numpy
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


class Place:
    def __init__(self, id: int, payload: Any):
        self._id = id
        self._payload = payload

    def __eq__(self, other: 'Place') -> bool:
        return self.id == other.id

    def __ne__(self, other: 'Place') -> bool:
        return not self == other

    def __ge__(self, other: 'Place') -> bool:
        return self.id >= other.id

    def __gt__(self, other: 'Place') -> bool:
        return self.id > other.id

    def __le__(self, other: 'Place') -> bool:
        return self.id <= other.id

    def __lt__(self, other: 'Place') -> bool:
        return self.id < other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return str(self.payload)

    @property
    def id(self) -> int:
        return self._id

    @property
    def payload(self) -> Any:
        return self._payload


class DynamicalTransition:
    def __init__(self, sources: Iterable[Place], targets: Iterable[Place], hyper_edge: mod.DGHyperEdge):
        self._sources: Tuple[Place] = tuple(sorted(sources, key=lambda place: place.id))
        self._targets: Tuple[Place] = tuple(sorted(targets, key=lambda place: place.id))
        self._hyper_edge: mod.DGHyperEdge = hyper_edge

        self._id: int = 17 * hash(self.sources) + 37 * hash(self.targets)

    @property
    def sources(self) -> Tuple[Place]:
        return self._sources

    @property
    def targets(self) -> Tuple[Place]:
        return self._targets


class Marking:
    def __init__(self, tokens: Dict[Place, int]):
        self._tokens: Dict[Place, int] = dict(tokens)

        self._place_multiset: Tuple[Place] = tuple(sorted(Counter(self._tokens).elements(), key=lambda place: place.id))

        self._hash: int = hash(self._place_multiset)

    def __eq__(self, other: 'Marking') -> bool:
        return self._place_multiset == other._place_multiset

    def __ne__(self, other: 'Marking') -> bool:
        return not self == other

    def __ge__(self, other: 'Marking') -> bool:
        result = Counter(self.tokens)
        result.subtract(other.tokens)
        return all(count >= 0 for count in result.values())

    def __gt__(self, other: 'Marking') -> bool:
        return self >= other and not self != other

    def __le__(self, other: 'Marking') -> bool:
        return other >= self

    def __lt__(self, other: 'Marking') -> bool:
        return other > self

    def __hash__(self) -> int:
        return self._hash

    def __add__(self, other: 'Marking') -> 'Marking':
        return Marking(Counter(self.tokens) + Counter(other.tokens))

    def __sub__(self, other: 'Marking') -> 'Marking':
        return Marking(Counter(self.tokens) - Counter(other.tokens))

    def __str__(self) -> str:
        return ", ".join(f"{place}: {count}" for place, count in self.tokens.items())

    @property
    def tokens(self) -> Dict[Place, int]:
        return self._tokens

    @property
    def place_multiset(self) -> Tuple[Place]:
        return self._place_multiset


class Transition:
    def __init__(self, sources: Marking, targets: Marking, payload: Any):
        self._sources: Marking = sources
        self._targets: Marking = targets
        self._payload: Any = payload

    def __eq__(self, other: 'Transition') -> bool:
        return self.sources == other.sources and self.targets == other.targets

    def __ne__(self, other: 'Transition') -> bool:
        return not self == other

    def __ge__(self, other: 'Transition') -> bool:
        return self == other or self > other

    def __gt__(self, other: 'Transition') -> bool:
        return self.sources > other.sources or (self.sources == other.sources and self.targets > self.targets)

    def __le__(self, other: 'Transition') -> bool:
        return other >= self

    def __lt__(self, other: 'Transition') -> bool:
        return other > self

    def __hash__(self) -> int:
        return 17 * hash(self.sources) + 37 * hash(self.targets)

    def __str__(self) -> str:
        return str(self.payload)

    @property
    def sources(self) -> Marking:
        return self._sources

    @property
    def targets(self) -> Marking:
        return self._targets

    @property
    def payload(self) -> Any:
        return self._payload

    @property
    def token_balance(self) -> Dict[Place, int]:
        result = Counter(self.targets.tokens)
        result.subtract(self.sources.tokens)
        return result

    def is_enabled(self, marking: Marking) -> bool:
        return self._sources <= marking

    def fire(self, marking: Marking) -> Optional[Marking]:
        if not self.is_enabled(marking):
            return None

        return marking - self.sources + self.targets


class PetriNet:
    def __init__(self):
        self._markings: Dict[Marking, List[Transition]] = {}

    @property
    def places(self) -> Iterable[Place]:
        return self._get_places()

    @property
    def markings(self) -> Set[Marking]:
        return set(self._markings.keys())

    def _get_places(self) -> Iterable[Place]:
        pass

    def _get_enabled_transitions(self, marking: Marking, verbosity: int = 0) -> Iterable[Transition]:
        pass

    def enabled_transitions(self, marking: Marking, verbosity: int = 0) -> List[Transition]:
        if marking not in self._markings:
            self._markings[marking] = list(self._get_enabled_transitions(marking, verbosity))

        return self._markings[marking]


class StaticPetriNet(PetriNet):
    def __init__(self, places: numpy.ndarray, transitions: List[Transition]):
        super().__init__()

        self._places: numpy.ndarray = numpy.array(places)
        self._transitions: List[Transition] = list(transitions)

    def _get_places(self) -> Iterable[Place]:
        return self._places

    def _get_enabled_transitions(self, marking: Marking, verbosity: int = 0) -> List[Transition]:
        return list(transition for transition in self._transitions if transition.is_enabled(marking))


class DynamicPetriNet(PetriNet):
    def __init__(self, grammar: Grammar):
        super().__init__()

        self._dg_expander: DGExpander2 = DGExpander2(grammar)
        self._places: Dict[mod.Graph, Place] = {vertex.graph: Place(index, vertex.graph) for
                                                index, vertex in enumerate(self._dg_expander.derivation_graph.vertices)}

    def _get_places(self) -> Iterable[Place]:
        return self._places.values()

    def _get_enabled_transitions(self, marking: Marking, verbosity: int = 0) -> Iterable[Transition]:
        for hyper_edge in sorted(self._dg_expander.compute_derivations(
                GraphMultiset.from_graph_iterable(Graph(place.payload) for place in marking.place_multiset),
                False, verbosity), key=lambda t: list(t.rules)[0].name):
            sources = Marking(Counter(self.get_place(source.graph) for source in hyper_edge.sources))
            targets = Marking(Counter(self.get_place(target.graph) for target in hyper_edge.targets))
            yield Transition(sources, targets, hyper_edge)

    def get_place(self, graph: mod.Graph) -> Place:
        if graph not in self._places:
            self._places[graph] = Place(len(self._places), graph)

        return self._places[graph]

    def lock(self):
        self._dg_expander.freeze()
