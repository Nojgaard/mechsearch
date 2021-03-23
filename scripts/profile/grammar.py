from mechsearch.grammar import Grammar
import cProfile


with cProfile.Profile() as pr:
    grammar_file_path = "../mcsadb/data/grammars/664_1.json"
    rules_file_path = "../mcsadb/data/rules/aminos_groups_context1_no_H.json"
    grammar = Grammar()
    grammar.load_file(grammar_file_path)
    grammar.load_file(rules_file_path)

pr.dump_stats("out/profile.prof")
