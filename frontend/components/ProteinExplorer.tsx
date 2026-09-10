"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
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
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"3d" | "2d">("3d");

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      apiGet<ProteinOverview>(`/api/proteins/${proteinId}`),
      apiGet<{ diseases: ProteinDiseaseLink[] }>(`/api/proteins/${proteinId}/diseases`),
      apiGet<NetworkGraph>(`/api/proteins/${proteinId}/network?hops=1&limit=80`),
      apiGet<ProteinGraphletContext>(`/api/proteins/${proteinId}/graphlets`),
    ])
      .then(([p, d, n, g]) => {
        if (cancelled) return;
        setProtein(p);
        setDiseases(d.diseases);
        setGraph(n);
        setGraphlets(g);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
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
      <header>
        <p className="text-xs uppercase tracking-[0.2em] text-muted">Protein explorer</p>
        <h1 className="mt-2 text-3xl font-semibold">{protein.label}</h1>
        <p className="mt-2 max-w-3xl text-sm text-muted">{protein.graphlet_note}</p>
        <dl className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="panel p-3"><dt className="text-xs text-muted">Gene ID</dt><dd className="font-mono">{protein.id}</dd></div>
          <div className="panel p-3"><dt className="text-xs text-muted">Degree</dt><dd className="font-mono">{formatInt(protein.degree)}</dd></div>
          <div className="panel p-3"><dt className="text-xs text-muted">Clustering</dt><dd className="font-mono">{formatScore(protein.clustering_coefficient)}</dd></div>
          <div className="panel p-3"><dt className="text-xs text-muted">Known diseases</dt><dd className="font-mono">{formatInt(protein.n_associated_diseases)}</dd></div>
        </dl>
      </header>

      <section>
        <h2 className="mb-3 text-xl">Disease associations</h2>
        {diseases.length === 0 ? (
          <p className="text-sm text-muted">No known associations in this dataset. The protein may still appear as a computational candidate.</p>
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
                      <Link className="text-accent" href={`/disease/${d.disease_id}`}>{d.disease_name}</Link>
                    </td>
                    <td className="px-3 py-2 font-mono">{d.disease_id}</td>
                    <td className="px-3 py-2 text-muted">{d.category || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xl">Network neighborhood</h2>
          <div className="inline-flex rounded-full border border-line p-1 text-sm">
            <button type="button" className={`rounded-full px-3 py-1 ${view === "3d" ? "bg-white/10" : "text-muted"}`} onClick={() => setView("3d")}>3D</button>
            <button type="button" className={`rounded-full px-3 py-1 ${view === "2d" ? "bg-white/10" : "text-muted"}`} onClick={() => setView("2d")}>2D</button>
          </div>
        </div>
        {graph && (
          <NetworkCanvas graph={graph} mode={view} showLabels={false} onSelect={() => undefined} highlightId={protein.id} />
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-xl">Graphlet context</h2>
        {orbitProfile ? (
          <GraphletChart orbits={orbitProfile.orbits} title={`Disease-level orbits: ${orbitProfile.disease_name}`} />
        ) : (
          <p className="text-sm text-muted">No associated disease orbit profile to display.</p>
        )}
        {mode === "research" && (
          <div className="panel p-4">
            <h3 className="text-sm text-muted">12-dimensional motif-signature proxy</h3>
            <dl className="mt-3 grid gap-2 md:grid-cols-3">
              {Object.entries(features).map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-muted">{k}</dt>
                  <dd className="font-mono text-sm">{formatScore(v as number)}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}
      </section>
    </div>
  );
}
