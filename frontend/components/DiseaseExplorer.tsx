"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { apiGet, downloadResource, isStaticMode } from "@/lib/api";
import { formatInt, formatScore } from "@/lib/format";
import type {
  DiseaseDetail,
  MetricCard as Metric,
  NetworkGraph,
  NetworkNode,
  GraphletProfile,
  PredictionEvidence,
  PredictionsResponse,
} from "@/types";
import { ConceptExplainer } from "@/components/ConceptExplainer";
import { GraphletChart } from "@/components/GraphletChart";
import { GraphletMotifs } from "@/components/GraphletMotifs";
import { MetricCard } from "@/components/MetricCard";
import { useMode } from "@/components/ModeProvider";
import { NetworkCanvas } from "@/components/NetworkCanvas";
import { PredictionTable } from "@/components/PredictionTable";
import {
  CandidateHighlight,
  DiseaseCluster,
  GraphletMotif,
  InteractionPair,
  ProteinMachine,
} from "@/components/ScientificArt";

type Tab = "overview" | "network" | "predictions" | "graphlets" | "story";
const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "network", label: "Network" },
  { id: "predictions", label: "Predictions" },
  { id: "graphlets", label: "Graphlets" },
  { id: "story", label: "Story" },
];
const RANK_OPTIONS = [10, 25, 50, 100] as const;

export function DiseaseExplorer({ diseaseId }: { diseaseId: string }) {
  const { mode } = useMode();
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<Tab>("overview");
  const [disease, setDisease] = useState<DiseaseDetail | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [graph, setGraph] = useState<NetworkGraph | null>(null);
  const [preds, setPreds] = useState<PredictionsResponse | null>(null);
  const [orbits, setOrbits] = useState<GraphletProfile | null>(null);
  const [story, setStory] = useState<{ steps: { step: number; title: string; body: string }[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"3d" | "2d">("2d");
  const [includePredicted, setIncludePredicted] = useState(false);
  const [topK, setTopK] = useState<(typeof RANK_OPTIONS)[number]>(25);
  const [hops, setHops] = useState(0);
  const [selected, setSelected] = useState<NetworkNode | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<PredictionEvidence | null>(null);
  const [loadingNet, setLoadingNet] = useState(false);
  const [loadingPred, setLoadingPred] = useState(false);
  const [similar, setSimilar] = useState<{ available: boolean; reason: string } | null>(null);

  useEffect(() => {
    const requested = searchParams.get("tab");
    if (requested && TABS.some((t) => t.id === requested)) setTab(requested as Tab);
    const requestedView = searchParams.get("view");
    if (requestedView === "2d" || requestedView === "3d") setView(requestedView);
  }, [searchParams]);

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
    void loadNetwork();
  }, [loadNetwork]);

  useEffect(() => {
    if (preds) return;
    setLoadingPred(true);
    apiGet<PredictionsResponse>(`/api/diseases/${diseaseId}/predictions?top_k=100`)
      .then(setPreds)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoadingPred(false));
  }, [diseaseId, preds]);

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

  useEffect(() => {
    if (!pendingId || !graph) return;
    const node = graph.nodes.find((n) => n.id === pendingId);
    if (node) {
      setSelected(node);
      setPendingId(null);
    }
  }, [graph, pendingId]);

  const overlayNote = useMemo(() => {
    if (!includePredicted || !preds) return null;
    const top = preds.predictions.slice(0, topK);
    const ids = new Set((graph?.nodes || []).map((n) => n.id));
    const shown = top.filter((p) => ids.has(p.protein_id)).length;
    const missing = top.length - shown;
    return { shown, missing, total: top.length };
  }, [includePredicted, preds, topK, graph]);

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
        <Link href="/diseases" className="mt-4 inline-block text-accent">
          Back to diseases
        </Link>
      </div>
    );
  }

  if (!disease) {
    return <p className="text-muted">Loading disease workspace…</p>;
  }

  return (
    <div className="space-y-8">
      <header className="stack-copy">
        <p className="eyebrow">Disease workspace</p>
        <h1 className="page-title max-w-4xl">{disease.name}</h1>
        <p className="lede">{disease.disclaimer}</p>
        <dl className="grid grid-cols-2 gap-3 md:grid-cols-6">
          <Stat label="Disease ID" value={disease.id} hint="disease" />
          <Stat label="Associated proteins" value={formatInt(disease.n_associated_proteins)} hint="protein" />
          <Stat label="Network nodes" value={formatInt(disease.n_network_nodes)} hint="node" />
          <Stat label="Edges" value={formatInt(disease.n_network_edges)} hint="edge" />
          <Stat label="Components" value={formatInt(disease.n_components)} />
          <Stat label="Predictions" value={disease.predictions_available ? "Available" : "No"} hint="prediction" />
        </dl>
      </header>

      <div className="flex flex-wrap gap-2" data-workspace-tabs>
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-full border px-4 py-2 text-sm ${tab === t.id ? "chip-on border-accent" : "border-line text-muted"}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <section className="space-y-4">
          <p className="max-w-3xl text-sm text-muted">
            These numbers describe the shape of this disease pathway. They are research measurements,
            not a risk score and not a judgement that the disease is “good” or “bad.”
          </p>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {metrics.map((m) => (
              <MetricCard key={m.key} metric={m} research={mode === "research"} />
            ))}
          </div>
        </section>
      )}

      {tab === "network" && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <div className="inline-flex rounded-full border border-line p-1">
              <button
                type="button"
                className={`rounded-full px-4 py-1.5 ${view === "2d" ? "chip-on" : "text-muted"}`}
                onClick={() => setView("2d")}
                aria-pressed={view === "2d"}
              >
                2D
              </button>
              <button
                type="button"
                className={`rounded-full px-4 py-1.5 ${view === "3d" ? "chip-on" : "text-muted"}`}
                onClick={() => setView("3d")}
                aria-pressed={view === "3d"}
              >
                3D
              </button>
            </div>
            <label className="flex items-center gap-2 text-muted">
              <input
                type="checkbox"
                checked={includePredicted}
                onChange={(e) => setIncludePredicted(e.target.checked)}
              />
              Show Predictions
            </label>
            <fieldset className="flex flex-wrap items-center gap-2" disabled={!includePredicted}>
              <legend className="sr-only">Prediction rank filter</legend>
              <span className="text-xs text-muted">Prediction Rank</span>
              {RANK_OPTIONS.map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => setTopK(n)}
                  className={`rounded-full border px-2.5 py-1 text-xs ${
                    topK === n ? "chip-on border-accent" : "border-line text-muted"
                  }`}
                >
                  {n === 100 ? "All / Top 100" : `Top ${n}`}
                </button>
              ))}
            </fieldset>
            <label className="flex items-center gap-2 text-muted">
              Neighborhood
              <select
                value={hops}
                onChange={(e) => setHops(Number(e.target.value))}
                className="rounded-md border border-line bg-transparent px-2 py-1"
              >
                <option value={0}>Pathway only</option>
                <option value={1}>{isStaticMode() ? "1-hop (not in static data)" : "1-hop (capped)"}</option>
              </select>
            </label>
          </div>
          {overlayNote && (
            <div className="panel p-4 text-sm leading-relaxed text-muted">
              <p>
                Top predicted proteins shown in this network: {overlayNote.shown} of {overlayNote.total}.
              </p>
              {overlayNote.missing > 0 && (
                <p className="mt-1">
                  Some predicted proteins may not appear because this visualization shows the selected
                  disease pathway network. {overlayNote.missing} of the current Top {overlayNote.total}{" "}
                  candidates have no displayed pathway edge in this view.
                </p>
              )}
            </div>
          )}
          {loadingNet && <p className="text-muted">Loading network subset…</p>}
          {graph && (
            <NetworkCanvas
              graph={graph}
              mode={view}
              onSelect={selectNode}
              highlightId={selected?.id}
              sizeByRank={includePredicted}
              footerNote={graph.truncated ? graph.truncation_note : null}
              inspector={
                selected ? (
                  <Inspector
                    selected={selected}
                    evidence={evidence}
                    diseaseName={disease.name}
                    associated={selected.type === "associated"}
                  />
                ) : null
              }
            />
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
                setPendingId(id);
              }}
            />
          )}
          {mode === "research" && (
            <button
              type="button"
              className="text-sm text-accent"
              onClick={() => void downloadResource(`/api/diseases/${diseaseId}/downloads/predictions.csv?top_k=100`)}
            >
              Download prediction table (CSV)
            </button>
          )}
        </section>
      )}

      {tab === "graphlets" && (
        <section className="space-y-6">
          <GraphletMotifs />
          {orbits && (
            <>
              <p className="max-w-3xl text-sm leading-relaxed text-muted">{orbits.explanation}</p>
              <p className="text-sm">
                {orbits.n_significant} of 73 orbits significant (p &lt; 0.01)
              </p>
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
            </>
          )}
        </section>
      )}

      {tab === "story" && story && (
        <section className="grid gap-4 md:grid-cols-2">
          {story.steps.map((s) => (
            <article key={s.step} className="panel p-5">
              <div className="mb-3" aria-hidden>
                {s.step === 1 ? (
                  <ProteinMachine />
                ) : s.step === 2 ? (
                  <InteractionPair />
                ) : s.step === 3 ? (
                  <DiseaseCluster />
                ) : s.step === 4 ? (
                  <CandidateHighlight />
                ) : (
                  <GraphletMotif />
                )}
              </div>
              <p className="font-tech text-xs text-muted">Step {s.step}</p>
              <h3 className="font-display mt-1 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{s.body}</p>
              <p className="art-caption mt-3">Illustration only — not measured data.</p>
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

function Inspector({
  selected,
  evidence,
  diseaseName,
  associated,
}: {
  selected: NetworkNode;
  evidence: PredictionEvidence | null;
  diseaseName: string;
  associated: boolean;
}) {
  return (
    <div className="space-y-2 text-sm">
      <h3 className="font-display text-lg font-semibold">
        Entrez <span className="font-tech">{selected.id}</span>
      </h3>
      <p className="text-xs text-muted">Entrez Gene ID — gene symbols are not in this dataset.</p>
      <p>
        Role in view:{" "}
        {selected.type === "associated"
          ? "disease-associated"
          : selected.type === "predicted"
            ? "predicted candidate"
            : "other"}
      </p>
      <p>Degree in this view: {selected.degree}</p>
      {selected.score != null && <p>Combined score: {formatScore(selected.score)}</p>}
      {associated ? (
        <p className="text-muted">
          This protein is already associated with {diseaseName} in the DisGeNET / SNAP tables. That
          is a catalogue association, not a statement that the protein causes the disease.
        </p>
      ) : (
        <p className="text-muted">
          This protein is shown as a computationally ranked candidate. A high rank is a research
          hypothesis, not a clinical finding.
        </p>
      )}
      {evidence && (
        <div className="space-y-1 text-muted">
          <p>Prediction rank {evidence.rank}</p>
          <p>
            Seed neighbors: {evidence.neighborhood_seed_neighbors} / degree {evidence.neighborhood_degree}
          </p>
          <p>{evidence.method_agreement_note}</p>
        </div>
      )}
      <Link className="inline-block text-accent" href={`/protein/${selected.id}`}>
        Open Protein Explorer
      </Link>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="panel px-3 py-2">
      <dt className="flex items-center text-[11px] uppercase tracking-wide text-muted">
        {label}
        {hint && <ConceptExplainer conceptId={hint} />}
      </dt>
      <dd className="font-tech mt-1 text-sm">{value}</dd>
    </div>
  );
}
