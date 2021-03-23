# Specify the present amino acids
aminos = [
    amino_acid("Serine"),
    amino_acid("Deprotonated Cysteine"),
    amino_acid("Cysteine"),
    amino_acid("Histidine-delta"),
    amino_acid("Histidine-epsilon")
]

# Build the relevant state space of depth 6, for a given rhea reaction ID
state_space = build_state_space("RHEA:12024", aminos, k=6)
state_space = build_relevant_state_space(state_space)

# Sample 3 mechanisms contained in the state space
mechanisms = sample_mechanisms(state_space, num_samples=3)

# Iterate the mechanisms and print them
for m in mechanisms:
    m.print_causality_graph()

# rst-name: Sampling of Mechanisms
