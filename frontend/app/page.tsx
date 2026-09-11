import { SearchBox } from "@/components/SearchBox";

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 -z-10 opacity-40" aria-hidden>
        <svg className="h-[480px] w-full" viewBox="0 0 800 400">
          <g stroke="rgba(74,163,240,0.25)" fill="none">
            <line x1="80" y1="220" x2="220" y2="90" />
            <line x1="220" y1="90" x2="390" y2="140" />
            <line x1="390" y1="140" x2="520" y2="60" />
            <line x1="390" y1="140" x2="480" y2="250" />
            <line x1="220" y1="90" x2="160" y2="300" />
            <line x1="480" y1="250" x2="670" y2="180" />
            <line x1="670" y1="180" x2="720" y2="80" />
          </g>
          <g fill="#4aa3f0">
            <circle cx="80" cy="220" r="4" />
            <circle cx="220" cy="90" r="5" />
            <circle cx="390" cy="140" r="6" />
            <circle cx="520" cy="60" r="4" />
            <circle cx="160" cy="300" r="3" />
          </g>
          <g fill="#e3a04a">
            <circle cx="480" cy="250" r="5" />
            <circle cx="670" cy="180" r="4" />
            <circle cx="720" cy="80" r="3" />
          </g>
        </svg>
      </div>

      <section className="max-w-3xl space-y-6 pb-10 pt-6 md:pt-16">
        <p className="text-xs uppercase tracking-[0.25em] text-muted">
          Research tool for computational disease–protein association analysis
        </p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight md:text-6xl">
          Disease–Protein Network Intelligence
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-muted">
          An interactive computational reproduction and exploration of disease pathways in
          the human interactome, based on Agrawal, Zitnik &amp; Leskovec,{" "}
          <em>Large-scale analysis of disease pathways in the human interactome</em> (PSB 2018),
          using the SNAP disease-pathway PPI and DisGeNET association datasets. Documented
          method deviations are listed on the Methodology page. This is a research presentation
          layer, not a new prediction algorithm and not a clinical diagnostic tool.
        </p>
        <SearchBox autoFocus />
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[
          ["Disease network analysis", "Structural metrics of disease-specific PPI pathways, including LCC size, density, conductance, and modularity."],
          ["Protein interaction exploration", "Rotate, zoom, and inspect real PPI edges among associated and neighboring proteins."],
          ["Candidate protein prediction", "Five computational methods plus a combined ranking of candidate associations."],
          ["Multiple computational methods", "Neighborhood, Random Walk, DIAMOnD, spectral embeddings, and NMF matrix completion."],
        ].map(([title, body]) => (
          <article key={title} className="panel p-5">
            <h2 className="text-base font-medium">{title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
