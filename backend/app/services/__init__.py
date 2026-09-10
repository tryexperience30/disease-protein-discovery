"""Disease lookup, metrics, story, and search — all from existing artifacts."""

from __future__ import annotations

import math
from typing import Optional

import networkx as nx
import pandas as pd

from ..config import METRIC_META, RESEARCH_DISCLAIMER
from ..schemas import (
    DiseaseDetail,
    DiseaseListResponse,
    DiseaseStory,
    DiseaseSummary,
    MetricCard,
    SearchHit,
    SearchResponse,
    SimilarityResponse,
    StoryStep,
)
from ..store import store


def _safe_float(value) -> Optional[float]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Optional[float], digits: int = 4) -> str:
    if value is None:
        return "Not available"
    if abs(value) < 1e-3 and value != 0:
        return f"{value:.2e}"
    return f"{value:.{digits}f}"


def _safe_int(value, default: int = 0) -> int:
    parsed = _safe_float(value)
    if parsed is None:
        return default
    return int(parsed)


def _summary(did: str) -> DiseaseSummary:
    store.load()
    name = store.disease_names[did]
    genes = store.disease_genes[did]
    Hd, Vd = store.pathway(did)
    return DiseaseSummary(
        id=did,
        name=name,
        category=store.disease_classes.get(did),
        n_associated_proteins=len(genes),
        n_proteins_in_ppi=len(Vd),
        n_network_nodes=Hd.number_of_nodes(),
        n_network_edges=Hd.number_of_edges(),
        n_components=nx.number_connected_components(Hd) if Hd.number_of_nodes() else 0,
        predictions_available=did in store.disease_genes,
    )


def _summary_from_artifacts(did: str) -> DiseaseSummary:
    """List/search cards use precomputed metrics instead of rebuilding each pathway."""
    store.load()
    name = store.disease_names[did]
    genes = store.disease_genes[did]
    metrics = store.computed_metrics
    if metrics is not None and did in metrics.index:
        row = metrics.loc[did]
        n_in_ppi = _safe_int(row.get("Num Genes (in PPI)"), len(genes))
        n_edges = _safe_int(row.get("Num Internal Edges"), 0)
        n_comp = _safe_int(row.get("Num Components"), 0)
        return DiseaseSummary(
            id=did,
            name=name,
            category=store.disease_classes.get(did),
            n_associated_proteins=len(genes),
            n_proteins_in_ppi=n_in_ppi,
            n_network_nodes=n_in_ppi,
            n_network_edges=n_edges,
            n_components=n_comp,
            predictions_available=True,
        )
    return _summary(did)


def list_diseases(q: Optional[str] = None, limit: int = 50) -> DiseaseListResponse:
    store.load()
    items = sorted(store.disease_names.items(), key=lambda x: x[1])
    if q:
        needle = q.lower().strip()
        items = [
            (did, name)
            for did, name in items
            if needle in name.lower() or needle in did.lower()
        ]
    diseases = [_summary_from_artifacts(did) for did, _ in items[: max(1, min(limit, 519))]]
    return DiseaseListResponse(count=len(diseases), diseases=diseases)


def get_disease(did: str) -> DiseaseDetail:
    store.load()
    base = _summary(did)
    genes = sorted(store.disease_genes[did])
    return DiseaseDetail(
        **base.model_dump(),
        associated_protein_ids=[str(g) for g in genes],
        disclaimer=RESEARCH_DISCLAIMER,
    )


def get_metrics(did: str) -> list[MetricCard]:
    store.load()
    metrics_df = store.computed_metrics
    paper_df = store.paper_features
    cards: list[MetricCard] = []
    for meta in METRIC_META.values():
        col = meta["source_column"]
        value = None
        if meta["key"] == "spatial_association":
            if paper_df is not None and did in paper_df.index:
                value = _safe_float(paper_df.loc[did, "Spatial Network Association"])
        elif metrics_df is not None and did in metrics_df.index:
            if col in metrics_df.columns:
                value = _safe_float(metrics_df.loc[did, col])
        cards.append(
            MetricCard(
                key=meta["key"],
                label=meta["label"],
                value=value,
                formatted=_fmt(value),
                description=meta["description"],
                interpretation=meta["interpretation"],
                available=value is not None,
            )
        )
    return cards


def search(q: str, limit: int = 12) -> SearchResponse:
    store.load()
    needle = q.lower().strip()
    results: list[SearchHit] = []
    if not needle:
        return SearchResponse(query=q, results=[])

    disease_hits = []
    for did, name in store.disease_names.items():
        hay = f"{name} {did}".lower()
        if needle in hay:
            disease_hits.append(
                SearchHit(
                    type="disease",
                    id=did,
                    label=name,
                    subtitle=f"Disease ID: {did}",
                )
            )
    disease_hits.sort(key=lambda h: (0 if h.label.lower().startswith(needle) else 1, h.label))
    results.extend(disease_hits[:limit])

    remaining = max(0, limit - len(results))
    if remaining and needle.isdigit():
        gid = int(needle)
        if store.protein_in_ppi(gid):
            results.append(
                SearchHit(
                    type="protein",
                    id=str(gid),
                    label=f"Gene {gid}",
                    subtitle="Entrez Gene ID in PPI network",
                )
            )
            remaining -= 1

    if remaining and not needle.isdigit():
        # Name-only protein search is not supported: nodes are Entrez IDs.
        pass

    return SearchResponse(query=q, results=results[:limit])


def disease_story(did: str) -> DiseaseStory:
    store.load()
    name = store.disease_names[did]
    genes = store.disease_genes[did]
    Hd, Vd = store.pathway(did)
    metrics = {c.key: c for c in get_metrics(did)}
    lcc = metrics["relative_lcc"].formatted
    dens = metrics["density"].formatted
    cond = metrics["conductance"].formatted
    steps = [
        StoryStep(
            step=1,
            title="Disease-associated proteins",
            body=(
                f"{name} has {len(genes)} associated proteins in DisGeNET. "
                f"{len(Vd)} of them are present in the human PPI network."
            ),
            highlight=str(len(Vd)),
        ),
        StoryStep(
            step=2,
            title="Their PPI connections",
            body=(
                f"The disease pathway is the PPI subgraph induced by those proteins: "
                f"{Hd.number_of_nodes()} nodes and {Hd.number_of_edges()} internal interactions."
            ),
            highlight=str(Hd.number_of_edges()),
        ),
        StoryStep(
            step=3,
            title="Largest connected component",
            body=(
                f"Relative LCC size is {lcc}. This is the fraction of disease proteins "
                "that sit in the single largest connected piece of the pathway."
            ),
            highlight=lcc,
        ),
        StoryStep(
            step=4,
            title="Network structural properties",
            body=(
                f"Pathway density is {dens} and conductance is {cond}. "
                "Together they describe how tightly the proteins connect to each other "
                "versus the rest of the interactome."
            ),
        ),
        StoryStep(
            step=5,
            title="Predicted candidate proteins",
            body=(
                "Five computational methods score other PPI proteins as candidate "
                "associations. Rankings are computational prioritizations, not clinical findings."
            ),
        ),
        StoryStep(
            step=6,
            title="Top candidate proteins",
            body=(
                "Open the Predictions table for ranked candidates and method scores. "
                "The combined score is the mean of min–max-normalized method scores."
            ),
        ),
        StoryStep(
            step=7,
            title="Protein-level investigation",
            body=(
                "Select a protein to inspect its degree, known disease associations, "
                "and local neighborhood, then continue to the Protein Explorer."
            ),
        ),
    ]
    return DiseaseStory(disease_id=did, disease_name=name, steps=steps)


def disease_similarity(did: str) -> SimilarityResponse:
    store.load()
    _ = did
    return SimilarityResponse(
        available=False,
        reason=(
            "Disease–disease similarity is not computed in the validated research "
            "pipeline. The UI is reserved for a future method; no similarity scores "
            "are fabricated here."
        ),
        diseases=[],
    )
