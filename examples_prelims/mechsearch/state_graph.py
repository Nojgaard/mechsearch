


# class StateGraph:
#     def __init__(self, name: str):
#         self._name: str = name
#
#         self._states: Set[AbstractState] = set()
#         self._transitions: Dict[AbstractState, Set[Transition]] = dict()
#
#     def add_state(self, state: AbstractState):
#         self._states.add(state)
#         self._transitions[state] = set()
#
#     def add_states(self, states: Set[AbstractState]):
#         for state in states:
#             self.add_state(state)
#
#     def add_transition(self, transition: Transition):
#         if transition.source not in self._transitions:
#             self._transitions[transition.source] = set()
#
#         self._transitions[transition.source].add(transition)
#
#     def add_transitions(self, transitions: Set[Transition]):
#         for transition in transitions:
#             self.add_transition(transition)
#
#     @property
#     def name(self) -> str:
#         return self._name
#
#     @property
#     def states(self) -> Set[AbstractState]:
#         return set(self._states)
#
#     @property
#     def number_of_states(self) -> int:
#         return len(self._states)
#
#     @property
#     def transitions(self) -> Dict[AbstractState, Set[Transition]]:
#         return dict(self._transitions)
#
#     @property
#     def number_of_transitions(self) -> int:
#         return sum(len(self._transitions[source]) for source in self._transitions)
#
#     def get_transition(self, source: AbstractState, target: AbstractState) -> Optional[Transition]:
#         if source not in self._transitions:
#             return None
#
#         return next((transition for transition in self._transitions[source] if transition.target == target), None)
#
#     def print(self, edge_labelling_function: Callable[[Transition], Optional[str]] = lambda transition: None):
#         graph: DotGraph = DotGraph()
#         for state in self._states:
#             graph.add_node(DotNode(str(state.id), str(state), "oval"))
#             if state in self._transitions:
#                 graph.add_edges(set(DotEdge(str(state.id), str(transition.target.id), edge_labelling_function(transition))
#                                     for transition in self._transitions[state]))
#
#         graph.print(self.name)
