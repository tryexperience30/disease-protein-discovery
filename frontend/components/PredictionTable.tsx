"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { PredictionRow, PredictionsResponse } from "@/types";
import { formatScore } from "@/lib/format";
import { useMode } from "./ModeProvider";

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

  const rows = useMemo(() => {
    let list = data.predictions.filter((r) => r.protein_id.includes(q.trim()));
    if (sort === "combined_score") {
      list = [...list].sort((a, b) => b.combined_score - a.combined_score);
    }
    return list.slice(0, limit);
  }, [data.predictions, limit, q, sort]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        {[10, 25, 50, 100].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setLimit(n)}
            className={`rounded-full border px-3 py-1 text-xs ${limit === n ? "border-accent text-foreground" : "border-line text-muted"}`}
          >
            Top {n}
          </button>
        ))}
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Filter Gene ID"
          className="h-9 rounded-lg border border-line bg-[#0c111b] px-3 text-sm"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as "rank" | "combined_score")}
          className="h-9 rounded-lg border border-line bg-[#0c111b] px-3 text-sm"
        >
          <option value="rank">Sort by rank</option>
          <option value="combined_score">Sort by combined score</option>
        </select>
      </div>
      <p className="text-sm text-muted">{data.combined_score_definition}</p>
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-white/3 text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">Rank</th>
              <th className="px-3 py-2 font-medium">Protein</th>
              <th className="px-3 py-2 font-medium">Score</th>
              <th className="px-3 py-2 font-medium">Method</th>
              <th className="px-3 py-2 font-medium">Evidence</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.protein_id} className="border-t border-line">
                <td className="px-3 py-2 font-mono">{row.rank}</td>
                <td className="px-3 py-2">
                  <button type="button" className="text-accent" onClick={() => onSelect?.(row.protein_id)}>
                    {row.protein_id}
                  </button>
                </td>
                <td className="px-3 py-2 font-mono">{formatScore(row.combined_score)}</td>
                <td className="px-3 py-2 text-muted">Combined</td>
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
      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="min-w-full text-left text-xs">
          <thead className="text-muted">
            <tr>
              <th className="px-3 py-2">Protein</th>
              <th className="px-3 py-2">Neighborhood</th>
              <th className="px-3 py-2">Random Walk</th>
              <th className="px-3 py-2">DIAMOnD</th>
              <th className="px-3 py-2">Embeddings</th>
              <th className="px-3 py-2">Matrix Completion</th>
              <th className="px-3 py-2">Combined Score</th>
              {mode === "research" && <th className="px-3 py-2">Edge to pathway</th>}
            </tr>
          </thead>
          <tbody>
            {rows.map((row: PredictionRow) => (
              <tr key={`r-${row.protein_id}`} className="border-t border-line font-mono">
                <td className="px-3 py-2">{row.protein_id}</td>
                <td className="px-3 py-2">{formatScore(row.neighborhood)}</td>
                <td className="px-3 py-2">{formatScore(row.random_walk)}</td>
                <td className="px-3 py-2">{formatScore(row.diamond)}</td>
                <td className="px-3 py-2">{formatScore(row.neural_embeddings)}</td>
                <td className="px-3 py-2">{formatScore(row.matrix_completion)}</td>
                <td className="px-3 py-2">{formatScore(row.combined_score)}</td>
                {mode === "research" && (
                  <td className="px-3 py-2">{row.has_edge_to_pathway ? "yes" : "no"}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
