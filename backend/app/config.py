"""Backend configuration. Research data and models stay in the project root."""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]
CORS_ORIGIN_REGEX = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None

METHOD_ORDER = [
    "Neighborhood",
    "Random Walk",
    "DIAMOnD",
    "Neural Embeddings",
    "Matrix Completion",
]

NMF_LEAKAGE_NOTE = (
    "In the cross-validation evaluation, NMF is fitted on the full "
    "protein×disease matrix before fold splitting. This means Matrix Completion "
    "has access to test-fold disease-protein associations during factorization, "
    "which inflates its reported CV metrics relative to the other four methods. "
    "This does not affect live predictions (where all known associations are "
    "legitimately available) or the other four methods (which use only "
    "train-fold seed proteins)."
)

RESEARCH_DISCLAIMER = (
    "Research tool for computational disease–protein association analysis. "
    "Predictions are computationally prioritized candidate associations, not "
    "clinical diagnoses or experimentally validated causal relationships."
)

METRIC_META = {
    "relative_lcc": {
        "key": "relative_lcc",
        "label": "Relative LCC size",
        "source_column": "Size of largest pathway component",
        "description": (
            "Fraction of disease proteins in the largest connected component (LCC). "
            "Range [0, 1]. Paper median: 0.21."
        ),
        "interpretation": (
            "Higher values mean more disease-associated proteins sit in one connected "
            "pathway component rather than many fragments."
        ),
    },
    "density": {
        "key": "density",
        "label": "Network density",
        "source_column": "Density of pathway",
        "description": (
            "Edge density = 2|E| / (|V|(|V|−1)). Range [0, 1]. Paper median: 0.07."
        ),
        "interpretation": (
            "Higher density means more PPI edges among disease-associated proteins."
        ),
    },
    "component_distance": {
        "key": "component_distance",
        "label": "Distance between pathway components",
        "source_column": "Distance of Pathway Components",
        "description": (
            "Average shortest-path length between disconnected pathway components "
            "in the full PPI network. Paper median: ~2.9."
        ),
        "interpretation": (
            "Lower distances mean disconnected pathway pieces sit closer together "
            "in the interactome. Undefined when the pathway is a single component."
        ),
    },
    "conductance": {
        "key": "conductance",
        "label": "Conductance",
        "source_column": "Conductance",
        "description": (
            "Fraction of edges leaving the pathway vs total: |Bd| / (|Bd| + 2|Ed|). "
            "Range [0, 1]. Paper median: 0.96."
        ),
        "interpretation": (
            "High conductance means the pathway is poorly separated from the rest "
            "of the PPI network."
        ),
    },
    "spatial_association": {
        "key": "spatial_association",
        "label": "Spatial network association (Ripley's K)",
        "source_column": "Spatial Network Association",
        "description": (
            "Ripley's K-function p-value testing whether disease proteins cluster "
            "in the PPI network more than random. p < 0.05 = significant clustering. "
            "Taken from the paper's pre-computed pathway features."
        ),
        "interpretation": (
            "Smaller p-values indicate disease proteins occupy more clustered "
            "positions in the interactome than expected by chance."
        ),
    },
    "modularity": {
        "key": "modularity",
        "label": "Modularity",
        "source_column": "Network Modularity",
        "description": (
            "Newman's modularity Q for the disease-vs-rest partition."
        ),
        "interpretation": (
            "Values near zero mean disease proteins do not form a well-defined "
            "module relative to the rest of the network."
        ),
    },
}

PROXY_FEATURE_LABELS = [
    "degree",
    "clustering_coefficient",
    "triangles",
    "average_neighbor_degree",
    "degree_centrality",
    "neighbor_degree_min",
    "neighbor_degree_max",
    "neighbor_degree_mean",
    "neighbor_degree_std",
    "two_paths",
    "square_count_approx",
    "local_bridge_score",
]
