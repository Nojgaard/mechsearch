from os import path
from scripts.postfilter_tools import *
from scripts.announcements import *
import mod
from mod import DGHyperEdge, DGVertex
import sys
import mechsearch.graph as msg
from mechsearch.state_space import StateSpaceEdge

if __name__ == '__main__':
    verbose = 2
    mod_print = False
    rhea_id = "RHEA:10076"
    state_space_dir = f"state_spaces/{rhea_id}"
    state_space_loc = path.join(state_space_dir, "state_space.json")
    dg_loc = path.join(state_space_dir, "dg.dg")
    # rule_loc = "tmp/rule.gml"
    # rule_loc = "tmp/rule_6.gml"
    rule_loc = "tmp/rule_7.gml"
    # rule_loc = "tmp/rule_8.gml"
    # rule_loc = "tmp/rule_4.gml"

    # Loading data
    message(f"Loading state space for {rhea_id}")
    state_space = load_state_sapce(rhea_id, state_space_loc, dg_loc,
                                   verbose=verbose)
    # message("Loading state space graphs",
    #         verbose=verbose)
    # graphs = state_space.vertice_graphs_derivation_graph()
    # message("Loading graphs per node",
    #         verbose=verbose)
    # nodes = {n.id: [g.graph for g in n.state.graph_multiset.graphs] for n in state_space.graph.nodes}
    # message("Loading state space edges",
    #         verbose=verbose)
    # edges = [{"src": nodes[e.source.id], "trgt": nodes[e.target.id]} for e in state_space.edges()]

    # Loading query rule
    query_rule: mod.Rule = mod.ruleGML(rule_loc)
    if mod_print:
        query_rule.print()

    # Extracting rule reaction center
    rule_rxn_center = msg.FilteredRule(query_rule)
    msg.add_reaction_center(rule_rxn_center)

    # Extracting used rules from the state space
    used_rules = state_space.edge_rules_derivation_graph()

    # check subgraph isomorphisms
    merged_rxn_center_q_rule = merge_rule_left_right(rule_rxn_center.to_mod_rule())
    keep_these_rules = [r for r in used_rules if is_embeddable(r, merged_rxn_center_q_rule) is True]

    message(f"Found {len(keep_these_rules)} rules where the query can be embedded.", verbose=verbose)
    if mod_print:
        for r in keep_these_rules:
            r.print()

    # Collect source and targets from the hyperedges based on the collected rules
    keep_sp_edges = state_space.statespace_using_rules(keep_these_rules)
    message(f"Found {len(keep_sp_edges)} state space edges associated to the query", verbose=verbose)

    # sys.exit()
    # Check whether the query rule can be applied to the collected source graphs

    # Create new DG with all graphs from the state space
    # provide all the graphs from the state space
    dg = mod.DG(graphDatabase=state_space.vertice_graphs_derivation_graph())
    builder = dg.build()
    # Need to take dynamic dg because the dg builder has been blocked by Jakob
    ddg = mod.makeDynamicDG(builder._builder, [query_rule])
    he: DGHyperEdge
    t: DGVertex
    edge: StateSpaceEdge
    for edge in keep_sp_edges:
        apply = ddg.apply([g.graph for g in edge.source.state.graph_multiset.graphs])

    del builder
    # dg.print()
