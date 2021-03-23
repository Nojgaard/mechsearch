import sys
from mechsearch.grammar import Grammar
from mechsearch.module import Module
from mechsearch.shortest_path_module import ShortestPathModule
from mechsearch.unfolding.unfolding_module import UnfoldingModule
import mod
import re
from typing import Any, Callable, Dict, List, Optional, Match


def set_verbosity_level(options: List[str]):
    global verbosity_level
    if len(options) == 0:
        verbosity_level = 1
    else:
        verbosity_level = int(options[0])


def execute_module(options: List[str]):
    if len(options) < 1:
        print("Missing module name. Cannot execute.")
        return

    module_name = options[0].strip().lower()
    if module_name not in module_initialisers:
        print(f"Unknown module '{module_name}'. Ignored.")
        return

    module: Module = module_initialisers[module_name](grammar)
    module.execute(options[1:], verbosity_level)


printer = mod.GraphPrinter()
mod.config.rule.printCombined = False


command_list: Dict[str, Callable[[List[str]], Any]] = {
    "execute": lambda options: execute_module(options),
    "grammar": lambda filepaths: grammar.load_files(filepaths, verbosity_level),
    "verbosity": lambda options: set_verbosity_level(options)
}

module_initialisers: Dict[str, Callable[[Grammar], Any]] = {
    "shortest": lambda grammar: ShortestPathModule(grammar),
    "unfolding": lambda grammar: UnfoldingModule(grammar)
}

verbosity_level: int = 0

# grammar_files: List[str] = []
# modules: List[str] = []
# for index, argument in enumerate(sys.argv):
#     if argument.startswith("-"):
#         if argument == "-g" or argument == "--grammar":
#             if index >= len(sys.argv):
#                 print(f"No grammar file provided for argument '{argument}'. Usage '-g <file>'")
#                 exit(1)
#             grammar_files.append(sys.argv[index + 1])
#         elif argument == "-m" or argument == "--module":
#             if index >= len(sys.argv):
#                 print(f"No module name provided for argument '{argument}'. Usage '-m <module>'")
#                 exit(1)
#             modules.append(sys.argv[index + 1].lower())
#         elif argument == "-v" or argument == "--verbosity":
#             if index >= len(sys.argv) or sys.argv[index + 1].startswith("-"):
#                 verbosity_level = 1
#             else:
#                 verbosity_level = int(sys.argv[index + 1])
#         else:
#             print(f"Unknown argument '{argument}'. Ignored.")

grammar: Grammar = Grammar(printer)
# for grammar_file in grammar_files:
#     grammar.load_file(grammar_file)

command_pattern = re.compile("^[\s]*[^\W\d_]+[\s]")
for line in sys.stdin:
    match: Optional[Match[str]] = command_pattern.match(line)
    if match is None:
        print(f"Malformed command '{line}'.")
        continue
    command: str = match.group(0).strip().lower()
    options: str = line[match.end():].strip()

    if command == "exit" or command == "quit":
        break

    if command not in command_list:
        print(f"Unknown command '{command}'")
        continue

    command_list[command](list(option.strip() for option in options.split(' ') if len(option.strip()) > 0))

# print(f"Filtered rule count: {len(grammar.filter_rules())}")
grammar.print(50)


