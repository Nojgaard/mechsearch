from mechsearch.edge_weight import ConstantEdgeWeight, EdgeWeight
from mechsearch.energy import EnergyBarrier, EnergyDifference
from mechsearch.explore import shortest_simple_paths
from mechsearch.grammar import Grammar
from mechsearch.state_space import Path
from mechsearch.module import Module
from mechsearch.state_space import StateSpace
import mod
# import mod.cargo as cargo
from typing import Dict, List, Optional, Set


#with open("cargo-pka/energy/model.json", "r") as file:
    #cargo_model = cargo.Model.fromJson(file.read())
cargo_model = None


edge_weight_heuristics: Dict[str, EdgeWeight] = {
    "constant": ConstantEdgeWeight(),
    "energy_barrier": EnergyBarrier(cargo_model),
    "energy_difference": EnergyDifference(cargo_model)
}


class ShortestPathModule(Module):
    def __init__(self, grammar: Grammar):
        super().__init__(grammar)

        self._state_space = StateSpace(self.grammar)

    @property
    def state_space(self) -> StateSpace:
        return self._state_space

    def get_shortest_paths(self, edge_weight_heuristic: EdgeWeight = edge_weight_heuristics["constant"],
                           number_of_paths: int = 0, expansion_limit: Optional[int] = None,
                           search_algorithm: str = "dijkstra", verbosity: int = 0) -> List[Path]:
        if expansion_limit is not None:
            self._state_space.set_expansion_limit(expansion_limit)

        paths: List[Path] = []
        for index, path in enumerate(shortest_simple_paths(self._state_space,
                                                           edge_weight_heuristic, search_algorithm,
                                                           verbosity=verbosity)):

            if verbosity > 1:
                print(f"Found path number {index + 1} of length {len(path)}.")

            paths.append(path)

            if number_of_paths and index + 1 >= number_of_paths:
                break

        return paths

    def print_shortest_paths(self, edge_weight_heuristic: EdgeWeight = edge_weight_heuristics["constant"],
                             number_of_paths: int = 0, print_derivations: bool = False, verbosity: int = 0):
        printer: Optional[mod.GraphPrinter] = None
        if print_derivations:
            printer = self.grammar.printer

        for index, path in enumerate(self.get_shortest_paths(edge_weight_heuristic, number_of_paths, verbosity=verbosity)):
            mod.postChapter(f"Path {index + 1}, length: {len(path)}")
            path.print(lambda transition: ", ".join(r.name for r in transition.dg_edge.rules) +
                                          ": %.2f" % edge_weight_heuristic(0, transition), printer)

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
            print(f"Searching for shortest paths in the state space with '{weight_heuristic}' edge weights.")
        self.print_shortest_paths(edge_weight_heuristics[weight_heuristic], path_count, print_derivations, verbosity)
