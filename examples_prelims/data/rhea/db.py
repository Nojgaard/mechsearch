import mod
import os
import json
from typing import List, Iterator


class RheaDB:
    class Reaction:
        def __init__(self, json_entry):
            self._rhea_id: str = json_entry["rhea_id"]
            self._ec: str = json_entry["ec"]
            parse = mod.graphDFS
            self._reactants: List[mod.Graph] = [parse(r["dfs"], name=r["name"]) for r in json_entry["reactants"]]
            self._products: List[mod.Graph] = [parse(p["dfs"], name=p["name"]) for p in json_entry["products"]]

        def serialize(self):
            return {
                "rhea_id": self._rhea_id,
                "ec": self._ec,
                "reactants": [{"name": graph.name, "dfs": graph.graphDFS} for graph in self._reactants],
                "products": [{"name": graph.name, "dfs": graph.graphDFS} for graph in self._products]
            }

        @staticmethod
        def deserialize(serial_reaction):
            return RheaDB.Reaction(serial_reaction)

        @property
        def rhea_id(self) -> str:
            return str(self._rhea_id)

        @property
        def ec(self) -> str:
            return str(self._ec)

        @property
        def reactants(self) -> List[mod.Graph]:
            return list(self._reactants)

        @property
        def products(self) -> List[mod.Graph]:
            return list(self._products)

    def __init__(self):
        dir_path = os.path.dirname(__file__)
        db_path = os.path.join(dir_path, "reactions.json")
        with open(db_path) as f:
            self._db = json.load(f)

        self._id2idx = {r["rhea_id"]: i for i, r in enumerate(self._db)}

    def get_reaction(self, rhea_id: str):
        idx = self._id2idx[rhea_id]
        return RheaDB.Reaction(self._db[idx])

    def reactions(self) -> Iterator['RheaDB.Reaction']:
        for r in self._db:
            try:
                yield RheaDB.Reaction(r)
            except mod.InputError:
                pass
