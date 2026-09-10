"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import type { NetworkGraph, NetworkNode } from "@/types";
import { nodeColor } from "@/lib/format";

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

type Props = {
  graph: NetworkGraph;
  mode: "3d" | "2d";
  showLabels: boolean;
  onSelect: (node: NetworkNode) => void;
  highlightId?: string | null;
};

export function NetworkCanvas({ graph, mode, showLabels, onSelect, highlightId }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 640 });

  useEffect(() => {
    const el = wrapRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const obs = new ResizeObserver(() => {
      setSize({ w: el.clientWidth || 800, h: el.clientHeight || 640 });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const data = useMemo(() => {
    const neighborIds = new Set<string>();
    if (highlightId) {
      for (const e of graph.edges) {
        if (e.source === highlightId) neighborIds.add(e.target);
        if (e.target === highlightId) neighborIds.add(e.source);
      }
    }
    return {
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.edges.map((e) => ({ source: e.source, target: e.target })),
      neighborIds,
    };
  }, [graph, highlightId]);

  const common = {
    graphData: { nodes: data.nodes, links: data.links },
    nodeId: "id",
    nodeLabel: (n: NetworkNode) =>
      `${n.label}\n${n.type}${n.score != null ? `\nscore ${n.score.toFixed(4)}` : ""}`,
    nodeColor: (n: NetworkNode) => {
      if (highlightId && n.id === highlightId) return "#ffffff";
      if (highlightId && data.neighborIds.has(n.id)) return "#9ad0ff";
      return nodeColor(n.type);
    },
    nodeVal: (n: NetworkNode) => Math.max(1, n.degree * 0.35 + (n.type === "predicted" ? 2 : 1)),
    onNodeClick: (n: NetworkNode) => onSelect(n),
    onNodeHover: (n: NetworkNode | null) => setHover(n?.id ?? null),
    linkColor: () => "rgba(148,163,184,0.28)",
    backgroundColor: "#07090f",
    cooldownTicks: 80,
    width: size.w,
    height: size.h,
  };

  return (
    <div ref={wrapRef} className="h-[520px] w-full overflow-hidden rounded-2xl border border-line md:h-[640px]">
      {mode === "3d" ? (
        <ForceGraph3D {...common} showNavInfo={false} />
      ) : (
        <ForceGraph2D
          {...common}
          nodeCanvasObject={
            showLabels
              ? (node: NetworkNode & { x?: number; y?: number }, ctx: CanvasRenderingContext2D, scale: number) => {
                  const x = node.x || 0;
                  const y = node.y || 0;
                  ctx.beginPath();
                  ctx.fillStyle = nodeColor(node.type);
                  ctx.arc(x, y, 4, 0, 2 * Math.PI);
                  ctx.fill();
                  if (scale > 1.4 || hover === node.id || highlightId === node.id) {
                    ctx.font = "10px sans-serif";
                    ctx.fillStyle = "#dbe7f5";
                    ctx.fillText(node.label, x + 6, y + 3);
                  }
                }
              : undefined
          }
        />
      )}
    </div>
  );
}
