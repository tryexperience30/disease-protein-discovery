"""Page 7: Methodology — complete pipeline explanation and disclaimer."""

import streamlit as st


def render():
    st.title("Methodology")
    st.markdown("Complete computational pipeline from data sources to "
                "candidate disease protein prioritization.")

    # ── Pipeline diagram ─────────────────────────────────────────────────
    st.subheader("Pipeline Overview")
    st.code("""
    PPI Network (21,557 proteins, 342,353 interactions)
                    │
                    ▼
    Disease Associations (519 diseases from DisGeNET)
                    │
                    ▼
    Disease Pathway Construction (induced subgraph per disease)
                    │
                    ├──► Structural Metrics (LCC, density, conductance, …)
                    │
                    ├──► Five Prediction Methods
                    │         ├─ Neighborhood Scoring
                    │         ├─ Random Walk with Restart
                    │         ├─ DIAMOnD
                    │         ├─ Spectral Embeddings + Logistic Regression
                    │         └─ NMF-based Matrix Completion
                    │
                    └──► Graphlet Orbit Signatures (73-dim structural features)
                                    │
                                    ▼
                    Feature Integration (embeddings + motif features)
                                    │
                                    ▼
                    Logistic Regression → Candidate Disease Proteins
    """, language=None)

    st.divider()

    # ── Stage descriptions ───────────────────────────────────────────────
    with st.expander("1. Human PPI Network", expanded=False):
        st.markdown("""
The human protein-protein interaction (PPI) network is compiled from Menche et al. (2015)
and BioGRID. It contains **21,557 proteins** connected by **342,353 experimentally validated
physical interactions** including metabolic enzyme-coupled interactions and signaling interactions.

The network is unweighted and undirected. Only the largest connected component (21,521 nodes)
is used for analysis. Proteins are mapped to Entrez Gene IDs.
        """)

    with st.expander("2. Disease-Protein Associations", expanded=False):
        st.markdown("""
Protein-disease associations are obtained from **DisGeNET**, a platform centralizing knowledge
on Mendelian and complex diseases. Each association is a tuple (protein, disease) indicating
that alteration of the protein is linked to the disease.

The dataset contains **21,357 associations** across **519 diseases**, each with at least
10 associated proteins. The median number of associations per disease is 21, ranging up to
485 for complex diseases like cancers.
        """)

    with st.expander("3. Disease Pathway Construction", expanded=False):
        st.markdown("""
For each disease, the **disease pathway** is the subgraph of the PPI network induced by the
set of disease-associated proteins:

- **Nodes (Vd):** Disease proteins present in the PPI network
- **Edges (Ed):** PPI edges between disease proteins
- **Boundary (Bd):** Edges connecting disease proteins to non-disease proteins

Key finding: Disease pathways are **fragmented** — median of 16 disconnected components per
disease, with only 21% of proteins in the largest connected component.
        """)

    with st.expander("4. Structural Metrics", expanded=False):
        st.markdown("""
Six metrics characterize each disease pathway:

| Metric | Formula | Interpretation |
|--------|---------|---------------|
| **LCC Fraction** | |largest component| / |Vd| | Fragmentation — lower = more fragmented |
| **Density** | 2|Ed| / (|Vd|(|Vd|-1)) | Internal connectivity |
| **Conductance** | |Bd| / (|Bd| + 2|Ed|) | Separation from rest — lower = better separated |
| **Modularity** | Newman's Q | Module quality vs random |
| **Component Distance** | Mean shortest path between components | Spatial spread |
| **Spatial Association** | Ripley's K p-value | Clustering significance |
        """)

    with st.expander("5. Prediction Methods", expanded=False):
        st.markdown("""
**Neighborhood Scoring:** Each protein is scored by the fraction of its direct neighbors
that are known disease proteins. Simple but limited to immediate connectivity.

**Random Walk with Restart (RWR):** A random walker starts at seed disease proteins.
At each step, it follows a random edge with probability α=0.7, or restarts at a seed
with probability 0.3. The stationary distribution gives protein scores.

**DIAMOnD:** Iteratively expands a seed module by adding the protein with the most
statistically significant connectivity to the current module (z-score based).

**Spectral Embeddings + Logistic Regression:** Truncated SVD of the normalized adjacency
matrix produces a 64-dimensional embedding per protein. A logistic regression classifier
trained on seed proteins predicts disease membership.

**NMF-based Matrix Completion:** Non-negative matrix factorization of the protein×disease
association matrix. Pre-computed factors are used to predict missing associations.

> **Evaluation note:** In the cross-validation evaluation, NMF is fitted on the full
> protein×disease matrix before fold splitting. This means Matrix Completion has access
> to test-fold disease-protein associations during factorization, which inflates its
> reported CV metrics relative to the other four methods. This does not affect live
> predictions (where all known associations are legitimately available) or the other
> four methods (which use only train-fold seed proteins).
        """)

    with st.expander("6. Graphlet Orbit Signatures", expanded=False):
        st.markdown("""
Higher-order network structure is captured through **graphlet orbits**. There are 30 possible
graphlets (connected non-isomorphic induced subgraphs) of 2–5 nodes, yielding 73 distinct
orbit positions.

For each disease, permutation testing (5,000 random samples) determines which orbits are
significantly over-represented in disease proteins (p < 0.01).

**Key finding:** 60% of diseases (310/519) show significant orbit over-representation,
indicating that disease proteins share higher-order structural roles even when not directly
connected in the PPI network.
        """)

    with st.expander("7. Augmented Prediction", expanded=False):
        st.markdown("""
Spectral embeddings are augmented with structural motif features:

1. Compute 12 local structural features per protein (degree, clustering coefficient,
   triangles, neighbor degree statistics, 2-paths, 4-cycles)
2. Transform: h'ᵢ = max(0, log(hᵢ))
3. Concatenate: [64-dim embedding | 12-dim motif features] → 76-dim vector
4. Train logistic regression on the augmented feature vector

**Result:** ~5.5% improvement in Recall@100, ~9.7% improvement in MRR compared to
embeddings alone. Paper reports 11% improvement with full 73-orbit signatures.
        """)

    st.divider()

    # ── Evaluation ───────────────────────────────────────────────────────
    with st.expander("Evaluation Protocol", expanded=False):
        st.markdown("""
**Disease-centric 10-fold cross-validation:**
- For each disease, its associated proteins are split into 10 folds
- In each round, 9 folds serve as seed proteins, 1 fold is held out for testing
- Each method scores all proteins; test proteins ranked in top-k are counted

**Metrics:**
- **Recall@25:** Fraction of test proteins ranked in the top 25
- **Recall@100:** Fraction of test proteins ranked in the top 100
- **MRR:** Mean reciprocal rank — average of 1/rank for each test protein
        """)

    st.divider()

    # ── References ───────────────────────────────────────────────────────
    st.subheader("References")
    st.markdown("""
1. Agrawal M, Zitnik M, Leskovec J. *Large-scale analysis of disease pathways in the
   human interactome.* Pacific Symposium on Biocomputing. 2018.
2. Menche J, et al. *Uncovering disease-disease relationships through the incomplete
   interactome.* Science. 2015;347(6224):1257601.
3. Ghiassian SD, Menche J, Barabási AL. *A DIAMOnD module detection algorithm.*
   PLoS Computational Biology. 2015;11(4):e1004120.
4. Grover A, Leskovec J. *node2vec: Scalable feature learning for networks.*
   ACM SIGKDD. 2016.
5. Piñero J, et al. *DisGeNET: a comprehensive platform integrating information on
   human disease-associated genes and variants.* Nucleic Acids Research. 2017.
    """)

    st.divider()

    st.warning(
        "**Research Disclaimer:** This platform provides computational prioritization of "
        "candidate disease-associated proteins based on network and machine-learning analyses. "
        "Predictions are intended for research purposes and should not be interpreted as "
        "clinical diagnoses or experimentally validated disease associations."
    )
