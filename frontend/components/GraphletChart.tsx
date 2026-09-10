"use client";

import { useMemo, useState } from "react";

type Orbit = {
  orbit: number;
  p_value: number | null;
  significant: boolean;
  graphlet_size: string;
};

export function GraphletChart({
  orbits,
  title,
}: {
  orbits: Orbit[];
  title?: string;
}) {
  const [open, setOpen] = useState(false);
  const compact = useMemo(() => {
    return orbits.map((o) => {
      const p = o.p_value;
      const height = p == null || p <= 0 ? 0 : Math.min(100, -Math.log10(p) * 18);
      return { ...o, height };
    });
  }, [orbits]);

  return (
    <div className="panel p-5">
      {title && <h3 className="mb-3 text-sm text-muted">{title}</h3>}
      <div className="flex h-40 items-end gap-px overflow-x-auto">
        {compact.map((o) => (
          <div
            key={o.orbit}
            title={`Orbit ${o.orbit} (${o.graphlet_size}) p=${o.p_value ?? "NA"}`}
            className={`w-1.5 min-w-[4px] rounded-t ${o.significant ? "bg-accent" : "bg-white/20"}`}
            style={{ height: `${Math.max(o.height, 2)}%` }}
          />
        ))}
      </div>
      <p className="mt-3 text-sm text-muted">
        Bars show −log10(p). Highlighted bars are significant at p &lt; 0.01.
        These are disease-level orbit p-values, not per-protein ORCA counts.
      </p>
      <button
        type="button"
        className="mt-3 text-sm text-accent"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? "Hide orbit values" : "Show all 73 orbit values"}
      </button>
      {open && (
        <div className="mt-3 max-h-72 overflow-auto rounded-lg border border-line text-xs">
          <table className="min-w-full">
            <thead className="text-muted">
              <tr>
                <th className="px-2 py-1 text-left">Orbit</th>
                <th className="px-2 py-1 text-left">Size</th>
                <th className="px-2 py-1 text-left">p-value</th>
              </tr>
            </thead>
            <tbody>
              {orbits.map((o) => (
                <tr key={o.orbit} className="border-t border-line">
                  <td className="px-2 py-1 font-mono">{o.orbit}</td>
                  <td className="px-2 py-1">{o.graphlet_size}</td>
                  <td className="px-2 py-1 font-mono">
                    {o.p_value == null ? "—" : o.p_value.toExponential(3)}
                    {o.significant ? " *" : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
