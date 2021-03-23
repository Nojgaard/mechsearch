from data.rhea.db import RheaDB
from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace
import mechsearch.explore as explore
import mechsearch.enzyme_planner as enzyme_planner
import scripts.rhea_analysis.util as util
import mod
import os
import shutil
import json
import multiprocessing as mp
from typing import List
import signal
import sys


def timeout(seconds_before_timeout):
    def decorate(f):
        def handler(signum, frame):
            raise TimeoutError()

        def new_f(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds_before_timeout)
            try:
                result = f(*args, **kwargs)
            finally:
                # reinstall the old signal handler
                signal.signal(signal.SIGALRM, old)
                # cancel the alarm
                # this line should be inside the "finally" block (per Sam Kortchmar)
                signal.alarm(0)
            return result

        new_f.__name__ = f.__name__
        return new_f

    return decorate


def timeout_handler(signum, frame):
    print("Timed Out")
    raise Exception("end of time")


def store_reaction_state_space(reaction: RheaDB.Reaction, state_space: StateSpace,
                               root_dir="state_space"):
    state_space.freeze()
    out_dir = f"{root_dir}/{reaction.rhea_id}"

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    dg_dump_path = state_space.derivation_graph.dump()
    shutil.move(dg_dump_path, os.path.join(out_dir, "dg.dg"))

    with open(os.path.join(out_dir, "state_space.json"), "w") as f:
        json.dump(state_space.to_json(), f, indent=2)


@timeout(180)
def compute_state_space(grammar, amino_graphs, k=1,
                        verbose=False):
    return enzyme_planner.compute_state_space(grammar, amino_graphs, max_depth=6, max_used_aminos=k,
                                              verbose=verbose)


def find_all_state_spaces_with_aminos(aminos: List[mod.Graph], root_dir: str):
    """
    Computes all states spaces that uses the list of given amino acids for
    each rhea reaction. Each state space for each reaction is combined
    into a single state space. If a mechanism is found for a rhea reaction,
    the combined state space is stored under "root_dir/RHEA_ID/state_space.json".
    Its underlying reaction network is stored in "root_dir/RHEA_ID/dg.dg".

    The time limit for computing the state spaces of each reaction
    is 180 seconds.

    :param aminos: the amino acids to place in the reactant and product state.
    :param root_dir: The directory path to store the computed state spaces.
    :return:
    """

    @timeout(180)
    def find_bfs_state_space(state_space: StateSpace):
        explore.bidirectional_bfs(state_space, 6, verbose=True)

    grammar_rules = util.load_rules()
    rhea_db = RheaDB()
    reactions: List[RheaDB.Reaction] = list(rhea_db.reactions())

    num_timed_out_reactions: int = 0

    for i, reaction in enumerate(reactions):

        print(f"Process {mp.current_process().pid}: {i}/{len(reactions)}")
        grammar_reaction = util.reaction2grammar(reaction)
        grammar = grammar_rules + grammar_reaction
        grammar.append_initial(aminos)
        grammar.append_target(aminos)
        try:
            state_space: StateSpace = StateSpace(grammar)
            find_bfs_state_space(state_space)
            state_space = enzyme_planner.prune_state_space(state_space)
            print(state_space)
            if state_space.num_edges > 0:
                store_reaction_state_space(reaction, state_space, root_dir)
            del state_space
        except TimeoutError as error:
            num_timed_out_reactions += 1
            print("State Space Computation Timed Out...")

    print(f"{num_timed_out_reactions}/{len(reactions)} timed out...")


def compute_state_spaces_with_1_amino(root_dir: str):
    """
    Computes all states spaces that uses a single amino acid for
    each rhea reaction. Each state space for each reaction is combined
    into a single state space. If a mechanism is found for a rhea reaction,
    the combined state space is stored under "root_dir/RHEA_ID/state_space.json".
    Its underlying reaction network is stored in "root_dir/RHEA_ID/dg.dg".

    The time limit for computing the state spaces of each reaction
    is 180 seconds.

    :param root_dir: The directory path to store the computed state spaces.
    :return:
    """

    grammar_aminos = Grammar()
    grammar_aminos.load_file("data/amino_acids.json")
    # amino_graphs = [graph.graph for graph in grammar_aminos.graphs if graph.graph.name == "Glutamate"]
    amino_graphs = [graph.graph for graph in grammar_aminos.graphs]
    print(f"Loaded {len(amino_graphs)} amino graphs.")
    rhea_db = RheaDB()
    # reactions: List[RheaDB.Reaction] = list(rhea_db.reactions())[441:][167:][434:][2016:]
    reactions: List[RheaDB.Reaction] = list(rhea_db.reactions())

    grammar_rules = util.load_rules()
    num_timed_out_reactions: int = 0

    for i, reaction in enumerate(reactions):
        print(f"Process {mp.current_process().pid}: {i}/{len(reactions)}, {reaction.rhea_id}")
        grammar_reaction = util.reaction2grammar(reaction)
        grammar = grammar_rules + grammar_reaction
        try:
            state_space: StateSpace = compute_state_space(grammar, amino_graphs, k=1, verbose=True)
            if state_space.num_edges > 0:
                store_reaction_state_space(reaction, state_space, root_dir)
            del state_space
        except TimeoutError as error:
            num_timed_out_reactions += 1
            print("State Space Computation Timed Out...")
            # sys.exit()

    print(f"{num_timed_out_reactions}/{len(reactions)} timed out...")


if __name__ == "__main__":
    grammar_aminos = Grammar()
    grammar_aminos.load_file("data/amino_acids.json")
    amino_map = {graph.name: graph.graph for graph in grammar_aminos.graphs}
    aminos = [amino_map["Serine"],
              amino_map["Deprotonated Cysteine"],
              amino_map["Cysteine"],
              amino_map["Histidine-delta"],
              amino_map["Histidine-epsilon"]
              ]
    find_all_state_spaces_with_aminos(aminos, "state_spaces_fixed_amino")
    compute_state_spaces_with_1_amino("state_spaces_1_amino")
