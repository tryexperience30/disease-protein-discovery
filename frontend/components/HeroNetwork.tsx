"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { NetworkGraph } from "@/types";
import { NetworkCanvas } from "@/components/NetworkCanvas";

const ALZHEIMER = "C0002395";

function inducedHighDegree(graph: NetworkGraph, maxNodes: number): NetworkGraph {
  const counts = new Map<number, number>();
  for (const n of graph.nodes) {
    if (n.component == null) continue;
    counts.set(n.component, (counts.get(n.component) || 0) + 1);
  }
  let best = 0;
  let bestN = -1;
  for (const [component, n] of counts) {
    if (n > bestN) {
      best = component;
      bestN = n;
    }
  }
  let nodes = graph.nodes.filter((n) => n.component === best);
  if (nodes.length > maxNodes) {
    nodes = [...nodes].sort((a, b) => b.degree - a.degree).slice(0, maxNodes);
  }
  const keep = new Set(nodes.map((n) => n.id));
  const edges = graph.edges.filter((e) => keep.has(e.source) && keep.has(e.target));
  return {
    ...graph,
    nodes,
    edges,
    n_associated: nodes.length,
    n_predicted: 0,
    n_other: 0,
    truncated: nodes.length < graph.nodes.length,
    truncation_note:
      "Hero view shows the highest-degree proteins from the largest connected piece of the existing Alzheimer pathway, with only those proteins’ recorded PPI edges.",
  };
}

export function HeroNetwork() {
  const [graph, setGraph] = useState<NetworkGraph | null>(null);

  useEffect(() => {
    apiGet<NetworkGraph>(`/api/diseases/${ALZHEIMER}/network?hops=0`)
      .then((g) => setGraph(inducedHighDegree(g, 42)))
      .catch(() => setGraph(null));
  }, []);

  if (!graph) {
    return <div className="h-[280px] animate-pulse rounded-2xl border border-line bg-white/5" aria-hidden />;
  }

  return (
    <div className="space-y-2">
      <NetworkCanvas graph={graph} mode="2d" compact onSelect={() => undefined} />
      <p className="text-xs leading-relaxed text-muted">
        A real sample of the Alzheimer disease pathway (C0002395) from the SNAP dataset: existing
        protein–protein interactions only. Isolated proteins are omitted so the hero stays readable.
        No relationships were invented for this picture.
      </p>
    </div>
  );
}
