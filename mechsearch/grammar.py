from collections import Counter
import json
import os.path
from mechsearch.atom_spectrum import AtomSpectrum
from mechsearch.graph import Graph, GraphMultiset, Rule, Step
from mechsearch.state import State, StateWithDistance
import mod
import networkx
from numpy import load, ndarray
from typing import Any, Dict, Iterator, List, Optional, Set, Union, Tuple


def _rule_graph_to_networkx(rule_graph: Union[mod.Rule.LeftGraph, mod.Rule.RightGraph]) -> networkx.Graph:
    graph: networkx.Graph = networkx.Graph()
    for vertex in rule_graph.vertices:
        graph.add_node(vertex, label=vertex.stringLabel)

    for edge in rule_graph.edges:
        graph.add_edge(edge.source, edge.target, label=edge.stringLabel)

    return graph


def _networkx_to_gml(graph: networkx.Graph) -> str:
    output_segments: List[str] = ['graph [']
    for node in graph.nodes:
        label = graph.nodes[node]['label']
        output_segments.append(f'node [ id {node.id} label "{label}" ]')

    for (source, target) in graph.edges:
        label = graph.edges[source, target]['label']
        output_segments.append(f'edge [ source {source.id} target {target.id} label "{label}" ]')

    output_segments.append(']')
    return '\n'.join(output_segments)


def _get_rule_graphs(rule_graph: Union[mod.Rule.LeftGraph, mod.Rule.RightGraph]) -> Iterator[str]:
    networkx_rule_graph: networkx.Graph = _rule_graph_to_networkx(rule_graph)
    connected_components: List[networkx.Graph] = [networkx_rule_graph.subgraph(component).copy() for
                                                  component in networkx.connected_components(networkx_rule_graph)]
    for connected_component in connected_components:
        yield _networkx_to_gml(connected_component)


class Grammar:
    def __init__(self, printer: mod.GraphPrinter = mod.GraphPrinter()):
        # mod.config.rule.printCombined = False
        mod.config.stereo.silenceDeductionWarnings = True
        self._printer = printer

        self._label_settings: mod.LabelSettings = mod.LabelSettings(mod.LabelType.String, mod.LabelRelation.Isomorphism)

        self._graphs: List[Graph] = []
        self._rules: List[Rule] = []
        self._filtered_rules: Optional[List[Rule]] = None

        self._initial_multiset: GraphMultiset = GraphMultiset()
        self._target_multiset: GraphMultiset = GraphMultiset()

        self._distance_matrix: Optional[ndarray] = None
        self._atom_id_map: Dict[mod.Graph.Vertex, int] = {}

        self._graph_aliases: Dict[str, str] = {}

    def __add__(self, other: 'Grammar') -> 'Grammar':
        result: Grammar = self.clone()
        list(result._get_graphs_by_isomorphism({graph.graph for graph in other._graphs}, True))
        result._rules.extend(other._rules)
        result._initial_multiset += GraphMultiset({result._get_graph_by_isomorphism(graph.graph, True): count for
                                                   graph, count in other.initial_multiset.counter.items()})
        result._target_multiset += GraphMultiset({result._get_graph_by_isomorphism(graph.graph, True): count for
                                                  graph, count in other.target_multiset.counter.items()})

        return result

    @property
    def alias(self):
        return self._graph_aliases

    @property
    def printer(self) -> mod.GraphPrinter:
        return self._printer

    @property
    def graphs(self) -> List[Graph]:
        return list(self._graphs)

    @property
    def unwrapped_graphs(self) -> Set[mod.Graph]:
        return {graph.graph for graph in self.graphs}

    @property
    def number_of_graphs(self) -> int:
        return len(self._graphs)

    @property
    def rules(self) -> List[Rule]:
        return list(self._rules)

    @property
    def filtered_rules(self) -> List[Rule]:
        if self._filtered_rules is None:
            self._filtered_rules = [rule for rule in self._rules if
                                    self.initial_multiset.atom_spectrum >= rule.atom_spectrum > AtomSpectrum({})]

        return self._filtered_rules

    @property
    def number_of_rules(self) -> int:
        return len(self._rules)

    @property
    def initial_multiset(self) -> GraphMultiset:
        return self._initial_multiset

    @property
    def initial_state(self) -> State:
        if self._distance_matrix is None:
            return State(self.initial_multiset)
        else:
            return StateWithDistance(self.initial_multiset, self._distance_matrix, self._atom_id_map)

    @property
    def target_multiset(self) -> GraphMultiset:
        return self._target_multiset

    @property
    def target_state(self) -> State:
        return State(self.target_multiset)

    @property
    def label_settings(self) -> mod.LabelSettings:
        return self._label_settings

    def get_graph(self, graph_name: str) -> Optional[Graph]:
        name = self._graph_aliases[graph_name] if graph_name in self._graph_aliases else graph_name
        return next((graph for graph in self.graphs if graph.name == name), None)

    def get_rule(self, rule_name: str) -> Optional[Rule]:
        return next((rule for rule in self.rules if rule.name == rule_name), None)

    def _get_graph_by_isomorphism(self, isomorphic_graph: mod.Graph, add: bool = False) -> Optional[Graph]:
        graph: Optional[Graph] = next((g for g in self.graphs if
                                       g.graph.isomorphism(isomorphic_graph, 1,
                                                           mod.LabelSettings(mod.LabelType.String,
                                                                             mod.LabelRelation.Isomorphism))), None)

        if graph is not None and graph.name != isomorphic_graph.name:
            self._graph_aliases[isomorphic_graph.name] = graph.name

        if add and graph is None:
            decorated_graph: Graph = Graph(isomorphic_graph)
            self._graphs.append(decorated_graph)
            return decorated_graph

        return graph

    def _get_graph_by_gml(self, gml_string: str, name: Optional[str] = None, add: bool = False) -> Optional[Graph]:
        new_graph: mod.Graph = mod.graphGMLString(gml_string, name=name, add=False)
        return self._get_graph_by_isomorphism(new_graph, add)

    def _get_graphs_by_isomorphism(self, isomorphic_graphs: Set[mod.Graph], add: bool = False) -> Iterator[Graph]:
        for isomorphic_graph in isomorphic_graphs:
            graph = self._get_graph_by_isomorphism(isomorphic_graph, add)
            if graph is not None:
                yield graph

    def _add_graph(self, graph: Graph) -> Graph:
        isomorphic_graph: Optional[Graph] = self._get_graph_by_isomorphism(graph.graph)
        if isomorphic_graph is not None:
            self._graph_aliases[graph.name] = isomorphic_graph.name
            return isomorphic_graph

        self._graphs.append(graph)
        return graph

    def _add_rule(self, rule: Rule) -> Rule:
        self._rules.append(rule)
        return rule

    def _load_graphs(self, graph_objects: List[Dict[str, Any]], verbosity: int = 0):
        if verbosity > 5:
            print(f"\tFound {len(graph_objects)} graph definitions.")

        for graph_object in graph_objects:
            self.load_graph(graph_object, verbosity)

    def _load_rules(self, rule_objects: List[Dict[str, Any]], verbosity: int = 0):
        if verbosity > 5:
            print(f"\tFound {len(rule_objects)} rule definitions.")

        for rule_object in rule_objects:
            self.load_rule(rule_object, verbosity)

    def _load_multiset(self, multiset_json: Dict[str, int]) -> GraphMultiset:
        return GraphMultiset({self.get_graph(name): count for name, count in multiset_json.items()})

    def _load_rule_functional_groups(self, rule_name: str, functional_group_objects: List[Dict[str, Any]],
                                     verbosity: int = 0) -> Dict[Graph, int]:
        return {self.load_graph(functional_group_object, verbosity):
                len(list(graph_json for graph_json in functional_group_object["graphs"] if
                         graph_json["rule"] == rule_name)) for functional_group_object in functional_group_objects}

    def clone(self) -> 'Grammar':
        clone = Grammar(self.printer)
        clone._graphs = self.graphs
        clone._rules = self.rules
        clone._initial_multiset = GraphMultiset(self.initial_multiset.counter)
        clone._target_multiset = GraphMultiset(self.target_multiset.counter)
        clone._distance_matrix = self._distance_matrix
        clone._atom_id_map = dict(self._atom_id_map)

        return clone

    def load_file(self, filepath: str, verbosity: int = 0):
        with open(filepath, "r") as file:
            json_object = json.load(file)

            if "graphs" in json_object:
                self._load_graphs(json_object["graphs"], verbosity)

            if "rules" in json_object:
                self._load_rules(json_object["rules"], verbosity)

            if "initial_state" in json_object:
                if verbosity > 1:
                    print(f"\tFound initial state specification. Loading...")
                self._initial_multiset += self._load_multiset(json_object["initial_state"])

            if "target_state" in json_object:
                if verbosity > 1:
                    print(f"\tFount target state specification. Loading...")
                self._target_multiset += self._load_multiset(json_object["target_state"])

    def add2multiset(self, mod_graphs: Tuple[mod.Graph, ...]):
        graphs = self._get_graphs_by_isomorphism(mod_graphs, add=True)
        source_counter = self._initial_multiset.counter
        target_counter = self._target_multiset.counter
        for g in graphs:
            source_counter[g] += 1
            target_counter[g] += 1
        self._initial_multiset = GraphMultiset(dict(source_counter))
        self._target_multiset = GraphMultiset(dict(target_counter))

    def append_initial(self, mod_graphs: List[mod.Graph]):
        graphs = self._get_graphs_by_isomorphism(mod_graphs, add=True)
        source_counter = self._initial_multiset.counter
        for g in graphs:
            source_counter[g] += 1
        self._initial_multiset = GraphMultiset(dict(source_counter))

    def append_target(self, mod_graphs: List[mod.Graph]):
        graphs = self._get_graphs_by_isomorphism(mod_graphs, add=True)
        target_counter = self._target_multiset.counter
        for g in graphs:
            target_counter[g] += 1
        self._target_multiset = GraphMultiset(dict(target_counter))

    def append_graphs(self, mod_graphs: List[mod.Graph]):
        list(self._get_graphs_by_isomorphism(set(mod_graphs), add=True))

    def load_files(self, filepaths: List[str], verbosity: int = 0):
        for filepath in filepaths:
            self.load_file(filepath, verbosity)

    def load_graph(self, graph_json: Dict[str, Any], verbosity: int = 0) -> Optional[Graph]:
        name: str = graph_json["name"]
        graph: Optional[mod.Graph] = None
        if "gml" in graph_json:
            graph = mod.graphGMLString(graph_json["gml"], name, add=False)
        elif "smiles" in graph_json:
            graph = mod.smiles(graph_json["smiles"], name, add=False)
        elif "dfs" in graph_json:
            graph = mod.graphDFS(graph_json["dfs"], name, add=False)

        if graph is None:
            if verbosity > 0:
                print(f"\tInvalid graph specification for graph {name}. Found neither `gml`, `smiles` or `dfs`.")
            return None

        functional_groups: Dict[Graph, int] = {}
        if "functional_groups" in graph_json:
            functional_groups = dict(Counter(self.load_graph(functional_group_object, verbosity) for
                                             functional_group_object in graph_json["functional_groups"]))

        if verbosity > 3:
            print(f"\tLoaded a graph {name} with {graph.numVertices} vertices.")
        return self._add_graph(Graph(graph, functional_groups))

    def load_rule(self, rule_json: Dict[str, Any], verbosity: int = 0) -> Optional[Rule]:
        rule: mod.Rule = mod.ruleGMLString(rule_json["gml"], add=False)

        steps: List[Step] = []
        if "steps" in rule_json:
            steps = list(Step.deserialise(step_object) for step_object in rule_json["steps"])

        left_functional_groups: Dict[Graph, int] = {}
        if "left_functional_groups" in rule_json:
            left_functional_groups = self._load_rule_functional_groups(rule.name, rule_json["left_functional_groups"],
                                                                       verbosity)

        right_functional_groups: Dict[Graph, int] = {}
        if "right_functional_groups" in rule_json:
            right_functional_groups = self._load_rule_functional_groups(rule.name, rule_json["right_functional_groups"],
                                                                        verbosity)

        # # functional groups are loaded first, if specified, for graph naming purposes
        # left_graphs: Dict[Graph, int] = dict(Counter(self._get_graph_by_gml(gml, f"{rule.name}-LG{index}", True) for
        #                                              index, gml in enumerate(_get_rule_graphs(rule.left))))
        # right_graphs: Dict[Graph, int] = dict(Counter(self._get_graph_by_gml(gml, f"{rule.name}-RG{index}", True) for
        #                                               index, gml in enumerate(_get_rule_graphs(rule.right))))

        if verbosity > 3:
            print(f"Loaded a new rule {rule.name} with {rule.numVertices} vertices.")
        return self._add_rule(Rule(rule, steps, left_functional_groups, right_functional_groups))

    def load_distance_matrix(self, distance_matrix_json: Dict[str, Any], directory_path: str, verbosity: int = 0):
        self._distance_matrix = load(os.path.abspath(os.path.join(directory_path, distance_matrix_json["matrix"])),
                                     allow_pickle=True)
        if verbosity > 5:
            print(f"Loaded atom distance matrix {self._distance_matrix}.")

        self._atom_id_map = load(os.path.abspath(os.path.join(directory_path, distance_matrix_json["id_map"])),
                                 allow_pickle=True)
        if verbosity > 5:
            print(f"Loaded global atom id map {self._atom_id_map}.")

    def remove_rule(self, rule_name: str) -> Optional[Rule]:
        rule: Optional[Rule] = self.get_rule(rule_name)

        if rule is not None:
            self._rules.remove(rule)

        return rule

    def print_graphs(self, print_limit: int = 0):
        mod.postSection("Named Graphs")
        for index, graph in enumerate(self.graphs):
            if print_limit and print_limit <= index:
                break

            graph.print(self.printer)

    def print_rules(self, print_limit: int = 0):
        mod.postSection("Rules")
        for index, rule in enumerate(self.rules):
            if print_limit and print_limit <= index:
                break

            rule.print(self.printer)

    def print(self, print_limit: int = 0):
        mod.postChapter("Grammar")
        self.print_graphs(print_limit)
        self.print_rules(print_limit)
