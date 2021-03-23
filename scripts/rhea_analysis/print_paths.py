from data.rhea.db import RheaDB
from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace, Path
from mechsearch.graph import Rule
import mechsearch.explore as explore
import scripts.rhea_analysis.util as util
import mod
import os
import json
import itertools
from typing import List, Dict


def store_readable_paths(root_dir, filepath):
    """
    Functions like print_interesting_paths, but also
    stores each printed mechanism.
    :param root_dir:
    :param filepath:
    :return:
    """
    grammar_aminos = Grammar()
    grammar_aminos.load_file("data/amino_acids.json")
    grammar_rules = grammar_aminos + util.load_rules()
    input_dir = root_dir
    rhea_db = RheaDB()
    count = 0

    def uses_amino_acid(path: Path):
        for edge in path:
            for he in edge.transitions:
                for hv in he.sources:
                    v: mod.GraphVertex
                    for v in hv.graph.vertices:
                        if v.stringLabel.startswith("Amino"):
                            return True
        return False

    def uses_different_rule_mechanisms(path: Path):
        modrule2rule: Dict[mod.Rule, Rule] = {r.rule: r for r in grammar_rules.rules}
        used_rules: List[Rule] = []
        for edge in path:
            for he in edge.transitions:
                used_rules.extend([modrule2rule[r] for r in he.rules if r in modrule2rule])

        used_mcsa_entries = set(step.entry for r in used_rules for step in r.steps)
        return len(used_mcsa_entries) > 1

    num_no_amino_paths = 0
    paths = []
    for rhea_id in os.listdir(input_dir):
        print(rhea_id)
        reaction = rhea_db.get_reaction(rhea_id)
        grammar_reaction = util.reaction2grammar(reaction)
        grammar = grammar_rules + grammar_reaction
        state_space_dir = os.path.join(input_dir, rhea_id)
        dg_path = os.path.join(state_space_dir, "dg.dg")
        state_space_path = os.path.join(state_space_dir, "state_space.json")
        with open(state_space_path) as f:
            state_space = StateSpace.from_json(json.load(f), grammar, dg_path)
        print(f"Analyzing StateSpace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})")
        print(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges})")
        state_space.freeze()
        path_generator = explore.shortest_simple_paths(state_space,
                                                       algorithm="bidirectional_dijkstra")
        print("Computing Paths...")
        path = list(itertools.islice(path_generator, 1))[0]

        if not uses_amino_acid(path) or not uses_different_rule_mechanisms(path):
            num_no_amino_paths += 1
            continue

        serial_path = []
        for e in path:
            serial_path.append({
                "rules": [r.name for t in e.transitions for r in t.rules]
            })

        paths.append({
            "rhea_id": rhea_id,
            "path": serial_path
        })

    with open(filepath, "w") as f:
        json.dump(paths, f)


def print_interesting_paths(root_dir: str):
    """
    Loads the each state space located in "root_dir/RHEA_ID/state_space.json".
    For each such state space, it will enumerate the shortest
    "interesting" mechanism
    and print a summary of them. Here, interesting is defined as any mechanism
    that uses at least two rules derived from different MCSA mechanisms.
    :param root_dir: the directory where each state space is located
    :return:
    """
    grammar_aminos = Grammar()
    grammar_aminos.load_file("data/amino_acids.json")
    grammar_rules = grammar_aminos + util.load_rules()
    input_dir = root_dir
    rhea_db = RheaDB()
    count = 0

    def uses_amino_acid(path: Path):
        for edge in path:
            for he in edge.transitions:
                for hv in he.sources:
                    v: mod.GraphVertex
                    for v in hv.graph.vertices:
                        if v.stringLabel.startswith("Amino"):
                            return True
        return False

    def uses_different_rule_mechanisms(path: Path):
        modrule2rule: Dict[mod.Rule, Rule] = {r.rule: r for r in grammar_rules.rules}
        used_rules: List[Rule] = []
        for edge in path:
            for he in edge.transitions:
                used_rules.extend([modrule2rule[r] for r in he.rules if r in modrule2rule])

        used_mcsa_entries = set(step.entry for r in used_rules for step in r.steps)
        return len(used_mcsa_entries) > 1

    num_no_amino_paths = 0
    for rhea_id in os.listdir(input_dir):
        print(rhea_id)
        reaction = rhea_db.get_reaction(rhea_id)
        grammar_reaction = util.reaction2grammar(reaction)
        grammar = grammar_rules + grammar_reaction
        state_space_dir = os.path.join(input_dir, rhea_id)
        dg_path = os.path.join(state_space_dir, "dg.dg")
        state_space_path = os.path.join(state_space_dir, "state_space.json")
        with open(state_space_path) as f:
            state_space = StateSpace.from_json(json.load(f), grammar, dg_path)
        print(f"Analyzing StateSpace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})")
        print(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges})")
        state_space.freeze()
        path_generator = explore.shortest_simple_paths(state_space,
                                                       algorithm="bidirectional_dijkstra")
        print("Computing Paths...")
        paths = list(itertools.islice(path_generator, 1))

        if not uses_amino_acid(paths[0]) or not uses_different_rule_mechanisms(paths[0]):
            num_no_amino_paths += 1
            continue

        print("Printing Paths...")
        mod.postChapter(rhea_id)
        for p in paths:
            p.print_causality_graph()
        count += 1

    print(f"Skipped {num_no_amino_paths} paths.")


def print_paths(root_dir="state_space",
                amino_path="data/amino_acids.json"):
    """
    Loads the each state space located in "root_dir/RHEA_ID/state_space.json".
    For each such state space, it will enumerate the 10k shortest mechanisms
    and print a summary of the shortest one.
    :param root_dir: the directory where each state space is located
    :param amino_path: the path to set of amino acids used to generate the state spaces
    :return:
    """
    grammar_aminos = Grammar()
    grammar_aminos.load_file(amino_path)
    grammar_rules = grammar_aminos + util.load_rules()
    input_dir = f"{root_dir}"
    rhea_db = RheaDB()
    count = 0

    def uses_amino_acid(path: Path):
        for edge in path:
            for he in edge.transitions:
                for hv in he.sources:
                    v: mod.GraphVertex
                    for v in hv.graph.vertices:
                        if v.stringLabel.startswith("Amino"):
                            return True
        return False

    num_no_amino_paths = 0
    paths = []
    serial_paths = []
    for rhea_id in os.listdir(input_dir):
        print(rhea_id)
        if rhea_id not in ["RHEA:12024",
                           #"RHEA:24116"
                           ]:
            continue
        reaction = rhea_db.get_reaction(rhea_id)
        grammar_reaction = util.reaction2grammar(reaction)
        grammar = grammar_rules + grammar_reaction
        grammar.append_initial([g.graph for g in grammar_aminos.graphs])
        grammar.append_target([g.graph for g in grammar_aminos.graphs])
        state_space_dir = os.path.join(input_dir, rhea_id)
        dg_path = os.path.join(state_space_dir, "dg.dg")
        state_space_path = os.path.join(state_space_dir, "state_space.json")
        with open(state_space_path) as f:
            state_space = StateSpace.from_json(json.load(f), grammar, dg_path)
        print(f"Analyzing StateSpace(|V| = {state_space.number_of_states}, |E| = {len(state_space.graph.edges)})")
        print(f"\t DG(|V| = {state_space.derivation_graph.numVertices}, |E| = {state_space.derivation_graph.numEdges})")
        state_space.freeze()
        path_generator = explore.shortest_simple_paths(state_space,
                                                       algorithm="bidirectional_dijkstra")
        print("Computing Paths...")
        paths = list(itertools.islice(path_generator, 10000))
        print(f"Found {len(paths)} paths")

        if not uses_amino_acid(paths[0]):
            num_no_amino_paths += 1
            continue

        print("Printing Paths...")
        mod.postChapter(rhea_id)
        diff_aminos = set()
        for p in paths:
            active_aminos = set()
            for e in p:
                for t in e.transitions:
                    for v in t.sources:
                        if v.graph in grammar_aminos.graphs:
                            active_aminos.add(v.graph.name)
            if active_aminos:
                diff_aminos.add(tuple(sorted(active_aminos)))

            if len(active_aminos) == 2:
                p.print_causality_graph()
                serial_path = []
                for e in p:
                    serial_path.append({
                        "rules": [r.name for t in e.transitions for r in t.rules]
                    })

                serial_paths.append({
                    "rhea_id": rhea_id,
                    "path": serial_path
                })

        print(diff_aminos)
        count += 1
    with open("paths.json", "w") as f:
        json.dump(serial_paths, f, indent=2)

    print(f"Skipped {num_no_amino_paths} paths.")


if __name__ == "__main__":
    print_paths("state_spaces_1_amino")
    print_interesting_paths("state_spaces_1_amino")
    store_readable_paths("state_spaces_1_amino", "rhea_paths.json")
