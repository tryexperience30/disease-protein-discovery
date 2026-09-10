"""Live predictions using existing vectorized methods. No Streamlit dependency."""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from ..config import METHOD_ORDER, PROJECT_ROOT
from ..store import store

import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from predict_disease_proteins import (  # noqa: E402
    diamond_vec,
    matrix_completion_predict_vec,
    neighborhood_scoring_vec,
    neural_embedding_predict_vec,
    rwr_vec,
)


def _predict_dataframe(disease_id: str) -> pd.DataFrame:
    engine = store.get_engine()
    nodes_list = engine["nodes_list"]
    node_to_idx = engine["node_to_idx"]
    n_nodes = engine["n_nodes"]
    A = engine["A"]

    all_disease_genes = store.disease_genes[disease_id]
    seed_genes_in_ppi = [g for g in all_disease_genes if g in node_to_idx]
    if not seed_genes_in_ppi:
        return pd.DataFrame()

    seed_idx = np.array([node_to_idx[g] for g in seed_genes_in_ppi])
    seed_mask = np.zeros(n_nodes, dtype=bool)
    seed_mask[seed_idx] = True

    scores = {
        "Neighborhood": neighborhood_scoring_vec(A, seed_mask, engine["degrees"]),
        "Random Walk": rwr_vec(engine["W_T"], seed_mask),
        "DIAMOnD": diamond_vec(A, seed_mask, n_nodes, engine["degrees_int"], max_added=100),
        "Neural Embeddings": neural_embedding_predict_vec(engine["X_scaled"], seed_mask),
    }
    target_col = engine["disease_to_col"].get(disease_id)
    if target_col is not None:
        scores["Matrix Completion"] = matrix_completion_predict_vec(
            engine["W_nmf"], engine["H_nmf"], target_col, seed_mask
        )
    else:
        scores["Matrix Completion"] = np.zeros(n_nodes)
        scores["Matrix Completion"][seed_mask] = np.inf

    rows = []
    for i, gene_id in enumerate(nodes_list):
        if seed_mask[i]:
            continue
        row = {"Gene ID": int(gene_id)}
        for method in METHOD_ORDER:
            row[method] = float(scores[method][i])
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for method in METHOD_ORDER:
        col = df[method]
        rng = col.max() - col.min()
        df[f"{method}_norm"] = (col - col.min()) / rng if rng > 0 else 0.0

    norm_cols = [f"{m}_norm" for m in METHOD_ORDER]
    df["Combined Score"] = df[norm_cols].mean(axis=1)
    df.drop(columns=norm_cols, inplace=True)
    df["Known Disease Protein"] = False
    df = df.sort_values("Combined Score", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    return df


@lru_cache(maxsize=64)
def predict_for_disease(disease_id: str) -> pd.DataFrame:
    store.load()
    return _predict_dataframe(disease_id)


def clear_prediction_cache() -> None:
    predict_for_disease.cache_clear()
