import type { Metadata } from "next";
import { ConceptExplainer, Term } from "@/components/ConceptExplainer";
import { PipelineStrip } from "@/components/ScientificArt";

export const metadata: Metadata = {
  title: "Methodology",
  description:
    "Computational pipeline for disease–protein association analysis on the human interactome.",
};

const STEPS = [
  "Disease Associations",
  "PPI Network",
  "Disease-Specific Network",
  "Structural Analysis",
  "Prediction Methods",
  "Graphlet Signatures",
  "Neural Embeddings",
  "Logistic Regression",
  "Candidate Proteins",
];

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-10">
      <header className="stack-copy">
        <p className="eyebrow">Research pipeline</p>
        <h1 className="page-title">Methodology</h1>
        <p className="lede">
          This platform is a presentation layer around a validated reproduction of Agrawal, Zitnik
          &amp; Leskovec, <em>Large-scale analysis of disease pathways in the human interactome</em>{" "}
          (PSB 2018). It is a research tool for computational disease–protein association analysis,
          not a clinical diagnostic system.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="section-title">Project workflow</h2>
        <p className="text-sm leading-relaxed text-muted">
          This strip is a teaching diagram of the product story. The numbered list below is the
          research pipeline implemented in this reproduction.
        </p>
        <PipelineStrip />
        <p className="art-caption">Decorative workflow — not a new scientific result.</p>
      </section>

      <ol className="space-y-2">
        {STEPS.map((step, i) => (
          <li key={step} className="flex items-center gap-3">
            <span className="font-tech w-8 text-sm text-muted">{i + 1}</span>
            <span className="panel flex-1 px-4 py-3">{step}</span>
          </li>
        ))}
      </ol>

      <section className="space-y-3">
        <h2 className="section-title">Data sources</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          <li>
            Human <Term conceptId="ppi">PPI network</Term>: 21,557 proteins, 342,353 interactions
            (Menche et al. / BioGRID via SNAP).
          </li>
          <li>
            Disease–protein associations: 519 diseases with ≥10 genes (DisGeNET via SNAP).
          </li>
          <li>
            Disease-level <Term conceptId="orbit">graphlet orbit</Term> p-values: 73 orbits per
            disease (paper supplementary).
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="section-title">Prediction methods</h2>
        <p className="text-sm text-muted">
          <Term conceptId="neighborhood">Neighborhood</Term> scoring,{" "}
          <Term conceptId="random_walk">Random Walk</Term> with Restart (α=0.7),{" "}
          <Term conceptId="diamond">DIAMOnD</Term> (z-score approximation),{" "}
          <Term conceptId="neural_embeddings">spectral embeddings</Term> (truncated SVD, 64-d) with
          logistic regression, and <Term conceptId="matrix_completion">NMF matrix completion</Term>.
          The <Term conceptId="combined_score">combined score</Term> is the mean of min–max-normalized
          method scores.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="section-title">Evaluation</h2>
        <p className="text-sm text-muted">
          Disease-centric 10-fold cross-validation. Metrics actually computed:{" "}
          <Term conceptId="recall25">Recall@25</Term>, <Term conceptId="recall100">Recall@100</Term>,{" "}
          <Term conceptId="mrr">MRR</Term>. ROC-AUC, PR-AUC, F1, MSE, and R² are not computed in this
          project and are not displayed.
        </p>
      </section>

      <section className="panel border-predict/40 p-5">
        <h2 className="section-title text-[1.2rem] text-predict">Matrix Completion / NMF limitation</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          In the cross-validation evaluation, NMF is fitted on the full protein×disease matrix
          before fold splitting. Matrix Completion therefore has access to test-fold associations
          during factorization, which inflates its reported CV metrics relative to the other four
          methods. This does not affect live predictions, where all known associations are
          legitimately available.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="section-title">Known deviations from the paper</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          <li>Neural embeddings use truncated SVD, not node2vec.</li>
          <li>DIAMOnD uses a z-score approximation rather than exact hypergeometric p-values.</li>
          <li>
            Per-protein graphlet signatures use 12 structural proxies, not full 73-orbit ORCA
            counts. <ConceptExplainer conceptId="motif" />
          </li>
          <li>Disease-level 73-orbit p-values from the SNAP dataset are shown as published.</li>
        </ul>
      </section>

      <section>
        <h2 className="section-title">References</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted">
          <li>
            Agrawal M, Zitnik M, Leskovec J. Large-scale analysis of disease pathways in the human
            interactome. PSB 2018.
          </li>
          <li>
            Menche J, et al. Uncovering disease-disease relationships through the incomplete
            interactome. Science 2015.
          </li>
          <li>
            Ghiassian SD, Menche J, Barabási AL. A DIAMOnD module detection algorithm. PLoS Comput
            Biol 2015.
          </li>
          <li>Piñero J, et al. DisGeNET. Nucleic Acids Research 2017.</li>
        </ol>
      </section>
    </div>
  );
}
