"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ConceptExplainer } from "@/components/ConceptExplainer";
import { SearchBox } from "@/components/SearchBox";
import { apiGet } from "@/lib/api";
import { formatInt } from "@/lib/format";
import type { DiseaseSummary } from "@/types";

const FEATURED = ["C0002395", "C0003873", "C0004352"];

export default function DiseasesPage() {
  const [diseases, setDiseases] = useState<DiseaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    apiGet<{ diseases: DiseaseSummary[] }>("/api/diseases?limit=519")
      .then((d) => setDiseases(d.diseases))
      .catch((e: Error) => setError(e.message));
  }, []);

  const featured = useMemo(
    () => FEATURED.map((id) => diseases.find((d) => d.id === id)).filter(Boolean) as DiseaseSummary[],
    [diseases]
  );
  const filtered = useMemo(() => {
    const query = q.trim().toLowerCase();
    if (!query) return diseases.slice(0, 24);
    return diseases
      .filter((d) => d.name.toLowerCase().includes(query) || d.id.toLowerCase().includes(query))
      .slice(0, 36);
  }, [diseases, q]);

  return (
    <div className="space-y-8">
      <header className="stack-copy max-w-3xl">
        <p className="eyebrow">Research workspace</p>
        <h1 className="page-title">
          Diseases <ConceptExplainer conceptId="disease" />
        </h1>
        <p className="lede">
          Choose a disease to open its protein pathway, structural metrics, and precomputed
          candidate rankings. Names and IDs come from DisGeNET via the SNAP disease-pathway
          resource.
        </p>
        <SearchBox />
      </header>

      {error && <p className="text-predict">{error}</p>}

      {featured.length > 0 && (
        <section className="space-y-3">
          <h2 className="section-title">Start here</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {featured.map((d) => (
              <DiseaseCard key={d.id} disease={d} featured />
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="section-title">Browse the catalogue</h2>
          <label className="text-sm text-muted">
            Filter list
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Name or disease ID"
              className="ml-2 h-9 rounded-lg border border-line bg-transparent px-3 text-foreground"
            />
          </label>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((d) => (
            <DiseaseCard key={d.id} disease={d} />
          ))}
        </div>
        <p className="text-xs text-muted">
          Showing {filtered.length} of {diseases.length} diseases. Use search above to jump directly
          to any of the 519 catalogue entries.
        </p>
      </section>
    </div>
  );
}

function DiseaseCard({ disease, featured }: { disease: DiseaseSummary; featured?: boolean }) {
  return (
    <Link href={`/disease/${disease.id}`} className={`panel panel-hover block p-4 ${featured ? "min-h-[150px]" : ""}`}>
      <p className="font-tech text-xs text-muted">{disease.id}</p>
      <h3 className="font-display mt-1 text-base font-semibold leading-snug">{disease.name}</h3>
      <p className="mt-2 text-xs text-muted">
        {formatInt(disease.n_associated_proteins)} associated proteins ·{" "}
        {formatInt(disease.n_network_edges)} pathway edges
      </p>
    </Link>
  );
}
