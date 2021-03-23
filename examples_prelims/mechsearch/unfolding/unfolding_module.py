from mechsearch.grammar import Grammar
from mechsearch.module import Module
from mechsearch.unfolding.unfolding import Unfolding
import mod
from typing import List


class UnfoldingModule(Module):
    def __init__(self, grammar: Grammar):
        super().__init__(grammar)

        self._unfolding: Unfolding = None

    def get_traces(self, verbosity: int = 0):
        traces = self._unfolding.get_target_traces(self._grammar.target_graphs, verbosity)
        print(f"Found a total of {len(traces)} traces.")

    def execute(self, options: List[str], verbosity: int = 0):
        if self._unfolding is None:
            self._unfolding = Unfolding(self.grammar, verbosity)

        for index, configuration in enumerate(self._unfolding.get_target_markings(
                self.grammar.target_graphs, verbosity)):
            mod.postChapter(f"Configuration {index + 1}")
            configuration.print()

        for option in options:
            if not option.startswith('-'):
                print(f"Unrecognised option for Unfolding module '{option}'. Ignored.")
                continue

            if option == "--print" or option == "-p":
                mod.postChapter(f"Unfolding")
                self._unfolding.print()
                continue

            if option == "--traces" or option == "-t":
                self.get_traces(verbosity)
