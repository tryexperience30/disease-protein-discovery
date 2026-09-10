from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse

from ..config import RESEARCH_DISCLAIMER
from ..schemas import DiseaseDetail, DiseaseListResponse, DiseaseStory, SimilarityResponse
from ..services import disease_similarity, disease_story, get_disease, get_metrics, list_diseases
from ..services.network import disease_network
from ..services.protein import disease_graphlets
from ..services.rankings import get_predictions, prediction_evidence, predictions_csv
from ..store import store

router = APIRouter(prefix="/api/diseases", tags=["diseases"])


@router.get("", response_model=DiseaseListResponse)
def diseases(q: str | None = None, limit: int = Query(50, ge=1, le=519)):
    return list_diseases(q=q, limit=limit)


@router.get("/{disease_id}", response_model=DiseaseDetail)
def disease_detail(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return get_disease(disease_id)


@router.get("/{disease_id}/metrics")
def disease_metrics(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return {"disease_id": disease_id, "metrics": [m.model_dump() for m in get_metrics(disease_id)]}


@router.get("/{disease_id}/network")
def disease_network_endpoint(
    disease_id: str,
    include_predicted: bool = False,
    top_k: int = Query(15, ge=1, le=100),
    hops: int = Query(0, ge=0, le=2),
    max_extra_nodes: int = Query(200, ge=0, le=500),
):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return disease_network(
        disease_id,
        include_predicted=include_predicted,
        top_k=top_k,
        hops=hops,
        max_extra_nodes=max_extra_nodes,
    )


@router.get("/{disease_id}/predictions")
def disease_predictions(disease_id: str, top_k: int = Query(50, ge=1, le=200)):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return get_predictions(disease_id, top_k=top_k)


@router.get("/{disease_id}/predictions/{protein_id}/evidence")
def disease_prediction_evidence(disease_id: str, protein_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    try:
        gid = int(protein_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="protein_id must be an Entrez Gene ID") from exc
    ev = prediction_evidence(disease_id, gid)
    if ev is None:
        raise HTTPException(status_code=404, detail="No prediction score for this protein in this disease")
    return ev


@router.get("/{disease_id}/graphlets")
def disease_graphlet_profile(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return disease_graphlets(disease_id)


@router.get("/{disease_id}/story", response_model=DiseaseStory)
def story(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return disease_story(disease_id)


@router.get("/{disease_id}/similar", response_model=SimilarityResponse)
def similar(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return disease_similarity(disease_id)


@router.get("/{disease_id}/downloads/predictions.csv")
def download_predictions(disease_id: str, top_k: int = Query(100, ge=1, le=500)):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return predictions_csv(disease_id, top_k=top_k)


@router.get("/{disease_id}/downloads/metrics.json")
def download_metrics(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    payload = {
        "disease_id": disease_id,
        "disclaimer": RESEARCH_DISCLAIMER,
        "metrics": [m.model_dump() for m in get_metrics(disease_id)],
    }
    return JSONResponse(payload)


@router.get("/{disease_id}/downloads/network.json")
def download_network(disease_id: str, include_predicted: bool = False, top_k: int = 15):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    graph = disease_network(disease_id, include_predicted=include_predicted, top_k=top_k)
    return JSONResponse(graph.model_dump())


@router.get("/{disease_id}/downloads/graphlets.csv")
def download_graphlets(disease_id: str):
    store.load()
    if not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    profile = disease_graphlets(disease_id)
    lines = ["orbit,p_value,significant,graphlet_size"]
    for o in profile.orbits:
        lines.append(f"{o.orbit},{'' if o.p_value is None else o.p_value},{o.significant},{o.graphlet_size}")
    csv_text = "\n".join(lines) + "\n"

    def iter_bytes():
        yield csv_text.encode("utf-8")

    return StreamingResponse(
        iter_bytes(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{disease_id}_graphlets.csv"'},
    )
