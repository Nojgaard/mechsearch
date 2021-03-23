import networkx as nx
import mod
import os

def printGraph(nxgraph):
	prefix = mod.makeUniqueFilePrefix()
	fn = prefix + "statespace"
	A = nx.nx_agraph.to_agraph(nxgraph)
	with open(fn + ".dot", "w") as f:
		f.write(str(A))
	os.system(f"dot -Tpdf {fn}.dot > {fn}.pdf")

	with open(f"{fn}.tex", "w") as f:
		f.write(r"\begin{center}" + "\n")
		f.write(r"\includegraphics[width=\textwidth]{./" + fn + ".pdf}" + "\n")
		f.write(r"\end{center}" + "\n")
	mod.post(f"summaryInput {fn}.tex")


def printPath(path, graph, printDerivations=False, edgeLabels=None):
	edges = [(path[i - 1], path[i]) for i in range(1, len(path))]
	subgraph = graph.edge_subgraph(edges)
	if edgeLabels:
		for i in range(1, len(path)):
			v, w = path[i - 1], path[i]
			graph.edges[v, w]["label"] = edgeLabels(v, w, graph)

	printGraph(subgraph)

	if printDerivations:
		for i in range(1, len(path)):
			v, w = path[i - 1], path[i]
			graph.edges[v, w]["dgEdge"].print()

