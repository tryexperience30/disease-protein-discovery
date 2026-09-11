"use client";

import { useEffect, useState } from "react";
import { ConceptExplainer } from "@/components/ConceptExplainer";
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

const METRIC_HELP = {
  recall_at_100: "recall100",
  recall_at_25: "recall25",
  mrr: "mrr",
} as const;

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
      <header className="stack-copy max-w-3xl">
        <p className="eyebrow">Cross-validation</p>
        <h1 className="page-title">Model comparison</h1>
        <p className="lede">
          These are research evaluation metrics from disease-centric 10-fold cross-validation on the
          validated pipeline. They measure how the methods rank held-out known associations. They
          are not clinical accuracy scores.
        </p>
        <p className="text-sm text-muted">
          Only metrics actually computed in this project are shown: Recall@25, Recall@100, and MRR.
        </p>
      </header>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="panel p-4">
          <h2 className="font-display text-base font-semibold">
            Recall@25 <ConceptExplainer conceptId="recall25" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Recall@25 asks: how many of the known relevant proteins did the model manage to place
            within its top 25 predictions?
          </p>
        </article>
        <article className="panel p-4">
          <h2 className="font-display text-base font-semibold">
            Recall@100 <ConceptExplainer conceptId="recall100" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Recall@100 asks the same question, but looks at the top 100 ranked proteins instead of
            the top 25.
          </p>
        </article>
        <article className="panel p-4">
          <h2 className="font-display text-base font-semibold">
            MRR <ConceptExplainer conceptId="mrr" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            MRR is higher when the first correct protein appears nearer the top of the list.
          </p>
        </article>
      </section>

      <aside className="panel border-predict/40 p-5">
        <h2 className="text-sm font-medium text-predict">Matrix Completion evaluation note</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">{data.nmf_leakage_note}</p>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          A larger displayed bar for Matrix Completion is not evidence that the method is
          scientifically best. Its cross-validation numbers are inflated by the leakage described
          above. Compare the other four methods on equal footing.
        </p>
      </aside>

      <div className="flex flex-wrap items-center gap-2">
        {(["recall_at_100", "recall_at_25", "mrr"] as const).map((m) => (
          <button
            key={m}
            type="button"
            onClick={() => setMetric(m)}
            className={`rounded-full border px-3 py-1 text-sm ${metric === m ? "chip-on border-accent" : "border-line text-muted"}`}
          >
            {m === "mrr" ? "MRR" : m === "recall_at_25" ? "Recall@25" : "Recall@100"}
          </button>
        ))}
        <ConceptExplainer conceptId={METRIC_HELP[metric]} tone="learn" />
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
            <div className="metric-value text-right text-[1.15rem]">{formatScore(p[metric])}</div>
          </div>
        ))}
      </div>

      <section className="grid gap-4 md:grid-cols-2">
        {data.methods.map((m) => (
          <article key={m.name} className="panel p-5">
            <h3 className="font-display text-lg font-semibold">{m.name}</h3>
            <p className="mt-2 text-sm text-muted">{m.description}</p>
          </article>
        ))}
      </section>

      <section className="panel p-5">
        <h2 className="section-title text-[1.25rem]">Augmented embeddings + motif features</h2>
        <p className="mt-2 text-sm text-muted">{String(data.augmented.description)}</p>
        <dl className="mt-4 grid gap-3 md:grid-cols-2">
          <div>
            <dt className="text-xs text-muted">Mean baseline Recall@100</dt>
            <dd className="metric-value text-[1.25rem]">{formatScore(Number(data.augmented.mean_baseline_recall_at_100))}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">Mean augmented Recall@100</dt>
            <dd className="metric-value text-[1.25rem]">{formatScore(Number(data.augmented.mean_augmented_recall_at_100))}</dd>
          </div>
        </dl>
      </section>
    </div>
  );
}
