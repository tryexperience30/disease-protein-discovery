# Disease Protein Discovery Platform

Network-based computational discovery and prioritization of candidate disease proteins using the human protein-protein interaction network.

Based on: **Agrawal M, Zitnik M, Leskovec J.** *Large-scale analysis of disease pathways in the human interactome.* Pacific Symposium on Biocomputing, 2018.

Data source: [SNAP Stanford — Disease Pathways](https://snap.stanford.edu/pathways/)

---

## Quick Start

```bash
# Install dependencies (Python 3.10+)
pip install -r requirements.txt

# Launch the interactive application
python3 -m streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## Web platform (local)

A Next.js + FastAPI presentation layer sits on top of the same research code, data, and precomputed results. It does not retrain models or change scientific definitions.

**Terminal 1 — API**

```bash
chmod +x scripts/run_api.sh scripts/run_web.sh
./scripts/run_api.sh
```

Open **http://127.0.0.1:8000/docs** for the interactive API.

**Terminal 2 — website**

```bash
./scripts/run_web.sh
```

Open **http://localhost:3000**. Search a disease (for example `Alzheimer`) to open the 3D/2D network explorer.

The Streamlit app remains available and unchanged.

---

## Project Structure

```
CLL798/
│
├── app.py                          # Streamlit entry point
├── app/
│   ├── config.py                   # Paths, constants, metric descriptions
│   ├── cache.py                    # Cached data loading (@st.cache_data)
│   ├── components/
│   │   ├── network_viz.py          # 2D/3D Plotly network visualization
│   │   ├── physics_network.py      # Physics-based vis.js network (elastic drag)
│   │   ├── metric_cards.py         # Metric display cards with tooltips
│   │   ├── prediction_table.py     # Ranked prediction table with CSV download
│   │   └── charts.py              # Reusable chart components
│   ├── pages/
│   │   ├── home.py                 # Landing page with disease search
│   │   ├── disease_explorer.py     # Disease overview + structural metrics
│   │   ├── disease_network.py      # Interactive PPI pathway (Physics/3D/2D)
│   │   ├── predictions.py          # Live predictions + explain prediction
│   │   ├── protein_explorer.py     # Single protein deep dive
│   │   ├── model_comparison.py     # Cross-disease method analysis
│   │   └── methodology.py          # Pipeline documentation + disclaimer
│   └── utils/
│       └── live_predict.py         # Live single-disease prediction engine
│
├── load_data.py                    # Data loading functions
├── build_pathways.py               # Disease pathway construction + metrics
├── predict_disease_proteins.py     # Five prediction methods + evaluation
├── motif_analysis.py               # Higher-order motif analysis
│
├── data/                           # Raw datasets (from SNAP Stanford)
│   ├── bio-pathways-network.csv        # PPI network (342,353 edges)
│   ├── bio-pathways-associations.csv   # Disease-gene associations (519 diseases)
│   ├── bio-pathways-diseaseclasses.csv # Disease category mappings (300 diseases)
│   ├── bio-pathways-features.csv       # Pre-computed pathway features
│   └── bio-pathways-diseasemotifs.csv  # Graphlet orbit p-values (73 orbits)
│
├── results/                        # Pre-computed results
│   ├── computed_pathway_metrics.csv    # Structural metrics for 519 diseases
│   ├── prediction_results.csv         # 10-fold CV results (499 diseases × 5 methods)
│   └── augmented_results.csv          # Baseline vs augmented prediction
│
└── requirements.txt
```

---

## Research Pipeline

```
PPI Network (21,557 proteins, 342,353 interactions)
        │
        ▼
Disease Associations (519 diseases from DisGeNET, ≥10 genes each)
        │
        ▼
Disease Pathway Construction (induced subgraph per disease)
        │
        ├──► Structural Metrics (LCC size, density, conductance,
        │    modularity, component distance, spatial association)
        │
        ├──► Five Prediction Methods
        │         ├─ Neighborhood Scoring
        │         ├─ Random Walk with Restart
        │         ├─ DIAMOnD (connectivity significance)
        │         ├─ Spectral Embeddings + Logistic Regression
        │         └─ NMF-based Matrix Completion
        │
        └──► Structural Motif Features (12-dim proxy for graphlet orbits)
                        │
                        ▼
              Augmented Prediction (embeddings + motif features)
                        │
                        ▼
              Candidate Disease Protein Prioritization
```

---

## Datasets

| Dataset | Source | Size |
|---------|--------|------|
| Human PPI Network | Menche et al. 2015 / BioGRID | 21,557 proteins, 342,353 edges |
| Disease-Protein Associations | DisGeNET | 519 diseases, 21,357 associations |
| Disease Categories | Disease Ontology | 300 diseases mapped to 30 categories |
| Graphlet Orbit p-values | Paper supplementary | 519 diseases × 73 orbits |

---

## Prediction Methods

| Method | Input | Approach |
|--------|-------|----------|
| Neighborhood Scoring | PPI + seed genes | Fraction of neighbors that are seeds |
| Random Walk with Restart | PPI + seed genes | Stationary distribution of biased random walk (α=0.7) |
| DIAMOnD | PPI + seed genes | Iterative z-score connectivity significance expansion |
| Spectral Embeddings | PPI adjacency | Truncated SVD → logistic regression on seed labels |
| Matrix Completion | Protein×disease matrix | NMF factorization → reconstructed association scores |

---

## Evaluation

- **Protocol:** Disease-centric 10-fold cross-validation
- **Metrics:** Recall@25, Recall@100, Mean Reciprocal Rank (MRR)
- **Note:** Matrix Completion CV metrics are optimistic because NMF is fitted on the full protein-disease matrix before fold splitting. The other four methods use only train-fold seed proteins.

---

## Known Deviations from Reference Paper

| Component | Paper | This Implementation |
|-----------|-------|-------------------|
| Neural Embeddings | node2vec (random walks + Word2Vec) | Spectral embeddings (truncated SVD) |
| DIAMOnD scoring | Exact hypergeometric p-value | Z-score approximation |
| Graphlet orbits | Full 73-orbit ORCA signatures | 12 approximate structural features |
| Hyperparameter tuning | 20 diseases set aside | Fixed hyperparameters |

---

## Application Pages

| Page | Description |
|------|-------------|
| **Home** | Landing page with disease search and pipeline overview |
| **Disease Explorer** | Structural metrics, context histograms, orbit significance |
| **Disease Network** | Interactive PPI pathway: Physics (elastic drag) / 3D / 2D |
| **Predictions** | Live 5-method scoring, ranked table, download CSV, explain prediction |
| **Protein Explorer** | Search any protein: network stats, disease associations, neighbors |
| **Model Comparison** | Cross-disease method analysis, by-category, augmented vs baseline |
| **Methodology** | Full pipeline documentation, references, research disclaimer |

---

## Disclaimer

This platform provides computational prioritization of candidate disease-associated proteins based on network and machine-learning analyses. Predictions are intended for research purposes and should not be interpreted as clinical diagnoses or experimentally validated disease associations.

---

## References

1. Agrawal M, Zitnik M, Leskovec J. *Large-scale analysis of disease pathways in the human interactome.* Pacific Symposium on Biocomputing. 2018.
2. Menche J, et al. *Uncovering disease-disease relationships through the incomplete interactome.* Science. 2015;347(6224):1257601.
3. Ghiassian SD, Menche J, Barabasi AL. *A DIAMOnD module detection algorithm.* PLoS Computational Biology. 2015.
4. Pinero J, et al. *DisGeNET: a comprehensive platform integrating information on human disease-associated genes and variants.* Nucleic Acids Research. 2017.
