# Specify the present amino acids
aminos = [
    amino_acid("Serine"),
    amino_acid("Deprotonated Cysteine"),
    amino_acid("Cysteine"),
    amino_acid("Histidine-delta"),
    amino_acid("Histidine-epsilon")
]

# Build the state space of depth 6, for a given rhea reaction ID
state_space = build_state_space("RHEA:12024", aminos, k=6)

# Probe the structure of the state space.
# DG refers to the vertices and edges in the underlying reaction network
# EXPANDED refers to the number of states that has been probed
print()
print("State Space")
state_space.print_info()

# Compute the relevant state space
relevant_state_space = build_relevant_state_space(state_space)

# Probe the structure of the relevant state space.
print()
print("Relevant State Space")
relevant_state_space.print_info()

# rst-name: State Space Construction
# rst: This is a description
