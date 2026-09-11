/**
 * Static JSON resolver for when NEXT_PUBLIC_API_URL is unset.
 * Shapes match the FastAPI responses so UI components stay unchanged.
 */

import type {
  DiseaseDetail,
  GraphletProfile,
  NetworkGraph,
  PredictionEvidence,
  PredictionRow,
  PredictionsResponse,
  ProteinDiseaseLink,
  ProteinGraphletContext,
  ProteinOverview,
  SearchHit,
} from "@/types";

type DiseasesFile = { count: number; disclaimer: string; diseases: DiseaseDetail[] };
type MetricsFile = Record<string, { disease_id: string; metrics: unknown[] }>;
type OrbitsFile = Record<string, GraphletProfile>;
type StoriesFile = Record<string, { disease_id: string; disease_name: string; steps: unknown[] }>;
type ProteinsFile = { count: number; proteins: Record<string, ProteinRecord> };
type ProteinRecord = {
  id: string;
  label: string;
  in_ppi: boolean;
  degree: number;
  n_associated_diseases: number;
  disease_ids: string[];
  graphlet_note: string;
};

type PredRow = PredictionRow & { pathway_neighbors?: string[]; degree?: number };
type PredFile = Omit<PredictionsResponse, "predictions"> & { predictions: PredRow[] };

const cache: Record<string, unknown> = {};

async function readGenerated<T>(relPath: string): Promise<T> {
  if (cache[relPath]) return cache[relPath] as T;
  if (typeof window === "undefined") {
    const fs = await import("fs/promises");
    const path = await import("path");
    const abs = path.join(process.cwd(), "public", "generated", relPath);
    const text = await fs.readFile(abs, "utf8");
    const data = JSON.parse(text) as T;
    cache[relPath] = data;
    return data;
  }
  const res = await fetch(`/generated/${relPath}`, { cache: "no-store" });
  if (!res.ok) {
    const error = new Error(`Static data not found (${relPath})`) as Error & { status?: number };
    error.status = res.status;
    throw error;
  }
  const data = (await res.json()) as T;
  cache[relPath] = data;
  return data;
}

function parseQuery(path: string): { pathname: string; params: URLSearchParams } {
  const [pathname, qs] = path.split("?");
  return { pathname, params: new URLSearchParams(qs || "") };
}

function notFound(detail: string): never {
  const error = new Error(detail) as Error & { status?: number };
  error.status = 404;
  throw error;
}

async function diseasesFile() {
  return readGenerated<DiseasesFile>("diseases.json");
}

function mergePredictedOverlay(graph: NetworkGraph, pred: PredFile, topK: number): NetworkGraph {
  const associated = new Set(graph.nodes.filter((n) => n.type === "associated").map((n) => n.id));
  const nodes = [...graph.nodes];
  const edges = [...graph.edges];
  const have = new Set(nodes.map((n) => n.id));
  let nPredicted = 0;
  for (const row of pred.predictions.slice(0, topK)) {
    if (!row.has_edge_to_pathway) continue;
    if (!have.has(row.protein_id)) {
      nodes.push({
        id: row.protein_id,
        label: row.protein_id,
        type: "predicted",
        score: row.combined_score,
        degree: row.degree ?? (row.pathway_neighbors || []).length,
        component: null,
      });
      have.add(row.protein_id);
    }
    nPredicted += 1;
    for (const nbr of row.pathway_neighbors || []) {
      if (!associated.has(nbr) && !have.has(nbr)) continue;
      const a = row.protein_id;
      const b = nbr;
      if (!edges.some((e) => (e.source === a && e.target === b) || (e.source === b && e.target === a))) {
        edges.push({ source: a, target: b });
      }
    }
  }
  return {
    ...graph,
    nodes,
    edges,
    n_predicted: nPredicted,
    n_other: nodes.filter((n) => n.type === "other").length,
  };
}

export async function staticGet<T>(path: string): Promise<T> {
  const { pathname, params } = parseQuery(path);
  const parts = pathname.replace(/\/+$/, "").split("/").filter(Boolean);

  if (pathname === "/api/diseases" || pathname === "/api/diseases/") {
    const all = await diseasesFile();
    const q = (params.get("q") || "").toLowerCase().trim();
    const limit = Math.max(1, Math.min(Number(params.get("limit") || 50), 519));
    let list = all.diseases;
    if (q) {
      list = list.filter((d) => d.name.toLowerCase().includes(q) || d.id.toLowerCase().includes(q));
    }
    return { count: Math.min(list.length, limit), diseases: list.slice(0, limit) } as T;
  }

  if (pathname === "/api/search" || pathname === "/api/search/") {
    const q = (params.get("q") || "").toLowerCase().trim();
    const limit = Math.max(1, Math.min(Number(params.get("limit") || 12), 30));
    const results: SearchHit[] = [];
    if (!q) return { query: params.get("q") || "", results } as T;
    const all = await diseasesFile();
    const hits = all.diseases
      .filter((d) => d.name.toLowerCase().includes(q) || d.id.toLowerCase().includes(q))
      .sort(
        (a, b) =>
          Number(a.name.toLowerCase().startsWith(q) ? 0 : 1) -
          Number(b.name.toLowerCase().startsWith(q) ? 0 : 1)
      )
      .slice(0, limit)
      .map((d) => ({
        type: "disease" as const,
        id: d.id,
        label: d.name,
        subtitle: `Disease ID: ${d.id}`,
      }));
    results.push(...hits);
    if (results.length < limit && /^\d+$/.test(q)) {
      try {
        const proteins = await readGenerated<ProteinsFile>("proteins.json");
        const rec = proteins.proteins[q];
        if (rec) {
          results.push({
            type: "protein",
            id: rec.id,
            label: rec.label,
            subtitle: rec.n_associated_diseases
              ? "Entrez Gene ID"
              : "Computational candidate (static export)",
          });
        }
      } catch {
        /* optional */
      }
    }
    return { query: params.get("q") || "", results: results.slice(0, limit) } as T;
  }

  if (pathname === "/api/models" || pathname === "/api/models/performance") {
    const models = await readGenerated<Record<string, unknown>>("models.json");
    const diseaseId = params.get("disease_id");
    if (!diseaseId) return models as T;
    return {
      ...models,
      disease_id: diseaseId,
      disease_performance: [],
      disease_note:
        "Per-disease CV rows are available from the live FastAPI backend. Static mode shows overall CV metrics only.",
    } as T;
  }

  if (parts[0] === "api" && parts[1] === "diseases" && parts[2]) {
    const id = parts[2];
    const all = await diseasesFile();
    const disease = all.diseases.find((d) => d.id === id);
    if (!disease) notFound(`Unknown disease ID: ${id}`);

    if (parts.length === 3) return disease as T;

    if (parts[3] === "metrics") {
      const metrics = await readGenerated<MetricsFile>("metrics.json");
      return (metrics[id] || { disease_id: id, metrics: [] }) as T;
    }
    if (parts[3] === "graphlets") {
      const orbits = await readGenerated<OrbitsFile>("orbits.json");
      if (!orbits[id]) notFound(`Unknown disease ID: ${id}`);
      return orbits[id] as T;
    }
    if (parts[3] === "story") {
      try {
        const stories = await readGenerated<StoriesFile>("stories.json");
        if (stories[id]) return stories[id] as T;
      } catch {
        /* fall through to a catalog-derived story */
      }
      const metricsFile = await readGenerated<MetricsFile>("metrics.json");
      const metrics = (metricsFile[id]?.metrics || []) as Array<{ key: string; formatted: string }>;
      const fmt = (key: string) => metrics.find((m) => m.key === key)?.formatted || "—";
      return {
        disease_id: disease.id,
        disease_name: disease.name,
        steps: [
          {
            step: 1,
            title: "Disease-associated proteins",
            body: `${disease.name} has ${disease.n_associated_proteins} associated proteins in DisGeNET. ${disease.n_proteins_in_ppi} of them are present in the human PPI network.`,
            highlight: String(disease.n_proteins_in_ppi),
          },
          {
            step: 2,
            title: "Their PPI connections",
            body: `The disease pathway is the PPI subgraph induced by those proteins: ${disease.n_network_nodes} nodes and ${disease.n_network_edges} internal interactions.`,
            highlight: String(disease.n_network_edges),
          },
          {
            step: 3,
            title: "Largest connected component",
            body: `Relative LCC size is ${fmt("relative_lcc")}. This is the fraction of disease proteins that sit in the single largest connected piece of the pathway.`,
            highlight: fmt("relative_lcc"),
          },
          {
            step: 4,
            title: "Network structural properties",
            body: `Pathway density is ${fmt("density")} and conductance is ${fmt("conductance")}. Together they describe how tightly the proteins connect to each other versus the rest of the interactome.`,
          },
          {
            step: 5,
            title: "Predicted candidate proteins",
            body: "Five computational methods score other PPI proteins as candidate associations. Rankings are computational prioritizations, not clinical findings.",
          },
          {
            step: 6,
            title: "Top candidate proteins",
            body: "Open the Predictions table for ranked candidates and method scores. The combined score is the mean of min–max-normalized method scores.",
          },
          {
            step: 7,
            title: "Protein-level investigation",
            body: "Select a protein to inspect its degree, known disease associations, and local neighborhood, then continue to the Protein Explorer.",
          },
        ],
      } as T;
    }
    if (parts[3] === "similar") {
      return {
        available: false,
        reason:
          "Disease–disease similarity is not computed in the validated research pipeline. The UI is reserved for a future method; no similarity scores are fabricated here.",
        diseases: [],
      } as T;
    }
    if (parts[3] === "network") {
      const graph = await readGenerated<NetworkGraph>(`networks/${id}.json`);
      const hops = Number(params.get("hops") || 0);
      const includePredicted = params.get("include_predicted") === "true";
      const topK = Math.max(1, Math.min(Number(params.get("top_k") || 15), 100));
      let out = graph;
      if (includePredicted) {
        const pred = await readGenerated<PredFile>(`predictions/${id}.json`);
        out = mergePredictedOverlay(graph, pred, topK);
      }
      if (hops >= 1) {
        out = {
          ...out,
          hops: 0,
          truncated: true,
          truncation_note:
            "1-hop expansion is not included in the static dataset. Use the local FastAPI/Docker backend for capped neighborhood expansion.",
        };
      }
      return out as T;
    }
    if (parts[3] === "predictions" && parts[4] && parts[5] === "evidence") {
      const pred = await readGenerated<PredFile>(`predictions/${id}.json`);
      const row = pred.predictions.find((p) => p.protein_id === parts[4]);
      if (!row) notFound("No prediction score for this protein in this disease");
      const scores = {
        Neighborhood: row.neighborhood,
        "Random Walk": row.random_walk,
        DIAMOnD: row.diamond,
        "Neural Embeddings": row.neural_embeddings,
        "Matrix Completion": row.matrix_completion,
      };
      const ranked = Object.values(scores).sort((a, b) => b - a);
      const evidence: PredictionEvidence & {
        protein_id: string;
        disease_id: string;
        combined_score: number;
        method_scores: Record<string, number>;
        disclaimer: string;
      } = {
        rank: row.rank,
        neighborhood_seed_neighbors: (row.pathway_neighbors || []).length,
        neighborhood_degree: row.degree ?? (row.pathway_neighbors || []).length,
        method_agreement_note:
          "Method scores are not calibrated onto a shared scale; agreement is descriptive. " +
          "The combined score averages min–max-normalized values. This is not a causal explanation. " +
          `Highest raw method score among the five is ${ranked[0]}.`,
        protein_id: row.protein_id,
        disease_id: id,
        combined_score: row.combined_score,
        method_scores: scores,
        disclaimer: disease.disclaimer,
      };
      return evidence as T;
    }
    if (parts[3] === "predictions") {
      const pred = await readGenerated<PredFile>(`predictions/${id}.json`);
      const topK = Math.max(1, Math.min(Number(params.get("top_k") || 50), 200));
      return {
        ...pred,
        top_k: Math.min(topK, pred.predictions.length),
        predictions: pred.predictions.slice(0, topK),
      } as T;
    }
    if (parts[3] === "downloads") {
      notFound("Use the in-page download in static mode");
    }
  }

  if (parts[0] === "api" && parts[1] === "proteins" && parts[2]) {
    const pid = parts[2];
    const proteins = await readGenerated<ProteinsFile>("proteins.json");
    const rec = proteins.proteins[pid];
    if (!rec) {
      notFound(
        `Unknown protein ID: ${pid}. Static mode includes associated proteins and exported Top-100 candidates only.`
      );
    }
    const all = await diseasesFile();
    const diseaseLinks: ProteinDiseaseLink[] = rec.disease_ids.map((did) => {
      const d = all.diseases.find((x) => x.id === did);
      return {
        disease_id: did,
        disease_name: d?.name || did,
        category: d?.category || null,
      };
    });

    if (parts.length === 3) {
      const overview: ProteinOverview = {
        id: rec.id,
        label: rec.label,
        in_ppi: rec.in_ppi,
        degree: rec.degree,
        clustering_coefficient: null,
        triangles: null,
        n_associated_diseases: rec.n_associated_diseases,
        graphlet_note: rec.graphlet_note,
      };
      return overview as T;
    }
    if (parts[3] === "diseases") {
      return { protein_id: pid, diseases: diseaseLinks } as T;
    }
    if (parts[3] === "network") {
      const error = new Error(
        "Protein neighborhood graphs are not included in the static dataset. Run the local FastAPI or Docker backend to inspect 1-hop PPI neighborhoods."
      ) as Error & { status?: number };
      error.status = 404;
      throw error;
    }
    if (parts[3] === "graphlets") {
      const orbits = await readGenerated<OrbitsFile>("orbits.json");
      const selected = rec.disease_ids[0];
      const ctx: ProteinGraphletContext = {
        local_structural_features: {
          features: { degree: rec.degree },
        },
        disease_orbit_profile: selected ? orbits[selected] : null,
      };
      return ctx as T;
    }
  }

  notFound(`No static mapping for ${pathname}`);
}

export async function staticDownload(path: string): Promise<void> {
  const { pathname, params } = parseQuery(path);
  const parts = pathname.split("/").filter(Boolean);
  if (parts[3] === "downloads" && parts[4] === "predictions.csv") {
    const id = parts[2];
    const pred = await staticGet<PredictionsResponse>(
      `/api/diseases/${id}/predictions?top_k=${params.get("top_k") || 100}`
    );
    const header =
      "Rank,Gene ID,Neighborhood,Random Walk,DIAMOnD,Neural Embeddings,Matrix Completion,Combined Score";
    const lines = pred.predictions.map(
      (p) =>
        `${p.rank},${p.protein_id},${p.neighborhood},${p.random_walk},${p.diamond},${p.neural_embeddings},${p.matrix_completion},${p.combined_score}`
    );
    triggerBlob([header, ...lines].join("\n"), `${id}_predictions.csv`, "text/csv");
    return;
  }
  if (parts[3] === "downloads" && parts[4] === "graphlets.csv") {
    const id = parts[2];
    const profile = await staticGet<GraphletProfile>(`/api/diseases/${id}/graphlets`);
    const header = "orbit,p_value,significant,graphlet_size";
    const lines = profile.orbits.map(
      (o) => `${o.orbit},${o.p_value ?? ""},${o.significant},${o.graphlet_size}`
    );
    triggerBlob([header, ...lines].join("\n"), `${id}_graphlets.csv`, "text/csv");
  }
}

function triggerBlob(text: string, filename: string, type: string) {
  if (typeof window === "undefined") return;
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
