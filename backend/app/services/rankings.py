"""Prediction ranking and evidence from the live research engine."""

from __future__ import annotations

from typing import Optional

from fastapi.responses import StreamingResponse

from ..config import METHOD_ORDER, RESEARCH_DISCLAIMER
from ..schemas import PredictionEvidence, PredictionRow, PredictionsResponse
from ..store import store
from .prediction import predict_for_disease


def _row_from_series(rank: int, row) -> PredictionRow:
    return PredictionRow(
        rank=int(rank),
        protein_id=str(int(row["Gene ID"])),
        combined_score=float(row["Combined Score"]),
        neighborhood=float(row["Neighborhood"]),
        random_walk=float(row["Random Walk"]),
        diamond=float(row["DIAMOnD"]),
        neural_embeddings=float(row["Neural Embeddings"]),
        matrix_completion=float(row["Matrix Completion"]),
        known_disease_protein=bool(row.get("Known Disease Protein", False)),
    )


def get_predictions(disease_id: str, top_k: int = 50) -> PredictionsResponse:
    store.load()
    df = predict_for_disease(disease_id)
    k = max(1, min(int(top_k), 200))
    rows = []
    if not df.empty:
        G = store.require_graph()
        Hd, Vd = store.pathway(disease_id)
        seeds = set(Vd)
        for rank, row in df.head(k).iterrows():
            item = _row_from_series(int(rank), row)
            gid = int(row["Gene ID"])
            item.has_edge_to_pathway = (
                gid in G and any(nbr in seeds for nbr in G.neighbors(gid))
            )
            rows.append(item)
    return PredictionsResponse(
        disease_id=disease_id,
        disease_name=store.disease_names[disease_id],
        method_order=METHOD_ORDER,
        combined_score_definition=(
            "Mean of min–max-normalized scores from the five methods. "
            "This is not a separately trained logistic regression over the five scores."
        ),
        n_candidates=0 if df.empty else int(len(df)),
        top_k=k,
        predictions=rows,
    )


def prediction_evidence(disease_id: str, protein_id: int) -> Optional[PredictionEvidence]:
    df = predict_for_disease(disease_id)
    if df.empty:
        return None
    match = df[df["Gene ID"] == protein_id]
    if match.empty:
        return None
    rank = int(match.index[0])
    row = match.iloc[0]
    G = store.require_graph()
    _, Vd = store.pathway(disease_id)
    degree = int(G.degree(protein_id)) if protein_id in G else 0
    seed_neighbors = 0
    if protein_id in G:
        nbrs = set(G.neighbors(protein_id))
        seed_neighbors = len(nbrs & set(Vd))
    scores = {m: float(row[m]) for m in METHOD_ORDER}
    ranked = sorted(scores.values(), reverse=True)
    agreement = (
        "Method scores are not calibrated onto a shared scale; agreement is descriptive. "
        "The combined score averages min–max-normalized values. This is not a causal explanation."
    )
    return PredictionEvidence(
        protein_id=str(protein_id),
        disease_id=disease_id,
        rank=rank,
        combined_score=float(row["Combined Score"]),
        method_scores=scores,
        method_agreement_note=agreement + f" Highest raw method score among the five is {ranked[0]:.4g}.",
        neighborhood_seed_neighbors=seed_neighbors,
        neighborhood_degree=degree,
        disclaimer=RESEARCH_DISCLAIMER,
    )


def predictions_csv(disease_id: str, top_k: int = 100) -> StreamingResponse:
    df = predict_for_disease(disease_id).head(max(1, min(int(top_k), 500))).copy()
    df = df.reset_index()
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    def iter_bytes():
        yield csv_bytes

    filename = f"{disease_id}_predictions.csv"
    return StreamingResponse(
        iter_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
