from __future__ import annotations

from fastapi import APIRouter, Query

from ..services import search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
def search_endpoint(q: str = Query("", max_length=80), limit: int = Query(12, ge=1, le=30)):
    return search(q=q, limit=limit)
