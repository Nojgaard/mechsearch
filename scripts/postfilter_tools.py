import re
from mechsearch.grammar import Grammar
import scripts.rhea_analysis.util as util
from data.rhea.db import RheaDB
from mechsearch.state_space import StateSpace
import mechsearch.graph as msg
from scripts.announcements import *
import json
import mod
from typing import Iterable
import networkx as nx


def check_rheaid_format(the_id: str):
    if re.match(r"(RHEA)(:)(\d\d\d\d\d)", the_id) is not None:
        return the_id
    elif re.match(r"\d\d\d\d\d", the_id) is not None:
        return f"RHEA:{the_id}"
    else:
        return None


def load_state_sapce(rhea_id: str, state_space_path: str, dg_path: str,
                     aa_loc: str = "data/amino_acids.json", verbose: int = 0) -> StateSpace:
    """
    Load a state space.
    """
    message(f"Loading state space for {rhea_id}")
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
        state_space = StateSpace.from_json(json.load(f), grammar, dg_path)  # TODO: Remove verbose output
    message(f"Analyzing StateSpace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})",
            verbose=verbose, verbose_level_threshold=2)
    message(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges})",
            verbose=verbose, verbose_level_threshold=2)
    state_space.freeze()
    return state_space


def is_embeddable(a_rule: mod.Rule, query_rule: nx.Graph, verbose: int = 0) -> bool:
    """
    A function to check whether a query rule is embeddable into a given rule.
    :param a_rule: A MOD rule
    :param query_rule: reaction center of the query rule. Left and right side need to be merged
    :param verbose: Verbose output
    """
    verbosity_level = 3
    message(f"{a_rule.name} | id: {a_rule.id}", verbose=verbose, verbose_level_threshold=verbosity_level)
    r_i_rxn_center = msg.FilteredRule(a_rule)
    msg.add_reaction_center(r_i_rxn_center)

    merged_rxn_center_r_i = merge_rule_left_right(r_i_rxn_center.to_mod_rule())
    return subgraph_iso(merged_rxn_center_r_i, query_rule)


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


def mod_rule_left_right_iso(arule: mod.Rule) -> bool:
    sep = seperate_mod_rule_to_gml(arule)
    left = nx.parse_gml(sep["left"], label="id")
    right = nx.parse_gml(sep["right"], label="id")
    matcher = nx.algorithms.isomorphism.GraphMatcher(left, right,
                                                     lambda node1, node2: node1["label"] == node2["label"],
                                                     lambda edge1, edge2: edge1["label"] == edge2["label"]
                                                     )
    return matcher.is_isomorphic()


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


def nx_to_gml(agraph: nx.Graph) -> str:
    gml = "graph [\n"
    for _n in agraph.nodes:
        gml += f"\tnode [ id {_n} label \"{agraph.nodes[_n]['label']}\"]\n"
    for _e in agraph.edges:
        src, trg = _e
        gml += f"\tedge [ source {src} target {trg} label \"{agraph.edges[_e]['label']}\"]\n"
    gml += "]"
    return gml


def subgraph_iso(rule_side: nx.Graph, query_rule: nx.Graph,
                 verbose: int = 0):
    verbosity = 3
    matcher = nx.algorithms.isomorphism.GraphMatcher(query_rule, rule_side,
                                                     lambda node1, node2: node1["label"] == node2["label"],
                                                     lambda edge1, edge2: edge1["label"] == edge2["label"]
                                                     )
    iso = matcher.subgraph_is_isomorphic()
    message(bool_color(iso), verbose=verbose, verbose_level_threshold=verbosity)
    return iso


def merge_rule_left_right(a_rule: mod.Rule) -> nx.Graph:
    """
    Merges left and right side of a mod rule and creates a NetworkX graph.
    :param a_rule: A MOD rule.
    """
    _v: mod.Graph.Vertex
    _e: mod.Graph.Edge

    # create a gml
    seperator = ";"
    gml = "graph [\n"

    # Loop through vertices
    for _v in a_rule.vertices:
        lbl = f"({_v.left.stringLabel}{seperator}{_v.right.stringLabel})"
        gml += f"\tnode [ id {_v.id} label \"{lbl}\" ]\n"

    # Loop through edges
    for _e in a_rule.edges:
        lbl_lr = {"left": None, "right": None}
        for _side in ["left", "right"]:
            try:
                lbl_lr[_side] = getattr(_e, _side).stringLabel
            except mod.libpymod.LogicError:
                lbl_lr[_side] = ""

        lbl = f"({lbl_lr['left']}{seperator}{lbl_lr['right']})"
        gml += f"\tedge [ source {_e.source.id} target {_e.target.id} label \"{lbl}\" ]\n"
    gml += "]"
    return nx.parse_gml(gml, label="id")
