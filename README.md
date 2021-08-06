# MechSearch

A python package prototype for the exploration of enzymatic mechanisms.
The code is published as part of the supplementary material to the submitted paper
"Graph Transformation for Enzymatic Mechanisms".

## Demo
We provide a demo version of our approach online which can be found at
[https://cheminf.imada.sdu.dk/mechsearch](https://cheminf.imada.sdu.dk/mechsearch/).

## Dependencies
MechSearch depends on [NetworkX](https://networkx.org/) and a custom version of
[MØD](https://cheminf.imada.sdu.dk/mod/) which can be found
[here](https://github.com/jakobandersen/mod/tree/archive/ECCB-21).

The dependencies can be installed as conda packages using the following command:

```
conda create -n mechsearch -c jakobandersen/label/ECCB-21 -c jakobandersen -c conda-forge networkx mod=0.12.0.19
conda activate mechsearch
```

## Docker

Additionally, a docker image of the custom version of MØD is available:

```
docker pull jakobandersen/mod:ECCB-21
```

## Usage
To test if the dependencies were installed correctly a small example
is provided in the file `scripts/square.py`. Said script also serves
as a simple example to see how state spaces are created and
pathways enumerated. To run the script from the root folder type:
```
mod -f scripts/square.py
```
A summary file will be located at `summary/summary.pdf`.

The state spaces of RHEA reactions that were analysed in
the submitted paper can be constructed by running the following command:
```
mod -f scripts/rhea_analysis/compute_state_spaces.py
```
The state spaces will by default be stored in the folders
`state_spaces_fixed_amino` and `state_spaces_1_amino`.

To generate pathways of a given set of state spaces, we run the
following command:
```
mod -f scripts/rhea_analysis/print_paths.py
```

For more information about how each script functions, please see the
docstrings located in both scripts.

# Postfilter for MechSearch

The additional `postfilter_main.py` script can be used to explore a state sapce created with the `MechSearch` package.
It allows the user to query for changes in the state space or look for interesting patterns in the state space.
The input is provided as a GML rule

Use the following command to run the script.

```shell
python postfilter_main.py -q <rule.gml> -r <RHEA ID>
```

Where `<rule.gml>` is the path to the query rule and `<RHEA ID>` is the RHEA ID of the reaction in order to access the correct state space.

Use the following commad to show all available command line options.
```shell
python postfilter_main.py --help
```