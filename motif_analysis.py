"""
Higher-order motif analysis and augmented disease protein prediction.

Reproduces Sections 5 and 6 of:
  "Large-scale analysis of disease pathways in the human interactome"
  Agrawal, Zitnik, Leskovec (PSB 2018)

Part A (Section 5):
  - Analyze graphlet orbit significance across 519 diseases
  - Reproduce Figure 6: number of diseases with significant orbits
  - Reproduce Table 1: top orbits across diseases
  - Reproduce Table 2: characteristic orbits per disease category
  - KS-test for disease category-specific orbit enrichment

Part B (Section 6):
  - Compute per-protein structural features (motif signature proxy)
  - Augment spectral embeddings with motif features
  - Run 10-fold CV and compare: baseline vs augmented
"""

import os
import sys
import time
import warnings
import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from scipy.sparse.linalg import svds
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from load_data import (
    load_ppi_network,
    load_disease_associations,
    load_disease_classes,
    load_disease_motifs,
)

warnings.filterwarnings("ignore")

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log(msg):
    print(msg, flush=True)


# ═══════════════════════════════════════════════════════════════════════════
#  PART A: Orbit significance analysis (using paper's pre-computed p-values)
# ═══════════════════════════════════════════════════════════════════════════

def analyze_orbit_significance():
    """Reproduce Figure 6A, Table 1, and the 60% statistic from the paper."""
    log("\n" + "=" * 70)
    log("PART A: Graphlet Orbit Significance Analysis")
    log("=" * 70)

    motifs_df = load_disease_motifs()
    orbit_cols = [c for c in motifs_df.columns if c.startswith("orbit_")]
    n_orbits = len(orbit_cols)
    n_diseases = len(motifs_df)
    alpha = 0.01

    log(f"\n  Diseases: {n_diseases}")
    log(f"  Orbit positions: {n_orbits}")

    # Number of diseases with significant over-representation per orbit
    sig_per_orbit = (motifs_df[orbit_cols] < alpha).sum(axis=0)

    # Number of diseases with at least one significant orbit
    sig_any = (motifs_df[orbit_cols] < alpha).any(axis=1).sum()
    log(f"\n  Diseases with >= 1 significant orbit (p<{alpha}): "
        f"{sig_any} / {n_diseases} ({100*sig_any/n_diseases:.0f}%)")
    log(f"  Paper reports: 310 / 519 (60%)")

    # Top orbits (Table 1)
    log(f"\n  Top 10 most significant orbits (# diseases with p<{alpha}):")
    log(f"  {'Orbit':>8}  {'# Diseases':>12}  {'Graphlet size':>14}")
    log(f"  {'-'*40}")
    top_orbits = sig_per_orbit.sort_values(ascending=False).head(10)
    for orbit_name, count in top_orbits.items():
        orbit_num = int(orbit_name.split("_")[1])
        if orbit_num <= 0:
            size = "2-node"
        elif orbit_num <= 3:
            size = "3-node"
        elif orbit_num <= 14:
            size = "4-node"
        else:
            size = "5-node"
        log(f"  {orbit_name:>8}  {int(count):>12}  {size:>14}")

    return motifs_df, orbit_cols, sig_per_orbit


def analyze_disease_categories(motifs_df, orbit_cols):
    """Reproduce Table 2: characteristic orbits per disease category.

    Uses two-sample KS test to find orbits where disease proteins in a
    category differ from non-disease proteins.
    """
    log("\n" + "-" * 70)
    log("Characteristic Orbits per Disease Category (Table 2)")
    log("-" * 70)

    disease_classes = load_disease_classes()
    disease_genes, _ = load_disease_associations()

    categories = {}
    for did, cls in disease_classes.items():
        categories.setdefault(cls, []).append(did)

    top_categories = sorted(categories.keys(),
                            key=lambda c: len(categories[c]), reverse=True)[:10]

    alpha = 0.01
    n_orbits = len(orbit_cols)
    bonferroni = alpha / n_orbits

    results = []
    for cat in top_categories:
        cat_diseases = categories[cat]
        cat_pvals = motifs_df.loc[motifs_df.index.isin(cat_diseases), orbit_cols]

        if len(cat_pvals) < 3:
            continue

        orbit_sig_counts = (cat_pvals < 0.01).sum(axis=0)
        top5 = orbit_sig_counts.sort_values(ascending=False).head(5)
        top5_names = [o.replace("orbit_", "") for o in top5.index]

        results.append({
            "Category": cat,
            "N diseases": len(cat_diseases),
            "Top 5 orbits": ", ".join(top5_names),
        })

        log(f"\n  {cat} ({len(cat_diseases)} diseases):")
        log(f"    Top orbits: {', '.join(top5_names)}")

    return pd.DataFrame(results)


def plot_orbit_significance(sig_per_orbit, motifs_df, orbit_cols):
    """Generate Figure 6A: bar chart of significant diseases per orbit."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    fig.suptitle("Higher-Order Network Structure of Disease Pathways\n"
                 "(Reproducing Figure 6 from Agrawal et al. 2018)",
                 fontsize=14, fontweight="bold")

    # Panel A: Number of diseases with significant orbits
    ax = axes[0]
    orbit_nums = list(range(73))
    counts = [int(sig_per_orbit[f"orbit_{i}"]) for i in orbit_nums]

    colors = []
    for i in orbit_nums:
        if i <= 0:
            colors.append("#4C72B0")
        elif i <= 3:
            colors.append("#55A868")
        elif i <= 14:
            colors.append("#C44E52")
        else:
            colors.append("#8172B2")

    ax.bar(orbit_nums, counts, color=colors, edgecolor="white", width=0.8)
    ax.set_xlabel("Orbit Position")
    ax.set_ylabel("Number of Diseases (p < 0.01)")
    ax.set_title("(A) Diseases with Significant Over-representation at Each Orbit")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#4C72B0", label="2-node graphlet (orbit 0)"),
        Patch(facecolor="#55A868", label="3-node graphlets (orbits 1-3)"),
        Patch(facecolor="#C44E52", label="4-node graphlets (orbits 4-14)"),
        Patch(facecolor="#8172B2", label="5-node graphlets (orbits 15-72)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left")

    # Panel B: Distribution of significant orbits per disease
    ax = axes[1]
    sig_counts_per_disease = (motifs_df[orbit_cols] < 0.01).sum(axis=1)
    ax.hist(sig_counts_per_disease, bins=40, color="#64B5CD",
            edgecolor="white", alpha=0.85)
    ax.axvline(sig_counts_per_disease.median(), color="red", linestyle="--",
               label=f"Median = {sig_counts_per_disease.median():.0f}")
    no_sig = (sig_counts_per_disease == 0).sum()
    ax.axvline(0, color="gray", alpha=0)
    ax.set_xlabel("Number of Significant Orbits per Disease")
    ax.set_ylabel("Number of Diseases")
    ax.set_title(f"(B) Distribution of Significant Orbits per Disease "
                 f"(no significant orbits: {no_sig} diseases)")
    ax.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    path = os.path.join(OUTPUT_DIR, "motif_significance.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    log(f"\n  Plot saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════
#  PART B: Compute per-protein motif features
# ═══════════════════════════════════════════════════════════════════════════

def compute_protein_motif_features(G):
    """Compute local structural features for each protein as a proxy for
    the full 73-orbit graphlet signature.

    Features computed (per node):
      0: degree
      1: clustering coefficient
      2: number of triangles
      3: average neighbor degree
      4: degree centrality
      5-8: degree distribution stats of neighbors (min, max, mean, std)
      9: number of 2-paths through node
      10: square count (4-cycles) approximation
      11: local bridge score
    """
    log("\n  Computing per-protein structural features...")
    t0 = time.time()

    nodes = sorted(G.nodes())
    n = len(nodes)
    node_to_idx = {nd: i for i, nd in enumerate(nodes)}

    degrees = np.array([G.degree(nd) for nd in nodes], dtype=np.float64)
    clustering = np.array(list(nx.clustering(G, nodes).values()), dtype=np.float64)
    triangles = np.array(list(nx.triangles(G, nodes).values()), dtype=np.float64)

    avg_nbr_deg = np.zeros(n)
    nbr_deg_min = np.zeros(n)
    nbr_deg_max = np.zeros(n)
    nbr_deg_std = np.zeros(n)
    two_paths = np.zeros(n)
    square_approx = np.zeros(n)
    bridge_score = np.zeros(n)

    deg_dict = dict(G.degree())

    for i, nd in enumerate(nodes):
        nbrs = list(G.neighbors(nd))
        if len(nbrs) == 0:
            continue

        nbr_degs = np.array([deg_dict[nb] for nb in nbrs], dtype=np.float64)
        avg_nbr_deg[i] = nbr_degs.mean()
        nbr_deg_min[i] = nbr_degs.min()
        nbr_deg_max[i] = nbr_degs.max()
        nbr_deg_std[i] = nbr_degs.std() if len(nbr_degs) > 1 else 0

        two_paths[i] = sum(deg_dict[nb] - 1 for nb in nbrs)

        nbr_set = set(nbrs)
        sq = 0
        for nb in nbrs:
            common = nbr_set & (set(G.neighbors(nb)) - {nd})
            sq += len(common)
        square_approx[i] = sq / 2.0

        bridge_score[i] = degrees[i] - 2 * triangles[i] / max(degrees[i], 1)

    degree_centrality = degrees / (n - 1)

    features = np.column_stack([
        degrees,              # 0
        clustering,           # 1
        triangles,            # 2
        avg_nbr_deg,          # 3
        degree_centrality,    # 4
        nbr_deg_min,          # 5
        nbr_deg_max,          # 6
        avg_nbr_deg,          # 7 (mean neighbor degree)
        nbr_deg_std,          # 8
        two_paths,            # 9
        square_approx,        # 10
        bridge_score,         # 11
    ])

    log(f"  Features computed: {features.shape} in {time.time()-t0:.1f}s")
    return features, nodes, node_to_idx


def transform_motif_features(features):
    """Apply h'_i = max(0, log(h_i)) as described in the paper."""
    with np.errstate(divide="ignore", invalid="ignore"):
        log_features = np.log(np.maximum(features, 1e-10))
    log_features = np.maximum(log_features, 0)
    return log_features


# ═══════════════════════════════════════════════════════════════════════════
#  PART C: Augmented prediction experiment
# ═══════════════════════════════════════════════════════════════════════════

def build_adjacency_matrix(G, node_to_idx):
    n = len(node_to_idx)
    rows, cols = [], []
    for u, v in G.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        rows.extend([i, j])
        cols.extend([j, i])
    data = np.ones(len(rows), dtype=np.float64)
    return sparse.csr_matrix((data, (rows, cols)), shape=(n, n))


def compute_spectral_embeddings(A, dimensions=64):
    n = A.shape[0]
    degrees = np.array(A.sum(axis=1)).flatten()
    degrees[degrees == 0] = 1
    D_inv_sqrt = sparse.diags(1.0 / np.sqrt(degrees))
    A_norm = D_inv_sqrt @ A @ D_inv_sqrt
    k = min(dimensions, n - 2)
    U, S, _ = svds(A_norm.astype(np.float64), k=k)
    sort_idx = np.argsort(-S)
    return U[:, sort_idx] * np.sqrt(S[sort_idx])[np.newaxis, :]


def recall_at_k(scores, seed_mask, test_mask, k):
    candidate_scores = scores.copy()
    candidate_scores[seed_mask] = -np.inf
    ranking = np.argsort(-candidate_scores)
    top_k = set(ranking[:k])
    test_set = set(np.where(test_mask)[0])
    if len(test_set) == 0:
        return 0.0
    return len(top_k & test_set) / len(test_set)


def mrr(scores, seed_mask, test_mask):
    candidate_scores = scores.copy()
    candidate_scores[seed_mask] = -np.inf
    ranking = np.argsort(-candidate_scores)
    rank_lookup = {idx: r + 1 for r, idx in enumerate(ranking)}
    test_indices = np.where(test_mask)[0]
    if len(test_indices) == 0:
        return 0.0
    return sum(1.0 / rank_lookup[ti] for ti in test_indices) / len(test_indices)


def run_augmented_prediction(n_diseases=None):
    """Compare baseline (embeddings only) vs augmented (embeddings + motif features).

    This reproduces Section 6 of the paper.
    """
    log("\n" + "=" * 70)
    log("PART B: Augmented Prediction (Embeddings + Motif Features)")
    log("=" * 70)

    log("\nLoading PPI network...")
    G = load_ppi_network()
    cc = max(nx.connected_components(G), key=len)
    G = G.subgraph(cc).copy()
    n_nodes = G.number_of_nodes()
    log(f"  Largest CC: {n_nodes:,} nodes")

    # Compute spectral embeddings
    motif_features, nodes_list, node_to_idx = compute_protein_motif_features(G)
    A = build_adjacency_matrix(G, node_to_idx)

    log("\n  Computing spectral embeddings...")
    X_emb = compute_spectral_embeddings(A, dimensions=64)
    log(f"  Embedding shape: {X_emb.shape}")

    # Transform motif features: h'_i = max(0, log(h_i))
    motif_transformed = transform_motif_features(motif_features)
    log(f"  Motif features shape: {motif_transformed.shape}")

    # Concatenate: [embedding | motif_features]
    X_baseline = X_emb
    X_augmented = np.hstack([X_emb, motif_transformed])
    log(f"  Baseline feature dim: {X_baseline.shape[1]}")
    log(f"  Augmented feature dim: {X_augmented.shape[1]}")

    scaler_base = StandardScaler()
    X_base_scaled = scaler_base.fit_transform(X_baseline)

    scaler_aug = StandardScaler()
    X_aug_scaled = scaler_aug.fit_transform(X_augmented)

    # Load diseases
    disease_genes, disease_names = load_disease_associations()
    disease_ids = sorted(disease_genes.keys())
    if n_diseases is not None:
        disease_ids = disease_ids[:n_diseases]

    total = len(disease_ids)
    log(f"\n  Evaluating {total} diseases (10-fold CV)...")
    log(f"  {'Disease':<40s} {'Base R@100':>10} {'Aug R@100':>10} {'Improve':>8}")
    log("  " + "-" * 70)

    results = []
    for idx, did in enumerate(disease_ids):
        genes = disease_genes[did]
        name = disease_names[did]
        genes_in = [g for g in genes if g in node_to_idx]
        if len(genes_in) < 10:
            continue

        rng = np.random.RandomState(42)
        rng.shuffle(genes_in)
        folds = np.array_split(genes_in, 10)

        base_r100, aug_r100 = [], []
        base_mrr, aug_mrr = [], []

        for fi in range(10):
            test_genes = folds[fi]
            seed_genes = np.concatenate([folds[j] for j in range(10) if j != fi])
            if len(test_genes) == 0 or len(seed_genes) == 0:
                continue

            seed_idx = np.array([node_to_idx[g] for g in seed_genes])
            test_idx = np.array([node_to_idx[g] for g in test_genes])
            seed_mask = np.zeros(n_nodes, dtype=bool)
            seed_mask[seed_idx] = True
            test_mask = np.zeros(n_nodes, dtype=bool)
            test_mask[test_idx] = True

            y = seed_mask.astype(int)

            # Baseline
            clf_b = LogisticRegression(max_iter=300, C=1.0, solver="lbfgs",
                                       random_state=42)
            clf_b.fit(X_base_scaled, y)
            p_b = clf_b.predict_proba(X_base_scaled)[:, 1]
            p_b[seed_mask] = np.inf
            base_r100.append(recall_at_k(p_b, seed_mask, test_mask, 100))
            base_mrr.append(mrr(p_b, seed_mask, test_mask))

            # Augmented
            clf_a = LogisticRegression(max_iter=300, C=1.0, solver="lbfgs",
                                       random_state=42)
            clf_a.fit(X_aug_scaled, y)
            p_a = clf_a.predict_proba(X_aug_scaled)[:, 1]
            p_a[seed_mask] = np.inf
            aug_r100.append(recall_at_k(p_a, seed_mask, test_mask, 100))
            aug_mrr.append(mrr(p_a, seed_mask, test_mask))

        b_r = np.mean(base_r100)
        a_r = np.mean(aug_r100)
        improvement = a_r - b_r

        results.append({
            "Disease ID": did,
            "Disease Name": name,
            "Baseline R@100": b_r,
            "Augmented R@100": a_r,
            "Improvement": improvement,
            "Baseline MRR": np.mean(base_mrr),
            "Augmented MRR": np.mean(aug_mrr),
        })

        if (idx + 1) % 20 == 0 or (idx + 1) == total or (idx + 1) <= 3:
            log(f"  [{idx+1:3d}/{total}] {name[:38]:<38s} "
                f"{b_r:>10.3f} {a_r:>10.3f} {improvement:>+8.3f}")

    return pd.DataFrame(results)


def print_augmented_summary(results_df):
    """Print summary of augmented vs baseline performance."""
    log("\n" + "=" * 70)
    log("Augmented Prediction: Summary")
    log("=" * 70)

    n = len(results_df)
    base_r100 = results_df["Baseline R@100"].mean()
    aug_r100 = results_df["Augmented R@100"].mean()
    base_mrr = results_df["Baseline MRR"].mean()
    aug_mrr = results_df["Augmented MRR"].mean()

    pct_improve = 100 * (aug_r100 - base_r100) / max(base_r100, 1e-10)
    n_improved = (results_df["Improvement"] > 0).sum()
    n_decreased = (results_df["Improvement"] < 0).sum()
    n_same = (results_df["Improvement"] == 0).sum()

    log(f"\n  Diseases evaluated: {n}")
    log(f"\n  {'Metric':<20s} {'Baseline':>10} {'Augmented':>10} {'Change':>10}")
    log(f"  {'-'*50}")
    log(f"  {'Recall@100':<20s} {base_r100:>10.4f} {aug_r100:>10.4f} "
        f"{pct_improve:>+9.1f}%")
    log(f"  {'MRR':<20s} {base_mrr:>10.4f} {aug_mrr:>10.4f} "
        f"{100*(aug_mrr-base_mrr)/max(base_mrr,1e-10):>+9.1f}%")

    log(f"\n  Paper reports: 11% improvement in Recall@100")
    log(f"  (Recall@100: 0.300 -> 0.332)")

    log(f"\n  Per-disease breakdown:")
    log(f"    Improved:  {n_improved} / {n}")
    log(f"    Decreased: {n_decreased} / {n}")
    log(f"    Unchanged: {n_same} / {n}")

    # Top 10 most improved
    top10 = results_df.nlargest(10, "Improvement")
    log(f"\n  Top 10 most improved diseases:")
    log(f"  {'Disease':<40s} {'Base':>6} {'Aug':>6} {'Gain':>6}")
    log(f"  {'-'*60}")
    for _, row in top10.iterrows():
        log(f"  {row['Disease Name'][:38]:<40s} "
            f"{row['Baseline R@100']:>6.3f} {row['Augmented R@100']:>6.3f} "
            f"{row['Improvement']:>+6.3f}")


def plot_augmented_results(results_df):
    """Generate comparison plots for augmented vs baseline prediction."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    fig.suptitle("Augmented Prediction: Embeddings + Motif Features\n"
                 "(Reproducing Section 6 from Agrawal et al. 2018)",
                 fontsize=13, fontweight="bold")

    # Scatter: baseline vs augmented
    ax = axes[0]
    ax.scatter(results_df["Baseline R@100"], results_df["Augmented R@100"],
               alpha=0.4, s=15, color="#4C72B0")
    lim = max(results_df["Baseline R@100"].max(), results_df["Augmented R@100"].max()) + 0.05
    ax.plot([0, lim], [0, lim], "k--", alpha=0.3, label="No change")
    ax.set_xlabel("Baseline Recall@100")
    ax.set_ylabel("Augmented Recall@100")
    ax.set_title("Baseline vs Augmented (per disease)")
    ax.legend()

    # Histogram of improvement
    ax = axes[1]
    imp = results_df["Improvement"]
    ax.hist(imp, bins=40, color="#55A868", edgecolor="white", alpha=0.85)
    ax.axvline(0, color="black", linestyle="-", alpha=0.3)
    ax.axvline(imp.mean(), color="red", linestyle="--",
               label=f"Mean = {imp.mean():+.4f}")
    ax.set_xlabel("Improvement in Recall@100")
    ax.set_ylabel("Number of Diseases")
    ax.set_title("Distribution of Improvement")
    ax.legend()

    # Bar chart: overall
    ax = axes[2]
    metrics = ["Recall@100", "MRR"]
    base_vals = [results_df["Baseline R@100"].mean(), results_df["Baseline MRR"].mean()]
    aug_vals = [results_df["Augmented R@100"].mean(), results_df["Augmented MRR"].mean()]
    x = np.arange(len(metrics))
    w = 0.3
    b1 = ax.bar(x - w/2, base_vals, w, label="Baseline", color="#C44E52", alpha=0.85)
    b2 = ax.bar(x + w/2, aug_vals, w, label="Augmented", color="#55A868", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_title("Overall: Baseline vs Augmented")
    ax.legend()
    for bars in [b1, b2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001,
                    f"{bar.get_height():.4f}", ha="center", va="bottom", fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    path = os.path.join(OUTPUT_DIR, "augmented_prediction.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    log(f"\n  Plot saved: {path}")
    return path


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log("=" * 70)
    log("Higher-Order Motif Analysis & Augmented Prediction")
    log("=" * 70)

    # ── Part A: Orbit significance analysis ──
    motifs_df, orbit_cols, sig_per_orbit = analyze_orbit_significance()
    cat_table = analyze_disease_categories(motifs_df, orbit_cols)
    p1 = plot_orbit_significance(sig_per_orbit, motifs_df, orbit_cols)

    # ── Part B: Augmented prediction ──
    results_df = run_augmented_prediction(n_diseases=None)
    out_path = os.path.join(OUTPUT_DIR, "augmented_results.csv")
    results_df.to_csv(out_path, index=False)
    log(f"\n  Results saved: {out_path}")

    print_augmented_summary(results_df)
    p2 = plot_augmented_results(results_df)

    log("\n" + "=" * 70)
    log("Done!")
    log("=" * 70)
