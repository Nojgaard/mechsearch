from mechsearch.grammar import Grammar
import scripts.rhea_analysis.util as util
from data.rhea.db import RheaDB
from mechsearch.state_space import StateSpace, Path
from scripts.announcements import *
import json
import mod
from typing import Iterable


def load_state_sapce(rhea_id: str, state_space_path: str, dg_path: str,
                     aa_loc: str = "data/amino_acids.json", verbose: int = 0):
    message("Loading grammar", verbose=verbose, verbose_level_threshold=2)
    grammar_aminos = Grammar()
    grammar_aminos.load_file(aa_loc)
    grammar_rules = grammar_aminos + util.load_rules()
    rhea_db = RheaDB()
    reaction = rhea_db.get_reaction(rhea_id)
    grammar_reaction = util.reaction2grammar(reaction)
    grammar = grammar_rules + grammar_reaction

    message("Loading state space", verbose=verbose, verbose_level_threshold=2)
    with open(state_space_path) as f:
        state_space = StateSpace.from_json(json.load(f), grammar, dg_path)
    message(f"Analyzing StateSpace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})",
            verbose=verbose, verbose_level_threshold=2)
    message(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges})",
            verbose=verbose, verbose_level_threshold=2)
    state_space.freeze()
    return state_space


def mod_labelled_graph_to_gml(vertices: Iterable[mod.Graph.Vertex], edges: Iterable[mod.Graph.Edge]):
    out = "graph[\n"
    for v in vertices:
        out += f"\tnode[ id {v.id} label \"{v.stringLabel}\" ]\n"

    for e in edges:
        out += f"\tedge [ source {e.source.id} target {e.target.id} label \"{e.stringLabel}\" ]\n"

    out += "]"
    return out


def seperate_mod_rule_to_gml(arule: mod.Rule):
    return {
        "left": mod_labelled_graph_to_gml([v for v in arule.left.vertices], [e for e in arule.left.edges]),
        "right": mod_labelled_graph_to_gml([v for v in arule.right.vertices], [e for e in arule.right.edges])
    }
