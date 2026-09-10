"""
Build disease pathways and compute structural metrics.

Reproduces the analysis from Sections 4.1 of:
  "Large-scale analysis of disease pathways in the human interactome"
  Agrawal, Zitnik, Leskovec (PSB 2018)

For each disease, the pathway is the subgraph of the PPI network induced
by the set of disease-associated proteins. We compute six structural
metrics per pathway:
  1. Size of largest pathway component (relative LCC size)
  2. Density
  3. Distance between pathway components
  4. Conductance
  5. Spatial network association (Ripley's K-function)
  6. Network modularity
"""

import os
import time
import numpy as np
import pandas as pd
import networkx as nx
from collections import defaultdict

from load_data import (
    load_ppi_network,
    load_disease_associations,
    load_disease_classes,
    load_pathway_features,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 1: Build disease pathway subgraphs
# ═══════════════════════════════════════════════════════════════════════════

def build_disease_pathway(G, disease_genes_set):
    """Extract the disease pathway subgraph from the PPI network.

    Parameters
    ----------
    G : nx.Graph
        Full PPI network.
    disease_genes_set : set of int
        Gene IDs associated with the disease.

    Returns
    -------
    Hd : nx.Graph
        Subgraph induced by disease genes present in G.
    Vd : set
        Disease genes that exist in the PPI network.
    """
    Vd = disease_genes_set & set(G.nodes())
    Hd = G.subgraph(Vd).copy()
    return Hd, Vd


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 2: Structural metric functions
# ═══════════════════════════════════════════════════════════════════════════

def largest_component_fraction(Hd):
    """Fraction of disease proteins in the largest connected component."""
    if Hd.number_of_nodes() == 0:
        return 0.0
    components = list(nx.connected_components(Hd))
    largest = max(components, key=len)
    return len(largest) / Hd.number_of_nodes()


def pathway_density(Hd):
    """Edge density: 2|Ed| / (|Vd| * (|Vd| - 1))."""
    n = Hd.number_of_nodes()
    if n < 2:
        return 0.0
    return (2.0 * Hd.number_of_edges()) / (n * (n - 1))


def pathway_conductance(G, Hd, Vd):
    """Conductance: |Bd| / (|Bd| + 2|Ed|).

    Bd = boundary edges (one endpoint in Vd, other outside).
    Ed = internal edges of the pathway.
    """
    if Hd.number_of_nodes() == 0:
        return 1.0

    boundary_count = 0
    for u in Vd:
        for v in G.neighbors(u):
            if v not in Vd:
                boundary_count += 1

    internal_edges = Hd.number_of_edges()
    denom = boundary_count + 2 * internal_edges
    if denom == 0:
        return 1.0
    return boundary_count / denom


def component_distance(G, Hd, shortest_paths=None):
    """Average shortest-path distance between pairs of pathway components,
    measured in the full PPI network.

    Parameters
    ----------
    G : nx.Graph
        Full PPI network (used for shortest paths).
    Hd : nx.Graph
        Disease pathway subgraph.
    shortest_paths : dict, optional
        Pre-computed shortest path lengths (for speed).

    Returns
    -------
    float or np.nan
        Mean distance across all component pairs, or NaN if < 2 components.
    """
    components = [list(c) for c in nx.connected_components(Hd)]
    if len(components) < 2:
        return np.nan

    pair_dists = []
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            dists = []
            for u in components[i]:
                for v in components[j]:
                    try:
                        d = nx.shortest_path_length(G, u, v)
                        dists.append(d)
                    except nx.NetworkXNoPath:
                        pass
            if dists:
                pair_dists.append(np.mean(dists))

    return np.mean(pair_dists) if pair_dists else np.nan


def network_modularity(G, Vd):
    """Newman's modularity Q for disease vs non-disease partition.

    Q = (1/2m) * sum_ij [ A_ij - k_i*k_j/(2m) ] * delta(c_i, c_j)

    where delta(c_i, c_j) = 1 if both i,j in Vd or both outside.
    """
    m = G.number_of_edges()
    if m == 0:
        return 0.0

    community_disease = set(Vd)
    community_other = set(G.nodes()) - community_disease

    Q = nx.community.modularity(G, [community_disease, community_other])
    return Q


def spatial_network_association(G, Vd, n_random=1000, max_s=6):
    """Spatial network association (simplified Ripley's K-function).

    Measures whether disease proteins cluster more tightly in the PPI network
    than random sets of the same size.

    Parameters
    ----------
    G : nx.Graph
        Full PPI network.
    Vd : set
        Disease genes in the network.
    n_random : int
        Number of random permutations for significance testing.
    max_s : int
        Maximum shortest-path distance to evaluate K(s).

    Returns
    -------
    p_value : float
        Fraction of random samples with AUC >= observed AUC.
    """
    all_nodes = list(G.nodes())
    n_total = len(all_nodes)
    n_disease = len(Vd)

    if n_disease < 2:
        return 1.0

    Vd_list = list(Vd)
    p_bar = n_disease / n_total

    def compute_k_auc(target_set):
        target_list = list(target_set)
        k_values = []
        for s in range(1, max_s + 1):
            k_s = 0.0
            for u in target_list:
                try:
                    lengths = nx.single_source_shortest_path_length(G, u, cutoff=s)
                except Exception:
                    continue
                for v, dist in lengths.items():
                    if v != u and v in target_set and dist < s:
                        k_s += 1.0
            k_s = k_s / (p_bar * n_total * n_disease) if (p_bar * n_total * n_disease) > 0 else 0
            k_values.append(k_s)
        return np.trapz(k_values, dx=1)

    observed_auc = compute_k_auc(Vd)

    count_ge = 0
    for _ in range(n_random):
        random_set = set(np.random.choice(all_nodes, size=n_disease, replace=False))
        random_auc = compute_k_auc(random_set)
        if random_auc >= observed_auc:
            count_ge += 1

    return count_ge / n_random


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 3: Compute all metrics for all diseases
# ═══════════════════════════════════════════════════════════════════════════

def compute_all_metrics(skip_spatial=False, skip_component_dist=False):
    """Compute structural metrics for all 519 disease pathways.

    Parameters
    ----------
    skip_spatial : bool
        If True, skip the expensive spatial association computation.
    skip_component_dist : bool
        If True, skip inter-component distance (also expensive).

    Returns
    -------
    pd.DataFrame
        One row per disease with all computed metrics.
    """
    print("Loading data...")
    G = load_ppi_network()
    disease_genes, disease_names = load_disease_associations()

    print(f"PPI network: {G.number_of_nodes():,} nodes, "
          f"{G.number_of_edges():,} edges")
    print(f"Diseases to process: {len(disease_genes)}")

    results = []
    total = len(disease_genes)

    for idx, (did, genes) in enumerate(disease_genes.items()):
        t0 = time.time()
        name = disease_names[did]

        Hd, Vd = build_disease_pathway(G, genes)
        n_genes_in_ppi = len(Vd)
        n_components = nx.number_connected_components(Hd)
        n_edges = Hd.number_of_edges()

        lcc_frac = largest_component_fraction(Hd)
        density = pathway_density(Hd)
        conductance = pathway_conductance(G, Hd, Vd)
        modularity = network_modularity(G, Vd)

        if skip_component_dist:
            comp_dist = np.nan
        else:
            comp_dist = component_distance(G, Hd)

        if skip_spatial:
            spatial_pval = np.nan
        else:
            spatial_pval = spatial_network_association(G, Vd, n_random=100)

        elapsed = time.time() - t0

        results.append({
            "Disease ID": did,
            "Disease Name": name,
            "Num Genes (total)": len(genes),
            "Num Genes (in PPI)": n_genes_in_ppi,
            "Num Components": n_components,
            "Num Internal Edges": n_edges,
            "Size of largest pathway component": lcc_frac,
            "Density of pathway": density,
            "Conductance": conductance,
            "Network Modularity": modularity,
            "Distance of Pathway Components": comp_dist,
            "Spatial Network Association (p-value)": spatial_pval,
        })

        if (idx + 1) % 25 == 0 or (idx + 1) == total:
            print(f"  [{idx+1}/{total}] {name} — "
                  f"{n_genes_in_ppi} genes, {n_components} components, "
                  f"LCC={lcc_frac:.2f}, density={density:.4f} "
                  f"({elapsed:.1f}s)")

    df = pd.DataFrame(results)
    df.set_index("Disease ID", inplace=True)
    return df


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 4: Validate against paper's pre-computed features
# ═══════════════════════════════════════════════════════════════════════════

def validate_against_paper(computed_df):
    """Compare our computed metrics against the paper's pre-computed values."""
    paper_df = load_pathway_features()

    metrics_to_check = [
        ("Size of largest pathway component", "Size of largest pathway component"),
        ("Density of pathway", "Density of pathway"),
        ("Network Modularity", "Network Modularity"),
    ]

    print("\n" + "=" * 60)
    print("Validation Against Paper's Pre-computed Features")
    print("=" * 60)

    for our_col, paper_col in metrics_to_check:
        common = computed_df.index.intersection(paper_df.index)
        ours = computed_df.loc[common, our_col].astype(float)
        theirs = paper_df.loc[common, paper_col].astype(float)

        mask = ours.notna() & theirs.notna()
        ours = ours[mask]
        theirs = theirs[mask]

        if len(ours) == 0:
            print(f"\n  {our_col}: no overlapping data to compare")
            continue

        corr = np.corrcoef(ours, theirs)[0, 1]
        max_diff = np.abs(ours - theirs).max()
        mean_diff = np.abs(ours - theirs).mean()

        print(f"\n  {our_col}:")
        print(f"    Correlation:     {corr:.6f}")
        print(f"    Mean abs diff:   {mean_diff:.6f}")
        print(f"    Max abs diff:    {max_diff:.6f}")
        print(f"    Match (diff<0.01): {(np.abs(ours - theirs) < 0.01).sum()}/{len(ours)}")


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 5: Generate distribution plots (Figures 2 & 3 from the paper)
# ═══════════════════════════════════════════════════════════════════════════

def generate_plots(df):
    """Generate the distribution plots from Figures 2 and 3 of the paper."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Structural Metrics of Disease Pathways in the Human Interactome",
                 fontsize=14, fontweight="bold")

    # Fig 2A: Size of largest pathway component
    ax = axes[0, 0]
    data = df["Size of largest pathway component"].dropna()
    ax.hist(data, bins=30, color="#4C72B0", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="red", linestyle="--", label=f"Median={data.median():.2f}")
    ax.set_xlabel("Fraction of proteins in largest component")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(A) Size of Largest Pathway Component")
    ax.legend()

    # Fig 2B: Density of pathway
    ax = axes[0, 1]
    data = df["Density of pathway"].dropna()
    ax.hist(data, bins=30, color="#55A868", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="red", linestyle="--", label=f"Median={data.median():.4f}")
    ax.set_xlabel("Pathway density")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(B) Density of Pathway")
    ax.legend()

    # Fig 2C: Distance of pathway components
    ax = axes[0, 2]
    data = df["Distance of Pathway Components"].dropna()
    ax.hist(data, bins=30, color="#C44E52", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="red", linestyle="--", label=f"Median={data.median():.2f}")
    ax.set_xlabel("Avg shortest path between components")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(C) Distance of Pathway Components")
    ax.legend()

    # Conductance
    ax = axes[1, 0]
    data = df["Conductance"].dropna()
    ax.hist(data, bins=30, color="#8172B2", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="red", linestyle="--", label=f"Median={data.median():.2f}")
    ax.set_xlabel("Conductance")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(D) Conductance")
    ax.legend()

    # Fig 3B: Network Modularity
    ax = axes[1, 1]
    data = df["Network Modularity"].dropna()
    log_data = np.log10(np.abs(data) + 1e-10)
    ax.hist(log_data, bins=30, color="#CCB974", edgecolor="white", alpha=0.85)
    ax.axvline(np.median(log_data), color="red", linestyle="--",
               label=f"Median(log10)={np.median(log_data):.2f}")
    ax.set_xlabel("Network modularity [log₁₀(|value|)]")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(E) Network Modularity")
    ax.legend()

    # Number of components
    ax = axes[1, 2]
    data = df["Num Components"].dropna()
    ax.hist(data, bins=30, color="#64B5CD", edgecolor="white", alpha=0.85)
    ax.axvline(data.median(), color="red", linestyle="--", label=f"Median={data.median():.0f}")
    ax.set_xlabel("Number of pathway components")
    ax.set_ylabel("Number of diseases")
    ax.set_title("(F) Number of Pathway Components")
    ax.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plot_path = os.path.join(OUTPUT_DIR, "pathway_metrics_distributions.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nPlot saved to: {plot_path}")
    return plot_path


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("Building Disease Pathways & Computing Structural Metrics")
    print("=" * 60)

    # Compute metrics (skip spatial association — it takes hours with full
    # permutation testing; we use the paper's pre-computed p-values for that).
    # Component distance is computed but takes ~10-20 min for all 519 diseases.
    df = compute_all_metrics(skip_spatial=True, skip_component_dist=False)

    # Save results
    out_path = os.path.join(OUTPUT_DIR, "computed_pathway_metrics.csv")
    df.to_csv(out_path)
    print(f"\nResults saved to: {out_path}")

    # Print summary statistics matching the paper
    print("\n" + "=" * 60)
    print("Summary Statistics (compare with paper)")
    print("=" * 60)

    print(f"\nDisease pathways analyzed: {len(df)}")
    print(f"\nMedian number of components per disease: "
          f"{df['Num Components'].median():.0f}  (paper: 16)")
    print(f"Median fraction in LCC: "
          f"{df['Size of largest pathway component'].median():.2f}  (paper: 0.21)")
    print(f"Median density: "
          f"{df['Density of pathway'].median():.4f}  (paper: 0.07)")
    print(f"Median conductance: "
          f"{df['Conductance'].median():.2f}  (paper: 0.96)")

    dist_data = df['Distance of Pathway Components'].dropna()
    print(f"Median component distance: "
          f"{dist_data.median():.2f}  (paper: ~2.9)")

    pct_over60 = (df['Size of largest pathway component'] > 0.60).mean() * 100
    print(f"Pathways with >60% in LCC: "
          f"{pct_over60:.1f}%  (paper: ~10%)")

    pct_below17 = (df['Density of pathway'] < 0.17).mean() * 100
    print(f"Pathways with density < 0.17: "
          f"{pct_below17:.1f}%  (paper: ~90%)")

    # Validate against paper
    validate_against_paper(df)

    # Generate plots
    print("\nGenerating distribution plots...")
    plot_path = generate_plots(df)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
