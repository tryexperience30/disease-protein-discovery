from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..services.network import protein_network
from ..services.protein import (
    get_protein,
    parse_protein_id,
    protein_diseases,
    protein_graphlet_context,
)
from ..store import store

router = APIRouter(prefix="/api/proteins", tags=["proteins"])


@router.get("/{protein_id}")
def protein_detail(protein_id: str):
    try:
        gid = parse_protein_id(protein_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.load()
    if not store.protein_in_ppi(gid) and gid not in store.protein_to_diseases:
        raise HTTPException(status_code=404, detail=f"Unknown protein ID: {protein_id}")
    return get_protein(gid)


@router.get("/{protein_id}/diseases")
def protein_disease_links(protein_id: str):
    try:
        gid = parse_protein_id(protein_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.load()
    if not store.protein_in_ppi(gid) and gid not in store.protein_to_diseases:
        raise HTTPException(status_code=404, detail=f"Unknown protein ID: {protein_id}")
    return {"protein_id": str(gid), "diseases": [d.model_dump() for d in protein_diseases(gid)]}


@router.get("/{protein_id}/network")
def protein_local_network(
    protein_id: str,
    hops: int = Query(1, ge=1, le=2),
    limit: int = Query(80, ge=5, le=250),
):
    try:
        gid = parse_protein_id(protein_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.load()
    if not store.protein_in_ppi(gid):
        raise HTTPException(status_code=404, detail=f"Protein {protein_id} is not in the PPI network")
    return protein_network(gid, hops=hops, limit=limit)


@router.get("/{protein_id}/graphlets")
def protein_graphlets(protein_id: str, disease_id: str | None = None):
    try:
        gid = parse_protein_id(protein_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    store.load()
    if not store.protein_in_ppi(gid) and gid not in store.protein_to_diseases:
        raise HTTPException(status_code=404, detail=f"Unknown protein ID: {protein_id}")
    if disease_id and not store.disease_exists(disease_id):
        raise HTTPException(status_code=404, detail=f"Unknown disease ID: {disease_id}")
    return protein_graphlet_context(gid, disease_id=disease_id)
