import Link from "next/link";
import { ConceptExplainer, Term } from "@/components/ConceptExplainer";
import { HeroNetwork } from "@/components/HeroNetwork";
import { SearchBox } from "@/components/SearchBox";
import {
  CandidateHighlight,
  DecorativeNetwork,
  DiseaseCluster,
  GraphletMotif,
  InteractionPair,
  PipelineStrip,
  ProteinMachine,
} from "@/components/ScientificArt";

const JOURNEY = [
  {
    href: "/diseases",
    title: "Disease",
    line: "Choose a disease",
    body: "Start from a named condition in the research catalogue.",
  },
  {
    href: "/disease/C0002395?tab=network",
    title: "Protein Network",
    line: "Explore how proteins interact",
    body: "See the protein–protein interaction map for that disease pathway.",
  },
  {
    href: "/disease/C0002395?tab=predictions",
    title: "Prediction",
    line: "See which proteins are ranked highly",
    body: "Inspect candidate proteins ranked by several computational methods.",
  },
  {
    href: "/explorer",
    title: "Graphlets",
    line: "Explore small patterns in the network",
    body: "Compare disease-level orbit profiles — the small building blocks of a network.",
  },
];

const STORY = [
  {
    art: <ProteinMachine />,
    title: "Think of proteins as tiny machines inside cells.",
    body: "In this website every protein is labeled only by its Entrez Gene ID.",
  },
  {
    art: <InteractionPair />,
    title: "Proteins interact with each other.",
    body: "A line means a recorded protein–protein interaction from the SNAP interactome, not a new lab experiment.",
  },
  {
    art: <DiseaseCluster />,
    title: "A disease can be associated with a group of proteins.",
    body: "Those associated proteins form a disease pathway: a small subgraph of the larger map.",
  },
  {
    art: <CandidateHighlight />,
    title: "Our models rank other proteins that may be worth investigating.",
    body: "A high rank is a computational hypothesis — a candidate, not a cause or a treatment.",
  },
  {
    art: <GraphletMotif />,
    title: "Graphlets describe small patterns inside the network.",
    body: "They are educational building blocks. Disease-level 73-orbit profiles are not the same as the 12-d protein motif proxy.",
  },
];

export default function HomePage() {
  return (
    <div className="relative space-y-16 md:space-y-20">
      <div className="pointer-events-none absolute inset-x-0 -top-6 -z-10 overflow-hidden" aria-hidden>
        <DecorativeNetwork className="mx-auto h-48 w-full max-w-7xl" />
      </div>

      <section className="grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="stack-copy">
          <p className="eyebrow">Computational biology • network science</p>
          <h1 className="hero-title">
            Discover the proteins
            <br />
            hidden inside disease networks.
          </h1>
          <p className="lede">
            Explore how protein interactions and computational prediction methods can help identify
            candidate proteins for further research.
          </p>
          <p className="panel max-w-xl px-4 py-3 text-sm leading-relaxed">
            This is a research and educational computational tool, not a clinical diagnostic system.
            Rankings are candidate hypotheses, not diagnoses or treatments.
          </p>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Link href="/diseases" className="cta">
              Explore a Disease →
            </Link>
          </div>
          <div className="max-w-xl pt-2">
            <SearchBox />
          </div>
          <p className="max-w-xl text-sm leading-relaxed text-muted">
            Interactive computational reproduction of Agrawal, Zitnik &amp; Leskovec,{" "}
            <em>Large-scale analysis of disease pathways in the human interactome</em> (PSB 2018),
            using the SNAP disease-pathway PPI and DisGeNET association datasets. Documented method
            deviations are listed on the{" "}
            <Link href="/methodology">Methodology</Link> page.
          </p>
        </div>
        <div className="panel p-5">
          <p className="eyebrow">Measured sample · Alzheimer pathway</p>
          <p className="mt-2 text-sm text-muted">
            This is a real subset of existing SNAP edges. Decorative drawings elsewhere on this page
            are not data.
          </p>
          <div className="mt-3">
            <HeroNetwork />
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {JOURNEY.map((card, i) => (
          <Link key={card.title} href={card.href} className="panel panel-hover block p-5">
            <p className="font-tech text-xs text-muted">0{i + 1}</p>
            <h2 className="section-title mt-2 text-[1.25rem]">{card.title}</h2>
            <p className="mt-1 text-sm font-medium text-[var(--accent-strong)]">{card.line}</p>
            <p className="mt-2 text-sm leading-relaxed text-muted">{card.body}</p>
          </Link>
        ))}
      </section>

      <section className="section-band space-y-6">
        <div className="stack-copy">
          <p className="eyebrow">How it works</p>
          <h2 className="section-title">From a disease name to a ranked candidate list</h2>
          <p className="lede">
            Think of a disease as a starting list of proteins. Those proteins sit in a larger map of
            protein partnerships. The computer studies that map, ranks other proteins that may be
            relevant, and then looks at small repeating patterns.
          </p>
        </div>
        <PipelineStrip />
        <p className="art-caption">
          This strip is a teaching diagram of the project workflow. It is not a new scientific
          result.
        </p>
      </section>

      <section className="space-y-6">
        <div className="stack-copy">
          <p className="eyebrow">A simple story</p>
          <h2 className="section-title">What this website is showing</h2>
          <p className="lede">
            The drawings below are educational illustrations. They are not measured protein
            interactions and they are not prediction results.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {STORY.map((step) => (
            <article key={step.title} className="panel flex flex-col p-5">
              <div className="mb-3">{step.art}</div>
              <h3 className="text-sm font-semibold leading-snug">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{step.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="panel p-5">
          <h3 className="section-title text-[1.15rem]">
            <Term conceptId="ppi" />
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Lines in the measured maps are recorded protein–protein interactions from the SNAP /
            BioGRID interactome, not new lab experiments run on this website.
          </p>
        </article>
        <article className="panel p-5">
          <h3 className="section-title text-[1.15rem]">
            <Term conceptId="candidate" />
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            A high rank means the computational model placed that protein near the top. It does not
            mean the protein causes or cures the disease.
          </p>
        </article>
        <article className="panel p-5">
          <h3 className="section-title text-[1.15rem]">
            Combined ranking <ConceptExplainer conceptId="combined_score" />
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Five methods each give a score. The Combined Score is the mean of those scores after
            each method is stretched onto a 0–1 scale.
          </p>
        </article>
      </section>
    </div>
  );
}
