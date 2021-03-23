from collections import Counter
from mechsearch.dot_printer import DotNode, DotEdge, DotGraph
from mechsearch.unfolding.petri_net import Place, Marking, Transition, PetriNet
import mod
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple
from queue import PriorityQueue


class Condition:
    def __init__(self, id: int, place: Place, parent: 'Event' = None):
        self._id: int = id
        self._place: Place = place
        self._parent: Event = parent
        self._poset: Set[Event] = set()
        self._coset: Set['Condition'] = {self}

    def __eq__(self, other: 'Condition') -> bool:
        return self.id == other.id

    def __ne__(self, other: 'Condition') -> bool:
        return self.id != other.id

    def __gt__(self, other: 'Condition') -> bool:
        return self.id > other.id

    def __ge__(self, other: 'Condition') -> bool:
        return self.id >= other.id

    def __lt__(self, other: 'Condition') -> bool:
        return self.id < other.id

    def __le__(self, other: 'Condition') -> bool:
        return self.id <= other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self):
        return f"{self.place} (c {self.id})"

    @property
    def id(self) -> int:
        return self._id

    @property
    def place(self) -> Place:
        return self._place

    @property
    def parent(self) -> 'Event':
        return self._parent

    def get_coset(self) -> Set['Condition']:
        return self._coset

    def set_coset(self, coset: Set['Condition']):
        self._coset = set(coset)

    coset = property(get_coset, set_coset)


class Event:
    def __init__(self, id: int, initial_marking: 'UnfoldingMarking', preset: Iterable[Condition],
                 transition: Transition):
        self._id: int = id
        self._transition: Transition = transition

        self._preset: Tuple[Condition] = tuple(sorted(preset))
        self._poset: Optional[Tuple[Condition]] = None

        self._marking: Optional[UnfoldingMarking] = None

        self._local_configuration: 'Configuration' = Configuration.local_configuration(initial_marking, self)

        self._parents: Set[Event] = {condition.parent for condition in self.preset if condition.parent is not None}
        self._coset: Set[Event] = {self}

        self._cutoff: bool = False
        self._equivalence_class: Set[Event] = {self}

    def __eq__(self, other: 'Event') -> bool:
        return self.transition == other.transition and self.preset == other.preset

    def __ne__(self, other: 'Event') -> bool:
        return not self == other

    def __gt__(self, other: 'Event') -> bool:
        return self.transition > other.transition

    def __ge__(self, other: 'Event') -> bool:
        return self > other or self == other

    def __lt__(self, other: 'Event') -> bool:
        return self.transition < other.transition

    def __le__(self, other: 'Event') -> bool:
        return self < other or self == other

    def __hash__(self) -> int:
        return 13 * hash(self.transition) + 17 * hash(self.preset)

    def __str__(self) -> str:
        return ", ".join(rule.name for rule in self.transition.payload.rules) + f" (e {self.id})"

    @property
    def id(self) -> int:
        return self._id

    @property
    def transition(self) -> Transition:
        return self._transition

    @property
    def preset(self) -> Tuple[Condition]:
        return self._preset

    @property
    def poset(self) -> Tuple[Condition]:
        return self._poset

    @property
    def local_configuration(self) -> 'Configuration':
        return self._local_configuration

    def get_cutoff(self) -> bool:
        return self._cutoff

    def set_cutoff(self, cutoff: bool):
        self._cutoff = cutoff

    cutoff = property(get_cutoff, set_cutoff)

    @property
    def marking(self) -> 'UnfoldingMarking':
        return self._marking

    @property
    def parents(self) -> Set['Event']:
        return self._parents

    @property
    def coset(self) -> Set['Event']:
        return self._coset

    @property
    def equivalence_class(self) -> Set['Event']:
        return self._equivalence_class

    def _get_valid_configurations(self, configuration: 'Configuration', coset: Set['Event']) ->\
            Iterable['Configuration']:
        yield configuration

        for event in coset:
            if event.id == self.id:
                continue

            yield from self._get_valid_configurations(configuration | event.local_configuration,
                                                      coset.intersection(event.coset))

    def append_poset(self, poset: Iterable[Condition]):
        self._poset = tuple(sorted(poset))
        self._marking = self._local_configuration.marking

        parent_coset: Optional[Set[Event]] = None if len(self.parents) > 0 else set()
        for parent in self.parents:
            if parent_coset is None:
                parent_coset = set(parent.coset)
            else:
                parent_coset = parent_coset.intersection(parent.coset)

        self._coset = self.coset.union(parent_coset) - self.parents

        # for child in self.poset:
        #     child.coset = parent_coset.union(self.poset) - set(self.preset)
        #
        #     for concurrent_condition in child.coset:
        #         concurrent_condition.coset.add(child)

        return self.poset

    def add_equivalent_event(self, event: 'Event'):
        self._equivalence_class.add(event)

    def add_equivalent_events(self, events: Set['Event']):
        self._equivalence_class |= events

    def coset_markings(self) -> List['UnfoldingMarking']:
        return list(configuration.marking for configuration in
                    self._get_valid_configurations(self.local_configuration, self.coset))


class UnfoldingMarking:
    def __init__(self, conditions: Iterable[Condition]):
        self._conditions: Tuple[Condition] = tuple(sorted(conditions))

        self._marking = Marking(Counter(condition.place for condition in self._conditions))

    def __len__(self) -> int:
        return len(self._conditions)

    def __iter__(self) -> Iterator[Condition]:
        return iter(self._conditions)

    def __eq__(self, other: 'UnfoldingMarking') -> bool:
        return self._marking == other._marking

    def __ne__(self, other: 'UnfoldingMarking') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self._marking)

    def __and__(self, other: 'UnfoldingMarking') -> 'UnfoldingMarking':
        return UnfoldingMarking(set(self).intersection(set(other)))

    def __or__(self, other: 'UnfoldingMarking') -> 'UnfoldingMarking':
        return UnfoldingMarking(set(self).union(set(other)))

    def __sub__(self, other: 'UnfoldingMarking') -> 'UnfoldingMarking':
        return UnfoldingMarking(set(self) - set(other))

    def __str__(self) -> str:
        return str(self._marking)

    @property
    def marking(self) -> Marking:
        return self._marking

    def contains(self, place: Place) -> bool:
        return place in self._marking.tokens

    def _generate_valid_submarkings(self, places: Tuple[Place], conditions: Dict[Place, List[Condition]]) ->\
            List[List[Condition]]:
        submarkings = []
        if len(places) == 0:
            return [[]]

        remaining_places = places[1:]
        for condition in conditions[places[0]]:
            new_conditions = dict(conditions)
            new_conditions[places[0]].remove(condition)

            submarkings.extend([condition] + submarking for submarking in
                        self._generate_valid_submarkings(remaining_places, new_conditions))

        return submarkings

    def submarkings(self, marking: Marking) -> List[List[Condition]]:
        conditions = {}
        for condition in self._conditions:
            if condition.place not in conditions:
                conditions[condition.place] = []

            conditions[condition.place].append(condition)

        return list(self._generate_valid_submarkings(marking.place_multiset, conditions))


class Configuration:
    def __init__(self, initial_marking: UnfoldingMarking, events: Iterable[Event]):
        self._initial_marking: UnfoldingMarking = initial_marking
        self._events: List[Event] = list(events)

        self._parikh: Optional[Tuple[Event]] = None
        self._foata: Optional[Tuple[Tuple[Event]]] = None

        self._marking: Optional[UnfoldingMarking] = None

        self._depth: Optional[int] = None

    def __eq__(self, other: 'Configuration') -> bool:
        return self._compare(other) == 0

    def __ne__(self, other: 'Configuration') -> bool:
        return self._compare(other) != 0

    def __gt__(self, other: 'Configuration') -> bool:
        return self._compare(other) > 0

    def __ge__(self, other: 'Configuration') -> bool:
        return self > other or self == other

    def __lt__(self, other: 'Configuration') -> bool:
        return self._compare(other) < 0

    def __le__(self, other: 'Configuration') -> bool:
        return self < other or self == other

    def __hash__(self) -> int:
        return hash(self.foata)

    def __and__(self, other: 'Configuration') -> 'Configuration':
        return Configuration(self._initial_marking, set(self._events).intersection(other._events))

    def __or__(self, other: 'Configuration') -> 'Configuration':
        return Configuration(self._initial_marking, set(self._events).union(other._events))

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    @property
    def parikh(self) -> Tuple[Event]:
        if self._parikh is None:
            self._parikh = Configuration._compute_parikh(self._events)

        return self._parikh

    @property
    def foata(self) -> Tuple[Tuple[Event]]:
        if self._foata is None:
            self._foata = Configuration._compute_foata(self._events)

        return self._foata

    @property
    def marking(self) -> UnfoldingMarking:
        if self._marking is None:
            conditions: Set[Condition] = set(self._initial_marking)
            for parikh in self.foata:
                for event in parikh:
                    conditions -= set(event.preset)
                    conditions = conditions.union(event.poset)
            self._marking = UnfoldingMarking(conditions)

        return self._marking

    @property
    def depth(self) -> int:
        if self._depth is None:
            self._depth = 0
            for event in self._events:
                if any(any(condition.parent is not None and condition.parent == event for condition in e.preset) for
                       e in self._events):
                    continue

                for condition in event.preset:
                    if condition.parent is None:
                        continue

                    self._depth = max(self._depth, condition.parent.local_configuration.depth + 1)

        return self._depth

    @staticmethod
    def local_configuration(initial_marking: UnfoldingMarking, event: Event) -> 'Configuration':
        events = {event}
        for condition in event.preset:
            if condition.parent is None:
                continue

            events |= set(condition.parent.local_configuration)

        return Configuration(initial_marking, events)

    @staticmethod
    def _compute_parikh(events: Iterable[Event]) -> Tuple[Event]:
        return tuple(sorted(events))

    @staticmethod
    def _compute_foata(events: Iterable[Event]) -> Tuple[Tuple[Event]]:
        foata = []
        temp_events = set(events)

        foata_level = set()
        for event in events:
            if len(event.local_configuration) == 1:
                foata_level.add(event)
                temp_events.remove(event)

        while len(foata_level):
            foata.append(Configuration._compute_parikh(foata_level))
            foata_level = set()
            for temp_event in temp_events:
                this_level = True
                for predecessor_event in temp_event.local_configuration:
                    if (predecessor_event in temp_events) and (predecessor_event != temp_event):
                        this_level = False
                        break
                if this_level:
                    foata_level.add(temp_event)

            temp_events -= foata_level

        return tuple(foata)

    def _compare_parikh(self, other: 'Configuration') -> int:
        return Configuration._compare_explicit_parikh_vectors(self.parikh, other.parikh)

    @staticmethod
    def _compare_explicit_parikh_vectors(vector1: Tuple['Event'], vector2: Tuple['Event']) -> int:
        for i in range(0, min(len(vector1), len(vector2))):
            if vector1[i].transition < vector2[i].transition:
                return -1
            if vector1[i].transition > vector2[i].transition:
                return 1

        return len(vector1) - len(vector2)

    def _compare_foata(self, other: 'Configuration'):
        for i in range(0, min(len(self.foata), len(other.foata))):
            result = Configuration._compare_explicit_parikh_vectors(self.foata[i], other.foata[i])
            if result:
                return result

        return len(self.foata) - len(other.foata)

    def _compare(self, other: 'Configuration'):
        if len(self) != len(other):
            return len(self) - len(other)

        result = self._compare_parikh(other)
        if result:
            return result

        return self._compare_foata(other)

    def merge(self, other: 'Configuration') -> 'Configuration':
        conditions = set()
        for event in self:
            conditions = conditions.union(event.preset)
            conditions = conditions.union(event.poset)

        condition_id_modifier = max(condition.id for condition in conditions) + 1
        event_id_modifier = max(event.id for event in self) + 1

        exposed_conditions = list(self.marking)

        new_events = {}
        for parikh in other.foata:
            for event in parikh:
                preset = set()
                for condition in event.preset:
                    if condition.parent is not None and condition.parent.id in new_events:
                        matching_condition = next(c for c in new_events[condition.parent.id].poset if
                                                  c.id == condition.id + condition_id_modifier)
                    else:
                        matching_condition = next((c for c in exposed_conditions if condition.place == c.place), None)

                    if matching_condition is None:
                        preset.add(Condition(condition.id + condition_id_modifier, condition.place))
                    else:
                        preset.add(matching_condition)
                        exposed_conditions.remove(matching_condition)

                new_event = Event(event.id + event_id_modifier, self._initial_marking, preset, event.transition)
                new_events[event.id] = new_event
                exposed_conditions.extend(new_event.append_poset({Condition(c.id + condition_id_modifier, c.place,
                                                                            new_event) for c in event.poset}))

        return Configuration(self._initial_marking, set(self._events).union(new_events.values()))

    def print(self, printer: mod.DGPrinter):
        if len(self) == 0:
            return

        derivation_graph: mod.DG = next(event for event in self._events).transition.payload.dg
        print_data: mod.DGPrintData = mod.DGPrintData(derivation_graph)

        for hyper_edge in list(derivation_graph.edges):
            print_data.removeDuplicate(hyper_edge, 0)

        for vertex in derivation_graph.vertices:
            print_data.removeVertexIfDegreeZero(vertex)

        for parikh in self.foata:
            for event in parikh:
                print_data.makeDuplicate(event.transition.payload, event.id)
                for condition in event.preset:
                    if condition.parent is None:
                        continue

                    vertex = next(source for source in event.transition.payload.sources if
                                  source.graph == condition.place.payload)
                    print_data.reconnectSource(event.transition.payload, event.id, vertex, condition.id)

                for condition in event.poset:
                    vertex = next((target for target in event.transition.payload.targets if
                                  target.graph == condition.place.payload), None)
                    print_data.reconnectTarget(event.transition.payload, event.id, vertex, condition.id)

        derivation_graph.print(printer, print_data)


class PossibleExtensionQueue:
    def __init__(self):
        self._priority_queue = PriorityQueue()
        self._event_cache: Set[Event] = set()

    def __len__(self) -> int:
        return self._priority_queue.qsize()

    def pop(self) -> Optional[Event]:
        if self._priority_queue.empty():
            return None

        local_configuration, event = self._priority_queue.get()
        return event

    def push(self, event: Event):
        self._priority_queue.put((event.local_configuration, event))

    # @staticmethod
    # def _get_coset_subsets(all_conditions: List[Condition], subset: List[Condition], count: int) ->\
    #         Iterator[List[Condition]]:
    #     if len(subset) >= count:
    #         yield subset
    #         return
    #
    #     for index, condition in enumerate(all_conditions):
    #         if all(condition in c.coset for c in subset):
    #             yield from PossibleExtensionQueue._get_coset_subsets(all_conditions[(index + 1):],
    #                                                                  subset + [condition], count)
    #
    # @staticmethod
    # def _expand_possible_preset(places: Dict[Place, int], possible_preset: Set[Condition],
    #                             place_cosets: Dict[Place, Set[Condition]]):
    #     place = next((place for place in places), None)
    #     if place is None:
    #         yield possible_preset
    #         return
    #
    #     if place not in place_cosets:
    #         return
    #
    #     new_places = dict(places)
    #     del new_places[place]
    #
    #     conditions = sorted(place_cosets[place], key=lambda c: c.id)
    #     for condition_set in PossibleExtensionQueue._get_coset_subsets(conditions, [], places[place]):
    #         new_place_cosets = {}
    #         for place, coset in place_cosets.items():
    #             new_coset = set(coset)
    #             for cc in condition_set:
    #                 new_coset &= cc.coset
    #
    #             if len(new_coset) > 0:
    #                 new_place_cosets[place] = new_coset
    #
    #         yield from PossibleExtensionQueue._expand_possible_preset(new_places, possible_preset.union(condition_set),
    #                                                                   new_place_cosets)
    #
    # def _compute_possible_extensions_for_transition(self, initial_marking: UnfoldingMarking, transition: Transition,
    #                                                 place_cosets: Dict[Place, Set[Condition]]):
    #     for possible_preset in PossibleExtensionQueue._expand_possible_preset(transition.sources.tokens,
    #                                                                           set(), place_cosets):
    #         event: Event = Event(len(self._event_cache), initial_marking, possible_preset, transition)
    #
    #         if event not in self._event_cache:
    #             self._event_cache.add(event)
    #             self.push(event)
    #
    # def compute_possible_extensions(self, initial_marking: UnfoldingMarking, condition: Condition, petri_net: PetriNet,
    #                                 verbosity: int = 0):
    #     coset_places: Dict[Place, int] = dict()
    #     place_cosets: Dict[Place, Set[Condition]] = dict()
    #     for concurrent_condition in condition.coset:
    #         if concurrent_condition.place not in place_cosets:
    #             place_cosets[concurrent_condition.place] = set()
    #         place_cosets[concurrent_condition.place].add(concurrent_condition)
    #         if concurrent_condition.place not in coset_places:
    #             coset_places[concurrent_condition.place] = 0
    #         coset_places[concurrent_condition.place] += 1
    #
    #     for transition in (transition for transition in
    #                        petri_net.enabled_transitions(Marking(coset_places), verbosity) if
    #                        condition.place in transition.sources.tokens):
    #         self._compute_possible_extensions_for_transition(initial_marking, transition, place_cosets)

    def _compute_posible_presets(self, initial_marking: UnfoldingMarking, marking: UnfoldingMarking,
                                 transition: Transition):
        for submarking in marking.submarkings(transition.sources):
            event: Event = Event(len(self._event_cache), initial_marking, submarking, transition)

            if event not in self._event_cache:
                self._event_cache.add(event)
                self.push(event)

    def compute_possible_extensions(self, petri_net: PetriNet, initial_marking: UnfoldingMarking,
                                    event: Optional[Event], verbosity: int = 0):
        for marking in event.coset_markings() if event is not None else [initial_marking]:
            for transition in petri_net.enabled_transitions(marking.marking, verbosity):
                self._compute_posible_presets(initial_marking, marking, transition)


class Step:
    def __init__(self, event: Event, target: UnfoldingMarking):
        self._event: Event = event

        self._source = (target | UnfoldingMarking(event.preset))
        self._source -= UnfoldingMarking(event.poset)

        self._target = target

    @property
    def event(self):
        return self._event

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    def is_valid(self):
        return self.source is not None and all(set(self.source).issubset(condition.coset) for condition in self.source)


class Trace:
    def __init__(self, marking: UnfoldingMarking):
        self._marking: UnfoldingMarking = marking
        self._steps: List[Step] = []
        self._visited_markings = {marking}

    def __eq__(self, other: 'Trace'):
        return self._serialise() == other._serialise()

    def __ne__(self, other: 'Trace'):
        return not self == other

    def __hash__(self) -> int:
        return hash(self._serialise())

    def __iter__(self) -> Iterator[Step]:
        return iter(self._steps)

    def __len__(self) -> int:
        return len(self._steps)

    def _serialise(self):
        return tuple(sorted({step.event for step in self._steps}))

    @property
    def steps(self):
        return self._steps

    def get_extensions(self):
        events = set()
        for condition in self._marking:
            if condition.parent is None:
                continue

            for event in condition.parent.equivalence_class:
                if event is None:
                    continue
                events |= event.equivalence_class

        for event in events:
            if event is None:
                continue

            extension = Step(event, self._marking)
            if extension.source in self._visited_markings or not extension.is_valid():
                continue

            yield extension

        return

    def expand(self, step: Step):
        expansion = Trace(step.source)
        expansion._steps = [step] + self._steps
        expansion._visited_markings |= self._visited_markings

        return expansion

    def print(self):
        graph = DotGraph()
        for step in self._steps:
            graph.add_node(DotNode(f"e{step.event.id}", str(step.event), "box"))
            graph.add_nodes({DotNode(f"c{condition.id}", str(condition), "oval") for condition in
                             set(step.source).union(set(step.target))})
            graph.add_edges({DotEdge(f"c{condition.id}", f"e{step.event.id}") for condition in step.source})
            graph.add_edges({DotEdge(f"e{step.event.id}", f"c{condition.id}") for condition in step.target})

        graph.print("Trace")


class Unfolding:
    def __init__(self, petri_net: PetriNet, initial_marking: Dict[Place, int]):
        self._petri_net: PetriNet = petri_net

        self._conditions: Set[Condition] = set()
        for place, count in initial_marking.items():
            for i in range(0, count):
                self._conditions.add(Condition(len(self._conditions), place))

        for condition in self._conditions:
            condition.coset |= set(self._conditions)

        self._events: List[Event] = []
        self._initial_marking: UnfoldingMarking = UnfoldingMarking(self._conditions)
        self._visited_markings: Dict[UnfoldingMarking, Set[Optional[Event]]] = {self._initial_marking: {None}}

        self._possible_extension_queue = PossibleExtensionQueue()

        self._possible_extension_queue.compute_possible_extensions(self._petri_net, self.initial_marking, None)
        # for condition in self._conditions:
        #     self._possible_extension_queue.compute_possible_extensions(self.initial_marking, condition, self._petri_net)

        self._maximum_depth: Optional[int] = None

    @property
    def initial_marking(self) -> UnfoldingMarking:
        return self._initial_marking

    @property
    def events(self) -> List[Event]:
        return self._events

    def _get_maximum_depth(self) -> Optional[int]:
        return self._maximum_depth

    def _set_maximum_depth(self, depth: int):
        self._maximum_depth = depth

    maximum_depth = property(_get_maximum_depth, _set_maximum_depth)

    def _is_maximum_depth(self, event: Event) -> bool:
        if self.maximum_depth is None:
            return False

        return event.local_configuration.depth >= self.maximum_depth

    def _add_condition(self, condition: Condition):
        self._conditions.add(condition)

    def _add_event(self, event: Event, goal: Optional[Place] = None, verbosity: int = 0):
        self._events.append(event)

        poset = set()
        for place in event.transition.targets.place_multiset:
            condition = Condition(len(self._conditions), place, event)
            self._add_condition(condition)
            poset.add(condition)

        event.append_poset(poset)

        if event.marking in self._visited_markings:
            event.cutoff = True
            event.add_equivalent_events(self._visited_markings[event.marking])
            for e in self._visited_markings[event.marking]:
                if e is not None:
                    e.add_equivalent_event(event)
            self._visited_markings[event.marking].add(event)
        else:
            self._visited_markings[event.marking] = {event}

        if verbosity:
            print(f"Adding {event}")
            print(f"Event count: {len(self._visited_markings)}/{len(self._events)}")
            # print(f"Derivation graph size: {self._dg_expander.dg.numVertices}")
            print(f"Queue size: {len(self._possible_extension_queue)}")
            if not event.cutoff:
                print(f"Visited new marking: {event.marking}")

        if event.cutoff or self._is_maximum_depth(event) or (goal is not None and event.marking.contains(goal)):
            return

        self._possible_extension_queue.compute_possible_extensions(self._petri_net, self.initial_marking, event,
                                                                   verbosity)
        # for condition in event.poset:
        #     self._possible_extension_queue.compute_possible_extensions(self.initial_marking, condition, self._petri_net,
        #                                                                verbosity)

    def _get_possible_extension(self) -> Event:
        return self._possible_extension_queue.pop()

    def non_cut_off_count(self) -> int:
        return sum(1 for event in self._events if not event.cutoff)

    def unfold_one(self, goal: Optional[Place] = None, verbosity: int = 0) -> Event:
        event = self._get_possible_extension()

        if event is not None:
            self._add_event(event, goal, verbosity)

        return event

    def unfold_all(self, verbosity: int):
        while self.unfold_one(verbosity=verbosity) is not None:
            pass

    def unfold_to_goal(self, goal: Place, verbosity: int = 0) -> Iterable[Configuration]:
        if any(condition.place == goal for condition in self.initial_marking):
            yield Configuration(self.initial_marking, set())
            return

        event = self.unfold_one(goal, verbosity)
        while event is not None:
            if any(condition.place == goal for condition in event.marking):
                yield event.local_configuration

            event = self.unfold_one(goal, verbosity)

    def get_target_markings(self, target_marking: Dict[Place, int], verbosity: int) -> List[Configuration]:
        self.unfold_all(verbosity)

        for event in self.events:
            if all(condition.place not in target_marking for condition in event.poset):
                continue

            coset: Optional[Set[Condition]] = None
            for condition in event.poset:
                if coset is None:
                    coset = set(condition.coset)
                else:
                    coset &= condition.coset

            visited_events: Set[Event] = set(event.local_configuration)
            configurations: List[Configuration] = [event.local_configuration]
            for condition in coset:
                if condition.place not in target_marking or condition.parent is None or\
                        condition.parent in visited_events:
                    continue

                for configuration in list(configurations):
                    configurations.append(configuration | condition.parent.local_configuration)
                configurations.append(condition.parent.local_configuration)

            for configuration in configurations:
                if tuple(sorted((condition.place for condition in configuration.marking), key=lambda place: place.id)) ==\
                        tuple(sorted(Counter(target_marking).elements(), key=lambda place: place.id)):
                    if verbosity:
                        print(f"Found target state {configuration.marking}")
                    yield configuration

        return

    def get_target_traces(self, target_marking: Dict[Place, int], verbosity: int) -> Set[Trace]:
        traces = set()
        for configuration in self.get_target_markings(target_marking, verbosity):
            local_traces = {Trace(configuration.marking)}
            significant_step = True
            while significant_step:
                significant_step = False
                for trace in set(local_traces):
                    new_traces = set()
                    for step in trace.get_extensions():
                        new_traces.add(trace.expand(step))

                    if len(new_traces) > 0:
                        significant_step = True
                        local_traces.remove(trace)
                        local_traces |= new_traces

                local_traces -= traces

            traces |= local_traces
            if verbosity:
                print(f"Found {len(traces)} traces and searching...")

        return traces
