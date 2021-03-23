from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace
from mechsearch.explore import shortest_simple_paths, dfs
import cProfile

grammar_file_path = "../mcsadb/data/grammars/243_1.json"
rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"

grammar = Grammar()
grammar.load_file(grammar_file_path)
grammar.load_file(rules_file_path)

"""
with cProfile.Profile() as pr:
    state_space = StateSpace(grammar)
    paths = shortest_simple_paths(state_space,
                                  algorithm="bidirectional_dijkstra",
                                  verbosity=0)
    for i, p in enumerate(paths):
        if i == 1:
            break
    print("NUM STATES: ", state_space.number_of_states)
pr.dump_stats("out/profile.prof")
"""

state_space = StateSpace(grammar)
paths = shortest_simple_paths(state_space,
                              algorithm="bidirectional_dijkstra",
                              verbosity=0)
#paths = dfs(state_space, max_len=3)

for i, p in enumerate(paths):
    print(len(paths))
    if i == 1:
        break
print("NUM STATES: ", state_space.number_of_states)
