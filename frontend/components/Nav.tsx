"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import { useMode } from "./ModeProvider";
import { SearchBox } from "./SearchBox";
import { useTheme } from "./ThemeProvider";
import { IconDisease, IconGraphlets, IconHome, IconMethod, IconModels } from "./ScientificArt";

const LINKS: { href: string; label: string; icon: ReactNode }[] = [
  { href: "/", label: "Home", icon: <IconHome /> },
  { href: "/diseases", label: "Diseases", icon: <IconDisease /> },
  { href: "/models", label: "Models", icon: <IconModels /> },
  { href: "/explorer", label: "Compare Graphlets", icon: <IconGraphlets /> },
  { href: "/methodology", label: "Methodology", icon: <IconMethod /> },
];

function active(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Nav() {
  const pathname = usePathname();
  const { mode, setMode } = useMode();
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-[color-mix(in_srgb,var(--background)_82%,transparent)] backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3 md:px-6">
        <Link href="/" className="font-display shrink-0 text-sm font-semibold tracking-tight text-foreground">
          Network Intelligence
        </Link>
        <div className="hidden min-w-0 flex-1 md:block">
          <SearchBox compact />
        </div>
        <nav className="hidden items-center gap-1 text-sm text-muted lg:flex">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1.5 ${
                active(pathname, l.href) ? "chip-on text-foreground" : "text-muted hover:text-foreground"
              }`}
            >
              {l.icon}
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
          className="rounded-full border border-line px-3 py-1 text-xs text-muted"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
        >
          {theme === "dark" ? "Light" : "Dark"}
        </button>
        <button
          type="button"
          className="rounded-md border border-line px-3 py-1 text-sm lg:hidden"
          aria-expanded={open}
          onClick={() => setOpen((v) => !v)}
        >
          Menu
        </button>
      </div>
      {open && (
        <div className="space-y-3 border-t border-line px-4 py-3 lg:hidden">
          <SearchBox compact />
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} className="flex items-center gap-2 text-sm" onClick={() => setOpen(false)}>
              {l.icon}
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
