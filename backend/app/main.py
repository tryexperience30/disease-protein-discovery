"""FastAPI application wrapping the validated disease–protein research pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .api.diseases import router as diseases_router
from .api.models import router as models_router
from .api.proteins import router as proteins_router
from .api.search import router as search_router
from .config import CORS_ORIGIN_REGEX, CORS_ORIGINS, RESEARCH_DISCLAIMER
from .store import store


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.load()
    yield


app = FastAPI(
    title="Disease–Protein Network Intelligence API",
    description=(
        "Research tool for computational disease–protein association analysis. "
        "Serves existing validated pipeline outputs (PPI pathways, structural metrics, "
        "live five-method rankings, disease-level graphlet orbit p-values, and CV metrics). "
        "Does not diagnose disease or claim causal protein–disease relationships.\n\n"
        f"**Disclaimer:** {RESEARCH_DISCLAIMER}\n\n"
        "Matrix Completion CV metrics are inflated because NMF is fitted on the full "
        "protein×disease matrix before fold splitting."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=CORS_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(diseases_router)
app.include_router(proteins_router)
app.include_router(models_router)
app.include_router(search_router)


@app.get("/health")
def liveness():
    """Cheap liveness probe. Does not expose internal dataset details."""
    return {"status": "ok"}


@app.get("/api/health")
def readiness():
    store.load()
    G = store.require_graph()
    return {
        "status": "ok",
        "n_ppi_nodes": G.number_of_nodes(),
        "n_ppi_edges": G.number_of_edges(),
        "n_diseases": len(store.disease_names),
        "disclaimer": RESEARCH_DISCLAIMER,
    }


@app.exception_handler(Exception)
async def unhandled_error(_request, exc: Exception):
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        raise exc
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The research pipeline did not return a result."},
    )
