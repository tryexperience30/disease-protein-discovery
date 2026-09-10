"""
Disease protein prediction methods and evaluation.

Reproduces Section 4.2 of:
  "Large-scale analysis of disease pathways in the human interactome"
  Agrawal, Zitnik, Leskovec (PSB 2018)

Implements five prediction methods:
  1. Neighborhood Scoring
  2. Random Walk with Restart (network diffusion)
  3. DIAMOnD (connectivity significance)
  4. Neural Embeddings (spectral embedding + logistic regression)
  5. Matrix Completion (NMF-based)

Evaluation:
  - Disease-centric 10-fold cross-validation
  - Metrics: Recall@25, Recall@100, MRR

All methods are optimized for speed using sparse matrix operations.
"""

import sys
import os
import time
import warnings
import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import svds
from scipy.stats import hypergeom
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import NMF
from sklearn.preprocessing import StandardScaler
from collections import defaultdict

from load_data import (
    load_ppi_network,
    load_disease_associations,
    load_pathway_features,
)

warnings.filterwarnings("ignore")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════

def build_node_index(G):
    nodes = sorted(G.nodes())
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    return nodes, node_to_idx


def build_adjacency_matrix(G, node_to_idx):
    n = len(node_to_idx)
    rows, cols = [], []
    for u, v in G.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        rows.extend([i, j])
        cols.extend([j, i])
    data = np.ones(len(rows), dtype=np.float64)
    return sparse.csr_matrix((data, (rows, cols)), shape=(n, n))


# ═══════════════════════════════════════════════════════════════════════════
#  METHOD 1: Neighborhood Scoring  (vectorized)
# ═══════════════════════════════════════════════════════════════════════════

def neighborhood_scoring_vec(A, seed_mask, degrees):
    """Score = (number of seed neighbors) / degree.  All via sparse matvec."""
    seed_vec = seed_mask.astype(np.float64)
    neighbor_counts = A.dot(seed_vec)
    scores = np.divide(neighbor_counts, degrees,
                       out=np.zeros_like(neighbor_counts),
                       where=degrees > 0)
    scores[seed_mask] = np.inf
    return scores


# ═══════════════════════════════════════════════════════════════════════════
#  METHOD 2: Random Walk with Restart  (sparse)
# ═══════════════════════════════════════════════════════════════════════════

def rwr_vec(W_T, seed_mask, alpha=0.7, max_iter=50, tol=1e-6):
    """W_T = transposed row-normalized adjacency (precomputed once)."""
    n = W_T.shape[0]
    seed_idx = np.where(seed_mask)[0]
    restart = np.zeros(n)
    restart[seed_idx] = 1.0 / len(seed_idx)

    p = restart.copy()
    for _ in range(max_iter):
        p_new = alpha * W_T.dot(p) + (1 - alpha) * restart
        if np.linalg.norm(p_new - p, 1) < tol:
            break
        p = p_new

    p[seed_mask] = np.inf
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  METHOD 3: DIAMOnD  (optimized loop)
# ═══════════════════════════════════════════════════════════════════════════

def diamond_vec(A, seed_mask, n_total, degrees_int, max_added=100):
    """Returns score array. Higher = predicted earlier by DIAMOnD.

    Uses a fast connectivity significance score instead of exact
    hypergeometric p-values. The score measures how many more connections
    to the seed a node has compared to what's expected by chance:
        z = (k - expected) / std
    where expected = degree * module_size / N.
    """
    in_module = seed_mask.copy()
    module_size = int(in_module.sum())

    neighbor_counts = np.array(A.dot(in_module.astype(np.float64))).flatten()
    neighbor_counts[in_module] = 0

    scores = np.zeros(n_total, dtype=np.float64)
    degrees_f = degrees_int.astype(np.float64)

    for step in range(max_added):
        candidates = np.where((neighbor_counts > 0) & (~in_module))[0]
        if len(candidates) == 0:
            break

        k_vals = neighbor_counts[candidates]
        d_vals = degrees_f[candidates]

        p = module_size / n_total
        expected = d_vals * p
        var = d_vals * p * (1.0 - p)
        std = np.sqrt(np.maximum(var, 1e-10))
        z_scores = (k_vals - expected) / std

        best_local = np.argmax(z_scores)
        best_node = candidates[best_local]

        scores[best_node] = max_added - step
        in_module[best_node] = True
        module_size += 1

        row = A.getrow(best_node)
        neighbor_counts[row.indices] += 1
        neighbor_counts[in_module] = 0

    scores[seed_mask] = np.inf
    return scores


# ═══════════════════════════════════════════════════════════════════════════
#  METHOD 4: Spectral Embeddings + Logistic Regression
# ═══════════════════════════════════════════════════════════════════════════

def compute_spectral_embeddings(A, dimensions=64):
    """One-time SVD of normalized adjacency. Returns (n_nodes, dim) matrix."""
    n = A.shape[0]
    degrees = np.array(A.sum(axis=1)).flatten()
    degrees[degrees == 0] = 1
    D_inv_sqrt = sparse.diags(1.0 / np.sqrt(degrees))
    A_norm = D_inv_sqrt @ A @ D_inv_sqrt

    k = min(dimensions, n - 2)
    U, S, _ = svds(A_norm.astype(np.float64), k=k)

    sort_idx = np.argsort(-S)
    U = U[:, sort_idx]
    S = S[sort_idx]

    return U * np.sqrt(S)[np.newaxis, :]


def neural_embedding_predict_vec(X_scaled, seed_mask):
    """Logistic regression on pre-scaled spectral embeddings."""
    y = seed_mask.astype(int)
    if y.sum() == 0 or y.sum() == len(y):
        return np.zeros(len(y))

    clf = LogisticRegression(max_iter=300, C=1.0, solver="lbfgs",
                             random_state=42)
    clf.fit(X_scaled, y)
    probs = clf.predict_proba(X_scaled)[:, 1]
    probs[seed_mask] = np.inf
    return probs


# ═══════════════════════════════════════════════════════════════════════════
#  METHOD 5: Matrix Completion (NMF)
# ═══════════════════════════════════════════════════════════════════════════

def build_disease_gene_matrix(disease_genes, disease_ids, node_to_idx, n_nodes):
    """Build the full binary (n_nodes x n_diseases) association matrix."""
    n_diseases = len(disease_ids)
    disease_to_col = {d: j for j, d in enumerate(disease_ids)}
    R = np.zeros((n_nodes, n_diseases), dtype=np.float32)
    for did, genes in disease_genes.items():
        if did not in disease_to_col:
            continue
        col = disease_to_col[did]
        for g in genes:
            if g in node_to_idx:
                R[node_to_idx[g], col] = 1.0
    return R, disease_to_col


def precompute_nmf(R, n_components=30):
    """Pre-compute NMF ONCE on the full matrix. Returns W, H."""
    model = NMF(n_components=n_components, init="nndsvda", max_iter=100,
                random_state=42)
    W = model.fit_transform(R)
    H = model.components_
    return W, H


def matrix_completion_predict_vec(W_nmf, H_nmf, target_col, seed_mask):
    """Use pre-computed NMF factors to predict scores for a disease."""
    pred = (W_nmf @ H_nmf)[:, target_col]
    pred[seed_mask] = np.inf
    return pred


# ═══════════════════════════════════════════════════════════════════════════
#  Evaluation metrics  (vectorized)
# ═══════════════════════════════════════════════════════════════════════════

def compute_metrics(scores, seed_mask, test_mask):
    """Compute Recall@25, Recall@100, MRR from a score array."""
    non_seed = ~seed_mask
    candidate_scores = scores.copy()
    candidate_scores[seed_mask] = -np.inf

    ranking = np.argsort(-candidate_scores)

    test_indices = set(np.where(test_mask)[0])
    n_test = len(test_indices)
    if n_test == 0:
        return 0.0, 0.0, 0.0

    top25 = set(ranking[:25])
    top100 = set(ranking[:100])
    r25 = len(top25 & test_indices) / n_test
    r100 = len(top100 & test_indices) / n_test

    rank_lookup = {node_idx: rank + 1 for rank, node_idx in enumerate(ranking)}
    mrr = sum(1.0 / rank_lookup[ti] for ti in test_indices if ti in rank_lookup) / n_test

    return r25, r100, mrr


# ═══════════════════════════════════════════════════════════════════════════
#  Cross-validation for one disease
# ═══════════════════════════════════════════════════════════════════════════

def cv_one_disease(did, genes, n_nodes, node_to_idx, A, W_T, degrees,
                   degrees_int, X_scaled, W_nmf, H_nmf, disease_to_col,
                   n_folds=10, seed=42):
    """10-fold CV for one disease. Returns dict {method: {metric: value}}."""
    genes_in_ppi = [g for g in genes if g in node_to_idx]
    if len(genes_in_ppi) < n_folds:
        return None

    rng = np.random.RandomState(seed)
    rng.shuffle(genes_in_ppi)
    folds = np.array_split(genes_in_ppi, n_folds)

    methods = ["Neighborhood", "Random Walk", "DIAMOnD",
               "Neural Embeddings", "Matrix Completion"]
    accum = {m: {"R@25": [], "R@100": [], "MRR": []} for m in methods}

    target_col = disease_to_col.get(did)

    for fold_idx in range(n_folds):
        test_genes = folds[fold_idx]
        seed_genes = np.concatenate([folds[j] for j in range(n_folds) if j != fold_idx])

        if len(test_genes) == 0 or len(seed_genes) == 0:
            continue

        seed_idx = np.array([node_to_idx[g] for g in seed_genes])
        test_idx = np.array([node_to_idx[g] for g in test_genes])

        seed_mask = np.zeros(n_nodes, dtype=bool)
        seed_mask[seed_idx] = True
        test_mask = np.zeros(n_nodes, dtype=bool)
        test_mask[test_idx] = True

        # 1. Neighborhood
        sc = neighborhood_scoring_vec(A, seed_mask, degrees)
        r25, r100, mrr = compute_metrics(sc, seed_mask, test_mask)
        accum["Neighborhood"]["R@25"].append(r25)
        accum["Neighborhood"]["R@100"].append(r100)
        accum["Neighborhood"]["MRR"].append(mrr)

        # 2. Random Walk
        sc = rwr_vec(W_T, seed_mask)
        r25, r100, mrr = compute_metrics(sc, seed_mask, test_mask)
        accum["Random Walk"]["R@25"].append(r25)
        accum["Random Walk"]["R@100"].append(r100)
        accum["Random Walk"]["MRR"].append(mrr)

        # 3. DIAMOnD
        sc = diamond_vec(A, seed_mask, n_nodes, degrees_int, max_added=100)
        r25, r100, mrr = compute_metrics(sc, seed_mask, test_mask)
        accum["DIAMOnD"]["R@25"].append(r25)
        accum["DIAMOnD"]["R@100"].append(r100)
        accum["DIAMOnD"]["MRR"].append(mrr)

        # 4. Neural Embeddings
        sc = neural_embedding_predict_vec(X_scaled, seed_mask)
        r25, r100, mrr = compute_metrics(sc, seed_mask, test_mask)
        accum["Neural Embeddings"]["R@25"].append(r25)
        accum["Neural Embeddings"]["R@100"].append(r100)
        accum["Neural Embeddings"]["MRR"].append(mrr)

        # 5. Matrix Completion (uses pre-computed NMF)
        if target_col is not None and W_nmf is not None:
            sc = matrix_completion_predict_vec(W_nmf, H_nmf, target_col,
                                               seed_mask)
            r25, r100, mrr = compute_metrics(sc, seed_mask, test_mask)
        else:
            r25, r100, mrr = 0.0, 0.0, 0.0
        accum["Matrix Completion"]["R@25"].append(r25)
        accum["Matrix Completion"]["R@100"].append(r100)
        accum["Matrix Completion"]["MRR"].append(mrr)

    result = {}
    for m in methods:
        result[m] = {
            "R@25":  np.mean(accum[m]["R@25"])  if accum[m]["R@25"]  else 0.0,
            "R@100": np.mean(accum[m]["R@100"]) if accum[m]["R@100"] else 0.0,
            "MRR":   np.mean(accum[m]["MRR"])   if accum[m]["MRR"]   else 0.0,
        }
    return result


# ═══════════════════════════════════════════════════════════════════════════
#  Full evaluation pipeline
# ═══════════════════════════════════════════════════════════════════════════

def run_full_evaluation(n_diseases=None):
    log("Loading PPI network...")
    G = load_ppi_network()
    largest_cc = max(nx.connected_components(G), key=len)
    G = G.subgraph(largest_cc).copy()
    n_nodes = G.number_of_nodes()
    log(f"  Largest CC: {n_nodes:,} nodes, {G.number_of_edges():,} edges")

    nodes_list, node_to_idx = build_node_index(G)

    log("Building adjacency & transition matrices...")
    A = build_adjacency_matrix(G, node_to_idx)
    degrees = np.array(A.sum(axis=1)).flatten()
    degrees_int = degrees.astype(int)
    deg_safe = degrees.copy()
    deg_safe[deg_safe == 0] = 1
    D_inv = sparse.diags(1.0 / deg_safe)
    W = D_inv @ A
    W_T = W.T.tocsr()

    log("Computing spectral embeddings...")
    t0 = time.time()
    X_emb = compute_spectral_embeddings(A, dimensions=64)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_emb)
    log(f"  Embeddings ready: {X_emb.shape} in {time.time()-t0:.1f}s")

    log("Loading disease associations...")
    disease_genes, disease_names = load_disease_associations()
    disease_ids = sorted(disease_genes.keys())

    log("Building disease-gene matrix & pre-computing NMF...")
    t0 = time.time()
    R_base, disease_to_col = build_disease_gene_matrix(
        disease_genes, disease_ids, node_to_idx, n_nodes)
    W_nmf, H_nmf = precompute_nmf(R_base, n_components=30)
    log(f"  NMF factorization done in {time.time()-t0:.1f}s")

    eval_diseases = disease_ids
    if n_diseases is not None:
        eval_diseases = eval_diseases[:n_diseases]

    total = len(eval_diseases)
    log(f"\nEvaluating {total} diseases x 5 methods x 10-fold CV")
    log("-" * 70)

    all_results = []
    for idx, did in enumerate(eval_diseases):
        t0 = time.time()
        genes = disease_genes[did]
        name = disease_names[did]

        result = cv_one_disease(
            did, genes, n_nodes, node_to_idx, A, W_T, degrees, degrees_int,
            X_scaled, W_nmf, H_nmf, disease_to_col
        )
        if result is None:
            continue

        for method, metrics in result.items():
            all_results.append({
                "Disease ID": did,
                "Disease Name": name,
                "Method": method,
                "Recall@25": metrics["R@25"],
                "Recall@100": metrics["R@100"],
                "MRR": metrics["MRR"],
            })

        elapsed = time.time() - t0
        if (idx + 1) % 10 == 0 or (idx + 1) == total or (idx + 1) <= 3:
            rw = result["Random Walk"]["R@100"]
            ne = result["Neural Embeddings"]["R@100"]
            log(f"  [{idx+1:3d}/{total}] {name[:40]:<40s} "
                f"RW={rw:.3f} NE={ne:.3f} ({elapsed:.1f}s)")

    return pd.DataFrame(all_results)


# ═══════════════════════════════════════════════════════════════════════════
#  Summary & plots
# ═══════════════════════════════════════════════════════════════════════════

def print_summary(results_df):
    paper = {
        "Neighborhood":      {"MRR": 0.029, "R@100": 0.242},
        "Random Walk":       {"MRR": 0.061, "R@100": 0.356},
        "DIAMOnD":           {"MRR": None,  "R@100": 0.300},
        "Neural Embeddings": {"MRR": 0.050, "R@100": 0.300},
        "Matrix Completion": {"MRR": None,  "R@100": None},
    }

    log("\n" + "=" * 75)
    log("Overall Performance (mean across all evaluated diseases)")
    log("=" * 75)
    log(f"\n{'Method':<22} {'R@25':>8} {'R@100':>8} {'MRR':>8}  "
        f"{'Paper R@100':>12} {'Paper MRR':>10}")
    log("-" * 75)

    for m in ["Neighborhood", "Random Walk", "DIAMOnD",
              "Neural Embeddings", "Matrix Completion"]:
        sub = results_df[results_df["Method"] == m]
        if len(sub) == 0:
            continue
        r25, r100, mrr = sub["Recall@25"].mean(), sub["Recall@100"].mean(), sub["MRR"].mean()
        pr = paper.get(m, {})
        pr100 = f"{pr['R@100']:.3f}" if pr.get("R@100") else "—"
        pmrr  = f"{pr['MRR']:.3f}" if pr.get("MRR") else "—"
        log(f"{m:<22} {r25:>8.3f} {r100:>8.3f} {mrr:>8.4f}  {pr100:>12} {pmrr:>10}")


def generate_plots(results_df):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    features_df = load_pathway_features()
    methods = ["Neighborhood", "Random Walk", "DIAMOnD",
               "Neural Embeddings", "Matrix Completion"]
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974"]
    struct = [
        ("Size of largest pathway component", "LCC Size"),
        ("Density of pathway", "Density"),
        ("Distance of Pathway Components", "Component Distance"),
    ]

    # Figure 5 style: 3 rows × 5 cols
    fig, axes = plt.subplots(3, 5, figsize=(22, 12), squeeze=False)
    fig.suptitle("Prediction Quality vs PPI Connectivity (Fig. 5 reproduction)",
                 fontsize=14, fontweight="bold")

    for ci, method in enumerate(methods):
        mdf = results_df[results_df["Method"] == method].set_index("Disease ID")
        for ri, (fc, fl) in enumerate(struct):
            ax = axes[ri, ci]
            common = mdf.index.intersection(features_df.index)
            x = features_df.loc[common, fc].astype(float)
            y = mdf.loc[common, "Recall@100"].astype(float)
            valid = x.notna() & y.notna()
            x, y = x[valid], y[valid]
            if len(x) < 5:
                continue
            ax.scatter(x, y, alpha=0.3, s=10, color=colors[ci])
            rho = np.corrcoef(x, y)[0, 1]
            z = np.polyfit(x, y, 1)
            xl = np.linspace(x.min(), x.max(), 50)
            ax.plot(xl, np.poly1d(z)(xl), color=colors[ci], lw=2, ls="--")
            ax.set_title(f"{method}\n\u03C1 = {rho:.2f}", fontsize=9)
            if ci == 0:
                ax.set_ylabel("Recall@100")
            if ri == 2:
                ax.set_xlabel(fl)

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    p1 = os.path.join(OUTPUT_DIR, "prediction_vs_structure.png")
    plt.savefig(p1, dpi=150, bbox_inches="tight")
    plt.close()
    log(f"  Saved: {p1}")

    # Bar chart
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Method Comparison", fontsize=13, fontweight="bold")
    for ai, (metric, title) in enumerate([("Recall@25", "Recall@25"),
                                           ("Recall@100", "Recall@100"),
                                           ("MRR", "MRR")]):
        vals = [results_df[results_df["Method"] == m][metric].mean()
                for m in methods]
        ax = axes[ai]
        bars = ax.bar(range(5), vals, color=colors, edgecolor="white")
        ax.set_xticks(range(5))
        ax.set_xticklabels([m.replace(" ", "\n") for m in methods], fontsize=7)
        ax.set_title(title)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.002,
                    f"{v:.3f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    p2 = os.path.join(OUTPUT_DIR, "method_comparison.png")
    plt.savefig(p2, dpi=150, bbox_inches="tight")
    plt.close()
    log(f"  Saved: {p2}")
    return p1, p2


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log("=" * 70)
    log("Disease Protein Prediction — 5 Methods x 10-Fold CV")
    log("=" * 70)

    results_df = run_full_evaluation(n_diseases=None)

    out_path = os.path.join(OUTPUT_DIR, "prediction_results.csv")
    results_df.to_csv(out_path, index=False)
    log(f"\nResults saved to: {out_path}")

    print_summary(results_df)

    log("\nGenerating plots...")
    generate_plots(results_df)

    log("\n" + "=" * 70)
    log("Done!")
    log("=" * 70)
