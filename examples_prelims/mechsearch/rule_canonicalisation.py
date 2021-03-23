import networkx as nx
import mod
from typing import List


_label_to_isotope_map = {}


def _rule_graph_to_nx(rule_graph):
    g = nx.Graph()
    dummy_v = rule_graph.numVertices + rule_graph.numEdges
    for v in rule_graph.vertices:
        left_label = v.left.stringLabel if not v.left.isNull() else ''
        right_label = v.right.stringLabel if not v.right.isNull() else ''
        g.add_node(v.id, label=f'({left_label},  {right_label}')

    for e in rule_graph.edges:
        left_label = e.left.stringLabel if not e.left.isNull() else ''
        right_label = e.right.stringLabel if not e.right.isNull() else ''
        g.add_node(dummy_v, label=f'({left_label},  {right_label}')
        g.add_edge(dummy_v, e.target.id, label='-')
        g.add_edge(e.source.id, dummy_v, label='-')
        dummy_v += 1

    return g


def _side_graph_to_nx(rule_graph):
    g = nx.Graph()
    dummy_v = rule_graph.numVertices + rule_graph.numEdges
    for v in rule_graph.vertices:
        g.add_node(v.id, label=f'{v.stringLabel}', rule_vertex=v)

    for e in rule_graph.edges:
        g.add_edge(e.source.id, e.target.id, label=e.stringLabel, rule_edge=e)
        dummy_v += 1

    return g


def _nx_to_gml(g: nx.Graph):
    out = ['graph [']
    for v in g.nodes:
        lbl: str = g.nodes[v]['label']
        if lbl not in _label_to_isotope_map:
            _label_to_isotope_map[lbl] = f'{len(_label_to_isotope_map) + 1}C'
        lbl = _label_to_isotope_map[lbl]
        out.append(f'node [ id {v} label "{lbl}" ]')

    for (src, tar) in g.edges:
        lbl = g.edges[src, tar]['label']
        out.append(f'edge [ source {src} target {tar} label "{lbl}" ]')

    out.append(']')
    return '\n'.join(out)


def _get_graphs(rule_graph):
    nxg = _rule_graph_to_nx(rule_graph)
    molecules = [nxg.subgraph(c).copy() for c in nx.connected_components(nxg)]
    modgraphs = [mod.graphGMLString(_nx_to_gml(g), add=False) for g in molecules]
    return modgraphs


# class CanonSmilesSideGraph:
#     def __init__(self, side_graph):
#         nxg = _side_graph_to_nx(side_graph)
#         molecules = [nxg.subgraph(c).copy() for c in nx.connected_components(nxg)]
#         smiles_strings = [mod.graphGMLString(_nx_to_gml(g)).smiles for g in molecules]
#         canon_graphs = [(s, m) for s, m in zip(smiles_strings, molecules)]
#         self._smiles2graphs = {s: [] for s in smiles_strings}
#         for s, m in canon_graphs:
#             self._smiles2graphs[s].append(m)
#         for s, graphs in self._smiles2graphs.items():
#             if len(graphs) > 1:
#                 # print(graphs)
#                 continue
#
#     def num_vertices(self):
#         num_verts = 0
#         for s, graphs in self._smiles2graphs.items():
#             num_verts += sum(len(g.nodes()) for g in graphs)
#
#         return num_verts
#
#     def remove(self, other: 'CanonSmilesSideGraph'):
#         diff_graphs = {}
#         for s, graphs in self._smiles2graphs.items():
#             if s not in other._smiles2graphs:
#                 diff_graphs[s] = graphs.copy()
#                 continue
#
#             num_graphs1 = len(other._smiles2graphs[s])
#             num_graphs2 = len(self._smiles2graphs[s])
#             if num_graphs1 < num_graphs2:
#                 diff = num_graphs2 - num_graphs1
#                 #print("TAKING")
#                 #print(graphs)
#                 diff_graphs[s] = list(reversed(graphs))[:diff]
#         return diff_graphs
#
#     def add_dict(self, dict_graphs: Dict[str, List[nx.Graph]]):
#         for s, graphs in dict_graphs.items():
#             if s not in self._smiles2graphs:
#                 self._smiles2graphs[s] = graphs.copy()
#             else:
#                 for g in graphs:
#                     if g in self._smiles2graphs[s]:
#                         print([g])
#                         print(self._smiles2graphs[s])
#                     assert(g not in self._smiles2graphs[s])
#                 self._smiles2graphs[s].extend(graphs)
#
#     @property
#     def key(self):
#         return tuple(sorted(((s, len(gs)) for s, gs in self._smiles2graphs.items())))
#
#     def __eq__(self, other: 'CanonSmilesSideGraph'):
#         return self.key == other.key


class CanonSmilesRule:
    def __init__(self, rule: mod.Rule):
        self._rule = rule
        graphs: List[mod.Graph] = _get_graphs(rule)

        smiles_strings = [g.smiles for g in graphs]
        smiles_strings.sort()

        self._key = tuple(smiles_strings)
    #     self._left = CanonSmilesSideGraph(rule.left)
    #     self._right = CanonSmilesSideGraph(rule.right)
    #
    # @property
    # def left(self):
    #     return self._left
    #
    # @property
    # def right(self):
    #     return self._right

    @property
    def key(self):
        return self._key

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other: 'CanonSmilesRule') -> bool:
        return self.key == other.key

    def __ne__(self, other: 'CanonSmilesRule') -> bool:
        return not self == other

    # def to_gml(self):
    #     class Container:
    #         def __init__(self):
    #             self.vertices = []
    #             self.edges = []
    #     left = Container()
    #     context = Container()
    #     right = Container()
    #     used = set()
    #     vids = {}
    #     for v in self._rule.vertices:
    #         used.add(v)
    #         vids[v] = len(used)
    #         if v.left.isNull():
    #             right.vertices.append(v.right)
    #         elif v.right.isNull():
    #             left.vertices.append(v.right)
    #         elif v.left.stringLabel != v.right.stringLabel:
    #             left.vertices.append(v.left)
    #             right.vertices.append(v.right)
    #         else:
    #             context.vertices.append(v.left)
    #
    #     for e in self._rule.edges:
    #         endpoints = tuple(sorted([e.source, e.target]))
    #         used.add(endpoints)
    #         if e.left.isNull():
    #             right.edges.append(e.right)
    #         elif e.right.isNull():
    #             left.edges.append(e.left)
    #         elif e.left.stringLabel != e.right.stringLabel:
    #             left.edges.append(e.left)
    #             right.edges.append(e.right)
    #         else:
    #             context.edges.append(e.left)
    #
    #     for graphs in self.left._smiles2graphs.values():
    #         g: nx.Graph
    #         for g in graphs:
    #             for v in g.nodes():
    #                 rv = g.nodes[v]['rule_vertex']
    #                 if rv.core not in used:
    #                     used.add(rv.core)
    #                     vids[rv.core] = len(used)
    #                     context.vertices.append(rv)
    #
    #             for e in g.edges():
    #                 re = g.edges[e]['rule_edge']
    #                 endpoints = tuple(sorted([re.core.source, re.core.target]))
    #                 if endpoints not in used:
    #                     context.edges.append(re)
    #
    #     out = ['rule  [']
    #     rule_sections = (('left', left), ('context', context), ('right', right))
    #     for name, container in rule_sections:
    #         out.append(f'{name} [')
    #         for u in container.vertices:
    #             label: str = u.stringLabel
    #             out.append(f'node [ id {vids[u.core]} label "{label}" ]')
    #
    #         for u in container.edges:
    #             src, tar = u.source, u.target
    #             out.append(f'edge [ source {vids[src.core]} target {vids[tar.core]} label "{u.stringLabel}" ]')
    #         out.append(']')
    #     out.append(']')
    #     return '\n'.join(out)
