"""Live single-disease prediction using existing research functions.

Runs all five methods for one disease and returns per-protein ranked scores.
Uses the optimized vectorized implementations from predict_disease_proteins.py.
Heavy setup (network, embeddings, NMF) is cached; per-disease prediction ~2s.
"""

import sys
import numpy as np
import pandas as pd
import networkx as nx
import streamlit as st
from scipy import sparse
from sklearn.preprocessing import StandardScaler

from app.config import PROJECT_ROOT, METHOD_ORDER
from app.cache import get_ppi_network, get_disease_associations

sys.path.insert(0, PROJECT_ROOT)
from predict_disease_proteins import (
    build_node_index,
    build_adjacency_matrix,
    compute_spectral_embeddings,
    neighborhood_scoring_vec,
    rwr_vec,
    diamond_vec,
    neural_embedding_predict_vec,
    precompute_nmf,
    build_disease_gene_matrix,
    matrix_completion_predict_vec,
)


@st.cache_resource(show_spinner="Preparing prediction engine (one-time)…")
def _get_prediction_engine():
    """Pre-compute all heavy objects once: adjacency, transition matrix,
    spectral embeddings, NMF factors."""
    G = get_ppi_network()
    nodes_list, node_to_idx = build_node_index(G)
    n_nodes = len(nodes_list)

    A = build_adjacency_matrix(G, node_to_idx)
    degrees = np.array(A.sum(axis=1)).flatten()
    degrees_int = degrees.astype(int)

    deg_safe = degrees.copy()
    deg_safe[deg_safe == 0] = 1
    D_inv = sparse.diags(1.0 / deg_safe)
    W_T = (D_inv @ A).T.tocsr()

    X_emb = compute_spectral_embeddings(A, dimensions=64)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_emb)

    disease_genes, _ = get_disease_associations()
    disease_ids = sorted(disease_genes.keys())
    R_base, disease_to_col = build_disease_gene_matrix(
        disease_genes, disease_ids, node_to_idx, n_nodes
    )
    W_nmf, H_nmf = precompute_nmf(R_base, n_components=30)

    return {
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


def predict_for_disease(disease_id):
    """Run all five prediction methods for a single disease.

    Returns
    -------
    pd.DataFrame with columns:
        Gene ID, Neighborhood, Random Walk, DIAMOnD,
        Neural Embeddings, Matrix Completion, Combined Score,
        Known Disease Protein
    sorted by Combined Score descending.
    """
    engine = _get_prediction_engine()
    disease_genes, _ = get_disease_associations()

    G = engine["G"]
    nodes_list = engine["nodes_list"]
    node_to_idx = engine["node_to_idx"]
    n_nodes = engine["n_nodes"]
    A = engine["A"]

    all_disease_genes = disease_genes[disease_id]
    seed_genes_in_ppi = [g for g in all_disease_genes if g in node_to_idx]

    if len(seed_genes_in_ppi) == 0:
        return pd.DataFrame()

    seed_idx = np.array([node_to_idx[g] for g in seed_genes_in_ppi])
    seed_mask = np.zeros(n_nodes, dtype=bool)
    seed_mask[seed_idx] = True

    scores = {}

    scores["Neighborhood"] = neighborhood_scoring_vec(
        A, seed_mask, engine["degrees"]
    )
    scores["Random Walk"] = rwr_vec(engine["W_T"], seed_mask)
    scores["DIAMOnD"] = diamond_vec(
        A, seed_mask, n_nodes, engine["degrees_int"], max_added=100
    )
    scores["Neural Embeddings"] = neural_embedding_predict_vec(
        engine["X_scaled"], seed_mask
    )

    target_col = engine["disease_to_col"].get(disease_id)
    if target_col is not None:
        scores["Matrix Completion"] = matrix_completion_predict_vec(
            engine["W_nmf"], engine["H_nmf"], target_col, seed_mask
        )
    else:
        scores["Matrix Completion"] = np.zeros(n_nodes)
        scores["Matrix Completion"][seed_mask] = np.inf

    rows = []
    known_set = set(seed_genes_in_ppi)
    for i, gene_id in enumerate(nodes_list):
        if seed_mask[i]:
            continue
        row = {"Gene ID": gene_id}
        for method in METHOD_ORDER:
            row[method] = float(scores[method][i])
        rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    for method in METHOD_ORDER:
        col = df[method]
        rng = col.max() - col.min()
        if rng > 0:
            df[f"{method}_norm"] = (col - col.min()) / rng
        else:
            df[f"{method}_norm"] = 0.0

    norm_cols = [f"{m}_norm" for m in METHOD_ORDER]
    df["Combined Score"] = df[norm_cols].mean(axis=1)
    df.drop(columns=norm_cols, inplace=True)

    df["Known Disease Protein"] = False
    df = df.sort_values("Combined Score", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"

    return df


def get_protein_network_stats(gene_id):
    """Return basic network stats for a protein."""
    G = get_ppi_network()
    if gene_id not in G:
        return None
    return {
        "Gene ID": gene_id,
        "Degree": G.degree(gene_id),
        "Neighbors": list(G.neighbors(gene_id))[:50],
        "Clustering Coefficient": nx.clustering(G, gene_id),
        "Triangles": nx.triangles(G, gene_id),
    }
