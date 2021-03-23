from mechsearch.grammar import Grammar
from typing import List


class Module:
    def __init__(self, grammar: Grammar):
        self._grammar: Grammar = grammar

    @property
    def grammar(self) -> Grammar:
        return self._grammar

    def execute(self, options: List[str], verbosity: int = 0):
        pass