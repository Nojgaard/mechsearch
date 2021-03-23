import mod

class DynamicMarking:
	def __init__(self, initialMarking, graphDatabase, strategy):
		labelSettings = mod.LabelSettings(mod.LabelType.String, mod.LabelRelation.Isomorphism)
		self._dg = mod.DG(graphDatabase=graphDatabase, labelSettings=labelSettings)
		self._builder = self._dg.build()

		self._strategy = strategy
		self._petriNet = mod.PetriNet(self._dg)
		self._marking = mod.PetriNetMarking(self._petriNet)

		self._builder.execute(mod.addSubset(initialMarking), verbosity=0)
		self._petriNet.syncSize()
		self._marking.syncSize()
		for g, c in initialMarking.items():
			v = self.dg.findVertex(g)
			assert v
			self._marking.add(v, c)
		subset = self._marking.getNonZeroPlaces()
		self.expandNeighbourhood(subset)

	def fire(self, edge: mod.DGHyperEdge):
		subset = self._marking.getEmptyPostPlaces(edge)
		self._marking.fire(edge)
		return subset

	def backfire(self, edge: mod.DGHyperEdge):
		for v in edge.sources:
			self._marking.add(v, 1)
		for v in edge.targets:
			assert (self._marking[v] > 0)
			self._marking.remove(v, 1)

	def resetMarking(self):
		for v in self._marking.getNonZeroPlaces():
			self._marking.remove(v, self._marking[v])

	def addToMarking(self, marking):
		for g, count in marking:
			v = self._dg.findVertex(g)
			assert v
			self._marking.add(v, count)

	def enabledEdges(self):
		return self._marking.getAllEnabled()

	def freeze(self):
		self._builder = None

	@property
	def nonZeroPlaces(self):
		return {v.graph: self._marking[v] for v in self._marking.getNonZeroPlaces()}

	@property
	def dg(self):
		return self._dg

	def expandNeighbourhood(self, subset):
		subsetGraphs = list(v.graph for v in subset)
		universeGraphs = list(v.graph for v in self._marking.getNonZeroPlaces())
		self._builder.execute(
			mod.addSubset(subsetGraphs) >> mod.addUniverse(universeGraphs)
			>> self._strategy,
			verbosity=0)
		self._petriNet.syncSize()
		self._marking.syncSize()
