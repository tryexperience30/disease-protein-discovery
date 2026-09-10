"""Pydantic response schemas for the public API."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class MetricCard(BaseModel):
    key: str
    label: str
    value: Optional[float] = None
    formatted: str
    description: str
    interpretation: str
    available: bool = True


class DiseaseSummary(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    n_associated_proteins: int
    n_proteins_in_ppi: int = 0
    n_network_nodes: int = 0
    n_network_edges: int = 0
    n_components: int = 0
    predictions_available: bool = True


class DiseaseDetail(DiseaseSummary):
    associated_protein_ids: list[str]
    disclaimer: str


class DiseaseListResponse(BaseModel):
    count: int
    diseases: list[DiseaseSummary]


class SearchHit(BaseModel):
    type: str
    id: str
    label: str
    subtitle: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchHit]


class NetworkNode(BaseModel):
    id: str
    label: str
    type: str
    score: Optional[float] = None
    degree: int = 0
    component: Optional[int] = None


class NetworkEdge(BaseModel):
    source: str
    target: str


class NetworkGraph(BaseModel):
    disease_id: Optional[str] = None
    protein_id: Optional[str] = None
    hops: int = 0
    truncated: bool = False
    truncation_note: Optional[str] = None
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]
    n_associated: int = 0
    n_predicted: int = 0
    n_other: int = 0


class PredictionRow(BaseModel):
    rank: int
    protein_id: str
    combined_score: float = Field(alias="combined_score")
    neighborhood: float
    random_walk: float
    diamond: float
    neural_embeddings: float
    matrix_completion: float
    known_disease_protein: bool = False
    has_edge_to_pathway: Optional[bool] = None

    model_config = {"populate_by_name": True}


class PredictionEvidence(BaseModel):
    protein_id: str
    disease_id: str
    rank: int
    combined_score: float
    method_scores: dict[str, float]
    method_agreement_note: str
    neighborhood_seed_neighbors: int
    neighborhood_degree: int
    disclaimer: str


class PredictionsResponse(BaseModel):
    disease_id: str
    disease_name: str
    method_order: list[str]
    combined_score_definition: str
    n_candidates: int
    top_k: int
    predictions: list[PredictionRow]


class ProteinOverview(BaseModel):
    id: str
    label: str
    in_ppi: bool
    degree: int = 0
    clustering_coefficient: Optional[float] = None
    triangles: Optional[int] = None
    n_associated_diseases: int = 0
    graphlet_note: str


class ProteinDiseaseLink(BaseModel):
    disease_id: str
    disease_name: str
    category: Optional[str] = None
    n_associated_proteins: int
    relation: str


class GraphletOrbit(BaseModel):
    orbit: int
    p_value: Optional[float] = None
    significant: bool = False
    graphlet_size: str


class GraphletProfile(BaseModel):
    scope: str
    disease_id: Optional[str] = None
    disease_name: Optional[str] = None
    n_significant: int
    alpha: float
    explanation: str
    orbits: list[GraphletOrbit]


class LocalStructuralFeatures(BaseModel):
    protein_id: str
    note: str
    features: dict[str, float]


class MethodInfo(BaseModel):
    name: str
    description: str
    evaluation_caveat: Optional[str] = None


class MethodPerformance(BaseModel):
    method: str
    n_diseases: int
    recall_at_25: float
    recall_at_100: float
    mrr: float


class ModelsResponse(BaseModel):
    methods: list[MethodInfo]
    metrics_available: list[str]
    metrics_not_computed: list[str]
    nmf_leakage_note: str
    performance: list[MethodPerformance]
    augmented: dict[str, Any]


class StoryStep(BaseModel):
    step: int
    title: str
    body: str
    highlight: Optional[str] = None


class DiseaseStory(BaseModel):
    disease_id: str
    disease_name: str
    steps: list[StoryStep]


class SimilarityResponse(BaseModel):
    available: bool
    reason: str
    diseases: list[Any] = []
