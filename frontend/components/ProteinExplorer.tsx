"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ConceptExplainer } from "@/components/ConceptExplainer";
import { GraphletChart } from "@/components/GraphletChart";
import { NetworkCanvas } from "@/components/NetworkCanvas";
import { apiGet } from "@/lib/api";
import { formatInt, formatScore } from "@/lib/format";
import { useMode } from "@/components/ModeProvider";
import type { NetworkGraph, ProteinDiseaseLink, ProteinGraphletContext, ProteinOverview } from "@/types";

export function ProteinExplorer({ proteinId }: { proteinId: string }) {
  const { mode } = useMode();
  const [protein, setProtein] = useState<ProteinOverview | null>(null);
  const [diseases, setDiseases] = useState<ProteinDiseaseLink[]>([]);
  const [graph, setGraph] = useState<NetworkGraph | null>(null);
  const [graphlets, setGraphlets] = useState<ProteinGraphletContext | null>(null);
  const [networkNote, setNetworkNote] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"3d" | "2d">("2d");

  useEffect(() => {
    let cancelled = false;
    setError(null);
    setNetworkNote(null);
    apiGet<ProteinOverview>(`/api/proteins/${proteinId}`)
      .then((p) => {
        if (!cancelled) setProtein(p);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    apiGet<{ diseases: ProteinDiseaseLink[] }>(`/api/proteins/${proteinId}/diseases`)
      .then((d) => {
        if (!cancelled) setDiseases(d.diseases);
      })
      .catch(() => {
        if (!cancelled) setDiseases([]);
      });
    apiGet<NetworkGraph>(`/api/proteins/${proteinId}/network?hops=1&limit=80`)
      .then((n) => {
        if (!cancelled) setGraph(n);
      })
      .catch((e: Error) => {
        if (!cancelled) setNetworkNote(e.message);
      });
    apiGet<ProteinGraphletContext>(`/api/proteins/${proteinId}/graphlets`)
      .then((g) => {
        if (!cancelled) setGraphlets(g);
      })
      .catch(() => {
        if (!cancelled) setGraphlets(null);
      });
    return () => {
      cancelled = true;
    };
  }, [proteinId]);

  if (error) {
    return (
      <div className="panel mx-auto max-w-xl p-8 text-center">
        <h1 className="text-xl">Protein not available</h1>
        <p className="mt-2 text-muted">{error}</p>
        <p className="mt-2 text-sm text-muted">IDs in this dataset are Entrez Gene IDs, for example 7157.</p>
      </div>
    );
  }
  if (!protein) return <p className="text-muted">Loading protein…</p>;

  const features = graphlets?.local_structural_features?.features || {};
  const orbitProfile = graphlets?.disease_orbit_profile;

  return (
    <div className="space-y-8">
      <header className="stack-copy">
        <p className="eyebrow">Protein explorer</p>
        <h1 className="page-title">
          Entrez <span className="font-tech">{protein.id}</span>
        </h1>
        <p className="lede">{protein.graphlet_note}</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="panel p-3">
            <dt className="text-xs text-muted">
              Gene ID <ConceptExplainer conceptId="gene" />
            </dt>
            <dd className="font-tech">{protein.id}</dd>
          </div>
          <div className="panel p-3">
            <dt className="text-xs text-muted">Degree</dt>
            <dd className="font-tech">{formatInt(protein.degree)}</dd>
          </div>
          <div className="panel p-3">
            <dt className="text-xs text-muted">Clustering</dt>
            <dd className="font-tech">{formatScore(protein.clustering_coefficient)}</dd>
          </div>
          <div className="panel p-3">
            <dt className="text-xs text-muted">Known diseases</dt>
            <dd className="font-tech">{formatInt(protein.n_associated_diseases)}</dd>
          </div>
        </dl>
      </header>

      <section>
        <h2 className="section-title mb-3">
          Disease associations <ConceptExplainer conceptId="disease" />
        </h2>
        {diseases.length === 0 ? (
          <p className="text-sm text-muted">
            No known associations in this dataset. The protein may still appear as a computational
            candidate.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-line">
            <table className="min-w-full text-sm">
              <thead className="text-muted">
                <tr>
                  <th className="px-3 py-2 text-left">Disease</th>
                  <th className="px-3 py-2 text-left">ID</th>
                  <th className="px-3 py-2 text-left">Category</th>
                </tr>
              </thead>
              <tbody>
                {diseases.map((d) => (
                  <tr key={d.disease_id} className="border-t border-line">
                    <td className="px-3 py-2">
                      <Link className="text-accent" href={`/disease/${d.disease_id}`}>
                        {d.disease_name}
                      </Link>
                    </td>
                    <td className="font-tech px-3 py-2">{d.disease_id}</td>
                    <td className="px-3 py-2 text-muted">{d.category || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="section-title">
            Network neighborhood <ConceptExplainer conceptId="neighborhood" />
          </h2>
          <div className="inline-flex rounded-full border border-line p-1 text-sm">
            <button
              type="button"
              className={`rounded-full px-3 py-1 ${view === "2d" ? "chip-on" : "text-muted"}`}
              onClick={() => setView("2d")}
            >
              2D
            </button>
            <button
              type="button"
              className={`rounded-full px-3 py-1 ${view === "3d" ? "chip-on" : "text-muted"}`}
              onClick={() => setView("3d")}
            >
              3D
            </button>
          </div>
        </div>
        {graph && (
          <NetworkCanvas graph={graph} mode={view} onSelect={() => undefined} highlightId={protein.id} />
        )}
        {!graph && networkNote && <p className="text-sm text-muted">{networkNote}</p>}
      </section>

      <section className="space-y-3">
        <h2 className="section-title">
          Graphlet context <ConceptExplainer conceptId="graphlet" />
        </h2>
        <p className="text-sm text-muted">
          If an associated disease exists, the chart below is that disease’s 73-dimensional orbit
          profile. It is not a per-protein ORCA signature. The 12-dimensional motif-signature proxy
          is shown separately in research mode.
        </p>
        {orbitProfile ? (
          <GraphletChart orbits={orbitProfile.orbits} title={`Disease-level orbits: ${orbitProfile.disease_name}`} />
        ) : (
          <p className="text-sm text-muted">No associated disease orbit profile to display.</p>
        )}
        {mode === "research" && (
          <div className="panel p-4">
            <h3 className="text-sm text-muted">
              12-dimensional motif-signature proxy <ConceptExplainer conceptId="motif" />
            </h3>
            <dl className="mt-3 grid gap-2 md:grid-cols-3">
              {Object.entries(features).map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-muted">{k}</dt>
                  <dd className="font-tech text-sm">{formatScore(v as number)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </section>
    </div>
  );
}
