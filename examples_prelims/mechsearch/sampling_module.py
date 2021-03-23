from mechsearch.explore import dfs
from mechsearch.state_graph import Transition
from mechsearch.grammar import Grammar
from mechsearch.module import Module
from mechsearch.shortest_path_module import edge_weight_heuristics
from mechsearch.state_space import StateSpace
from mod import GraphPrinter, postChapter
from typing import Callable, List, Optional


class SamplingModule(Module):
    def __init__(self, grammar: Grammar):
        super().__init__(grammar)

        self._state_space = StateSpace(self.grammar)

    def print_shortest_path_sample(self, number_of_paths: int,
                                   edge_weight_heuristic: Callable[[float, Transition], float], print_derivations: bool,
                                   verbosity: int = 0):
        printer: Optional[GraphPrinter] = None
        if print_derivations:
            printer = self.grammar.printer

        for index, path in enumerate(dfs(self._state_space, self.grammar.target_graphs, edge_weight_heuristic)):
            if verbosity > 1:
                print(f"Found path number {index + 1} of length {len(path)}.")

            postChapter(f"Path {index + 1}, length: {len(path)}")
            path.print(lambda transition: ", ".join(r.name for r in transition.dg_edge.rules) +
                                          ": %.2f" % edge_weight_heuristic(0, transition), printer)

            if number_of_paths and index + 1 >= number_of_paths:
                break

    def execute(self, options: List[str], verbosity: int = 0):
        path_count: int = 0
        weight_heuristic: str = "constant"
        print_derivations: bool = False
        for index, option in enumerate(options):
            if option == "-h" or option == "--heuristic":
                if index >= len(options):
                    print(f"Missing parameter for the '{option}' argument of Shortest Path Module.")
                    continue

                weight_heuristic = options[index + 1].strip().lower()
            elif option == "-c" or option == "--count":
                if index >= len(options):
                    print(f"Missing parameter for the '{option}' argument of Shortest Path Module.")
                    continue

                path_count = int(options[index + 1])
            elif option == "-d" or option == "--print-derivations":
                print_derivations = True

        if verbosity:
            print(f"Sampling shortest paths in the state space with '{weight_heuristic}' edge weights.")
        self.print_shortest_path_sample(path_count, edge_weight_heuristics[weight_heuristic], print_derivations,
                                        verbosity)