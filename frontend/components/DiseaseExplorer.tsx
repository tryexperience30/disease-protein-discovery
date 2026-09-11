"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiGet, downloadResource, isStaticMode } from "@/lib/api";
import { formatInt } from "@/lib/format";
import type {
  DiseaseDetail,
  MetricCard as Metric,
  NetworkGraph,
  NetworkNode,
  GraphletProfile,
  PredictionEvidence,
  PredictionsResponse,
} from "@/types";
import { GraphletChart } from "@/components/GraphletChart";
import { MetricCard } from "@/components/MetricCard";
import { useMode } from "@/components/ModeProvider";
import { NetworkCanvas } from "@/components/NetworkCanvas";
import { PredictionTable } from "@/components/PredictionTable";

type Tab = "overview" | "network" | "predictions" | "graphlets" | "story";

export function DiseaseExplorer({ diseaseId }: { diseaseId: string }) {
  const { mode } = useMode();
  const [tab, setTab] = useState<Tab>("overview");
  const [disease, setDisease] = useState<DiseaseDetail | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [graph, setGraph] = useState<NetworkGraph | null>(null);
  const [preds, setPreds] = useState<PredictionsResponse | null>(null);
  const [orbits, setOrbits] = useState<GraphletProfile | null>(null);
  const [story, setStory] = useState<{ steps: { step: number; title: string; body: string }[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"3d" | "2d">("3d");
  const [showLabels, setShowLabels] = useState(false);
  const [includePredicted, setIncludePredicted] = useState(false);
  const [topK, setTopK] = useState(15);
  const [hops, setHops] = useState(0);
  const [selected, setSelected] = useState<NetworkNode | null>(null);
  const [evidence, setEvidence] = useState<PredictionEvidence | null>(null);
  const [loadingNet, setLoadingNet] = useState(false);
  const [loadingPred, setLoadingPred] = useState(false);
  const [similar, setSimilar] = useState<{ available: boolean; reason: string } | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    Promise.all([
      apiGet<DiseaseDetail>(`/api/diseases/${diseaseId}`),
      apiGet<{ metrics: Metric[] }>(`/api/diseases/${diseaseId}/metrics`),
    ])
      .then(([d, m]) => {
        if (cancelled) return;
        setDisease(d);
        setMetrics(m.metrics);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [diseaseId]);

  const loadNetwork = useCallback(async () => {
    setLoadingNet(true);
    try {
      const g = await apiGet<NetworkGraph>(
        `/api/diseases/${diseaseId}/network?include_predicted=${includePredicted}&top_k=${topK}&hops=${hops}`
      );
      setGraph(g);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoadingNet(false);
    }
  }, [diseaseId, includePredicted, topK, hops]);

  useEffect(() => {
    if (tab === "network") loadNetwork();
  }, [tab, loadNetwork]);

  useEffect(() => {
    if (tab !== "predictions" || preds) return;
    setLoadingPred(true);
    apiGet<PredictionsResponse>(`/api/diseases/${diseaseId}/predictions?top_k=100`)
      .then(setPreds)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoadingPred(false));
  }, [tab, diseaseId, preds]);

  useEffect(() => {
    if (tab !== "graphlets" || orbits) return;
    apiGet<GraphletProfile>(`/api/diseases/${diseaseId}/graphlets`).then(setOrbits).catch((e: Error) => setError(e.message));
  }, [tab, diseaseId, orbits]);

  useEffect(() => {
    if (tab !== "story" || story) return;
    apiGet<{ steps: { step: number; title: string; body: string }[] }>(`/api/diseases/${diseaseId}/story`)
      .then(setStory)
      .catch((e: Error) => setError(e.message));
    apiGet<{ available: boolean; reason: string }>(`/api/diseases/${diseaseId}/similar`)
      .then(setSimilar)
      .catch(() => undefined);
  }, [tab, diseaseId, story]);

  async function selectNode(node: NetworkNode) {
    setSelected(node);
    setEvidence(null);
    if (node.type === "predicted") {
      try {
        const ev = await apiGet<PredictionEvidence>(`/api/diseases/${diseaseId}/predictions/${node.id}/evidence`);
        setEvidence(ev);
      } catch {
        setEvidence(null);
      }
    }
  }

  if (error && !disease) {
    return (
      <div className="panel mx-auto max-w-xl p-8 text-center">
        <h1 className="text-xl">Disease not available</h1>
        <p className="mt-2 text-muted">{error}</p>
        <Link href="/" className="mt-4 inline-block text-accent">
          Back to search
        </Link>
      </div>
    );
  }

  if (!disease) {
    return <p className="text-muted">Loading disease network…</p>;
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "network", label: "Network" },
    { id: "predictions", label: "Predictions" },
    { id: "graphlets", label: "Graphlets" },
    { id: "story", label: "Story" },
  ];

  return (
    <div className="space-y-8">
      <header className="space-y-3">
        <p className="text-xs uppercase tracking-[0.2em] text-muted">Disease explorer</p>
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">{disease.name}</h1>
        <p className="text-sm text-muted">{disease.disclaimer}</p>
        <dl className="grid grid-cols-2 gap-3 md:grid-cols-6">
          <Stat label="Disease ID" value={disease.id} />
          <Stat label="Associated proteins" value={formatInt(disease.n_associated_proteins)} />
          <Stat label="Network nodes" value={formatInt(disease.n_network_nodes)} />
          <Stat label="Edges" value={formatInt(disease.n_network_edges)} />
          <Stat label="Components" value={formatInt(disease.n_components)} />
          <Stat label="Predictions" value={disease.predictions_available ? "Available" : "No"} />
        </dl>
      </header>

      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-full border px-4 py-2 text-sm ${tab === t.id ? "border-accent" : "border-line text-muted"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {metrics.map((m) => (
            <MetricCard key={m.key} metric={m} research={mode === "research"} />
          ))}
        </section>
      )}

      {tab === "network" && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <div className="inline-flex rounded-full border border-line p-1">
              <button type="button" className={`rounded-full px-3 py-1 ${view === "3d" ? "bg-white/10" : "text-muted"}`} onClick={() => setView("3d")}>
                3D Network
              </button>
              <button type="button" className={`rounded-full px-3 py-1 ${view === "2d" ? "bg-white/10" : "text-muted"}`} onClick={() => setView("2d")}>
                2D Network
              </button>
            </div>
            <label className="flex items-center gap-2 text-muted">
              <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} />
              Labels
            </label>
            <label className="flex items-center gap-2 text-muted">
              <input type="checkbox" checked={includePredicted} onChange={(e) => setIncludePredicted(e.target.checked)} />
              Predicted proteins
            </label>
            <label className="flex items-center gap-2 text-muted">
              Top-K
              <input
                type="range"
                min={5}
                max={50}
                value={topK}
                disabled={!includePredicted}
                onChange={(e) => setTopK(Number(e.target.value))}
              />
              {topK}
            </label>
            <label className="flex items-center gap-2 text-muted">
              Neighborhood
              <select value={hops} onChange={(e) => setHops(Number(e.target.value))} className="rounded-md border border-line bg-[#0c111b] px-2 py-1">
                <option value={0}>Pathway only</option>
                <option value={1}>{isStaticMode() ? "1-hop (not in static data)" : "1-hop (capped)"}</option>
              </select>
            </label>
            <span className="text-xs text-muted">
              Blue = associated · Amber = predicted candidate · Gray = other
            </span>
          </div>
          {loadingNet && <p className="text-muted">Loading network subset…</p>}
          {graph && (
            <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
              <NetworkCanvas
                graph={graph}
                mode={view}
                showLabels={showLabels}
                onSelect={selectNode}
                highlightId={selected?.id}
              />
              <aside className={`panel p-4 ${selected ? "" : "hidden lg:block"}`}>
                {selected ? (
                  <div className="space-y-2 text-sm">
                    <h3 className="text-lg">Gene {selected.id}</h3>
                    <p>Type: {selected.type}</p>
                    <p>Degree in view: {selected.degree}</p>
                    {selected.score != null && <p>Combined score: {selected.score.toFixed(4)}</p>}
                    {evidence && (
                      <div className="space-y-1 text-muted">
                        <p>Rank {evidence.rank}</p>
                        <p>Seed neighbors: {evidence.neighborhood_seed_neighbors} / degree {evidence.neighborhood_degree}</p>
                        <p>{evidence.method_agreement_note}</p>
                      </div>
                    )}
                    <Link className="inline-block text-accent" href={`/protein/${selected.id}`}>
                      Open Protein Explorer
                    </Link>
                  </div>
                ) : (
                  <p className="text-sm text-muted">Click a protein to inspect it. Nodes are Entrez Gene IDs; gene symbols are not in this dataset.</p>
                )}
                {graph.truncated && <p className="mt-3 text-xs text-predict">{graph.truncation_note}</p>}
              </aside>
            </div>
          )}
        </section>
      )}

      {tab === "predictions" && (
        <section className="space-y-4">
          {loadingPred && (
            <p className="text-muted">Loading precomputed rankings from the validated research pipeline…</p>
          )}
          {preds && preds.predictions.length === 0 && <p className="text-muted">No ranked candidates for this disease.</p>}
          {preds && preds.predictions.length > 0 && (
            <PredictionTable
              data={preds}
              onSelect={(id) => {
                setTab("network");
                setIncludePredicted(true);
                setSelected({ id, label: id, type: "predicted", score: null, degree: 0, component: null });
              }}
            />
          )}
          {mode === "research" && (
            <button
              type="button"
              className="text-sm text-accent"
              onClick={() =>
                void downloadResource(`/api/diseases/${diseaseId}/downloads/predictions.csv?top_k=100`)
              }
            >
              Download prediction table (CSV)
            </button>
          )}
        </section>
      )}

      {tab === "graphlets" && orbits && (
        <section className="space-y-4">
          <p className="max-w-3xl text-sm leading-relaxed text-muted">{orbits.explanation}</p>
          <p className="text-sm">{orbits.n_significant} of 73 orbits significant (p &lt; 0.01)</p>
          <GraphletChart orbits={orbits.orbits} />
          {mode === "research" && (
            <button
              type="button"
              className="text-sm text-accent"
              onClick={() => void downloadResource(`/api/diseases/${diseaseId}/downloads/graphlets.csv`)}
            >
              Download orbit p-values (CSV)
            </button>
          )}
        </section>
      )}

      {tab === "story" && story && (
        <section className="grid gap-4 md:grid-cols-2">
          {story.steps.map((s) => (
            <article key={s.step} className="panel p-5">
              <p className="text-xs text-muted">Step {s.step}</p>
              <h3 className="mt-1 text-lg">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
            </article>
          ))}
          {similar && !similar.available && (
            <article className="panel p-5 md:col-span-2">
              <h3 className="text-lg">Similar diseases</h3>
              <p className="mt-2 text-sm text-muted">{similar.reason}</p>
            </article>
          )}
        </section>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel px-3 py-2">
      <dt className="text-[11px] uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-sm">{value}</dd>
    </div>
  );
}
