import mod
from mechsearch.grammar import Grammar
from mechsearch.graph import Rule, GraphMultiset
from mechsearch.rule_canonicalisation import CanonSmilesRule
from typing import List, Dict


def make_inverse_derivation(edge: mod.DGHyperEdge, inverse_rule: mod.Rule):
    d = mod.Derivation()
    d.left = [v.graph for v in edge.targets]
    d.right = [v.graph for v in edge.sources]
    d.rule = inverse_rule
    return d


class DGExpander:
    def __init__(self, grammar: Grammar, use_filtered: bool = True):
        mod.config.graph.isomorphismAlg = mod.Config.IsomorphismAlg.Canon
        self._grammar = grammar

        rules = grammar.filtered_rules if use_filtered else grammar.rules
        # rules = [r for r in rules if r.rule.numLeftComponents <= 5]
        self._rules: List[Rule] = sorted(rules, key=lambda rule: rule.rule.id)
        self._canonical_rules: Dict[CanonSmilesRule, Rule] = {rule.canonical_smiles: rule for rule in self._rules}
        self._inverse_rules: List[Rule] = []
        self._inverse_map: Dict[mod.Rule, Rule] = {}

        for rule in self._rules:
            inverse = rule.inverse_rule
            if inverse.canonical_smiles not in self._canonical_rules:
                self._canonical_rules[inverse.canonical_smiles] = inverse

            self._inverse_rules.append(self._canonical_rules[inverse.canonical_smiles])
            self._inverse_map[self._canonical_rules[inverse.canonical_smiles].rule] = rule

        self._dg = mod.DG(graphDatabase=grammar.unwrapped_graphs,
                          labelSettings=grammar.label_settings)
        self._builder = self._dg.build()

        self._ddg = mod.makeDynamicDG(self._builder._builder,
                                      [r.rule for r in self._rules])

        self._ddg_inverse = mod.makeDynamicDG(self._builder._builder,
                                              [r.rule for r in self._inverse_rules])

    def compute_derivations(self, graph_multiset: GraphMultiset, inverse: bool = False, verbosity: int = 0):
        graphs = [g.graph for g in graph_multiset.graphs]
        #print("GRAPHS: ", [g.graphDFS for g in graphs])
        #print("GRAPHS: ", [g.graphDFS for g in graphs])
        if not inverse:
            ders = set(self._ddg.apply(graphs))
            return ders
            ders_temp = set()
            for r in self._rules:
                ders_temp.update(self._builder.apply(graphs, r.rule, onlyProper=False))
            print(len(ders), len(ders_temp))
            #print(self._rules[226].rule.getGMLString())
            if len(ders) != len(ders_temp):
                diff = ders.symmetric_difference(ders_temp)
                e = list(diff)[0]
                print(diff)
                rules: List[mod.Rule] = [r for r in e.rules]
                printer = mod.GraphPrinter()
                printer.withIndex = True
                print("RULES:", len(rules))
                print([g.graph.graphDFS for g in e.sources], "->", [g.graph.graphDFS for g in e.targets])
                print(rules[0].getGMLString())
                rules[0].print(printer)
                [g.graph.print() for g in e.sources]
                mod.graphDFS("[C]1([N]([C](=[N][C]2=[C]([N]=[C]([C]([N](2)[H])([H])[H])[C]([C]([O][H])([C]([O][H])([H])[H])[H])([H])[O-])1)[N]([H])[H])[H])([O][C]([C]([C]([Amino{C, Glu, *, *}])([H])[H])([H])[H])=[O])[O][H]").print(printer)
                print("NUM EDGES:", len(set(self._builder.apply([g.graph for g in e.sources], rules[0], onlyProper=False))))


            assert(len(ders) == len(ders_temp))
            return ders

        inverse_edges = self._ddg_inverse.apply(graphs)
        edges = []
        for e in inverse_edges:
            ir = None
            for r in e.rules:
                if r in self._inverse_map:
                    ir = self._inverse_map[r].rule
                    break

            assert(ir is not None)
            inv_der = make_inverse_derivation(e, ir)
            edges.append(self._builder.addDerivation(inv_der))
        return edges

    def freeze(self):
        self._builder = None

    def is_frozen(self):
        return self._builder is None

    def update(self, dg: mod.DG, edges: List[mod.DGHyperEdge] = None):
        e: mod.DGHyperEdge
        edges = dg.edges if edges is None else edges
        for e in edges:
            d = mod.Derivations()
            d.left = [v.graph for v in e.sources]
            d.right = [v.graph for v in e.targets]
            d.rules = e.rules
            newEdge = self._builder.addDerivation(d)
            #assert(e.id == newEdge.id)


    @property
    def derivation_graph(self):
        return self._dg
