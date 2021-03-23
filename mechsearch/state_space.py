from mechsearch.dg_expander import DGExpander
from mechsearch.grammar import Grammar
from mechsearch.state import State
from mechsearch.dot_printer import DotNode, DotGraph, DotEdge
import mod
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple
import networkx as nx
import itertools
from mechsearch.print import printGraph


def compute_stubborn(edges: List[mod.DGHyperEdge], inverse=False):
    if len(edges) == 0:
        return []

    ke = next(iter(edges))
    marked = {e: False for e in edges}
    marked[ke] = True
    ssets = [ke]
    stack = [ke]
    while stack:
        e = stack.pop()
        sources, targets = e.sources, e.targets
        if inverse:
            sources, targets = targets, sources
        for hv in sources:
            out_edges = hv.inEdges if inverse else hv.outEdges
            for ep in out_edges:
                if ep not in marked or marked[ep]: continue
                marked[ep] = True
                stack.append(ep)
                ssets.append(ep)
        for hv in targets:
            out_edges = hv.inEdges if inverse else hv.outEdges
            for ep in out_edges:
                if ep not in marked or marked[ep]: continue
                marked[ep] = True
                stack.append(ep)
    return ssets


class StateSpaceNode:
    def __init__(self, id: int, state: State):
        self._id = id
        self._state = state

    @staticmethod
    def from_json(jNode, name2graph: Dict[str, mod.Graph]):
        node_id = jNode["id"]
        state = State.from_json(jNode["state"], name2graph)
        return StateSpaceNode(node_id, state)

    def to_json(self):
        return {"id": self.id, "state": self.state.to_json()}

    def __eq__(self, other: 'StateSpaceNode') -> bool:
        return self.id == other.id

    def __ne__(self, other: 'StateSpaceNode') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return f"Node ID: {self.id};\t{self.state}"

    @property
    def id(self) -> int:
        return self._id

    @property
    def state(self) -> State:
        return self._state


class StateSpaceEdge:
    def __init__(self, source: StateSpaceNode, target: StateSpaceNode, transitions: Iterable[mod.DGHyperEdge]):
        self._source: StateSpaceNode = source
        self._target: StateSpaceNode = target
        self._transitions: Set[mod.DGHyperEdge] = set(transitions)

    def __eq__(self, other: 'StateSpaceEdge') -> bool:
        return self.source == other.source and self.target == other.target

    def __ne__(self, other: 'StateSpaceEdge') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash((self.source, self.target))

    def __str__(self):
        return f"{self.source} -> {self.target}"

    def to_json(self):
        return {"src": self.source.id,
                "tar": self.target.id,
                "edges": [e.id for e in self._transitions]}

    @staticmethod
    def from_json(jEdge, id2node: Dict[int, StateSpaceNode],
                  id2hyper: Dict[int, mod.DGHyperEdge]):
        src = id2node[jEdge["src"]]
        tar = id2node[jEdge["tar"]]
        transitions = [id2hyper[hid] for hid in jEdge["edges"]]
        return StateSpaceEdge(src, tar, transitions)

    @property
    def source(self) -> StateSpaceNode:
        return self._source

    @property
    def target(self) -> StateSpaceNode:
        return self._target

    @property
    def transitions(self) -> Set[mod.DGHyperEdge]:
        return set(self._transitions)

    def add_transition(self, transition: mod.DGHyperEdge):
        self._transitions.add(transition)


class Path:
    def __init__(self, edges: Iterable[StateSpaceEdge]):
        self._edges: Tuple[StateSpaceEdge] = tuple(edges)

    def __eq__(self, other: 'Path') -> bool:
        return self._edges == other._edges

    def __ne__(self, other: 'Path') -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash(self._edges)

    def __len__(self) -> int:
        return len(self._edges)

    def __iter__(self) -> Iterator[StateSpaceEdge]:
        return iter(self._edges)

    def __getitem__(self, item: int) -> StateSpaceEdge:
        return self._edges[item]

    def __add__(self, other: 'Path') -> 'Path':
        return Path(list(self._edges) + list(other._edges))

    def __str__(self) -> str:
        return str(self._edges)

    def print_causality_graph(self, printer: mod.DGPrinter = mod.DGPrinter()):
        assert (len(self._edges) > 0)
        edges = [e for e in self._edges if len(e.transitions) > 0]
        dg: mod.DG = list(edges[0].transitions)[0].dg
        print_data = mod.DGPrintData(dg)
        for e in dg.edges:
            print_data.removeDuplicate(e, 0)

        for v in dg.vertices:
            print_data.removeVertexIfDegreeZero(v)

        v_dup_id = 1
        e_dup_id = 0
        state: Dict[mod.Graph, List[int]] = {}
        for graph, count in edges[0].source.state.graph_multiset.counter.items():
            state[graph.graph] = [i + v_dup_id for i in range(count)]
            v_dup_id += len(state[graph.graph])
        event_trace = [list(e.transitions)[0] for e in edges]

        for e in event_trace:
            print_data.makeDuplicate(e, e_dup_id)
            for v in e.sources:
                assert (v.graph in state and len(state[v.graph]) > 0)
                vid = state[v.graph].pop()
                print_data.reconnectSource(e, e_dup_id, v, vid)

            for v in e.targets:
                vid = v_dup_id
                v_dup_id += 1
                if v.graph not in state:
                    state[v.graph] = []
                state[v.graph].append(vid)
                print_data.reconnectTarget(e, e_dup_id, v, vid)
            e_dup_id += 1

        dg.print(printer, data=print_data)

    @property
    def start_state(self) -> Optional[StateSpaceNode]:
        if len(self._edges) == 0:
            return None

        return self._edges[0].source

    @property
    def end_state(self) -> Optional[StateSpaceNode]:
        if len(self._edges) == 0:
            return None

        return self._edges[-1].target

    @staticmethod
    def deserialise(json_list: List[Dict[str, Any]], state_space: 'StateSpace') -> 'Path':
        return Path(StateSpaceEdge.from_json(json_object["edge"], {n.id: n for n in state_space.graph.nodes},
                                             {e.id: e for e in state_space.derivation_graph.edges}) for
                    json_object in sorted((json_object for json_object in json_list),
                                          key=lambda json_object: json_object["index"]))

    def serialise(self) -> List[Dict[str, Any]]:
        return list({"index": index, "edge": edge.to_json()} for index, edge in enumerate(self._edges))

    def prefix(self, prefix_length: int) -> 'Path':
        return Path(list(self._edges)[:prefix_length])

    def print(self, edge_labelling_function: Callable[[StateSpaceEdge], Optional[str]] = lambda transition: None,
              printer: Optional[mod.GraphPrinter] = None):
        graph: DotGraph = DotGraph()
        for edge in self._edges:
            graph.add_node(DotNode(str(edge.source.id), str(edge.source), "oval"))
            graph.add_node(DotNode(str(edge.target.id), str(edge.target), "oval"))
            graph.add_edge(DotEdge(str(edge.source.id), str(edge.target.id),
                                   edge_labelling_function(edge)))

        graph.print("Path")

        if printer is not None:
            for edge in self._edges:
                for transition in edge.transitions:
                    for rule in transition.rules:
                        rule.print(printer)

                    transition.print(printer)


class StateSpace:
    def __init__(self, grammar: Grammar, dg_expander: DGExpander = None):
        # self._dg_expander: DGExpander = DGExpander(grammar)
        if dg_expander is None:
            self._dg_expander: DGExpander = DGExpander(grammar)
        else:
            self._dg_expander = dg_expander

        self._graph = nx.DiGraph()
        self._grammar = grammar
        self._state2node: Dict[State, StateSpaceNode] = {}
        self._expanded_nodes: Set[StateSpaceNode] = set()
        self._inverse_expanded_nodes: Set[StateSpaceNode] = set()
        if grammar.number_of_graphs > 0:
            self._initial_node: StateSpaceNode = self._add_state(grammar.initial_state)
            self._target_node: StateSpaceNode = self._add_state(grammar.target_state)

        self._expansion_limit: Optional[int] = None

    def sub_space(self, use_node: Set[StateSpaceNode],
                  update_dg: bool = False):
        state_space = StateSpace(self._grammar, self._dg_expander)

        nodes = [n for n in self._graph.nodes if n in use_node]
        state_space._graph = self._graph.subgraph(nodes).copy()
        state_space._state2node = {
            state: node for state, node in self._state2node.items() if node in use_node
        }
        state_space._expanded_nodes = {
            n for n in self._expanded_nodes if n in use_node
        }
        state_space._inverse_expanded_nodes = {
            n for n in self._inverse_expanded_nodes if n in use_node
        }

        mod_edges = list(itertools.chain.from_iterable([list(self.get_edge(src, tar).transitions)
                                                        for src, tar in self._graph.edges]))
        if update_dg:
            state_space._dg_expander.update(self._dg_expander.derivation_graph, mod_edges)

        return state_space

    def append_state_space(self, state_space: 'StateSpace'):
        node2node = {n: self._add_state(n.state) for n in state_space._graph.nodes}
        for oldSrc, oldTar in state_space._graph.edges:
            newSrc, newTar = node2node[oldSrc], node2node[oldTar]
            oldEdge = state_space.get_edge(oldSrc, oldTar)
            newEdge = StateSpaceEdge(newSrc, newTar, oldEdge.transitions)
            self._graph.add_edge(newSrc, newTar, edge=newEdge)

        rootEdge = StateSpaceEdge(self._initial_node, node2node[state_space._initial_node], [])
        self._graph.add_edge(self._initial_node, node2node[state_space._initial_node], edge=rootEdge)

        targetRootEdge = StateSpaceEdge(node2node[state_space._target_node],
                                        self._target_node, [])
        self._graph.add_edge(node2node[state_space._target_node],
                             self._target_node, edge=targetRootEdge)

        assert(state_space._dg_expander == self._dg_expander)
        #self._dg_expander.update(state_space.derivation_graph)

    def to_json(self):
        return {
            "nodes": [n.to_json() for n in self._graph.nodes],
            "edges": [self.get_edge(src, tar).to_json() for src, tar in self._graph.edges],
            "expanded": [n.id for n in self._expanded_nodes],
            "inverse_expanded": [n.id for n in self._inverse_expanded_nodes]
        }

    @staticmethod
    def from_json(jStateSpace, grammar: Grammar, dg_path: str):
        dg: mod.DG = mod.DG.load(graphDatabase=grammar.unwrapped_graphs,
                                 file=mod.CWDPath(dg_path),
                                 ruleDatabase=[r.rule for r in grammar.rules])
        state_space = StateSpace(grammar)
        state_space._dg_expander.update(dg)
        name2graph: Dict[str, mod.Graph] = {
            v.graph.name: v.graph for v in dg.vertices
        }
        name2graph.update({g.name: g for g in grammar.unwrapped_graphs})
        name2graph.update({key: grammar.get_graph(val).graph for key, val in grammar.alias.items()})

        for jNode in jStateSpace["nodes"]:
            node = StateSpaceNode.from_json(jNode, name2graph)
            if state_space._graph.has_node(node):
                continue
            state_space._state2node[node.state] = node
            state_space._graph.add_node(node)
            # assert(node.id == len(state_space._graph))
            # state_space._add_state(node.state)

        id2node: Dict[int, StateSpaceNode] = {
            n.id: n for n in state_space._graph.nodes
        }
        id2hyper: Dict[int, mod.DGHyperEdge] = {
            e.id: e for e in dg.edges
        }
        for jEdge in jStateSpace["edges"]:
            edge = StateSpaceEdge.from_json(jEdge, id2node, id2hyper)
            src, tar = edge.source, edge.target
            assert (not state_space._graph.has_edge(src, tar))
            state_space._graph.add_edge(src, tar, edge=edge)

        state_space._expanded_nodes = {
            id2node[node_id] for node_id in jStateSpace["expanded"]
        }

        state_space._inverse_expanded_nodes = {
            id2node[node_id] for node_id in jStateSpace["inverse_expanded"]
        }
        return state_space

    def edges(self):
        for src, tar in self._graph.edges:
            yield self.get_edge(src, tar)

    @property
    def initial_node(self) -> StateSpaceNode:
        return self._initial_node

    @property
    def target_node(self) -> StateSpaceNode:
        return self._target_node

    @property
    def derivation_graph(self) -> mod.DG:
        return self._dg_expander.derivation_graph

    @property
    def num_edges(self) -> int:
        return len(self._graph.edges)

    def num_expanded(self, inverse: bool = False):
        return len(self._expanded_nodes) if not inverse else len(self._inverse_expanded_nodes)

    @property
    def number_of_states(self) -> int:
        return len(self._graph)

    @property
    def number_of_expanded_states(self) -> int:
        return len(self._expanded_nodes)

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    @property
    def expanded_nodes(self) -> Set[StateSpaceNode]:
        return set(self._expanded_nodes)

    @property
    def can_expand(self) -> bool:
        if self._expansion_limit is None:
            return True

        return self._expansion_limit > len(self.expanded_nodes)

    def _add_state(self, state: State) -> StateSpaceNode:
        node = StateSpaceNode(len(self._graph), state)
        self._state2node[state] = node
        self._graph.add_node(node)
        return node

    def _add_edge(self, source: StateSpaceNode, target: StateSpaceNode, transition: mod.DGHyperEdge):
        edge = StateSpaceEdge(source, target, {transition})
        self._graph.add_edge(source, target, edge=edge)
        return edge

    def set_expansion_limit(self, limit: int):
        self._expansion_limit = limit

    def get_edge(self, source: StateSpaceNode, target: StateSpaceNode) -> StateSpaceEdge:
        return self._graph.edges[source, target]["edge"]

    def get_path(self, nodes: List[StateSpaceNode]) -> Path:
        return Path([self.get_edge(node, nodes[index + 1]) for index, node in enumerate(nodes[:-1])])

    def freeze(self):
        self._dg_expander.freeze()

    def is_frozen(self):
        return self._dg_expander.is_frozen()

    def print(self):
        printGraph(self._graph)

    def __str__(self) -> str:
        return f"StateSpace(|V|={self.number_of_states}, |E|={self.num_edges}, " \
               f"DG(|V|={self.derivation_graph.numVertices}, |E|={self.derivation_graph.numEdges}), " \
               f"EXPANDED=({len(self._expanded_nodes), len(self._inverse_expanded_nodes)}))"

    def print_info(self):
        print("Size:")
        print(f"\t{self.number_of_states} states and")
        print(f"\t{self.num_edges} transitions.")
        print("Underlying reaction network size:")
        print(f"\t{self.derivation_graph.numVertices} species and")
        print(f"\t{self.derivation_graph.numEdges} reactions.")
        print("All transitions have been explored for:")
        print(f"\t{len(self._expanded_nodes)} states from the initial state and")
        print(f"\t{len(self._inverse_expanded_nodes)} states from the target state.")

    def expand_node(self, node: StateSpaceNode,
                    inverse: bool = False, verbosity: int = 0) -> Iterable[StateSpaceEdge]:
        expanded_nodes = self._expanded_nodes if not inverse else self._inverse_expanded_nodes
        if node in expanded_nodes or self.is_frozen():
            if verbosity > 10:
                print(f"\t{node} has already been expanded. Returning cached transitions.")
            edges = self._graph.edges if not inverse else self._graph.in_edges
            for (source, target) in edges(node):
                yield self.get_edge(source, target)
            return

        if not self.can_expand:
            return

        if verbosity > 1:
            print(f"\tExpanding {node} for the first time. Computing derivations...")

        # dg_expander = lambda graph_multiset: self._dg_expander.compute_derivations(graph_multiset, inverse, verbosity)
        # transitions = node.state.get_transitions(dg_expander) if not inverse else node.state.get_inverse_transitions(dg_expander)

        # ts = sorted(self._dg_expander.compute_derivations(node.state.graph_multiset, inverse, verbosity),
        # key=lambda t: list(t.rules)[0].name)
        ts = self._dg_expander.compute_derivations(node.state.graph_multiset, inverse, verbosity)
        # ts = compute_stubborn(ts)
        for transition in ts:
            target = node.state.fire(transition, inverse)
            # num_tar_atoms = sum(g.number_of_vertices for g in target.graph_multiset.as_multiset())
            # num_src_atoms = sum(g.number_of_vertices for g in node.state.graph_multiset.as_multiset())
            # print([g.graph.graphDFS for g in node.state.graph_multiset.as_multiset()])
            # print([g.graph.graphDFS for g in transition.sources], "->", [g.graph.graphDFS for g in transition.targets])
            # print(num_src_atoms, num_tar_atoms)
            # assert(num_src_atoms == num_tar_atoms)
            if target is None:
                continue

            if target not in self._state2node:
                if verbosity > 5:
                    print(f"\t\tFound transition to a new state {target}.")
                target_node = self._add_state(target)
            else:
                if verbosity > 10:
                    print(f"\t\tFound transition to state {target}")
                target_node = self._state2node[target]

            src, tar = (node, target_node) if not inverse else (target_node, node)
            if self._graph.has_edge(src, tar):
                edge: StateSpaceEdge = self.get_edge(src, tar)
                edge.add_transition(transition)
                yield edge
            else:
                yield self._add_edge(src, tar, transition)
        expanded_nodes.add(node)

        if verbosity:
            print(f"\tFound {self.number_of_states} states, {len(self._expanded_nodes)} have been expanded...")
