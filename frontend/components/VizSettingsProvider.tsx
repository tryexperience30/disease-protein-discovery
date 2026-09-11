"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type VizSettings = {
  associated: string;
  predicted: string;
  other: string;
  edge: string;
  nodeSize: number;
  edgeOpacity: number;
  showLabels: boolean;
  hidden: Record<"associated" | "predicted" | "other", boolean>;
};

const DEFAULTS: VizSettings = {
  associated: "#71C9CE",
  predicted: "#C45C26",
  other: "#6B7C80",
  edge: "#2F8B91",
  nodeSize: 1,
  edgeOpacity: 0.56,
  showLabels: false,
  hidden: { associated: false, predicted: false, other: false },
};

const KEY = "dpni-viz-v3";
const LEGACY_KEY = "dpni-viz-v2";
const LEGACY_EDGE_OPACITY = 0.4;

function normalize(parsed: Partial<VizSettings>): VizSettings {
  return {
    ...DEFAULTS,
    ...parsed,
    hidden: { ...DEFAULTS.hidden, ...(parsed.hidden || {}) },
  };
}

function migrateLegacy(parsed: Partial<VizSettings>): VizSettings {
  const next = normalize(parsed);
  if (parsed.edgeOpacity == null || parsed.edgeOpacity === LEGACY_EDGE_OPACITY) {
    next.edgeOpacity = DEFAULTS.edgeOpacity;
  }
  return next;
}

const VizContext = createContext<{
  settings: VizSettings;
  setSettings: (next: Partial<VizSettings>) => void;
  reset: () => void;
}>({ settings: DEFAULTS, setSettings: () => undefined, reset: () => undefined });

export function VizSettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setState] = useState<VizSettings>(DEFAULTS);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const current = localStorage.getItem(KEY);
      if (current) {
        setState(normalize(JSON.parse(current) as Partial<VizSettings>));
      } else {
        const legacy = localStorage.getItem(LEGACY_KEY);
        if (legacy) {
          setState(migrateLegacy(JSON.parse(legacy) as Partial<VizSettings>));
          localStorage.removeItem(LEGACY_KEY);
        }
      }
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(KEY, JSON.stringify(settings));
    } catch {
      /* ignore */
    }
  }, [settings, ready]);

  const setSettings = useCallback((next: Partial<VizSettings>) => {
    setState((s) => ({ ...s, ...next }));
  }, []);
  const reset = useCallback(() => setState(DEFAULTS), []);

  const value = useMemo(
    () => ({
      settings,
      setSettings,
      reset,
    }),
    [settings, setSettings, reset]
  );

  return <VizContext.Provider value={value}>{children}</VizContext.Provider>;
}

export function useVizSettings() {
  return useContext(VizContext);
}

export function colorForType(settings: VizSettings, type: string): string {
  if (type === "associated") return settings.associated;
  if (type === "predicted") return settings.predicted;
  return settings.other;
}
