export type Concept = {
  term: string;
  simple: string;
  research: string;
};

export const CONCEPTS: Record<string, Concept> = {
  disease: {
    term: "Disease",
    simple: "A disease here is a named condition from a research catalogue, not a diagnosis for a person.",
    research:
      "Each disease is a DisGeNET identifier with at least ten associated genes in the SNAP disease-pathway dataset used by this project.",
  },
  protein: {
    term: "Protein",
    simple: "A protein is a molecule that does work in cells. In this website every protein is shown by its Entrez Gene ID.",
    research:
      "Nodes are Entrez Gene IDs. Gene symbols are not present in this dataset, so labels are numeric identifiers only.",
  },
  gene: {
    term: "Gene",
    simple: "A gene is the DNA instruction for making a protein. This project uses gene IDs as protein labels.",
    research: "Protein nodes use Entrez Gene IDs from the SNAP PPI and association tables.",
  },
  ppi: {
    term: "Protein–protein interaction (PPI)",
    simple: "A PPI is a recorded contact or partnership between two proteins.",
    research:
      "Edges come from the human PPI network compiled for the SNAP disease-pathway resource (BioGRID / Menche et al.), not from new experiments run on this website.",
  },
  network: {
    term: "Network",
    simple: "A network is a map of dots (proteins) connected by lines (interactions).",
    research: "The full interactome has 21,557 proteins and 342,353 interactions. The public site shows disease-specific subsets, not the entire PPI.",
  },
  node: {
    term: "Node",
    simple: "A node is one protein drawn as a circle in the map.",
    research: "Each node is an Entrez Gene ID present in the displayed subgraph.",
  },
  edge: {
    term: "Edge",
    simple: "An edge is a line showing that two proteins are connected in the network.",
    research: "In this project, edges represent protein–protein interactions from the underlying interaction network.",
  },
  pathway: {
    term: "Disease pathway",
    simple: "The disease pathway is the small network made only from proteins already linked to that disease.",
    research:
      "It is the PPI subgraph induced by disease-associated proteins that are present in the interactome. Layout coordinates are not locations inside a cell.",
  },
  candidate: {
    term: "Candidate protein",
    simple: "A candidate is a protein the computer ranked as possibly relevant. It is not a proven cause or treatment.",
    research:
      "Candidates are proteins that are not known seeds for the disease, ranked by the five computational methods and the combined score.",
  },
  prediction: {
    term: "Prediction",
    simple: "A prediction is a computer ranking, not a medical test result.",
    research:
      "Public pages show precomputed rankings from the validated research pipeline. They are not recomputed on Vercel.",
  },
  neighborhood: {
    term: "Neighborhood",
    simple: "This method looks at how many of a protein’s neighbors are already linked to the disease.",
    research: "Fraction of PPI neighbors that are known disease-associated (seed) proteins.",
  },
  random_walk: {
    term: "Random Walk",
    simple: "Imagine a walker hopping along protein connections, often restarting from known disease proteins. Proteins visited more often rank higher.",
    research: "Random walk with restart (α=0.7) on the PPI network, seeded at known disease proteins.",
  },
  diamond: {
    term: "DIAMOnD",
    simple: "This method grows a group of proteins by repeatedly adding the one that looks most connected to the current disease group.",
    research:
      "Iterative module expansion adding the protein with the most significant connectivity to the current seed module (z-score approximation, max 100 added).",
  },
  neural_embeddings: {
    term: "Neural Embeddings",
    simple: "The computer turns the network into numbers that describe each protein’s place in the map, then learns to tell disease proteins apart.",
    research:
      "64-dimensional spectral embeddings (truncated SVD of the normalized adjacency) with logistic regression trained on seed proteins. This is not node2vec.",
  },
  matrix_completion: {
    term: "Matrix Completion",
    simple: "This method fills in a large table of proteins × diseases to guess missing links.",
    research:
      "Non-negative matrix factorization of the protein×disease association matrix. Cross-validation metrics for this method are inflated because NMF is fitted before fold splitting. That leakage does not apply to the other four methods.",
  },
  combined_score: {
    term: "Combined Score",
    simple: "The Combined Score averages the five method scores after stretching each method onto a 0–1 scale.",
    research:
      "Mean of the min–max-normalized scores from Neighborhood, Random Walk, DIAMOnD, Neural Embeddings, and Matrix Completion. It is not a separately trained model.",
  },
  graphlet: {
    term: "Graphlet",
    simple: "A graphlet is a small pattern made from a few connected nodes.",
    research:
      "This project shows disease-level 73-orbit significance profiles from the SNAP supplementary data. Per-protein 73-orbit ORCA signatures are not computed here.",
  },
  orbit: {
    term: "Orbit",
    simple: "An orbit is a specific way a node can sit inside a small graphlet pattern.",
    research: "Disease-level orbit p-values cover 73 orbits. They are not the same as the 12-dimensional protein motif-signature proxy.",
  },
  motif: {
    term: "Motif",
    simple: "A motif is a repeating small shape in a network.",
    research:
      "Protein-level structure in this project uses a 12-dimensional motif-signature proxy from motif_analysis.py, not full ORCA orbit counts.",
  },
  density: {
    term: "Density",
    simple: "Density tells us how many of the possible protein connections actually exist.",
    research: "Edge density = 2|E| / (|V|(|V|−1)). Range [0, 1]. Paper median: 0.07.",
  },
  conductance: {
    term: "Conductance",
    simple: "Conductance asks how leaky the disease group is: how many links leave the group versus stay inside.",
    research: "Fraction of edges leaving the pathway vs total: |Bd| / (|Bd| + 2|Ed|). Paper median: 0.96.",
  },
  relative_lcc: {
    term: "Largest connected component (LCC)",
    simple: "The LCC is the biggest island of proteins that can reach each other by following links.",
    research: "Relative LCC size is the fraction of disease proteins in that largest connected piece. Paper median: 0.21.",
  },
  component_distance: {
    term: "Distance between pathway components",
    simple: "If the disease proteins form several islands, this number estimates how far those islands sit from each other in the full map.",
    research:
      "Average shortest-path length between disconnected pathway components in the full PPI. Undefined when the pathway is a single component.",
  },
  modularity: {
    term: "Network modularity",
    simple: "Modularity asks whether disease proteins form a tidy cluster compared with the rest of the map.",
    research: "Newman’s modularity Q for the disease-versus-rest partition. Values near zero mean a weak module.",
  },
  spatial_association: {
    term: "Spatial network association",
    simple: "This test asks whether disease proteins sit closer together in the map than random proteins would.",
    research: "Ripley's K-function p-value from the paper’s pre-computed pathway features. p < 0.05 indicates significant clustering.",
  },
  recall25: {
    term: "Recall@25",
    simple: "Recall@25 asks: of the known relevant proteins held out in a test, how many did the method place in its top 25?",
    research: "Disease-centric 10-fold CV metric. Only Recall@25, Recall@100, and MRR are computed in this project.",
  },
  recall100: {
    term: "Recall@100",
    simple: "Recall@100 is the same idea as Recall@25, but looking at the top 100 ranked proteins.",
    research: "Mean Recall@100 across evaluated diseases in the existing CV tables. ROC-AUC, PR-AUC, F1, MSE, and R² were not computed.",
  },
  mrr: {
    term: "MRR",
    simple: "MRR (mean reciprocal rank) is higher when the first correct protein appears nearer the top of the list.",
    research: "Mean reciprocal rank from the project’s disease-centric 10-fold cross-validation.",
  },
};

export const METRIC_CONCEPT: Record<string, string> = {
  relative_lcc: "relative_lcc",
  density: "density",
  component_distance: "component_distance",
  conductance: "conductance",
  spatial_association: "spatial_association",
  modularity: "modularity",
};
