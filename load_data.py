"""
Load and explore the disease pathway datasets from:
  "Large-scale analysis of disease pathways in the human interactome"
  Agrawal, Zitnik, Leskovec (PSB 2018)

Data source: http://snap.stanford.edu/pathways

Datasets
--------
1. PPI Network        : 21,557 proteins, 342,353 interactions
2. Disease Associations: 519 diseases with >=10 associated genes each
3. Disease Classes     : 290 diseases mapped to 10 disease categories
4. Pathway Features    : Pre-computed structural metrics per disease
5. Disease Motifs      : Graphlet orbit p-values per disease (73 orbits)
"""

import os
import pandas as pd
import networkx as nx
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ── 1. Load PPI Network ─────────────────────────────────────────────────────

def load_ppi_network():
    """Load the human protein-protein interaction network as an undirected
    NetworkX graph. Nodes are Entrez Gene IDs (integers)."""
    path = os.path.join(DATA_DIR, "bio-pathways-network.csv")
    edges_df = pd.read_csv(path)
    G = nx.from_pandas_edgelist(edges_df, "Gene ID 1", "Gene ID 2")
    return G


# ── 2. Load Protein-Disease Associations ─────────────────────────────────────

def load_disease_associations():
    """Load protein-disease associations.

    Returns
    -------
    disease_genes : dict
        {disease_id: set of gene IDs}
    disease_names : dict
        {disease_id: disease name string}
    """
    path = os.path.join(DATA_DIR, "bio-pathways-associations.csv")
    df = pd.read_csv(path)

    disease_genes = {}
    disease_names = {}

    for _, row in df.iterrows():
        did = row["Disease ID"]
        dname = row["Disease Name"]
        genes_str = str(row["Associated Gene IDs"])
        gene_ids = set()
        for g in genes_str.split(","):
            g = g.strip()
            if g:
                try:
                    gene_ids.add(int(g))
                except ValueError:
                    pass
        disease_genes[did] = gene_ids
        disease_names[did] = dname

    return disease_genes, disease_names


# ── 3. Load Disease Classes ──────────────────────────────────────────────────

def load_disease_classes():
    """Load the mapping from diseases to disease categories.

    Returns
    -------
    disease_classes : dict
        {disease_id: disease_class string}
    """
    path = os.path.join(DATA_DIR, "bio-pathways-diseaseclasses.csv")
    df = pd.read_csv(path)
    return dict(zip(df["Disease ID"], df["Disease Class"]))


# ── 4. Load Pre-computed Pathway Features ────────────────────────────────────

def load_pathway_features():
    """Load structural metrics for each disease pathway.

    Columns: Disease ID, Disease Name, Size of largest pathway component,
             Density of pathway, Network Modularity,
             Distance of Pathway Components, Spatial Network Association
    """
    path = os.path.join(DATA_DIR, "bio-pathways-features.csv")
    df = pd.read_csv(path)
    df.set_index("Disease ID", inplace=True)
    return df


# ── 5. Load Disease Motifs (Graphlet Orbit p-values) ─────────────────────────

def load_disease_motifs():
    """Load the graphlet orbit significance analysis per disease.

    Returns a DataFrame with 519 rows (diseases) and 73 orbit p-value columns.
    """
    path = os.path.join(DATA_DIR, "bio-pathways-diseasemotifs.csv")

    orbit_cols = [f"orbit_{i}" for i in range(73)]
    col_names = ["Disease ID", "Disease Name"] + orbit_cols

    df = pd.read_csv(path, header=0, names=col_names)
    df.set_index("Disease ID", inplace=True)
    return df


# ── Main: Run if executed directly to verify everything loads ────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Loading Disease Pathway Data")
    print("=" * 60)

    # 1. PPI Network
    print("\n[1/5] Loading PPI network...")
    G = load_ppi_network()
    largest_cc = max(nx.connected_components(G), key=len)
    print(f"  Nodes (proteins): {G.number_of_nodes():,}")
    print(f"  Edges (interactions): {G.number_of_edges():,}")
    print(f"  Largest connected component: {len(largest_cc):,} nodes")

    # 2. Disease-Gene Associations
    print("\n[2/5] Loading disease-gene associations...")
    disease_genes, disease_names = load_disease_associations()
    total_assoc = sum(len(v) for v in disease_genes.values())
    gene_counts = [len(v) for v in disease_genes.values()]
    print(f"  Diseases: {len(disease_genes)}")
    print(f"  Total associations: {total_assoc:,}")
    print(f"  Genes per disease: median={np.median(gene_counts):.0f}, "
          f"min={min(gene_counts)}, max={max(gene_counts)}")

    # 3. Disease Classes
    print("\n[3/5] Loading disease classes...")
    disease_classes = load_disease_classes()
    class_counts = pd.Series(disease_classes).value_counts()
    print(f"  Diseases with class mapping: {len(disease_classes)}")
    print(f"  Disease categories ({len(class_counts)}):")
    for cls, cnt in class_counts.items():
        print(f"    {cls}: {cnt}")

    # 4. Pathway Features
    print("\n[4/5] Loading pathway features...")
    features_df = load_pathway_features()
    print(f"  Shape: {features_df.shape}")
    print(f"  Columns: {list(features_df.columns)}")
    numeric_cols = features_df.select_dtypes(include=[np.number]).columns
    print(f"  Summary statistics:")
    print(features_df[numeric_cols].describe().round(4).to_string())

    # 5. Disease Motifs
    print("\n[5/5] Loading disease motifs (graphlet orbits)...")
    motifs_df = load_disease_motifs()
    orbit_cols = [c for c in motifs_df.columns if c.startswith("orbit_")]
    sig_count = (motifs_df[orbit_cols] < 0.01).sum(axis=0)
    print(f"  Shape: {motifs_df.shape}")
    print(f"  Orbit columns: {len(orbit_cols)}")
    sig_diseases = (motifs_df[orbit_cols] < 0.01).any(axis=1).sum()
    print(f"  Diseases with at least one significant orbit (p<0.01): "
          f"{sig_diseases} / {len(motifs_df)}")

    print("\n" + "=" * 60)
    print("All data loaded successfully!")
    print("=" * 60)
