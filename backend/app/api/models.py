from __future__ import annotations

from fastapi import APIRouter, Query

from ..services.models import models_payload, per_disease_performance
from ..store import store

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("")
def list_models():
    payload = models_payload()
    return {
        "methods": [m.model_dump() for m in payload.methods],
        "metrics_available": payload.metrics_available,
        "metrics_not_computed": payload.metrics_not_computed,
        "nmf_leakage_note": payload.nmf_leakage_note,
    }


@router.get("/performance")
def model_performance(disease_id: str | None = Query(None)):
    payload = models_payload()
    body = payload.model_dump()
    if disease_id:
        store.load()
        if store.disease_exists(disease_id):
            body["disease_id"] = disease_id
            body["disease_performance"] = per_disease_performance(disease_id)
        else:
            body["disease_id"] = disease_id
            body["disease_performance"] = []
            body["disease_note"] = "Unknown disease ID; overall metrics still returned."
    return body
