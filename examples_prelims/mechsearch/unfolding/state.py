import mod
from typing import Dict, ItemsView, Tuple


class State:
    def __init__(self, marking: Dict[mod.Graph, int]):
        self._marking: Dict[mod.Graph, int] = marking

    def __eq__(self, other: 'State') -> bool:
        return self._serialise() == other._serialise()

    def __ne__(self, other: 'State') -> bool:
        return self._serialise() != other._serialise()

    def __hash__(self) -> int:
        return hash(self._serialise())

    def __str__(self) -> str:
        return "{" + ", ".join(f"{graph.name}: {count}" for graph, count in self.get_places()) + "}"

    def _serialise(self) -> Tuple:
        return tuple(sorted(self._marking))

    def get_places(self) -> ItemsView[mod.Graph, int]:
        return self._marking.items()
