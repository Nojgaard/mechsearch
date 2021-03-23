from mechsearch.state_space import StateSpace, StateSpaceNode
from mechsearch.grammar import Grammar
from mechsearch.explore import bidirectional_bfs
from mechsearch.dg_expander import DGExpander
from typing import List, Set
import mod
import itertools


def run_bfs(graph, source, inverse: bool = False):
    reachable: Set[StateSpaceNode] = set()

    stack = [source]
    while len(stack) > 0:
        v = stack.pop()
        reachable.add(v)

        for w in (s for s, _ in graph.in_edges(v)) if inverse else (t for _, t in graph.edges(v)):
            if w not in reachable:
                stack.append(w)

    return reachable


def prune_state_space(state_space: StateSpace):
    reachable = run_bfs(state_space.graph, state_space.initial_node)
    basin = run_bfs(state_space.graph, state_space.target_node, True)

    sub_space = state_space.sub_space(reachable.intersection(basin))

    return sub_space


def compute_state_space(grammar: Grammar,
                        amino_db: List[mod.Graph],
                        max_depth: int,
                        max_used_aminos: int = 1,
                        verbose: bool = False):
    grammar.append_graphs(amino_db)
    dg_expander = DGExpander(grammar, False)
    full_state_space = StateSpace(grammar, dg_expander)
    for aminos in itertools.combinations(amino_db, max_used_aminos):
        if verbose:
            print(f"Constructing StateSpace using aminos {[a.name for a in aminos]}")
        tmp_grammar = grammar.clone()
        tmp_grammar.add2multiset(aminos)
        state_space = StateSpace(tmp_grammar, dg_expander)
        bidirectional_bfs(state_space, max_depth, verbose=verbose)

        print(state_space)
        state_space = prune_state_space(state_space)
        if state_space.num_edges > 0:
            full_state_space.append_state_space(state_space)
        del state_space

    print("FULL STATE SPACE:", full_state_space.number_of_states)
    return full_state_space
