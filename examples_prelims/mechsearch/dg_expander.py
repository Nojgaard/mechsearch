from collections import Counter
from itertools import product
from mechsearch.grammar import Grammar
from mechsearch.graph import GraphMultiset, Rule, Graph
import mod
from typing import Dict, Iterator, List, Set, Tuple


# taken from https://codereview.stackexchange.com/questions/195277/enumerate-multi-subsets-for-a-multiset-in-python
def subMultisets(counts):
    """Generate the sub-multisets of the iterable elements.
    For example:

    >>> [''.join(s) for s in sub_multisets('aab')]
    ['', 'b', 'a', 'ab', 'aa', 'aab']

    """
    keys, values = zip(*counts)
    for sub_counts in product(*[range(n + 1) for n in values]):
        yield Counter(dict(zip(keys, sub_counts))).elements()


def expand_multiset(i: int, graphs: List[Graph], rules: List[Rule],
                    all_graphs: List[Tuple[Graph, int]]):
    if len(graphs) > 5:
        return
    if len(graphs) > 0:
        yield tuple(g.graph for g in graphs), rules

    for j in range(i+1, len(all_graphs)):
        g, n = all_graphs[j]
        new_rules = [r for r in rules if any(rg <= g for rg in r.left_multiset.graphs)]
        if len(new_rules) == 0:
            continue
        new_graphs = graphs.copy()
        for k in range(n):
            new_graphs.append(g)
            new_rules = [r for r in new_rules if r.rule.numLeftComponents >= len(new_graphs)]
            if len(new_rules) == 0:
                break
            yield from expand_multiset(j, new_graphs,
                                       new_rules, all_graphs)


def get_sub_multisets(graph_multiset: GraphMultiset, rules: List[Rule]):
    sorted_graphs: List[Tuple[Graph,int]] = [(k,v) for k,v in graph_multiset.graphs.items()]
    sorted_graphs.sort(key=lambda g: g[0].graph.id)
    yield from expand_multiset(-1, [], [r for r in rules if r.left_multiset <= graph_multiset], sorted_graphs)


# def expand_multiset(graphs: List[Graph], rules: Set[Rule], possible_expansions: Dict[Graph, int]) ->\
#         Iterator[Tuple[List[Graph], Set[Rule]]]:
#     yield graphs, rules
#
#     for graph in possible_expansions:
#         new_multiset = graphs + [graph]
#         valid_rules = {rule for rule in rules if len(rule.left_multiset) >= len(new_multiset) and
#                        any(rule_graph <= graph for rule_graph in rule.left_multiset.graphs)}
#
#         if len(valid_rules) == 0:
#             continue
#
#         new_possible_expansions = {g: count for g, count in possible_expansions if g.id >= graph.id}
#         new_possible_expansions[graph] -= 1
#         if new_possible_expansions[graph] <= 0:
#             del new_possible_expansions[graph]
#
#         yield from expand_multiset(new_multiset, valid_rules, new_possible_expansions)


def make_inverse_derivation(edge: mod.DGHyperEdge, inverse_rule: mod.Rule):
    d = mod.Derivation()
    d.left = [v.graph for v in edge.targets]
    d.right = [v.graph for v in edge.sources]
    d.rule = inverse_rule
    return d


class DGExpander:
    def __init__(self, grammar: Grammar):
        self._grammar: Grammar = grammar
        self._dg = mod.DG(graphDatabase=self._grammar.unwrapped_graphs, labelSettings=self._grammar.label_settings)
        self._builder = self._dg.build()
        self._derivation_cache: Dict[GraphMultiset, Set[mod.DGHyperEdge]] = {}
        self._inverse_derivation_cache: Dict[GraphMultiset, Set[mod.DGHyperEdge]] = {}
        self._rules: List[Rule] = sorted(grammar.rules, key=lambda rule: rule.rule.id)
        self._inverse_rules: List[Rule] = []
        self._inverse_map: Dict[mod.Rule, Rule] = {}
        for rule in self._rules:
            inverse = rule.make_inverse()
            isomorphic = next((rr for rr in self._rules if rr.rule.isomorphism(inverse.rule, 1) != 0), inverse)

            self._inverse_rules.append(isomorphic)
            self._inverse_map[isomorphic.rule] = rule

    def compute_derivations(self, graph_multiset: GraphMultiset,
                            inverse: bool = False, verbosity: int = 0):
        derivations: Set[mod.DGHyperEdge] = set()
        rules = self._rules if not inverse else self._inverse_rules

        # rules = self._rules if not inverse else [rule.invert() for rule in self._rules]

        """
        print("Running MØD")
        for rule in rules:
            edges = set(self._builder.apply([g.graph for g in graph_multiset.graphs], rule.rule, verbosity=verbosity, onlyProper=False))
            if inverse:
                inverse_derivations = [make_inverse_derivation(e, self._inverse_map[rule.rule].rule) for e in edges]
                edges = set(self._builder.addDerivation(d) for d in inverse_derivations)
            derivations.update(edges)
        print("DONE RUNNING MØD")
        return derivations
        """

        # max_num_comps = max(r.rule.numLeftComponents for r in rules)
        # num_iter = 0
        for graphs, valid_rules in get_sub_multisets(graph_multiset, rules):
            # print("FOUND MULTISET", len(graphs), len(valid_rules))
            key = graphs
            if not inverse and key in self._derivation_cache:
                derivations |= self._derivation_cache[key]
                continue
            elif inverse and key in self._inverse_derivation_cache:
                derivations |= self._inverse_derivation_cache[key]
                continue
            multiset_derivations: Set[mod.DGHyperEdge] = set()

            # print("PROCESSING RULES")
            for rule in valid_rules:
                if verbosity:
                    print(f"\t\tApplying rule {rule.name}, size: {rule.rule.numVertices} to {graphs}")

                #print("Graphs", self._dg.numVertices)
                #print([g.graphDFS for g in graphs])
                #print(rule.rule.getGMLString())
                # edges = set(self._builder.apply(graphs, rule.rule, verbosity=0))
                edges = set(self._builder.apply(graphs, rule.rule))
                #print("WWWW")
                if inverse:
                    # inverse_derivations = [make_inverse_derivation(e, rule.inverse_rule) for e in edges]
                    inverse_derivations = [make_inverse_derivation(e, self._inverse_map[rule.rule].rule) for e in edges]
                    edges = set(self._builder.addDerivation(d) for d in inverse_derivations)
                #print("WHAAAT")
                #print("Updating Multisit", len(edges))
                multiset_derivations.update(edges)
                #print("Updating Cache")
                #print("Updating derivations")

                if verbosity:
                    print(f"\t\tDone applying rule...")

            derivations |= multiset_derivations
            if not inverse:
                self._derivation_cache[key] = multiset_derivations
            else:
                self._inverse_derivation_cache[key] = multiset_derivations
            # print("DONE RULES")
        """

        for i, rule in enumerate(rules):
            n = min(rule.rule.numLeftComponents, 5)
            for sub_multiset in graph_multiset.sub_multisets(maximum_size=n):
                num_iter += 1
                print(max_num_comps, len(sub_multiset), num_iter, sub_multiset)
                if len(sub_multiset) == 0:
                    continue

                key = (rule, sub_multiset)
                if not inverse and key in self._derivation_cache:
                    derivations |= self._derivation_cache[key]
                    continue
                elif inverse and key in self._inverse_derivation_cache:
                    derivations |= self._inverse_derivation_cache[key]
                    continue
                graphs = tuple(graph.graph for graph in sub_multiset.as_multiset())
                multiset_derivations: Set[mod.DGHyperEdge] = set()
                if len(rule.left_multiset) < len(graphs) or not rule.left_multiset <= sub_multiset:
                    continue

                if verbosity:
                    print(f"\tApplying rule {rule.name}, size: {rule.rule.numVertices} to {sub_multiset}")

                print("Graphs", self._dg.numVertices)
                print([g.graphDFS for g in graphs])
                print(rule.rule.getGMLString())
                edges = set(self._builder.apply(graphs, rule.rule, verbosity=verbosity))
                if inverse:
                    inverse_derivations = [make_inverse_derivation(e, self._rules[i].rule) for e in edges]
                    edges = set(self._builder.addDerivation(d) for d in inverse_derivations)
                print("Updating Multisit")
                multiset_derivations.update(edges)
                print("Processed Rule", i)
                print("Updating Cache")
                if not inverse:
                    self._derivation_cache[key] = multiset_derivations
                else:
                    self._inverse_derivation_cache[key] = multiset_derivations
                print("Updating derivations")
                derivations |= multiset_derivations
                print("DONE Multiset", len(derivations))

        if verbosity > 1:
            print(f"Derivation Graph Size: {self.derivation_graph.numVertices}")
        """

        # for sub_multiset in graph_multiset.sub_multisets(maximum_size=5):
        #     num_iter += 1
        #     # print(max_num_comps, len(graph_multiset), num_iter, sub_multiset)
        #     if len(sub_multiset) == 0:
        #         continue
        #
        #     if not inverse and sub_multiset in self._derivation_cache:
        #         derivations |= self._derivation_cache[sub_multiset]
        #         continue
        #     elif inverse and sub_multiset in self._inverse_derivation_cache:
        #         derivations |= self._inverse_derivation_cache[sub_multiset]
        #         continue
        #
        #     graphs = tuple(graph.graph for graph in sub_multiset.as_multiset())
        #
        #     multiset_derivations: Set[mod.DGHyperEdge] = set()
        #     for i, rule in enumerate(rules):
        #         if len(rule.left_multiset) < len(graphs) or not rule.left_multiset <= sub_multiset:
        #             continue
        #         if verbosity:
        #             print(f"\tApplying rule {rule.name}, size: {rule.rule.numVertices} to {sub_multiset}")
        #
        #         # print("Graphs", self._dg.numVertices)
        #         # print([g.graphDFS for g in graphs])
        #         # print(rule.rule.getGMLString())
        #         edges = set(self._builder.apply(graphs, rule.rule, verbosity=0))
        #         if inverse:
        #             inverse_derivations = [make_inverse_derivation(e, self._rules[i].rule) for e in edges]
        #             edges = set(self._builder.addDerivation(d) for d in inverse_derivations)
        #         # print("Updating Multisit")
        #         multiset_derivations.update(edges)
        #         print("\tProcessed Rule", i)
        #
        #     # print("Updating Cache")
        #     if not inverse:
        #         self._derivation_cache[sub_multiset] = multiset_derivations
        #     else:
        #         self._inverse_derivation_cache[sub_multiset] = multiset_derivations
        #     # print("Updating derivations")
        #     derivations |= multiset_derivations
        #     # print("DONE Multiset", len(derivations))

        if verbosity > 1:
            print(f"\tDerivation Graph Size: {self.derivation_graph.numVertices}")

        return derivations

    def freeze(self):
        self._builder = None

    @property
    def derivation_graph(self):
        return self._dg
