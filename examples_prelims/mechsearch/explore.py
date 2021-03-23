from mechsearch.state import State
from mechsearch.state_space import StateSpace, StateSpaceNode, Path
from collections import deque
import heapq
import itertools
from typing import Set, List


def equal_weights(w: float, transition):
    return w + 1


def compute_state_space(state_space: StateSpace):
    source = state_space.initial_node

    seen = set()
    Q = deque()
    Q.append(source)
    while Q:
        v = Q.popleft()

        for w in state_space.expand_node(v):
            if w not in seen:
                seen.add(w.target)
                Q.append(w.target)


def dfs(state_space: StateSpace, weight=equal_weights, max_len=None):
    source = state_space.initial_node
    target = state_space.target_node

    stack: List[StateSpaceNode] = [source]
    path: List[StateSpaceNode] = []
    seen = set()

    visited_states: Set[StateSpaceNode] = set()
    counter = 0

    while stack:
        v = stack.pop()
        if v in seen:
            if len(path) == 0:
                return
            path.pop()
            continue

        seen.add(v)
        stack.append(v)
        path.append(v)

        if max_len is not None and len(path) == max_len:
            continue

        transitions = list(state_space.expand_node(v))
        transitions.sort(key=lambda transition: -weight(0, transition))

        print("EXPANDED: ", state_space.number_of_expanded_states, "TOTAL STATES:", state_space.number_of_states)
        #if state_space.number_of_states > 100:
            #return
        for transition in transitions:
            if transition.target not in visited_states and transition.target.state != target.state:
                stack.append(transition.target)
                visited_states.add(transition.target)

            if transition.target.state == target.state:
                path.append(transition.target)
                yield state_space.get_path(path)
                path.pop()


def _bfs(state_space: StateSpace, source: StateSpaceNode,
         target: StateSpaceNode,
         inverse: bool, max_length: int,
         verbose=True):
    stack: List[StateSpaceNode] = [source]
    stack_next: List[StateSpaceNode] = []
    seen: Set[StateSpaceNode] = set()
    length: int = 1

    if verbose:
        print(f"Executing BFS (max_length={max_length}, inverse={inverse})")
        print("\tROUND", length, f"(N = {len(stack)})")

    counter = 0
    while len(stack) > 0:
        counter += 1
        v = stack.pop()
        if v == target:
            continue

        if verbose and counter%500 == 0:
            num_expanded = state_space.num_expanded(inverse)
            print(f"\t\tN = {counter}, LEFT: {len(stack)}, EXPANDED: ", num_expanded, "TOTAL STATES:", state_space.number_of_states)

        for edge in state_space.expand_node(v, inverse=inverse):
            w = edge.source if inverse else edge.target

            if w not in seen:
                stack_next.append(w)
                seen.add(w)

        if len(stack) == 0 and length < max_length:
            counter = 0
            stack, stack_next = stack_next, stack
            length += 1
            if verbose:
                print("\tROUND", length, f"(N = {len(stack)})")


def bidirectional_bfs(state_space: StateSpace,
                      max_length: int,
                      verbose: bool=False):
    source = state_space.initial_node
    target = state_space.target_node
    forward_max_length = int(max_length/2) + max_length%2
    backward_max_length = int(max_length/2)
    _bfs(state_space, source, target, False, forward_max_length, verbose)
    _bfs(state_space, target, source, True, backward_max_length, verbose)


# Most of the algorithm has been copied from NetworkX
def _bidirectional_dijkstra(state_space: StateSpace,
                            source: StateSpaceNode,
                            target: StateSpaceNode,
                            weight,
                            ignore_nodes=None,
                            ignore_edges=None,
                            expansion_limit=0,
                            verbosity=0):
    push = heapq.heappush
    pop = heapq.heappop

    # Init:   Forward             Backward
    dists = [{}, {}]  # dictionary of final distances
    paths = [{source: [source]}, {target: [target]}]  # dictionary of paths
    fringe = [[], []]  # heap of (distance, node) tuples for
    # extracting next node to expand
    seen = [{source: 0}, {target: 0}]  # dictionary of distances to
    # nodes seen
    c = itertools.count()
    # initialize fringe heap
    push(fringe[0], (0, next(c), source))
    push(fringe[1], (0, next(c), target))
    
    # variables to hold shortest discovered path
    finaldist = 1e30000
    finalpath = []
    dir = 1
    while fringe[0] and fringe[1]:
        # choose direction
        # dir == 0 is forward direction and dir == 1 is back
        dir = 1 - dir

        # extract closest to expand
        (dist, _, v) = pop(fringe[dir])
        if v in dists[dir]:
            # Shortest path to v has already been found
            continue

        # update distance
        dists[dir][v] = dist  # equal to seen[dir][v]
        if v in dists[1 - dir]:
            # if we have scanned v in both directions we are done
            # we have now discovered the shortest path
            return (finaldist, finalpath)

        for edge in state_space.expand_node(v, inverse=(dir == 1), verbosity=verbosity):
            w = edge.target if dir == 0 else edge.source
            if (ignore_nodes and w in ignore_nodes) or (ignore_edges and edge in ignore_edges):
                continue
            minweight = weight(dist, edge)
            #vwLength = dists[dir][v] + minweight
            vwLength = minweight
            if w in dists[dir]:
                if vwLength < dists[dir][w]:
                    raise ValueError("Contradictory paths found: negative weights?")
            elif w not in seen[dir] or vwLength < seen[dir][w]:
                # relaxing
                seen[dir][w] = vwLength
                push(fringe[dir], (vwLength, next(c), w))
                paths[dir][w] = paths[dir][v] + [w]
                if w in seen[0] and w in seen[1]:
                    # see if this path is better than than the already
                    # discovered shortest path
                    totaldist = seen[0][w] + seen[1][w]
                    if finalpath == [] or finaldist > totaldist:
                        finaldist = totaldist
                        revpath = paths[1][w][:]
                        revpath.reverse()
                        finalpath = paths[0][w] + revpath[1:]
    return None, None


def _dijkstra(state_space: StateSpace, source: StateSpaceNode, target: StateSpaceNode, weight, ignore_nodes = None,
              ignore_edges = None, expansion_limit: int = 0, verbosity: int = 0) -> (float, Path):
    push = heapq.heappush
    pop = heapq.heappop
    used = set()
    dists = {source: 0}
    prev = {source: None}
    c = itertools.count()
    fringe = []
    push(fringe, (0, next(c), source))
    while fringe:
        dist, _, v = pop(fringe)
        if v is None or v in used:
            continue

        if v == target:
            path: List[StateSpaceNode] = []
            prev_node = v
            while prev_node is not None:
                path.append(prev_node)
                prev_node = prev[prev_node]
            path.reverse()
            return dist, path

        used.add(v)
        for edge in state_space.expand_node(v, verbosity=verbosity):
            if (ignore_nodes and edge.target in ignore_nodes) or (ignore_edges and edge in ignore_edges):
                continue

            assert(v == edge.source)

            alt = weight(dist, edge)
            if edge.target not in dists or alt < dists[edge.target]:
                dists[edge.target] = alt
                # assert (prev[edge.source] is None or prev[edge.source] != edge.target)
                prev[edge.target] = edge.source
                push(fringe, (alt, next(c), edge.target))

        if expansion_limit and len(state_space.expanded_nodes) >= expansion_limit:
            break

    return None, None


def shortest_path(state_space: StateSpace, weight=equal_weights,
                  algorithm="dijkstra", verbosity: int = 0):
    source = state_space.initial_node
    target = state_space.target_node
    if algorithm == "dijkstra":
        dist, path = _dijkstra(state_space, source, target, weight, verbosity=verbosity)
    elif algorithm == "bidirectional_dijkstra":
        dist, path = _bidirectional_dijkstra(state_space, source, target, weight, verbosity=verbosity)
    return dist, state_space.get_path(path)


# Copied from NetworkX
class PathBuffer:

    def __init__(self):
        self.paths = set()
        self.sortedpaths = list()
        self.counter = itertools.count()

    def __len__(self):
        return len(self.sortedpaths)

    def push(self, cost, path):
        hashable_path = tuple(path)
        if hashable_path not in self.paths:
            heapq.heappush(self.sortedpaths, (cost, next(self.counter), path))
            self.paths.add(hashable_path)

    def pop(self):
        (cost, num, path) = heapq.heappop(self.sortedpaths)
        hashable_path = tuple(path)
        self.paths.remove(hashable_path)
        return path


def shortest_simple_paths(state_space: StateSpace, weight=equal_weights,
                          algorithm="dijkstra",
                          expansion_limit: int = 0, verbosity: int = 0):
    source = state_space.initial_node
    target = state_space.target_node

    listA = list()
    listB = PathBuffer()
    prevPath = None

    path_algorithm = None
    if algorithm == "dijkstra":
        path_algorithm = _dijkstra
    elif algorithm == "bidirectional_dijkstra":
        path_algorithm = _bidirectional_dijkstra
    else:
        assert(False and "given algorithm not implemented")

    def lengthFunc(path):
        cost = 0
        for transition in path:
            cost = weight(cost, transition)
        return cost

    while True:
        if not prevPath:
            dist, path = path_algorithm(state_space, source, target, weight, expansion_limit=expansion_limit,
                                        verbosity=verbosity)
            if path is None:
                return
            listB.push(dist, path)
        else:
            ignore_nodes, ignore_edges = set(), set()
            for i in range(1, len(prevPath)):
                root = prevPath[:i]
                rootDist = lengthFunc(root)
                for path in listA:
                    if path[:i] == root:
                        ignore_edges.add(state_space.get_edge(path[i - 1], path[i]))

                dist, spur = path_algorithm(state_space, root[-1], target, weight, ignore_nodes, ignore_edges,
                                            verbosity=verbosity)
                ignore_nodes.add(root[-1])

                if spur is None:
                    continue

                path = root[:-1] + spur
                listB.push(rootDist + dist, path)

        if listB:
            path = listB.pop()
            yield state_space.get_path(path)
            listA.append(path)
            prevPath = path
        else:
            break
