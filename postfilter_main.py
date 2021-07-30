from os import path
from scripts.postfilter_tools import *
from scripts.announcements import *
import mod
from mod import DGHyperEdge, DGVertex
import sys
import mechsearch.graph as msg
import networkx as nx

if __name__ == '__main__':
    verbose = 3
    rhea_id = "RHEA:10076"
    state_space_dir = f"state_spaces/{rhea_id}"
    state_space_loc = path.join(state_space_dir, "state_space.json")
    dg_loc = path.join(state_space_dir, "dg.dg")
    # rule_loc = "tmp/rule.gml"
    rule_loc = "tmp/rule_6.gml"
    # rule_loc = "tmp/rule_4.gml"

    # Loading data
    message(f"Loading state space for {rhea_id}")
    state_space = load_state_sapce(rhea_id, state_space_loc, dg_loc,
                                   verbose=verbose)
    message("Loading state space graphs",
            verbose=verbose)
    graphs = [v.graph for v in state_space.derivation_graph.vertices]
    message("Loading graphs per node",
            verbose=verbose)
    nodes = {n.id: [g.graph for g in n.state.graph_multiset.graphs] for n in state_space.graph.nodes}
    message("Loading state space edges",
            verbose=verbose)
    edges = [{"src": nodes[e.source.id], "trgt": nodes[e.target.id]} for e in state_space.edges()]

    # Loading query rule
    query_rule: mod.Rule = mod.ruleGML(rule_loc)
    query_rule.name = "Query Rule"
    query_rule.print()

    # Extracting rule reaction center
    rule_rxn_center = msg.FilteredRule(query_rule)
    msg.add_reaction_center(rule_rxn_center)

    # Extracting used rules
    used_rules = []
    for e in state_space.derivation_graph.edges:
        for r in e.rules:
            used_rules.append(r)
    used_rules = set(used_rules)
    message(f"Found {len(used_rules)} used rules in the state space",
            verbose=verbose)

    q_rule_gml = seperate_mod_rule_to_gml(query_rule)
    q_rule_left_nx: nx.Graph = nx.parse_gml(q_rule_gml["left"], label="id")
    q_rule_right_nx: nx.Graph = nx.parse_gml(q_rule_gml["right"], label="id")

    # check subgraph isomorphisms
    keep_these_rules = []
    r_i: mod.Rule
    for i, r_i in enumerate(list(used_rules)):
        if r_i.name not in  ["r_{5195}", "r_{5092}"]:
            continue
        message(f"{r_i.name} | id: {r_i.id}")
        r_i_rxn_center = msg.FilteredRule(r_i)
        msg.add_reaction_center(r_i_rxn_center)
        r_gml = seperate_mod_rule_to_gml(r_i)
        r_left_nx = nx.parse_gml(r_gml["left"], label="id")
        r_right_nx = nx.parse_gml(r_gml["right"], label="id")
        # left_iso = subgraph_iso(r_left_nx, q_rule_left_nx, extra="---\nleft", verbose=verbose)
        # right_iso = subgraph_iso(r_right_nx, q_rule_right_nx, extra="---\nright", verbose=verbose)

        left_iso = subgraph_iso_connected(r_left_nx, q_rule_left_nx)
        right_iso = subgraph_iso(r_right_nx, q_rule_right_nx)

        if left_iso is True and right_iso is True:
            keep_these_rules.append(r_i)

        message(f"Left: {left_iso} | Right: {right_iso}", c="GREEN", verbose=verbose)

        r_i_rxn_center.to_mod_rule().print()

    message(f"Found {len(keep_these_rules)} into which the query can be embedded.", verbose=verbose)
    # # for _ in keep_these_rules:
    # #     _.print()

    # TODO: check for rule embedding

    sys.exit()

    # Create new DG with all graphs from the state space
    dg = mod.DG(graphDatabase=graphs)  # provide all the graphs from the state space
    builder = dg.build()
    # Need to take dynamic dg because the dg builder has been blocked by Jakob
    ddg = mod.makeDynamicDG(builder._builder, [query_rule])
    he: DGHyperEdge
    t: DGVertex
    for e in edges:
        hyper_edges = ddg.apply(e["src"])
        # TODO: check number of graphs\
        for i, he in enumerate(hyper_edges):
            for t in he.targets:
                print(t.graph, e["trgt"])
            # for s in he.targets:
            #     print(s)

    del builder
    # dg.print()
