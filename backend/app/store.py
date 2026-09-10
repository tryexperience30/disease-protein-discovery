"""In-memory research data store. Loads existing CSVs and the PPI graph once.

Does not retrain models or rewrite scientific definitions.
"""

from __future__ import annotations

import sys
from typing import Any, Optional

import networkx as nx
import pandas as pd

from .config import METHOD_ORDER, PROJECT_ROOT, RESULTS_DIR

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from build_pathways import build_disease_pathway  # noqa: E402
from load_data import (  # noqa: E402
    load_disease_associations,
    load_disease_classes,
    load_disease_motifs,
    load_pathway_features,
    load_ppi_network,
)


class DataStore:
    """Process-wide cache of validated research artifacts."""

    def __init__(self) -> None:
        self.G: Optional[nx.Graph] = None
        self.disease_genes: dict[str, set[int]] = {}
        self.disease_names: dict[str, str] = {}
        self.disease_classes: dict[str, str] = {}
        self.computed_metrics: Optional[pd.DataFrame] = None
        self.paper_features: Optional[pd.DataFrame] = None
        self.motifs: Optional[pd.DataFrame] = None
        self.prediction_results: Optional[pd.DataFrame] = None
        self.augmented_results: Optional[pd.DataFrame] = None
        self.protein_to_diseases: dict[int, list[str]] = {}
        self._loaded = False
        self._engine: Optional[dict[str, Any]] = None

    def load(self) -> None:
        if self._loaded:
            return

        G = load_ppi_network()
        largest_cc = max(nx.connected_components(G), key=len)
        self.G = G.subgraph(largest_cc).copy()

        self.disease_genes, self.disease_names = load_disease_associations()
        self.disease_classes = load_disease_classes()
        self.paper_features = load_pathway_features()
        self.motifs = load_disease_motifs()
        self.computed_metrics = pd.read_csv(
            RESULTS_DIR / "computed_pathway_metrics.csv", index_col="Disease ID"
        )
        self.prediction_results = pd.read_csv(RESULTS_DIR / "prediction_results.csv")
        self.augmented_results = pd.read_csv(RESULTS_DIR / "augmented_results.csv")

        protein_to_diseases: dict[int, list[str]] = {}
        for did, genes in self.disease_genes.items():
            for gid in genes:
                protein_to_diseases.setdefault(gid, []).append(did)
        self.protein_to_diseases = protein_to_diseases
        self._loaded = True

    def require_graph(self) -> nx.Graph:
        self.load()
        assert self.G is not None
        return self.G

    def disease_exists(self, disease_id: str) -> bool:
        self.load()
        return disease_id in self.disease_names

    def protein_in_ppi(self, gene_id: int) -> bool:
        G = self.require_graph()
        return gene_id in G

    def pathway(self, disease_id: str):
        G = self.require_graph()
        genes = self.disease_genes[disease_id]
        return build_disease_pathway(G, genes)

    def get_engine(self) -> dict[str, Any]:
        """Lazy prediction engine using existing research functions."""
        if self._engine is not None:
            return self._engine

        from predict_disease_proteins import (
            build_adjacency_matrix,
            build_disease_gene_matrix,
            build_node_index,
            compute_spectral_embeddings,
            precompute_nmf,
        )
        from scipy import sparse
        from sklearn.preprocessing import StandardScaler

        G = self.require_graph()
        nodes_list, node_to_idx = build_node_index(G)
        n_nodes = len(nodes_list)
        A = build_adjacency_matrix(G, node_to_idx)
        import numpy as np

        degrees = np.array(A.sum(axis=1)).flatten()
        degrees_int = degrees.astype(int)
        deg_safe = degrees.copy()
        deg_safe[deg_safe == 0] = 1
        D_inv = sparse.diags(1.0 / deg_safe)
        W_T = (D_inv @ A).T.tocsr()
        X_emb = compute_spectral_embeddings(A, dimensions=64)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_emb)
        disease_ids = sorted(self.disease_genes.keys())
        R_base, disease_to_col = build_disease_gene_matrix(
            self.disease_genes, disease_ids, node_to_idx, n_nodes
        )
        W_nmf, H_nmf = precompute_nmf(R_base, n_components=30)
        self._engine = {
            "G": G,
            "nodes_list": nodes_list,
            "node_to_idx": node_to_idx,
            "n_nodes": n_nodes,
            "A": A,
            "degrees": degrees,
            "degrees_int": degrees_int,
            "W_T": W_T,
            "X_scaled": X_scaled,
            "W_nmf": W_nmf,
            "H_nmf": H_nmf,
            "disease_to_col": disease_to_col,
        }
        return self._engine


store = DataStore()
METHOD_ORDER  # re-export convenience
