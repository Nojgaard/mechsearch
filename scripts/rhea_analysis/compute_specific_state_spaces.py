from data.rhea.db import RheaDB
from mechsearch.grammar import Grammar
from mechsearch.state_space import StateSpace, Path
from mechsearch.graph import Rule
import mechsearch.explore as explore
import mechsearch.enzyme_planner as enzyme_planner
import scripts.rhea_analysis.util as util
import mod
from typing import List
import resource


def load_amino_map():
    grammar_aminos = Grammar()
    grammar_aminos.load_file("data/amino_acids.json")
    return {graph.name: graph.graph for graph in grammar_aminos.graphs}


def rhea_56832():
    rhea_db = RheaDB()
    reaction = rhea_db.get_reaction("RHEA:56832")
    amino_map = load_amino_map()
    aminos = [amino_map["Cysteine"],
              amino_map["Deprotonated Cysteine"]]
    grammar = util.load_rules()
    grammar.append_initial(reaction.reactants + aminos)
    grammar.append_target(reaction.products + aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 20, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


def rhea_3247():
    fmn = mod.smiles("N=2C(=O)NC(=O)C3=Nc1cc(C)c(C)cc1N(C=23)CC(O)C(O)C(O)COP(=O)(O)O", "FMN")
    l_tyro = mod.smiles("[NH3+][C@@H](Cc1ccc(O)cc1)C([O-])=O", "L-tyrosine")
    i_l_tyro = mod.smiles("[NH3+][C@@H](Cc1cc(I)c([O-])c(I)c1)C([O-])=O", "3,5-diiodo-L-tyrosine")
    proton = mod.smiles("[H+]", "proton")
    iodide = mod.smiles(" [I-]", "iodide")


def rhea_21144():
    reactants = [
        mod.smiles("[H][C@]1([C@@H](C)Nc2ccc(C[C@H](O)[C@H](O)[C@H](O)CO[C@H]3O[C@H](COP([O-])(=O)O[C@@H](CCC([O-])=O)C([O-])=O)[C@@H](O)[C@H]3O)cc2)[C@H](C)Nc2nc(N)[nH]c(=O)c2N1C", name="5-methyl-5,6,7,8-tetrahydromethanopterin"),
        mod.smiles("OC[C@@H](O)[C@@H](O)[C@@H](O)Cn1c2cc(O)ccc2cc2c1nc(=O)[n-]c2=O", name="F420"),
        mod.smiles("[H+]", "proton")
    ]
    products = [
        mod.smiles("[H][C@]12[C@H](C)Nc3nc(N)[nH]c(=O)c3N1CN([C@@H]2C)c1ccc(C[C@H](O)[C@H](O)[C@H](O)CO[C@H]2O[C@H](COP([O-])(=O)O[C@@H](CCC([O-])=O)C([O-])=O)[C@@H](O)[C@H]2O)cc1", name=" 5,10-methylenetetrahydromethanopterin "),
        mod.smiles("OC[C@@H](O)[C@@H](O)[C@@H](O)Cn1c2cc(O)ccc2cc2c1nc(=O)[nH]c2=O", "reduced F420")
    ]
    grammar = util.load_rules()
    grammar.append_initial(reactants)
    grammar.append_target(products)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 20, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)



def rhea_14525():
    water = mod.smiles("O", "water")
    hydronium = mod.smiles("[OH3+]", "hydronium")
    ascorbic_acid = mod.smiles("C(C(C1C(=C(C(=O)O1)O)O)O)O", "ascorbic acid")
    dehydroascorbic_acid = mod.smiles("O=C1C(=O)C(=O)O[C@@H]1[C@@H](O)CO", "dehydroascorbic acid")
    reactants = [
        mod.smiles("[H][C@@]1(Cc2c[nH]c3cccc(CC=C(C)C)c23)NC(=O)\C(C1=O)=C(\C)[O-]", name="B-cyclopiazonate"),
        ascorbic_acid, ascorbic_acid
    ]
    products = [
        mod.smiles("[H][C@@]12N(C(=O)\C(C1=O)=C(\C)[O-])C(C)(C)[C@]1([H])Cc3cccc4[nH]cc(c34)[C@]21[H]", name="A-cyclopiazonate"),
        dehydroascorbic_acid, dehydroascorbic_acid
    ]
    grammar = util.load_rules()
    amino_map = load_amino_map()
    leu = amino_map["Leucine"]
    lys = amino_map["Lysine"]
    ser = amino_map["Serine"]
    tyr = amino_map["Deprotonated Tyrosine"]
    dhis = amino_map["Histidine-delta"]
    ghis = amino_map["Histidine-epsilon"]
    present_aminos = [leu, lys, ser, tyr, dhis, ghis]
    grammar.append_initial(reactants + present_aminos)
    grammar.append_target(products + present_aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 10, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


def rhea_17041():
    water = mod.smiles("O", "water")
    proton = mod.smiles("[H+]", "proton")
    ascorbic_acid = mod.smiles("C(C(C1C(=C(C(=O)O1)O)O)O)O", "ascorbic acid")
    dehydroascorbic_acid = mod.smiles("O=C1C(=O)C(=O)O[C@@H]1[C@@H](O)CO", "dehydroascorbic acid")
    reactants = [
        mod.smiles("Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP([O-])(=O)OS([O-])(=O)=O)[C@@H](O)[C@H]1O", name="adenosine 5'-phosphosulfate"),
        water
    ]
    products = [
        mod.smiles("Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP([O-])([O-])=O)[C@@H](O)[C@H]1O", name="AMP"),
        mod.smiles("[O-]S([O-])(=O)=O", "sulfate"),
        proton, proton
    ]
    #rhea_db = RheaDB()
    #reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEA:17041")
    grammar = util.load_rules()
    amino_map = load_amino_map()
    #present_aminos = list(amino_map.values())
    glu = amino_map["Deprotonated Glutamate"]
    cys = amino_map["Deprotonated Cysteine"]
    arg = amino_map["Protonated Arginine"]
    gln = amino_map["Glutamine"]
    his = amino_map["Protonated Histidine-epsilon"]
    met = amino_map["Methionine"]
    tyr = amino_map["Deprotonated Tyrosine"]
    present_aminos = [cys, glu, glu, arg, arg, arg, arg, arg]
    present_aminos.extend([gln, his, met, tyr])
    grammar.append_initial(reactants + present_aminos)
    grammar.append_target(products + present_aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 10, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


def rhea_13173():
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEA:13173")
    grammar = util.load_rules()
    amino_map = load_amino_map()
    arg = amino_map["Protonated Arginine"]
    parg = amino_map["Arginine"]
    g_his = amino_map["Histidine-delta"]
    d_his = amino_map["Histidine-epsilon"]

    pg_his = amino_map["Protonated Histidine-epsilon"]
    pd_his = amino_map["Protonated Histidine-delta"]
    present_aminos = [arg, parg, pg_his, pd_his, g_his, d_his]
    grammar.append_initial(reaction.reactants + present_aminos)
    grammar.append_target(reaction.products + present_aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 8, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


def rhea_34427():
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEA:34427")
    grammar = util.load_rules()
    amino_map = load_amino_map()
    present_aminos = list(amino_map.values())
    grammar.append_initial(reaction.reactants + present_aminos)
    grammar.append_target(reaction.products + present_aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 5, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


def rhea_13569():
    """
    The state space for this rhea reaction uses more than 3 minutes to compute
    :return:
    """
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEA:13569")
    grammar = util.load_rules() + util.reaction2grammar(reaction)
    amino_map = load_amino_map()
    # glu = amino_map["Histidine-delta"]
    # grammar.append_initial([glu])
    # grammar.append_target([glu])
    # state_space = StateSpace(grammar)
    # explore.bidirectional_bfs(state_space, 6, verbose=True)
    # state_space.freeze()

    state_space = enzyme_planner.compute_state_space(grammar, list(amino_map.values()), max_depth=6, max_used_aminos=1,
                                                     verbose=True)
    print(state_space)
    #16085
    #RHEA:16773: 33k verts
    #18021 32k


def rhea_bfs_with_glu(rhea_id: str, k=6):
    """
    The state space for this rhea reaction uses more than 3 minutes to compute
    :return:
    """
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction(rhea_id)
    grammar = util.load_rules() + util.reaction2grammar(reaction)
    amino_map = load_amino_map()
    glu = amino_map["Glutamate"]
    grammar.append_initial([glu])
    grammar.append_target([glu])
    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, k, verbose=True)
    state_space.freeze()
    print(state_space)
    print("MEM USAGE:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1000,"MB")
    print("AVG VERTS: ", sum(v.graph.numVertices for v in state_space.derivation_graph.vertices)/state_space.derivation_graph.numVertices)

def rhea_28158():
    """
    The state space for this rhea reaction uses more than 3 minutes to compute
    :return:
    """
    rhea_db = RheaDB()
    reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEA:28158")
    grammar = util.load_rules() + util.reaction2grammar(reaction)
    amino_map = load_amino_map()
    glu = amino_map["Glutamate"]
    grammar.append_initial([glu])
    grammar.append_target([glu])
    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 6, verbose=True)
    state_space.freeze()


def count_rules():
    grammar = util.load_rules()
    metals = util.metal_atomic_symbols()
    rule: Rule
    valid_rules = []
    for rule in grammar.rules:
        valid_rules.append(rule)
        for v in rule.rule.vertices:
            if any(v.left.stringLabel.startswith(m) for m in metals):
                valid_rules.pop()
                break
    print(f"ALL  RULES: {len(grammar.rules)}")
    print(f"NO METAL RULES: {len(valid_rules)}")



def main():
    #rhea_db = RheaDB()
    #reaction: RheaDB.Reaction = rhea_db.get_reaction("RHEAID:43384")
    reactants = [
        mod.smiles("Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP([O-])(=O)OP([O-])(=O)OP([O-])([O-])=O)[C@@H](O)[C@H]1O", name="ATP"),
        mod.smiles("O=C(*)[C@@H](N*)CCCNC(=[NH2+])N", name="L-arginine residue")
    ]
    products = [
        mod.smiles("Nc1ncnc2n(cnc12)[C@@H]1O[C@H](COP([O-])(=O)OP([O-])([O-])=O)[C@@H](O)[C@H]1O", name="ADP"),
        mod.smiles("[H+]", name="proton"),
        mod.smiles("[O-]P([O-])(=O)NC(=[NH2+])NCCC[C@H](N-*)C(-*)=O", name="N-phospho-L-arginine residue")
    ]
    grammar = util.load_rules()
    amino_map = load_amino_map()
    glu = amino_map["Deprotonated Glutamate"]
    cys = amino_map["Deprotonated Cysteine"]
    arg = amino_map["Protonated Arginine"]
    gln = amino_map["Glutamine"]
    his = amino_map["Protonated G-Histidine"]
    met = amino_map["Methionine"]
    tyr = amino_map["Deprotonated Tyrosine"]
    present_aminos = [cys, glu, glu, arg, arg, arg, arg, arg]
    present_aminos.extend([gln, his, met, tyr])
    grammar.append_initial(reactants + present_aminos)
    grammar.append_target(products + present_aminos)

    state_space = StateSpace(grammar)
    explore.bidirectional_bfs(state_space, 10, verbose=True)
    state_space.freeze()

    for path in explore.shortest_simple_paths(state_space, algorithm="bidirectional_dijkstra"):
        print("FOUND PATH")
        path.print_causality_graph()
        break
    print(state_space)


if __name__ == "__main__":
    # main()
    # rhea_34427()
    # rhea_14525()
    # rhea_17041()
    # rhea_13173()
    # rhea_21144()
    #count_rules()
    # rhea_13569()
    # rhea_28158()
    #rhea_bfs_with_glu("RHEA:28402")
    rhea_bfs_with_glu("RHEA:16773", k=2)
    rhea_bfs_with_glu("RHEA:16773", k=4)
    rhea_bfs_with_glu("RHEA:16773", k=6)

