import mod
from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace, StateSpaceNode
import os
import json
from typing import List, Dict, Any, Set

mechanism_grammar_dir = "../mcsadb/data/grammars"


def get_mechanism_names():
    for grammar_file in os.listdir(mechanism_grammar_dir):
        yield grammar_file.split('.')[0].strip()


def load_rules():
    # rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"
    rules_file_path = "data/rules.json"
    grammar = Grammar()
    grammar.load_file(rules_file_path)
    return grammar


def load_rules_for_mechanism(mechanism_entry: str):
    rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"
    with open(rules_file_path) as f:
        rule_data = json.load(f)
    rule_db = {
        f'{step["entry"]}_{step["proposal"]}': rule["gml"]
        for rule in rule_data["rules"] for step in rule["steps"]
    }
    rules: List[Dict[str, Any]] = []
    for rule in rule_data["rules"]:
        for step in rule["steps"]:
            if mechanism_entry == f'{step["entry"]}_{step["proposal"]}':
                rules.append(rule)
                break
    grammar = Grammar()
    for rule in rules:
        grammar.load_rule(rule)
    return grammar


def load_mechanism(mechanism_entry: str):
    grammar_file = os.path.abspath(f"../mcsadb/data/grammars/{mechanism_entry}.json")
    grammar = Grammar()
    grammar.load_file(grammar_file)
    return grammar


def metal_atomic_symbols() -> List[str]:
    return ["Mg", "Zn", "Fe", "Cu", "Co", "Ca", "Mo", "Mn"]


def contains_metals(grammar: Grammar):
    metals = metal_atomic_symbols()
    for g in grammar.graphs:
        for v in g.graph.vertices:
            if any(v.stringLabel.startswith(m) for m in metals) or g.graph.numVertices > 50:
                return True
    return False


def contains_uranium(grammar: Grammar):
    for g in grammar.graphs:
        for v in g.graph.vertices:
            if v.stringLabel.startswith("U"):
                return True
    return False


def load_state_space(mechanism_entry: str, grammar: Grammar):
    state_space_dir = os.path.join("data", "state_space", mechanism_entry)
    dg_path = os.path.join(state_space_dir, "dg.dg")
    state_space_path = os.path.join(state_space_dir, "state_space.json")
    print("Loading ", mechanism_entry)
    with open(state_space_path) as f:
        state_space = StateSpace.from_json(json.load(f), grammar, dg_path)
    print(f"Analyzing Statespace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})")
    print(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges}")
    state_space.freeze()
    return state_space


def prune_state_space(state_space: StateSpace):
    source = state_space.initial_node
    target = state_space.target_node
    is_reachable: Set[StateSpaceNode] = {target}
    seen: Set[StateSpaceNode] = set()
    on_stack: Set[StateSpaceNode] = {source}
    #is_target_reachable(source, target, state_space, is_reachable, seen)

    graph = state_space.graph
    stack = [(source, [tar for _, tar in graph.edges(source)])]
    while len(stack) > 0:
        v, adj = stack.pop()
        seen.add(v)
        on_stack.remove(v)
        if v == target:
            is_reachable.add(v)
            continue

        if len(adj) == 0:
            continue

        w = adj.pop()

        if w in is_reachable and w not in on_stack:
            is_reachable.add(v)

        if w not in seen:
            on_stack.add(v)
            on_stack.add(w)
            adj.append(w)
            stack.append((v, adj))
            stack.append((w, [tar for _, tar in graph.edges(w)]))
        elif len(adj) > 0:
            on_stack.add(v)
            stack.append((v, adj))

    sub_space = state_space.sub_space(is_reachable)
    print(f"Analyzing Statespace(|V| = {sub_space.number_of_states}, |E| = {len(sub_space.graph.edges)})")
    print(f"\t DG(|V| = {sub_space.derivation_graph.numVertices}, |E| = {sub_space.derivation_graph.numEdges}")

    return sub_space


def graph_contains_metals(graph: mod.Graph) -> bool:
    metals = metal_atomic_symbols()
    v: mod.GraphVertex
    for v in graph.vertices:
        lbl: str = v.stringLabel
        lbl = lbl.replace("-", "").replace("+", "")
        if lbl in metals:
            return True
    return False


def load_amino_db(path: str = "../mcsadb/data/amino_acids_unique.json") -> Dict[str, List[mod.Graph]]:
    with open(path) as f:
        json_amino_db = json.load(f)
    amino_db = {}
    for name, representations in json_amino_db.items():
        amino_db[name] = []
        for i, repr in enumerate(representations):
            graph: mod.Graph = mod.graphDFS(repr["dfs"], f"{name}-{i}")
            if graph_contains_metals(graph):
                continue
            amino_db[name].append(graph)
    return amino_db


def reaction2grammar(reaction):
    grammar = Grammar()
    grammar.append_initial(reaction.reactants)
    grammar.append_target(reaction.products)
    return grammar
