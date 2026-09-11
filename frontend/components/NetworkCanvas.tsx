"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { NetworkGraph, NetworkNode } from "@/types";
import { colorForType, useVizSettings } from "@/components/VizSettingsProvider";
import { ConceptExplainer } from "@/components/ConceptExplainer";
import { useTheme } from "@/components/ThemeProvider";

const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), { ssr: false });
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const HIGHLIGHT = "#A6E3E9";

type Props = {
  graph: NetworkGraph;
  mode: "3d" | "2d";
  onSelect: (node: NetworkNode) => void;
  highlightId?: string | null;
  sizeByRank?: boolean;
  compact?: boolean;
  showLabels?: boolean;
  inspector?: ReactNode;
  footerNote?: string | null;
};

type FgApi = {
  zoom: (k?: number, ms?: number) => number;
  zoomToFit: (ms?: number, padding?: number, filter?: (n: NetworkNode) => boolean) => void;
  centerAt: (x?: number, y?: number, ms?: number) => void;
  cameraPosition: (pos?: object, lookAt?: object, ms?: number) => { x: number; y: number; z: number };
  controls: () => { autoRotate: boolean; autoRotateSpeed: number };
};

type SimNode = NetworkNode & { x?: number; y?: number; z?: number; fx?: number; fy?: number; fz?: number };
type Dock = "legend" | "settings" | "inspector";

export function NetworkCanvas({
  graph,
  mode,
  onSelect,
  highlightId,
  sizeByRank,
  compact,
  showLabels,
  inspector,
  footerNote,
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<FgApi | null>(null);
  const fittedKey = useRef("");
  const [hover, setHover] = useState<string | null>(null);
  const [size, setSize] = useState({ w: 800, h: 560 });
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [dock, setDock] = useState<Dock>("legend");
  const [preparing3d, setPreparing3d] = useState(false);
  const { settings, setSettings, reset } = useVizSettings();
  const { theme } = useTheme();
  const canvasBg = theme === "dark" ? "#143033" : "#E3FDFD";
  const labelFill = theme === "dark" ? "#E3FDFD" : "#163038";

  useEffect(() => {
    if (showLabels == null) return;
    setSettings({ showLabels });
  }, [showLabels, setSettings]);

  useEffect(() => {
    if (inspector) setDock("inspector");
    else setDock((d) => (d === "inspector" ? "legend" : d));
  }, [inspector]);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const obs = new ResizeObserver(() => {
      setSize({ w: el.clientWidth || 800, h: el.clientHeight || 560 });
    });
    obs.observe(el);
    setSize({ w: el.clientWidth || 800, h: el.clientHeight || 560 });
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    setPlaying(false);
    setPreparing3d(mode === "3d");
  }, [mode, graph.disease_id, graph.protein_id]);

  useEffect(() => {
    if (mode !== "3d") return;
    const id = window.setInterval(() => {
      const controls = fgRef.current?.controls?.();
      if (!controls) return;
      controls.autoRotate = playing;
      controls.autoRotateSpeed = 0.7 * speed;
    }, 250);
    return () => window.clearInterval(id);
  }, [mode, playing, speed]);

  const neighborIds = useMemo(() => {
    const focus = highlightId || hover;
    const set = new Set<string>();
    if (!focus) return set;
    for (const e of graph.edges) {
      if (e.source === focus) set.add(e.target);
      if (e.target === focus) set.add(e.source);
    }
    return set;
  }, [graph.edges, highlightId, hover]);

  const data = useMemo(() => {
    const nodes = graph.nodes.filter((n) => !settings.hidden[n.type]);
    const keep = new Set(nodes.map((n) => n.id));
    return {
      nodes: nodes.map((n) => ({ ...n })),
      links: graph.edges
        .filter((e) => keep.has(e.source) && keep.has(e.target))
        .map((e) => ({ source: e.source, target: e.target })),
    };
  }, [graph, settings.hidden]);

  const focus = highlightId || hover;

  function typeColor(n: NetworkNode) {
    const base = colorForType(settings, n.type);
    if (!focus) return base;
    if (n.id === focus) return HIGHLIGHT;
    if (neighborIds.has(n.id)) return base;
    return dimHex(base, 0.14);
  }

  function nodeVal(n: NetworkNode) {
    const base = Math.max(1, n.degree * 0.28 + (n.type === "predicted" ? 2 : 1));
    if (sizeByRank && n.score != null) return (base + n.score * 8) * settings.nodeSize;
    return base * settings.nodeSize;
  }

  function zoomBy(factor: number) {
    const api = fgRef.current;
    if (!api) return;
    if (mode === "2d" && typeof api.zoom === "function") {
      const current = api.zoom();
      api.zoom(current * factor, 300);
      return;
    }
    if (mode === "3d" && typeof api.cameraPosition === "function") {
      const pos = api.cameraPosition();
      if (!pos) return;
      api.cameraPosition({ x: pos.x / factor, y: pos.y / factor, z: pos.z / factor }, undefined, 400);
    }
  }

  const layoutReady = useCallback(() => {
    const nodes = data.nodes as SimNode[];
    if (!nodes.length) return false;
    let positioned = 0;
    let minX = Infinity;
    let maxX = -Infinity;
    for (const n of nodes) {
      if (n.x == null || n.y == null || !Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      if (mode === "3d" && (n.z == null || !Number.isFinite(n.z))) continue;
      positioned += 1;
      minX = Math.min(minX, n.x);
      maxX = Math.max(maxX, n.x);
    }
    if (positioned === 0) return false;
    if (nodes.length === 1) return true;
    return positioned >= Math.min(2, nodes.length) && (maxX - minX > 0.8 || positioned >= nodes.length * 0.4);
  }, [data.nodes, mode]);

  const fit = useCallback(() => {
    const api = fgRef.current;
    if (!api?.zoomToFit) return;
    const connected = data.nodes.some((n) => n.degree > 0);
    try {
      api.zoomToFit(450, 80, connected ? (n: NetworkNode) => n.degree > 0 : undefined);
    } catch {
      api.zoomToFit(450, 80);
    }
  }, [data.nodes]);

  function resetView() {
    fit();
  }

  useEffect(() => {
    const key = `${mode}:${graph.disease_id || ""}:${graph.protein_id || ""}:${data.nodes.length}:${size.w}x${size.h}`;
    if (!data.nodes.length) return;
    fittedKey.current = "";
    if (mode === "3d") setPreparing3d(true);
    const delays = mode === "3d" ? [700, 1400, 2200, 3200] : [450, 1100];
    const timers = delays.map((ms) =>
      window.setTimeout(() => {
        if (mode === "3d" && !layoutReady()) {
          fit();
          return;
        }
        fit();
        fittedKey.current = key;
        if (mode === "3d") setPreparing3d(false);
      }, ms)
    );
    const fallback = window.setTimeout(() => {
      fit();
      fittedKey.current = key;
      setPreparing3d(false);
    }, mode === "3d" ? 5200 : 1800);
    return () => {
      timers.forEach((id) => window.clearTimeout(id));
      window.clearTimeout(fallback);
    };
  }, [mode, graph.disease_id, graph.protein_id, data.nodes.length, size.w, size.h, fit, layoutReady]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      if (e.key === "+" || e.key === "=") zoomBy(1.25);
      if (e.key === "-" || e.key === "_") zoomBy(0.8);
      if (e.key === "0") resetView();
      if (e.key === "f" || e.key === "F") fit();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const common = {
    ref: fgRef,
    graphData: data,
    nodeId: "id",
    nodeLabel: (n: NetworkNode) =>
      `Gene ${n.label}\n${n.type}${n.score != null ? `\ncombined ${n.score.toFixed(4)}` : ""}`,
    nodeColor: typeColor,
    nodeVal,
    onNodeClick: (n: NetworkNode) => onSelect(n),
    onNodeHover: (n: NetworkNode | null) => setHover(n?.id ?? null),
    linkColor: (link: { source?: { id?: string } | string; target?: { id?: string } | string }) => {
      const s = typeof link.source === "object" ? link.source.id : link.source;
      const t = typeof link.target === "object" ? link.target.id : link.target;
      const hot = Boolean(focus && (s === focus || t === focus));
      if (!focus) return hexToRgba(settings.edge, settings.edgeOpacity);
      if (hot) return hexToRgba(settings.edge, Math.min(1, settings.edgeOpacity + 0.5));
      return hexToRgba(settings.edge, Math.max(0.05, settings.edgeOpacity * 0.12));
    },
    backgroundColor: canvasBg,
    cooldownTicks: mode === "2d" ? 160 : 90,
    warmupTicks: 24,
    enableNodeDrag: false,
    width: size.w,
    height: size.h,
    onEngineStop: () => {
      if (mode === "2d") {
        for (const n of data.nodes as SimNode[]) {
          if (n.x != null) n.fx = n.x;
          if (n.y != null) n.fy = n.y;
        }
      }
      const key = `${mode}:${graph.disease_id || ""}:${graph.protein_id || ""}:${data.nodes.length}:${size.w}x${size.h}`;
      if (fittedKey.current !== key) {
        fit();
        fittedKey.current = key;
      }
      if (mode === "3d" && layoutReady()) setPreparing3d(false);
    },
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <ControlButton label="Zoom in" onClick={() => zoomBy(1.25)}>
          +
        </ControlButton>
        <ControlButton label="Zoom out" onClick={() => zoomBy(0.8)}>
          −
        </ControlButton>
        <ControlButton label="Fit network to view" onClick={fit}>
          Fit
        </ControlButton>
        <ControlButton label="Reset camera" onClick={resetView}>
          Reset
        </ControlButton>
        {mode === "3d" && (
          <>
            <ControlButton
              label={playing ? "Pause auto-rotation" : "Play auto-rotation"}
              onClick={() => setPlaying((v) => !v)}
            >
              {playing ? "Pause" : "Play"}
            </ControlButton>
            <label className="flex items-center gap-2 text-xs text-muted">
              Speed
              <input
                type="range"
                min={0.4}
                max={2.5}
                step={0.1}
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
                aria-label="Auto-rotation speed"
              />
            </label>
          </>
        )}
        <label className="flex items-center gap-2 text-xs text-muted">
          <input
            type="checkbox"
            checked={settings.showLabels}
            onChange={(e) => setSettings({ showLabels: e.target.checked })}
          />
          Labels
        </label>
        <span className="text-xs text-muted">
          {mode === "2d"
            ? "2D is a settled map: drag to pan, scroll to zoom."
            : "Drag to rotate · Shift+drag to pan · scroll to zoom. Auto-rotate stays off until you press Play."}
        </span>
      </div>

      <div
        ref={wrapRef}
        className={`relative w-full overflow-hidden rounded-2xl border border-line ${
          compact ? "h-[280px]" : "h-[520px] md:h-[640px]"
        }`}
        style={{ background: canvasBg }}
      >
        {mode === "3d" ? (
          <ForceGraph3D {...common} showNavInfo={false} nodeRelSize={7} linkWidth={1.15} />
        ) : (
          <ForceGraph2D
            {...common}
            enableZoomInteraction
            enablePanInteraction
            d3AlphaDecay={0.08}
            d3VelocityDecay={0.45}
            nodeCanvasObject={(node: SimNode, ctx: CanvasRenderingContext2D, scale: number) => {
              const x = node.x || 0;
              const y = node.y || 0;
              const selected = node.id === highlightId || node.id === hover;
              const neighbor = Boolean(focus && neighborIds.has(node.id));
              const faded = Boolean(focus && !selected && !neighbor);
              const r = 3.4 * settings.nodeSize + (selected ? 2 : neighbor ? 0.8 : 0);
              const outline = node.type === "predicted" ? "#7A3A14" : "#163038";
              ctx.beginPath();
              ctx.fillStyle = hexToRgba("#2F8B91", faded ? 0.04 : selected ? 0.2 : 0.16);
              ctx.arc(x, y, r + 2.6, 0, 2 * Math.PI);
              ctx.fill();
              ctx.beginPath();
              ctx.fillStyle = typeColor(node);
              ctx.arc(x, y, r, 0, 2 * Math.PI);
              ctx.fill();
              ctx.strokeStyle = hexToRgba(outline, faded ? 0.18 : selected || neighbor || !focus ? 0.88 : 0.35);
              ctx.lineWidth = selected ? 2 : 1.45;
              ctx.stroke();
              if (selected) {
                ctx.beginPath();
                ctx.strokeStyle = HIGHLIGHT;
                ctx.lineWidth = 2.2;
                ctx.arc(x, y, r + 4, 0, 2 * Math.PI);
                ctx.stroke();
              }
              if (settings.showLabels && (scale > 1.2 || selected)) {
                ctx.font = "10px sans-serif";
                ctx.fillStyle = labelFill;
                ctx.fillText(node.label, x + 6, y + 3);
              }
            }}
          />
        )}
        {mode === "3d" && preparing3d && (
          <div
            className="absolute inset-0 z-10 flex items-center justify-center"
            style={{ background: canvasBg }}
            aria-live="polite"
            aria-busy="true"
          >
            <p className="rounded-full border border-line bg-[var(--panel)] px-4 py-2 text-sm text-muted">
              Preparing 3D network…
            </p>
          </div>
        )}
      </div>

      {!compact && (
        <div className="panel p-3">
          <div className="mb-3 flex flex-wrap gap-2">
            <button
              type="button"
              className={`rounded-full border px-3 py-1 text-xs ${dock === "legend" ? "chip-on border-accent" : "border-line text-muted"}`}
              onClick={() => setDock("legend")}
            >
              Legend
            </button>
            <button
              type="button"
              className={`rounded-full border px-3 py-1 text-xs ${dock === "settings" ? "chip-on border-accent" : "border-line text-muted"}`}
              onClick={() => setDock("settings")}
            >
              Visualization settings
            </button>
            {inspector && (
              <button
                type="button"
                className={`rounded-full border px-3 py-1 text-xs ${dock === "inspector" ? "chip-on border-accent" : "border-line text-muted"}`}
                onClick={() => setDock("inspector")}
              >
                Inspector
              </button>
            )}
          </div>
          {dock === "legend" && <Legend sizeByRank={sizeByRank} />}
          {dock === "settings" && <VisualizationSettings onResetColors={reset} onFit={fit} onResetView={resetView} />}
          {dock === "inspector" && inspector}
          {footerNote && <p className="mt-3 text-xs text-predict">{footerNote}</p>}
        </div>
      )}
    </div>
  );
}

function Legend({ sizeByRank }: { sizeByRank?: boolean }) {
  const { settings, setSettings } = useVizSettings();
  return (
    <div className="text-sm">
      <p className="text-xs text-muted">
        Click a category to hide or show it. Click a protein in the map to open the inspector. Color
        is a display choice — the inspector still names each type.
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {(["associated", "predicted", "other"] as const).map((type) => (
          <button
            key={type}
            type="button"
            className={`flex items-center gap-2 rounded-lg border border-line px-2 py-1.5 text-left ${
              settings.hidden[type] ? "opacity-40" : ""
            }`}
            onClick={() => setSettings({ hidden: { ...settings.hidden, [type]: !settings.hidden[type] } })}
            aria-pressed={!settings.hidden[type]}
          >
            <span className="h-3 w-3 rounded-full" style={{ background: colorForType(settings, type) }} />
            <span>
              {type === "associated"
                ? "Known disease-associated protein"
                : type === "predicted"
                  ? "Predicted candidate protein"
                  : "Other protein"}
            </span>
          </button>
        ))}
        <div className="flex items-center gap-2 text-xs text-muted">
          <span className="h-px w-6" style={{ background: settings.edge }} />
          Protein–protein interaction
          <ConceptExplainer conceptId="edge" />
        </div>
      </div>
      {sizeByRank && (
        <p className="mt-2 text-xs text-muted">
          Predicted node size also uses Combined Score. That is a display choice, not a new scientific model.
        </p>
      )}
    </div>
  );
}

function VisualizationSettings({
  onResetColors,
  onFit,
  onResetView,
}: {
  onResetColors: () => void;
  onFit: () => void;
  onResetView: () => void;
}) {
  const { settings, setSettings } = useVizSettings();
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Node and edge colors</h3>
        <p className="text-xs text-muted">Presentation only. Colors do not change the underlying data.</p>
        <ColorRow label="Disease-associated" value={settings.associated} onChange={(associated) => setSettings({ associated })} />
        <ColorRow label="Predicted" value={settings.predicted} onChange={(predicted) => setSettings({ predicted })} />
        <ColorRow label="Other" value={settings.other} onChange={(other) => setSettings({ other })} />
        <ColorRow label="PPI / pathway edges" value={settings.edge} onChange={(edge) => setSettings({ edge })} />
      </div>
      <div className="space-y-2">
        <label className="block text-xs text-muted">
          Node size
          <input
            className="mt-1 w-full"
            type="range"
            min={0.6}
            max={2.2}
            step={0.1}
            value={settings.nodeSize}
            onChange={(e) => setSettings({ nodeSize: Number(e.target.value) })}
            aria-label="Node size"
          />
        </label>
        <label className="block text-xs text-muted">
          Edge opacity
          <input
            className="mt-1 w-full"
            type="range"
            min={0.08}
            max={0.9}
            step={0.02}
            value={settings.edgeOpacity}
            onChange={(e) => setSettings({ edgeOpacity: Number(e.target.value) })}
            aria-label="Edge opacity"
          />
        </label>
        <div className="flex flex-wrap gap-2 pt-1">
          <ControlButton label="Reset camera" onClick={onResetView}>
            Reset
          </ControlButton>
          <ControlButton label="Fit network" onClick={onFit}>
            Fit
          </ControlButton>
        </div>
        <button type="button" className="text-xs text-[var(--accent-strong)]" onClick={onResetColors}>
          Restore default colors
        </button>
      </div>
    </div>
  );
}

function ColorRow({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="flex items-center justify-between gap-2 text-xs text-muted">
      {label}
      <input type="color" value={toHex(value)} onChange={(e) => onChange(e.target.value)} aria-label={`${label} color`} />
    </label>
  );
}

function ControlButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="rounded-full border border-line px-3 py-1 text-xs hover:border-accent hover:bg-[var(--highlight)]"
    >
      {children}
    </button>
  );
}

function toHex(color: string): string {
  if (color.startsWith("#") && color.length === 7) return color;
  return "#6B7C80";
}

function hexToRgba(hex: string, alpha: number): string {
  const h = hex.replace("#", "");
  if (h.length !== 6) return `rgba(107,124,128,${alpha})`;
  const r = parseInt(h.slice(0, 2), 16);
  const g = parseInt(h.slice(2, 4), 16);
  const b = parseInt(h.slice(4, 6), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function dimHex(hex: string, alpha: number): string {
  return hexToRgba(hex.startsWith("#") ? hex : "#6B7C80", alpha);
}
