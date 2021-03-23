from mechsearch.grammar import Grammar
from mechsearch.unfolding.petri_net import DynamicPetriNet
from mechsearch.unfolding.unfolding import Unfolding
import cProfile

# import mod

grammar_file_path = "../mcsadb/data/grammars/Bernhard.json"
rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"

grammar = Grammar()
grammar.load_file(grammar_file_path)
grammar.load_file(rules_file_path)


def run():
    petri_net = DynamicPetriNet(grammar)
    unfolding = Unfolding(petri_net, {petri_net.get_place(graph.graph): count for
                                      graph, count in grammar.initial_multiset.counter.items()})
    target_place = petri_net.get_place(grammar.get_graph("beta-D-fructofuranose 6-phosphate").graph)

    unfolding.maximum_depth = 3

    configurations = list(unfolding.unfold_to_goal(target_place, verbosity=11))
    print("NUM CONF: ", len(configurations))

    # petri_net.lock()
    # printer = mod.DGPrinter()
    # printer.pushEdgeLabel(lambda e: "(" + ", ".join([r.name for r in e.rules]) + ")")
    # for configuration in configurations:
    #     configuration.print(printer)


if True:
    with cProfile.Profile() as pr:
        run()
    pr.dump_stats("out/profile.prof")
else:
    run()

