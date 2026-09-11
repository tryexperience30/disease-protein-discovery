"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { PredictionRow, PredictionsResponse } from "@/types";
import { formatScore } from "@/lib/format";
import { useMode } from "./ModeProvider";
import { ConceptExplainer, Term } from "@/components/ConceptExplainer";

const METHODS = [
  { key: "neighborhood", label: "Neighborhood", concept: "neighborhood" },
  { key: "random_walk", label: "Random Walk", concept: "random_walk" },
  { key: "diamond", label: "DIAMOnD", concept: "diamond" },
  { key: "neural_embeddings", label: "Neural Embeddings", concept: "neural_embeddings" },
  { key: "matrix_completion", label: "Matrix Completion", concept: "matrix_completion" },
] as const;

export function PredictionTable({
  data,
  onSelect,
}: {
  data: PredictionsResponse;
  onSelect?: (proteinId: string) => void;
}) {
  const { mode } = useMode();
  const [limit, setLimit] = useState(25);
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"rank" | "combined_score">("rank");
  const [openMethods, setOpenMethods] = useState(false);

  const rows = useMemo(() => {
    let list = data.predictions.filter((r) => r.protein_id.includes(q.trim()));
    if (sort === "combined_score") {
      list = [...list].sort((a, b) => b.combined_score - a.combined_score);
    }
    return list.slice(0, limit);
  }, [data.predictions, limit, q, sort]);

  const ranges = useMemo(() => {
    const keys = [
      "neighborhood",
      "random_walk",
      "diamond",
      "neural_embeddings",
      "matrix_completion",
      "combined_score",
    ] as const;
    const out: Record<string, { min: number; max: number }> = {};
    for (const key of keys) {
      const vals = data.predictions.map((r) => r[key]);
      out[key] = { min: Math.min(...vals), max: Math.max(...vals) };
    }
    return out;
  }, [data.predictions]);

  return (
    <div className="space-y-4">
      <div className="panel space-y-3 p-4">
        <p className="text-sm leading-relaxed">
          Each method gives the protein a score. The Combined Score is the mean of the
          min–max-normalized method scores. <ConceptExplainer conceptId="combined_score" tone="learn" />
        </p>
        <p className="text-sm text-muted">{data.combined_score_definition}</p>
        <button type="button" className="text-sm text-accent" onClick={() => setOpenMethods((v) => !v)}>
          {openMethods ? "Hide method explanations" : "What do these methods mean?"}
        </button>
        {openMethods && (
          <ul className="grid gap-3 md:grid-cols-2">
            {METHODS.map((m) => (
              <li key={m.key} className="rounded-xl border border-line p-3 text-sm">
                <Term conceptId={m.concept}>{m.label}</Term>
              </li>
            ))}
          </ul>
        )}
        <p className="text-xs text-muted">
          Score bars are scaled within each column so you can scan ranks. They do not put the five
          methods on one shared scientific scale.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {[10, 25, 50, 100].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setLimit(n)}
            className={`rounded-full border px-3 py-1 text-xs ${limit === n ? "chip-on border-accent" : "border-line text-muted"}`}
          >
            Top {n}
          </button>
        ))}
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter Gene ID"
          className="h-9 rounded-lg border border-line bg-transparent px-3 text-sm"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as "rank" | "combined_score")}
          className="h-9 rounded-lg border border-line bg-transparent px-3 text-sm"
        >
          <option value="rank">Sort by rank</option>
          <option value="combined_score">Sort by combined score</option>
        </select>
      </div>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/3 text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">Rank</th>
              <th className="px-3 py-2 font-medium">Protein</th>
              {METHODS.map((m) => (
                <th key={m.key} className="px-3 py-2 font-medium">
                  {m.label}
                </th>
              ))}
              <th className="px-3 py-2 font-medium">Combined Score</th>
              {mode === "research" && <th className="px-3 py-2 font-medium">Edge to pathway</th>}
              <th className="px-3 py-2 font-medium">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row: PredictionRow) => (
              <tr key={row.protein_id} className="border-t border-line">
                <td className="font-tech px-3 py-2">{row.rank}</td>
                <td className="px-3 py-2">
                  <button type="button" className="font-tech text-accent" onClick={() => onSelect?.(row.protein_id)}>
                    Entrez {row.protein_id}
                  </button>
                </td>
                {METHODS.map((m) => (
                  <td key={m.key} className="px-3 py-2">
                    <ScoreCell value={row[m.key]} range={ranges[m.key]} />
                  </td>
                ))}
                <td className="px-3 py-2">
                  <ScoreCell value={row.combined_score} range={ranges.combined_score} strong />
                </td>
                {mode === "research" && (
                  <td className="px-3 py-2 text-xs text-muted">{row.has_edge_to_pathway ? "yes" : "no"}</td>
                )}
                <td className="px-3 py-2">
                  <Link className="text-accent" href={`/protein/${row.protein_id}`}>
                    Investigate
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ScoreCell({
  value,
  range,
  strong,
}: {
  value: number;
  range: { min: number; max: number };
  strong?: boolean;
}) {
  const width = range.max === range.min ? (value > 0 ? 100 : 0) : ((value - range.min) / (range.max - range.min)) * 100;
  return (
    <div className="min-w-[88px]">
      <div className={`font-tech text-xs ${strong ? "text-lg font-semibold text-foreground" : "text-muted"}`}>
        {formatScore(value)}
      </div>
      <div className="score-bar mt-1" aria-hidden>
        <span style={{ width: `${Math.max(4, width)}%` }} />
      </div>
    </div>
  );
}
