"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { CONCEPTS, type Concept } from "@/lib/concepts";

export function ConceptExplainer({
  conceptId,
  concept,
  label,
  tone = "icon",
  className = "",
}: {
  conceptId?: string;
  concept?: Concept;
  label?: string;
  tone?: "icon" | "learn";
  className?: string;
}) {
  const data = concept || (conceptId ? CONCEPTS[conceptId] : undefined);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"simple" | "research">("simple");
  const [pos, setPos] = useState({ top: 0, left: 0, width: 320, maxHeight: 280, mobile: false });
  const boxRef = useRef<HTMLSpanElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const popupId = useId();

  function place() {
    const trigger = boxRef.current;
    if (!trigger) return;
    const r = trigger.getBoundingClientRect();
    const mobile = window.innerWidth < 640;
    const width = mobile ? Math.min(window.innerWidth - 24, 420) : Math.min(320, window.innerWidth - 24);
    const margin = 12;
    const navClear = 72;
    if (mobile) {
      setPos({ top: 0, left: 12, width, maxHeight: Math.min(360, window.innerHeight - 24), mobile: true });
      return;
    }
    const height = popupRef.current?.offsetHeight || 240;
    let left = r.left;
    if (left + width > window.innerWidth - margin) left = window.innerWidth - width - margin;
    if (left < margin) left = margin;

    const tabRow = document.querySelector("[data-workspace-tabs]");
    const tabRect = tabRow?.getBoundingClientRect();
    const overlapsTabs = (top: number) => {
      if (!tabRect) return false;
      return top < tabRect.bottom + 6 && top + height > tabRect.top - 6;
    };

    const below = r.bottom + 8;
    const above = r.top - height - 8;
    const belowFits =
      below + height <= window.innerHeight - margin && below >= navClear && !overlapsTabs(below);
    const aboveFits = above >= navClear && !overlapsTabs(above);

    let top = below;
    if (belowFits) {
      top = below;
    } else if (aboveFits) {
      top = above;
    } else if (r.right + 8 + width <= window.innerWidth - margin && !overlapsTabs(Math.max(navClear, tabRect ? tabRect.top - height - 8 : r.top))) {
      left = r.right + 8;
      top = Math.max(navClear, tabRect ? tabRect.top - height - 8 : r.top);
    } else if (r.left - width - 8 >= margin && !overlapsTabs(Math.max(navClear, tabRect ? tabRect.top - height - 8 : r.top))) {
      left = r.left - width - 8;
      top = Math.max(navClear, tabRect ? tabRect.top - height - 8 : r.top);
    } else if (tabRect) {
      const aboveTabs = tabRect.top - margin;
      top = navClear;
      setPos({
        top,
        left,
        width,
        maxHeight: Math.max(140, aboveTabs - navClear),
        mobile: false,
      });
      return;
    } else {
      top = Math.max(navClear, above);
    }

    if (top < navClear) top = navClear;
    const maxHeight = Math.max(160, window.innerHeight - top - margin);
    if (top + Math.min(height, maxHeight) > window.innerHeight - margin) {
      top = Math.max(navClear, window.innerHeight - Math.min(height, maxHeight) - margin);
    }
    setPos({ top, left, width, maxHeight, mobile: false });
  }

  useLayoutEffect(() => {
    if (!open) return;
    place();
    const id = window.requestAnimationFrame(() => place());
    return () => window.cancelAnimationFrame(id);
  }, [open, tab]);

  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      const t = e.target as Node;
      if (boxRef.current?.contains(t) || popupRef.current?.contains(t)) return;
      setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    function onMove() {
      place();
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onMove);
    window.addEventListener("scroll", onMove, true);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onMove);
      window.removeEventListener("scroll", onMove, true);
    };
  }, [open]);

  if (!data) return null;

  const dialog = open
    ? createPortal(
        <div
          ref={popupRef}
          id={popupId}
          role="dialog"
          aria-label={data.term}
          className={`concept-popover z-[90] overflow-y-auto border border-line bg-[var(--panel)] p-4 text-left shadow-2xl ${
            pos.mobile ? "fixed inset-x-3 bottom-3 rounded-2xl" : "fixed rounded-xl"
          }`}
          style={
            pos.mobile
              ? { maxHeight: pos.maxHeight }
              : {
                  top: pos.top,
                  left: pos.left,
                  width: pos.width,
                  maxWidth: "calc(100vw - 24px)",
                  maxHeight: pos.maxHeight,
                }
          }
        >
          <p className="text-sm font-medium text-foreground">{data.term}</p>
          <div className="mt-2 flex gap-2 text-xs">
            <button
              type="button"
              className={`rounded-full px-2 py-1 ${tab === "simple" ? "chip-on" : "text-muted"}`}
              onClick={() => setTab("simple")}
            >
              Simple
            </button>
            <button
              type="button"
              className={`rounded-full px-2 py-1 ${tab === "research" ? "chip-on" : "text-muted"}`}
              onClick={() => setTab("research")}
            >
              Research
            </button>
          </div>
          <p className="mt-2 text-sm font-normal leading-relaxed text-muted normal-case">
            {tab === "simple" ? data.simple : data.research}
          </p>
        </div>,
        document.body
      )
    : null;

  return (
    <span ref={boxRef} className={`relative inline-flex items-center ${className}`}>
      <button
        type="button"
        className={
          tone === "learn"
            ? "ml-1 normal-case text-xs font-normal tracking-normal text-[var(--accent-strong)] underline-offset-2 hover:underline"
            : "ml-1 inline-flex h-5 w-5 items-center justify-center rounded-full border border-line text-[11px] font-normal normal-case tracking-normal text-muted hover:border-accent hover:text-accent"
        }
        aria-expanded={open}
        aria-controls={popupId}
        aria-label={`What does ${data.term} mean?`}
        title={`What does ${data.term} mean?`}
        onClick={() => setOpen((v) => !v)}
      >
        {label || (tone === "learn" ? "What does this mean?" : "i")}
      </button>
      {dialog}
    </span>
  );
}

export function Term({ conceptId, children }: { conceptId: string; children?: ReactNode }) {
  const data = CONCEPTS[conceptId];
  return (
    <span className="inline-flex items-center">
      <span>{children || data?.term}</span>
      <ConceptExplainer conceptId={conceptId} />
    </span>
  );
}
