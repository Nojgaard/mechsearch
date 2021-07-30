from mechsearch.grammar import Grammar
import scripts.rhea_analysis.util as util
from data.rhea.db import RheaDB
from mechsearch.state_space import StateSpace, Path
from scripts.announcements import *
import json
import mod
from typing import Iterable
import networkx as nx


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


def seperate_nx_connected_components(graph: nx.Graph):
    if nx.is_connected(graph) is True:
        return [graph]

    sep_graphs = []
    for g in nx.connected_components(graph):
        gml = "graph [\n"
        for g_i in graph.nodes:
            if g_i in g:
                gml += f"\tnode [ id {g_i} label \"{graph.nodes[g_i]['label']}\"]\n"

        for e_i in graph.edges:
            src, trg = e_i
            if (src in g) and (trg in g):
                gml += f"\tedge [ source {src} target {trg} label \"{graph.edges[e_i]['label']}\"]\n"

        gml += "]"
        sep_graphs.append(nx.parse_gml(gml, label="id"))

    return sep_graphs


def subgraph_iso(rule_side: nx.Graph, query_rule: nx.Graph,
                 extra: str = None, verbose: int = 0):
    verbosity = 3
    if extra != "":
        message(extra, verbose=verbose, c="BLUE", verbose_level_threshold=verbosity)
    all_checks = list()
    subg_q_rule: nx.Graph
    message(f"Number of connected components: {nx.number_connected_components(query_rule)}", c="BLUE",
            verbose=verbose, verbose_level_threshold=verbosity)
    for _i, subg_q_rule in enumerate(seperate_nx_connected_components(query_rule)):
        message(f"connected component {_i}", c="BLUE",
                verbose=verbose, verbose_level_threshold=verbosity)
        message(f"Number of nodes: {subg_q_rule.number_of_nodes()}", c="BLUE",
                verbose=verbose, verbose_level_threshold=verbosity)
        for v in subg_q_rule.nodes:
            message(f"{subg_q_rule.nodes[v]}: {subg_q_rule.nodes[v]['label']}", c="BLUE",
                    verbose=verbose, verbose_level_threshold=verbosity)
        message(f"Number of edges: {subg_q_rule.number_of_edges()}", c="BLUE",
                verbose=verbose, verbose_level_threshold=verbosity)
        for e in subg_q_rule.edges:
            message(f"{subg_q_rule.edges[e]}: {subg_q_rule.edges[e]['label']}", c="BLUE",
                    verbose=verbose, verbose_level_threshold=verbosity)
        check = next(
            (
                True for subg_rule in seperate_nx_connected_components(rule_side)
                if nx.algorithms.isomorphism.GraphMatcher(subg_rule, subg_q_rule).subgraph_is_isomorphic() is True
            ), False
        )
        message(f"{check}", c="BLUE", verbose=verbose, verbose_level_threshold=verbosity)
        if check is True:
            all_checks.append(check)
    message(f"{all_checks} {extra}", c="BLUE", verbose_level_threshold=verbosity, verbose=verbose)

    if False in all_checks or len(all_checks) == 0:
        return False

    return True


def subgraph_iso_connected(rule_side: nx.Graph, query_rule: nx.Graph,
                           extra: str = None, verbose: int = 0):
    verbosity = 3
    iso = nx.algorithms.isomorphism.GraphMatcher(rule_side, query_rule).subgraph_is_isomorphic()
    return iso
