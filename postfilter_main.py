import os
import argparse
from scripts.announcements import *

# Tackling the MØD issue
mod_loc_file = "mod.location"
if not os.path.exists(mod_loc_file):
    error_m(f"Create a file \"{os.getcwd()}/mod.location\" with the location of MØD.")
with open("mod.location", "r") as f:
    mod_loc = f.read().splitlines()[0]
sys.path.append(mod_loc)
from scripts.postfilter_tools import *
from mod import DGHyperEdge, DGVertex
import mechsearch.graph as msg
from mechsearch.state_space import StateSpaceEdge, Path
from subprocess import call

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Postfilter for State Spaces generated with mechsearch.",
        usage="python postfilter_main.py -q <rule.gml> -r <RHEA ID> "
              "[--mod_print [--state_soace_root [--report [-j [-v]]]]]"
    )
    parser.add_argument("-v", "--verbose", action="count", default=0,
                        help="Verbose output")
    parser.add_argument("-r", "--rheaid", type=str, required=True,
                        help="The ID of the RHEA reaction")
    parser.add_argument("--mod_print", action="store_true")
    parser.add_argument("--state_space_root", type=str, default="state_spaces/",
                        help="directory of the state spaces")
    parser.add_argument("-q", "--query", type=str, required=True,
                        help="The query in a GML rule format")
    parser.add_argument("-j", "--njobs", type=int, default=4,
                        help="Number of processes to use for mod_post")
    parser.add_argument("--report", action="store_true",
                        help="Write a short summary file")
    parser.add_argument("--side", type=str, choices=["source", "target", "both"], default="source",
                        help="If pattern, look in sources or targets")
    args = parser.parse_args()
    verbose = args.verbose
    mod_print = args.mod_print
    # RHEA:10076
    rhea_id = check_rheaid_format(args.rheaid)
    if rhea_id is None:
        error_m("Check RHEA ID fromat (e.g., \"RHEA:10076\")")
    state_space_dir = os.path.join(args.state_space_root, rhea_id)
    state_space_loc = os.path.join(state_space_dir, "state_space.json")
    dg_loc = os.path.join(state_space_dir, "dg.dg")
    rule_loc = args.query

    # Loading data
    state_space = load_state_sapce(rhea_id, state_space_loc, dg_loc,
                                   verbose=verbose)
    if isinstance(state_space, KeyError):
        err = f"{rhea_id}\t{state_space}"
        with open("missing_graphs.txt", "a") as _f:
            _f.write(f"{err}\n")
        error_m(err)

    # Extracting used rules from the state space
    used_rules = state_space.edge_rules_derivation_graph()
    # Extracting all graphs from the state space
    state_space_graphs = state_space.vertice_graphs_derivation_graph()
    # Loading query rule
    query_rule: mod.Rule = mod.ruleGML(rule_loc)
    # Check whether the left and the right side are isomorphic
    lr_iso = mod_rule_left_right_iso(query_rule)
    if mod_print:
        query_rule.print()

    keep_these_rules = list()

    if lr_iso is False:
        message("Regular rule", verbose=verbose)
        # Extracting rule reaction center
        rule_rxn_center = msg.FilteredRule(query_rule)
        msg.add_reaction_center(rule_rxn_center)

        # check subgraph isomorphisms
        merged_rxn_center_q_rule = merge_rule_left_right(rule_rxn_center.to_mod_rule())
        keep_these_rules = [r for r in used_rules if is_embeddable(r, merged_rxn_center_q_rule) is True]

        message(f"Found {len(keep_these_rules)} rules where the query reaction center can be embedded.",
                verbose=verbose)
        if mod_print:
            for r in keep_these_rules:
                r.print()

        # Collect source and targets from the hyperedges based on the collected rules
        keep_sp_edges = state_space.statespace_using_rules(keep_these_rules)
        message(f"Found {len(keep_sp_edges)} state space edges associated to the reaction center of the query.",
                verbose=verbose)

        # Check whether the query rule can be applied to the collected source graphs

        # Create new DG with all graphs from the state space
        # provide all the graphs from the state space
        dg = mod.DG(graphDatabase=state_space_graphs)
        builder = dg.build()
        # Need to take dynamic dg because the dg builder has been blocked by Jakob
        ddg = mod.makeDynamicDG(builder._builder, [query_rule])
        he: DGHyperEdge
        t: DGVertex
        edge: StateSpaceEdge
        apply_targets = []
        for edge in keep_sp_edges:
            these_graphs = [g.graph for g in edge.source.state.graph_multiset.graphs]
            apply = ddg.apply(these_graphs)
            if len(apply) > 0:
                apply_targets.append(apply)
                if mod_print:
                    a_path = Path([edge])
                    a_path.print_causality_graph()

        del builder
        color = "NORMAL"
        answer = "False"
        if len(apply_targets) > 0:
            color = "GREEN"
            answer = "True"
        message(f"\"{rule_loc}\" ({query_rule.name}) could be applied to {len(apply_targets)} out of {len(keep_sp_edges)} sources.",
                verbose=verbose, c=color)

        if args.report:
            report_dir = os.path.join(os.getcwd(), "short_summary")
            report_fname = os.path.join(report_dir, f"{rhea_id}.txt")
            if not os.path.isdir(report_dir):
                os.mkdir(report_dir)
            with open(report_fname, "w") as f:
                f.write(
                    f"({answer}) \"{rule_loc}\" ({query_rule.name}) could be applied to {len(apply_targets)} out of {len(keep_sp_edges)} sources.")
            message(f"Wrote a short summary for {rhea_id} to \"{report_fname}\"",
                    verbose=verbose)

    elif lr_iso is True:
        message("The left and the right side of the query seem to be identical.", verbose=verbose)
        side = args.side
        nx_q_rule_g = nx.parse_gml(seperate_mod_rule_to_gml(query_rule)["left"], label="id")
        matched = set()

        if side in ["source", "target"]:
            message(f"Trying to match query into {side} graphs.", verbose=verbose)
            graphs_to_check = get_graphs_from_side(state_space, side)
        else:
            message("Trying to match query into all state space graphs.", verbose=verbose)
            graphs_to_check = state_space_graphs
        message(f"Found {len(graphs_to_check)} graphs.", verbose=verbose, verbose_level_threshold=2)
        end = "\r"
        for sp_g_i, sp_g in enumerate(state_space_graphs, start=1):
            if sp_g_i == len(state_space_graphs):
                end = "\n"
            message(f"{sp_g_i:4d}/{len(graphs_to_check):4d}",
                    verbose=verbose, verbose_level_threshold=2, end=end)
            nx_sp_g = nx.parse_gml(mod_labelled_graph_to_gml(sp_g), label="id")
            iso = subgraph_iso(nx_q_rule_g, nx_sp_g)
            if iso is True:
                matched.add(sp_g)
        message(f"Found {len(matched)} graphs out of {len(state_space_graphs)} "
                f"into which the query can be embedded.")

        if mod_print:
            end = "\r"
            for sp_g_i, sp_g in enumerate(matched, start=1):
                if sp_g_i == len(matched):
                    end = "\n"
                message(f"MØD printing {sp_g_i:4d}/{len(matched):4d} graphs.",
                        verbose=verbose, verbose_level_threshold=2, end=end)
                sp_g.print()
            message("", verbose=verbose, verbose_level_threshold=2)

    # dg.print()
    if mod_print:
        call(f"mod_post -j {args.njobs}", shell=True)

# TODOs
# * Add support for R atoms
