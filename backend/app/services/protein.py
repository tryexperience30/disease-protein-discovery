"""Protein explorer adapters over the existing PPI and association tables."""

from __future__ import annotations

from typing import Optional

import networkx as nx

from ..config import PROXY_FEATURE_LABELS, RESEARCH_DISCLAIMER
from ..schemas import (
    GraphletOrbit,
    GraphletProfile,
    LocalStructuralFeatures,
    ProteinDiseaseLink,
    ProteinOverview,
)
from ..store import store

ORBIT_SIZE = []
for i in range(73):
    if i <= 0:
        ORBIT_SIZE.append("2-node")
    elif i <= 3:
        ORBIT_SIZE.append("3-node")
    elif i <= 14:
        ORBIT_SIZE.append("4-node")
    else:
        ORBIT_SIZE.append("5-node")


def parse_protein_id(protein_id: str) -> int:
    try:
        return int(str(protein_id).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Protein IDs in this dataset are Entrez Gene IDs (integers).") from exc


def local_structural_features(gene_id: int) -> dict[str, float]:
    """Compute the 12 proxy features for one protein (motif_analysis.py definitions)."""
    G = store.require_graph()
    n = G.number_of_nodes()
    deg = G.degree(gene_id)
    clustering = nx.clustering(G, gene_id)
    triangles = nx.triangles(G, gene_id)
    nbrs = list(G.neighbors(gene_id))
    if nbrs:
        nbr_degs = [G.degree(nb) for nb in nbrs]
        avg_nbr = float(sum(nbr_degs) / len(nbr_degs))
        nbr_min = float(min(nbr_degs))
        nbr_max = float(max(nbr_degs))
        mean = avg_nbr
        var = sum((d - mean) ** 2 for d in nbr_degs) / len(nbr_degs)
        nbr_std = var ** 0.5
        two_paths = float(sum(G.degree(nb) - 1 for nb in nbrs))
        nbr_set = set(nbrs)
        sq = 0
        for nb in nbrs:
            common = nbr_set & (set(G.neighbors(nb)) - {gene_id})
            sq += len(common)
        square_approx = sq / 2.0
    else:
        avg_nbr = nbr_min = nbr_max = nbr_std = two_paths = square_approx = 0.0
    degree_centrality = deg / (n - 1) if n > 1 else 0.0
    bridge = deg - 2 * triangles / max(deg, 1)
    values = [
        float(deg),
        float(clustering),
        float(triangles),
        float(avg_nbr),
        float(degree_centrality),
        float(nbr_min),
        float(nbr_max),
        float(avg_nbr),
        float(nbr_std),
        float(two_paths),
        float(square_approx),
        float(bridge),
    ]
    return dict(zip(PROXY_FEATURE_LABELS, values))


def get_protein(gene_id: int) -> ProteinOverview:
    G = store.require_graph()
    in_ppi = gene_id in G
    diseases = store.protein_to_diseases.get(gene_id, [])
    feats = local_structural_features(gene_id) if in_ppi else {}
    return ProteinOverview(
        id=str(gene_id),
        label=f"Gene {gene_id}",
        in_ppi=in_ppi,
        degree=int(feats.get("degree", 0)),
        clustering_coefficient=feats.get("clustering_coefficient"),
        triangles=int(feats["triangles"]) if "triangles" in feats else None,
        n_associated_diseases=len(diseases),
        graphlet_note=(
            "Per-protein 73-orbit ORCA signatures are not computed in this project. "
            "Disease-level 73-orbit p-values are available for associated diseases. "
            "Per-protein structure uses the 12-dimensional motif-signature proxy "
            "from motif_analysis.py."
        ),
    )


def protein_diseases(gene_id: int) -> list[ProteinDiseaseLink]:
    store.load()
    links = []
    for did in store.protein_to_diseases.get(gene_id, []):
        links.append(
            ProteinDiseaseLink(
                disease_id=did,
                disease_name=store.disease_names[did],
                category=store.disease_classes.get(did),
                n_associated_proteins=len(store.disease_genes[did]),
                relation="known_association",
            )
        )
    links.sort(key=lambda x: x.disease_name)
    return links


def disease_graphlets(disease_id: str) -> GraphletProfile:
    store.load()
    motifs = store.motifs
    name = store.disease_names[disease_id]
    if motifs is None or disease_id not in motifs.index:
        return GraphletProfile(
            scope="disease",
            disease_id=disease_id,
            disease_name=name,
            n_significant=0,
            alpha=0.01,
            explanation=(
                "Graphlets capture local network topology by describing how proteins "
                "participate in small network motifs. No orbit p-values are stored "
                "for this disease."
            ),
            orbits=[],
        )
    orbit_cols = [c for c in motifs.columns if str(c).startswith("orbit_")]
    orbits = []
    n_sig = 0
    for col in orbit_cols:
        idx = int(str(col).split("_")[1])
        raw = motifs.loc[disease_id, col]
        try:
            pval = float(raw)
        except (TypeError, ValueError):
            pval = None
        sig = pval is not None and pval < 0.01
        if sig:
            n_sig += 1
        orbits.append(
            GraphletOrbit(
                orbit=idx,
                p_value=pval,
                significant=sig,
                graphlet_size=ORBIT_SIZE[idx] if idx < len(ORBIT_SIZE) else "unknown",
            )
        )
    return GraphletProfile(
        scope="disease",
        disease_id=disease_id,
        disease_name=name,
        n_significant=n_sig,
        alpha=0.01,
        explanation=(
            "Graphlets capture local network topology by describing how a protein "
            "participates in small network motifs. These 73 values are disease-level "
            "orbit significance p-values from the SNAP dataset (permutation test), "
            "not per-protein ORCA counts."
        ),
        orbits=orbits,
    )


def protein_graphlet_context(gene_id: int, disease_id: Optional[str] = None):
    diseases = protein_diseases(gene_id)
    if disease_id is None and diseases:
        disease_id = diseases[0].disease_id
    profile = disease_graphlets(disease_id) if disease_id else None
    features = LocalStructuralFeatures(
        protein_id=str(gene_id),
        note=(
            "These 12 features are the motif-signature proxy defined in "
            "motif_analysis.compute_protein_motif_features. They are not the "
            "full 73-orbit ORCA signature."
        ),
        features=local_structural_features(gene_id) if store.protein_in_ppi(gene_id) else {},
    )
    return {
        "protein_id": str(gene_id),
        "disclaimer": RESEARCH_DISCLAIMER,
        "associated_diseases": [d.model_dump() for d in diseases],
        "selected_disease_id": disease_id,
        "disease_orbit_profile": profile.model_dump() if profile else None,
        "local_structural_features": features.model_dump(),
    }
