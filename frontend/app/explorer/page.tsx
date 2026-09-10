"use client";

import { useEffect, useState } from "react";
import { GraphletChart } from "@/components/GraphletChart";
import { apiGet } from "@/lib/api";

type OrbitProfile = {
  disease_id: string;
  disease_name: string;
  n_significant: number;
  explanation: string;
  orbits: { orbit: number; p_value: number | null; significant: boolean; graphlet_size: string }[];
};

type DiseaseList = { diseases: { id: string; name: string }[] };

export default function GraphletExplorerPage() {
  const [diseases, setDiseases] = useState<{ id: string; name: string }[]>([]);
  const [a, setA] = useState("C0002395");
  const [b, setB] = useState("C0003873");
  const [pa, setPa] = useState<OrbitProfile | null>(null);
  const [pb, setPb] = useState<OrbitProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<DiseaseList>("/api/diseases?limit=519")
      .then((d) => setDiseases(d.diseases.map((x) => ({ id: x.id, name: x.name }))))
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    if (!a) return;
    apiGet<OrbitProfile>(`/api/diseases/${a}/graphlets`).then(setPa).catch((e: Error) => setError(e.message));
  }, [a]);

  useEffect(() => {
    if (!b) return;
    apiGet<OrbitProfile>(`/api/diseases/${b}/graphlets`).then(setPb).catch((e: Error) => setError(e.message));
  }, [b]);

  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <h1 className="text-4xl font-semibold">Graphlet explorer</h1>
        <p className="text-muted">
          Graphlets capture local network topology by describing how a protein participates in small network motifs.
          This page compares disease-level 73-orbit significance profiles from the existing SNAP dataset.
          Per-protein 73-orbit ORCA signatures are not available in this project.
        </p>
      </header>
      {error && <p className="text-predict">{error}</p>}
      <div className="grid gap-4 md:grid-cols-2">
        <label className="text-sm">
          Disease A
          <select value={a} onChange={(e) => setA(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-[#0c111b] px-3 py-2">
            {diseases.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Disease B
          <select value={b} onChange={(e) => setB(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-[#0c111b] px-3 py-2">
            {diseases.map((d) => (
              <option key={`b-${d.id}`} value={d.id}>{d.name}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {pa && <GraphletChart orbits={pa.orbits} title={`${pa.disease_name} (${pa.n_significant} significant)`} />}
        {pb && <GraphletChart orbits={pb.orbits} title={`${pb.disease_name} (${pb.n_significant} significant)`} />}
      </div>
    </div>
  );
}
