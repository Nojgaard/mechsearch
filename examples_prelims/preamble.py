_root_path_folder = "examples_prelims"
#_root_path_folder = "/opt/mechsearch"

import sys 
sys.path.append(_root_path_folder)
from mechsearch.state_space import StateSpace
from mechsearch.grammar import Grammar
from mechsearch import explore
from data.rhea.db import RheaDB
from typing import Dict, List
import json
import mod
import itertools

def _load_amino_map():
    grammar_aminos = Grammar()
    grammar_aminos.load_file(f"{_root_path_folder}/amino_acids.json")
    return {graph.name.lower(): graph.graph for graph in grammar_aminos.graphs}


def _build_base_grammar() -> Grammar:
    rules_file_path = f"{_root_path_folder}/rules.json"
    grammar = Grammar()
    grammar.load_file(rules_file_path)
    grammar.load_file(f"{_root_path_folder}/amino_acids.json")
    return grammar


def build_state_space(rhea_id: str, amino_acids: List[mod.Graph],
                      k: int = 6):
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction(rhea_id)

    grammar = _build_base_grammar()
    grammar.append_initial(reaction.reactants + amino_acids)
    grammar.append_target(reaction.products + amino_acids)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, k)
    state_space.freeze()
    return state_space


def sample_mechanisms(state_space: StateSpace, num_samples: int):
    state_space.freeze()
    path_gen = explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra")
    paths = itertools.islice(path_gen, num_samples)
    return paths


def _run_bfs(graph, source, inverse: bool = False):
    reachable: Set[StateSpaceNode] = set()

    stack = [source]
    while len(stack) > 0:
        v = stack.pop()
        reachable.add(v)

        for w in (s for s, _ in graph.in_edges(v)) if inverse else (t for _, t in graph.edges(v)):
            if w not in reachable:
                stack.append(w)

    return reachable


def build_relevant_state_space(state_space: StateSpace):
    reachable = _run_bfs(state_space.graph, state_space.initial_node)
    basin = _run_bfs(state_space.graph, state_space.target_node, True)

    sub_space = state_space.sub_space(reachable.intersection(basin))
    return sub_space

def amino_acid(name: str):
    return amino_map[name.lower()]


amino_map = _load_amino_map()
