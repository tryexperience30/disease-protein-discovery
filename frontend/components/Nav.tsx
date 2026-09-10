"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useMode } from "./ModeProvider";
import { SearchBox } from "./SearchBox";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/models", label: "Models" },
  { href: "/explorer", label: "Graphlets" },
  { href: "/methodology", label: "Methodology" },
];

export function Nav() {
  const pathname = usePathname();
  const { mode, setMode } = useMode();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-[#080b12]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 md:px-6">
        <Link href="/" className="shrink-0 text-sm font-semibold tracking-tight">
          Network Intelligence
        </Link>
        <div className="hidden flex-1 md:block">
          <SearchBox compact />
        </div>
        <nav className="hidden items-center gap-4 text-sm text-muted md:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={pathname === l.href ? "text-foreground" : "hover:text-foreground"}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <button
          type="button"
          className="hidden rounded-full border border-line px-3 py-1 text-xs text-muted md:inline"
          onClick={() => setMode(mode === "explorer" ? "research" : "explorer")}
          aria-pressed={mode === "research"}
        >
          {mode === "explorer" ? "Explorer mode" : "Research mode"}
        </button>
        <button
          type="button"
          className="ml-auto rounded-md border border-line px-3 py-1 text-sm md:hidden"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>
      {open && (
        <div className="space-y-3 border-t border-line px-4 py-3 md:hidden">
          <SearchBox compact />
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="block text-sm" onClick={() => setOpen(false)}>
              {l.label}
            </Link>
          ))}
          <button
            type="button"
            className="text-sm text-muted"
            onClick={() => setMode(mode === "explorer" ? "research" : "explorer")}
          >
            Switch to {mode === "explorer" ? "Research" : "Explorer"} mode
          </button>
        </div>
      )}
    </header>
  );
}
