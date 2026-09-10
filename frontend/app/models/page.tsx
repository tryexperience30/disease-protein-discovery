"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { formatScore } from "@/lib/format";

type Perf = {
  method: string;
  n_diseases: number;
  recall_at_25: number;
  recall_at_100: number;
  mrr: number;
};

type Payload = {
  metrics_available: string[];
  metrics_not_computed: string[];
  nmf_leakage_note: string;
  performance: Perf[];
  methods: { name: string; description: string }[];
  augmented: Record<string, number | string>;
};

export default function ModelsPage() {
  const [data, setData] = useState<Payload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metric, setMetric] = useState<"recall_at_100" | "recall_at_25" | "mrr">("recall_at_100");

  useEffect(() => {
    apiGet<Payload>("/api/models/performance")
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="text-predict">{error}</p>;
  if (!data) return <p className="text-muted">Loading model comparison…</p>;

  const max = Math.max(...data.performance.map((p) => p[metric]));

  return (
    <div className="space-y-8">
      <header className="max-w-3xl space-y-3">
        <h1 className="text-4xl font-semibold">Model comparison</h1>
        <p className="text-muted">
          Disease-centric 10-fold cross-validation on the validated pipeline.
          Only metrics actually computed in this project are shown: Recall@25, Recall@100, and MRR.
        </p>
      </header>

      <div className="flex gap-2">
        {(["recall_at_100", "recall_at_25", "mrr"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMetric(m)}
            className={`rounded-full border px-3 py-1 text-sm ${metric === m ? "border-accent" : "border-line text-muted"}`}
          >
            {m === "mrr" ? "MRR" : m === "recall_at_25" ? "Recall@25" : "Recall@100"}
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {data.performance.map((p) => (
          <div key={p.method} className="grid items-center gap-3 md:grid-cols-[220px_1fr_80px]">
            <div className="text-sm">{p.method}</div>
            <div className="h-3 rounded-full bg-white/5">
              <div
                className="h-3 rounded-full bg-accent"
                style={{ width: `${max ? (p[metric] / max) * 100 : 0}%` }}
              />
            </div>
            <div className="font-mono text-sm">{formatScore(p[metric])}</div>
          </div>
        ))}
      </div>

      <aside className="panel border-predict/40 p-5">
        <h2 className="text-sm font-medium text-predict">Matrix Completion evaluation note</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">{data.nmf_leakage_note}</p>
      </aside>

      <section className="grid gap-4 md:grid-cols-2">
        {data.methods.map((m) => (
          <article key={m.name} className="panel p-5">
            <h3>{m.name}</h3>
            <p className="mt-2 text-sm text-muted">{m.description}</p>
          </article>
        ))}
      </section>

      <section className="panel p-5">
        <h2 className="text-lg">Augmented embeddings + motif features</h2>
        <p className="mt-2 text-sm text-muted">{String(data.augmented.description)}</p>
        <dl className="mt-4 grid gap-3 md:grid-cols-2">
          <div>
            <dt className="text-xs text-muted">Mean baseline Recall@100</dt>
            <dd className="font-mono">{formatScore(Number(data.augmented.mean_baseline_recall_at_100))}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Mean augmented Recall@100</dt>
            <dd className="font-mono">{formatScore(Number(data.augmented.mean_augmented_recall_at_100))}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
