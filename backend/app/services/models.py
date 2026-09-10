"""Model comparison from precomputed CV CSVs. No new evaluation metrics."""

from __future__ import annotations

from ..config import METHOD_ORDER, NMF_LEAKAGE_NOTE
from ..schemas import MethodInfo, MethodPerformance, ModelsResponse
from ..store import store

METHOD_DESCRIPTIONS = {
    "Neighborhood": (
        "Fraction of PPI neighbors that are known disease-associated (seed) proteins."
    ),
    "Random Walk": (
        "Random walk with restart (α=0.7) on the PPI network, seeded at known "
        "disease proteins."
    ),
    "DIAMOnD": (
        "Iterative module expansion adding the protein with the most significant "
        "connectivity to the current seed module (z-score approximation, max 100 added)."
    ),
    "Neural Embeddings": (
        "64-dimensional spectral embeddings (truncated SVD of the normalized adjacency) "
        "with logistic regression trained on seed proteins. This is not node2vec."
    ),
    "Matrix Completion": (
        "Non-negative matrix factorization of the protein×disease association matrix; "
        "reconstructed scores prioritize missing associations."
    ),
}


def models_payload() -> ModelsResponse:
    store.load()
    pred = store.prediction_results
    performance = []
    for method in METHOD_ORDER:
        sub = pred[pred["Method"] == method]
        performance.append(
            MethodPerformance(
                method=method,
                n_diseases=int(sub["Disease ID"].nunique()) if not sub.empty else 0,
                recall_at_25=float(sub["Recall@25"].mean()) if not sub.empty else 0.0,
                recall_at_100=float(sub["Recall@100"].mean()) if not sub.empty else 0.0,
                mrr=float(sub["MRR"].mean()) if not sub.empty else 0.0,
            )
        )

    aug = store.augmented_results
    augmented = {
        "description": (
            "Separate 10-fold CV experiment: spectral embeddings vs embeddings "
            "concatenated with 12 local structural motif-proxy features and logistic "
            "regression. This is not a sixth live ranking method."
        ),
        "n_diseases": int(len(aug)),
        "mean_baseline_recall_at_100": float(aug["Baseline R@100"].mean()),
        "mean_augmented_recall_at_100": float(aug["Augmented R@100"].mean()),
        "mean_baseline_mrr": float(aug["Baseline MRR"].mean()),
        "mean_augmented_mrr": float(aug["Augmented MRR"].mean()),
        "metrics_available": [
            "Baseline R@100",
            "Augmented R@100",
            "Improvement",
            "Baseline MRR",
            "Augmented MRR",
        ],
    }

    methods = []
    for name in METHOD_ORDER:
        methods.append(
            MethodInfo(
                name=name,
                description=METHOD_DESCRIPTIONS[name],
                evaluation_caveat=NMF_LEAKAGE_NOTE if name == "Matrix Completion" else None,
            )
        )

    return ModelsResponse(
        methods=methods,
        metrics_available=["Recall@25", "Recall@100", "MRR"],
        metrics_not_computed=["ROC-AUC", "PR-AUC", "Precision", "Recall", "F1", "MSE", "R²"],
        nmf_leakage_note=NMF_LEAKAGE_NOTE,
        performance=performance,
        augmented=augmented,
    )


def per_disease_performance(disease_id: str) -> list[dict]:
    store.load()
    pred = store.prediction_results
    sub = pred[pred["Disease ID"] == disease_id]
    rows = []
    for method in METHOD_ORDER:
        row = sub[sub["Method"] == method]
        if row.empty:
            continue
        r = row.iloc[0]
        rows.append(
            {
                "method": method,
                "recall_at_25": float(r["Recall@25"]),
                "recall_at_100": float(r["Recall@100"]),
                "mrr": float(r["MRR"]),
            }
        )
    return rows
