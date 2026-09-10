"""Shared configuration: paths, constants, color palettes, metric definitions."""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

METHOD_ORDER = [
    "Neighborhood", "Random Walk", "DIAMOnD",
    "Neural Embeddings", "Matrix Completion",
]

METHOD_COLORS = {
    "Neighborhood":      "#4C72B0",
    "Random Walk":       "#55A868",
    "DIAMOnD":           "#C44E52",
    "Neural Embeddings": "#8172B2",
    "Matrix Completion": "#CCB974",
}

ORBIT_SIZE_LABEL = {}
for _i in range(73):
    if _i <= 0:
        ORBIT_SIZE_LABEL[_i] = "2-node"
    elif _i <= 3:
        ORBIT_SIZE_LABEL[_i] = "3-node"
    elif _i <= 14:
        ORBIT_SIZE_LABEL[_i] = "4-node"
    else:
        ORBIT_SIZE_LABEL[_i] = "5-node"

METRIC_DESCRIPTIONS = {
    "Num Genes (total)": (
        "Total number of genes associated with this disease in DisGeNET."
    ),
    "Num Genes (in PPI)": (
        "Number of disease genes that have a corresponding node in the PPI network."
    ),
    "Num Components": (
        "Number of disconnected connected components in the disease pathway subgraph. "
        "Higher values indicate a more fragmented pathway."
    ),
    "Num Internal Edges": (
        "Number of PPI edges between disease-associated proteins (internal pathway edges)."
    ),
    "Size of largest pathway component": (
        "Fraction of disease proteins in the largest connected component (LCC). "
        "Range [0, 1]. Paper median: 0.21."
    ),
    "Density of pathway": (
        "Edge density = 2|E| / (|V|(|V|−1)). Range [0, 1]. "
        "Paper median: 0.07. Higher means more edges among disease proteins."
    ),
    "Conductance": (
        "Fraction of edges leaving the pathway vs total: |Bd| / (|Bd| + 2|Ed|). "
        "Range [0, 1]. Paper median: 0.96. High = poorly separated from the rest."
    ),
    "Network Modularity": (
        "Newman's modularity Q for the disease-vs-rest partition. "
        "Near zero = disease proteins do not form a well-defined module."
    ),
    "Distance of Pathway Components": (
        "Average shortest-path length between disconnected pathway components "
        "in the full PPI network. Paper median: ~2.9."
    ),
    "Spatial Network Association (p-value)": (
        "Ripley's K-function p-value testing whether disease proteins cluster "
        "in the PPI network more than random. p < 0.05 = significant clustering."
    ),
}
