import type { ReactNode } from "react";
import { ConceptExplainer } from "@/components/ConceptExplainer";

function Shape({ title, children }: { title: string; children: ReactNode }) {
  return (
    <figure className="panel flex flex-col items-center gap-2 p-4 text-center">
      <svg viewBox="0 0 80 56" className="h-16 w-24" aria-hidden>
        {children}
      </svg>
      <figcaption className="art-caption">{title} · illustration only</figcaption>
    </figure>
  );
}

export function GraphletMotifs() {
  return (
    <section className="section-band space-y-4">
      <div className="stack-copy">
        <p className="eyebrow">Educational shapes</p>
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="section-title">Graphlets are small building blocks of a network</h2>
          <ConceptExplainer conceptId="graphlet" tone="learn" />
        </div>
      </div>
      <p className="max-w-3xl text-sm leading-relaxed text-muted">
        These drawings are educational shapes, not counts from a particular disease. A graphlet is a
        tiny connected pattern. An orbit is a specific seat inside that pattern. A motif is a
        repeating small shape. This project keeps two different measurements separate.
      </p>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Shape title="2-node edge">
          <line x1="16" y1="28" x2="64" y2="28" stroke="#71C9CE" strokeWidth="2" />
          <circle cx="16" cy="28" r="5" fill="#71C9CE" />
          <circle cx="64" cy="28" r="5" fill="#71C9CE" />
        </Shape>
        <Shape title="3-node path">
          <line x1="12" y1="40" x2="40" y2="14" stroke="#71C9CE" strokeWidth="2" />
          <line x1="40" y1="14" x2="68" y2="40" stroke="#71C9CE" strokeWidth="2" />
          <circle cx="12" cy="40" r="5" fill="#71C9CE" />
          <circle cx="40" cy="14" r="5" fill="#A6E3E9" />
          <circle cx="68" cy="40" r="5" fill="#71C9CE" />
        </Shape>
        <Shape title="Triangle">
          <line x1="18" y1="44" x2="40" y2="12" stroke="#71C9CE" strokeWidth="2" />
          <line x1="40" y1="12" x2="62" y2="44" stroke="#71C9CE" strokeWidth="2" />
          <line x1="18" y1="44" x2="62" y2="44" stroke="#71C9CE" strokeWidth="2" />
          <circle cx="18" cy="44" r="5" fill="#71C9CE" />
          <circle cx="40" cy="12" r="5" fill="#71C9CE" />
          <circle cx="62" cy="44" r="5" fill="#71C9CE" />
        </Shape>
        <Shape title="4-node star">
          <line x1="40" y1="28" x2="16" y2="12" stroke="#71C9CE" strokeWidth="2" />
          <line x1="40" y1="28" x2="64" y2="12" stroke="#71C9CE" strokeWidth="2" />
          <line x1="40" y1="28" x2="18" y2="46" stroke="#71C9CE" strokeWidth="2" />
          <line x1="40" y1="28" x2="62" y2="46" stroke="#71C9CE" strokeWidth="2" />
          <circle cx="40" cy="28" r="5" fill="#C45C26" />
          <circle cx="16" cy="12" r="4" fill="#71C9CE" />
          <circle cx="64" cy="12" r="4" fill="#71C9CE" />
          <circle cx="18" cy="46" r="4" fill="#71C9CE" />
          <circle cx="62" cy="46" r="4" fill="#71C9CE" />
        </Shape>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <article className="panel p-5">
          <h3 className="font-display text-sm font-semibold">
            Disease-level 73-dimensional orbit information <ConceptExplainer conceptId="orbit" />
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Each disease has a published SNAP profile of 73 orbit p-values. Those numbers describe
            how unusual the disease pathway’s small patterns are, compared with a null model from
            the paper. They are not computed per protein on this website.
          </p>
        </article>
        <article className="panel p-5">
          <h3 className="font-display text-sm font-semibold">
            Protein-level 12-dimensional motif proxy <ConceptExplainer conceptId="motif" />
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Per-protein structure here uses a 12-dimensional motif-signature proxy from the research
            pipeline. That is not the same as a 73-orbit ORCA signature, and the two must not be
            collapsed into one idea.
          </p>
        </article>
      </div>
    </section>
  );
}
