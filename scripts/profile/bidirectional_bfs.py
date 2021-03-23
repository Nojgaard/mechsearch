from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace
from mechsearch.explore import shortest_simple_paths, bidirectional_bfs
import cProfile

grammar_file_path = "../mcsadb/data/grammars/664_1.json"
rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"

grammar = Grammar()
grammar.load_file(grammar_file_path)
grammar.load_file(rules_file_path)


def run():
    state_space = StateSpace(grammar)
    bidirectional_bfs(state_space, 50)
    print("NUM STATES: ", state_space.number_of_states)


if True:
    with cProfile.Profile() as pr:
        run()
    pr.dump_stats("out/profile.prof")
else:
    run()

