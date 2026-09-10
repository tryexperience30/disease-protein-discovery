export type MetricCard = {
  key: string;
  label: string;
  value: number | null;
  formatted: string;
  description: string;
  interpretation: string;
  available: boolean;
};

export type DiseaseSummary = {
  id: string;
  name: string;
  category: string | null;
  n_associated_proteins: number;
  n_proteins_in_ppi: number;
  n_network_nodes: number;
  n_network_edges: number;
  n_components: number;
  predictions_available: boolean;
};

export type DiseaseDetail = DiseaseSummary & {
  associated_protein_ids: string[];
  disclaimer: string;
};

export type SearchHit = {
  type: "disease" | "protein";
  id: string;
  label: string;
  subtitle: string | null;
};

export type NetworkNode = {
  id: string;
  label: string;
  type: "associated" | "predicted" | "other";
  score: number | null;
  degree: number;
  component: number | null;
};

export type NetworkEdge = { source: string; target: string };

export type NetworkGraph = {
  disease_id?: string | null;
  protein_id?: string | null;
  hops: number;
  truncated: boolean;
  truncation_note: string | null;
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  n_associated: number;
  n_predicted: number;
  n_other: number;
};

export type PredictionRow = {
  rank: number;
  protein_id: string;
  combined_score: number;
  neighborhood: number;
  random_walk: number;
  diamond: number;
  neural_embeddings: number;
  matrix_completion: number;
  known_disease_protein: boolean;
  has_edge_to_pathway: boolean | null;
};

export type PredictionsResponse = {
  disease_id: string;
  disease_name: string;
  method_order: string[];
  combined_score_definition: string;
  n_candidates: number;
  top_k: number;
  predictions: PredictionRow[];
};

export type ProteinOverview = {
  id: string;
  label: string;
  in_ppi: boolean;
  degree: number;
  clustering_coefficient: number | null;
  triangles: number | null;
  n_associated_diseases: number;
  graphlet_note: string;
};

export type GraphletOrbit = {
  orbit: number;
  p_value: number | null;
  significant: boolean;
  graphlet_size: string;
};

export type GraphletProfile = {
  n_significant: number;
  explanation: string;
  orbits: GraphletOrbit[];
  disease_id?: string | null;
  disease_name?: string | null;
};

export type PredictionEvidence = {
  rank: number;
  neighborhood_seed_neighbors: number;
  neighborhood_degree: number;
  method_agreement_note: string;
};

export type ProteinDiseaseLink = {
  disease_id: string;
  disease_name: string;
  category: string | null;
};

export type ProteinGraphletContext = {
  local_structural_features?: { features?: Record<string, number> };
  disease_orbit_profile?: GraphletProfile | null;
};
