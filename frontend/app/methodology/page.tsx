import type { Metadata } from "next";

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
      <header className="space-y-3">
        <h1 className="text-4xl font-semibold">Methodology</h1>
        <p className="text-muted">
          This platform is a presentation layer around a validated reproduction of
          Agrawal, Zitnik & Leskovec, <em>Large-scale analysis of disease pathways in the human interactome</em> (PSB 2018).
          It is a research tool for computational disease–protein association analysis, not a clinical diagnostic system.
        </p>
      </header>

      <ol className="space-y-2">
        {STEPS.map((step, i) => (
          <li key={step} className="flex items-center gap-3">
            <span className="w-8 font-mono text-sm text-muted">{i + 1}</span>
            <span className="panel flex-1 px-4 py-3">{step}</span>
          </li>
        ))}
      </ol>

      <section className="space-y-3">
        <h2 className="text-2xl">Data sources</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          <li>Human PPI network: 21,557 proteins, 342,353 interactions (Menche et al. / BioGRID via SNAP).</li>
          <li>Disease–protein associations: 519 diseases with ≥10 genes (DisGeNET via SNAP).</li>
          <li>Disease-level graphlet orbit p-values: 73 orbits per disease (paper supplementary).</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl">Prediction methods</h2>
        <p className="text-sm text-muted">
          Neighborhood scoring, Random Walk with Restart (α=0.7), DIAMOnD (z-score approximation),
          spectral embeddings (truncated SVD, 64-d) with logistic regression, and NMF matrix completion.
          The combined score is the mean of min–max-normalized method scores.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl">Evaluation</h2>
        <p className="text-sm text-muted">
          Disease-centric 10-fold cross-validation. Metrics actually computed: Recall@25, Recall@100, MRR.
          ROC-AUC, PR-AUC, F1, MSE, and R² are not computed in this project and are not displayed.
        </p>
      </section>

      <section className="panel border-predict/40 p-5">
        <h2 className="text-lg text-predict">Matrix Completion / NMF limitation</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted">
          In the cross-validation evaluation, NMF is fitted on the full protein×disease matrix before fold splitting.
          Matrix Completion therefore has access to test-fold associations during factorization, which inflates its
          reported CV metrics relative to the other four methods. This does not affect live predictions, where all
          known associations are legitimately available.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl">Known deviations from the paper</h2>
        <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
          <li>Neural embeddings use truncated SVD, not node2vec.</li>
          <li>DIAMOnD uses a z-score approximation rather than exact hypergeometric p-values.</li>
          <li>Per-protein graphlet signatures use 12 structural proxies, not full 73-orbit ORCA counts.</li>
          <li>Disease-level 73-orbit p-values from the SNAP dataset are shown as published.</li>
        </ul>
      </section>

      <section>
        <h2 className="text-2xl">References</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted">
          <li>Agrawal M, Zitnik M, Leskovec J. Large-scale analysis of disease pathways in the human interactome. PSB 2018.</li>
          <li>Menche J, et al. Uncovering disease-disease relationships through the incomplete interactome. Science 2015.</li>
          <li>Ghiassian SD, Menche J, Barabási AL. A DIAMOnD module detection algorithm. PLoS Comput Biol 2015.</li>
          <li>Piñero J, et al. DisGeNET. Nucleic Acids Research 2017.</li>
        </ol>
      </section>
    </div>
  );
}
