import mod
from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace
from mechsearch.explore import shortest_simple_paths

printer = mod.GraphPrinter()
grammar = Grammar(printer)
grammar.load_file('data/grammars/square.json')

state_space = StateSpace(grammar)
path = None
for i, p in enumerate(shortest_simple_paths(state_space, verbosity=2)):
    print(p)
    path = p
    if i == 1:
        break


state_space.freeze()
state_space.derivation_graph.print()

print("Printing Path")
path.print_causality_graph()
