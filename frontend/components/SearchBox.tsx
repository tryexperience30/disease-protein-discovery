"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { SearchHit } from "@/types";

export function SearchBox({ compact = false, autoFocus = false }: { compact?: boolean; autoFocus?: boolean }) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!q.trim()) {
      setHits([]);
      setOpen(false);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const data = await apiGet<{ results: SearchHit[] }>(`/api/search?q=${encodeURIComponent(q)}&limit=8`);
        setHits(data.results);
        setOpen(true);
        setActive(0);
        setError(null);
      } catch {
        setError("Unable to load search data. Please try again.");
        setHits([]);
        setOpen(true);
      }
    }, 180);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!boxRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  function go(hit: SearchHit) {
    setOpen(false);
    setQ("");
    router.push(hit.type === "disease" ? `/disease/${hit.id}` : `/protein/${hit.id}`);
  }

  return (
    <div ref={boxRef} className="relative w-full">
      <label htmlFor={compact ? "nav-search" : "home-search"} className="sr-only">
        Search disease or protein
      </label>
      <input
        id={compact ? "nav-search" : "home-search"}
        value={q}
        autoFocus={autoFocus}
        placeholder="Search disease or Entrez Gene ID…"
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => hits.length && setOpen(true)}
        onKeyDown={(e) => {
          if (!open) return;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setActive((i) => Math.min(i + 1, Math.max(hits.length - 1, 0)));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setActive((i) => Math.max(i - 1, 0));
          } else if (e.key === "Enter" && hits[active]) {
            e.preventDefault();
            go(hits[active]);
          } else if (e.key === "Escape") setOpen(false);
        }}
        className={`w-full rounded-xl border border-line bg-[var(--panel)] px-4 text-foreground placeholder:text-muted ${
          compact ? "h-10 text-sm" : "h-14 text-base"
        }`}
        autoComplete="off"
      />
      {open && (
        <ul
          role="listbox"
          className="absolute z-50 mt-2 w-full overflow-hidden rounded-xl border border-line bg-[var(--panel)] shadow-2xl"
        >
          {error && <li className="px-4 py-3 text-sm text-predict">{error}</li>}
          {!error && hits.length === 0 && (
            <li className="px-4 py-3 text-sm text-muted">No matching disease or protein ID.</li>
          )}
          {hits.map((hit, i) => (
            <li key={`${hit.type}-${hit.id}`} role="option" aria-selected={i === active}>
              <button
                type="button"
                className={`block w-full px-4 py-3 text-left ${i === active ? "bg-white/5" : ""}`}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(hit)}
              >
                <div className="text-sm">{hit.label}</div>
                <div className="text-xs text-muted">{hit.subtitle}</div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
