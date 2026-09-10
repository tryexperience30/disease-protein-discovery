"""Page 6: Model Comparison — cross-disease method analysis."""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.config import METHOD_ORDER, METHOD_COLORS
from app.cache import (
    get_prediction_results, get_pathway_features,
    get_augmented_results, get_disease_classes,
)


def render():
    st.title("Model Analysis")
    st.markdown("Cross-disease comparison of five prediction methods, "
                "performance vs pathway structure, and the effect of "
                "augmenting embeddings with motif features.")

    pred_df = get_prediction_results()
    features_df = get_pathway_features()
    disease_classes = get_disease_classes()

    # ── Overall performance ──────────────────────────────────────────────
    st.subheader("Overall Method Performance")

    metric = st.radio("Metric", ["Recall@100", "Recall@25", "MRR"], horizontal=True)

    agg = pred_df.groupby("Method")[metric].mean().reindex(METHOD_ORDER)
    fig = px.bar(
        x=agg.index, y=agg.values, color=agg.index,
        color_discrete_map=METHOD_COLORS,
        text=[f"{v:.4f}" for v in agg.values],
        labels={"x": "", "y": metric},
    )
    fig.update_layout(showlegend=False, height=380,
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "**Note on Matrix Completion:** Its cross-validation metrics are optimistic "
        "because NMF was fitted on the full protein-disease matrix before fold splitting, "
        "giving it access to test-fold associations. The other four methods use only "
        "train-fold seed proteins and are not affected."
    )

    st.divider()

    # ── Performance vs structure ─────────────────────────────────────────
    st.subheader("Performance vs Pathway Structure")

    struct_metric = st.selectbox("Structural metric (x-axis)", [
        "Size of largest pathway component",
        "Density of pathway",
        "Distance of Pathway Components",
    ])

    tabs = st.tabs(METHOD_ORDER)
    for tab, method in zip(tabs, METHOD_ORDER):
        with tab:
            mdf = pred_df[pred_df["Method"] == method].set_index("Disease ID")
            common = mdf.index.intersection(features_df.index)
            x = features_df.loc[common, struct_metric].astype(float)
            y = mdf.loc[common, "Recall@100"].astype(float)
            valid = x.notna() & y.notna()
            x, y = x[valid], y[valid]

            if len(x) < 5:
                st.warning("Insufficient data.")
                continue

            corr = np.corrcoef(x, y)[0, 1]
            sdf = pd.DataFrame({"x": x, "y": y})
            fig = px.scatter(sdf, x="x", y="y", trendline="ols",
                             color_discrete_sequence=[METHOD_COLORS[method]],
                             opacity=0.4,
                             labels={"x": struct_metric, "y": "Recall@100"})
            fig.update_layout(title=f"{method} — ρ = {corr:.3f}",
                              height=400, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Performance by disease category ──────────────────────────────────
    st.subheader("Performance by Disease Category")

    pred_with_class = pred_df.copy()
    pred_with_class["Category"] = pred_with_class["Disease ID"].map(disease_classes)
    pred_with_class = pred_with_class.dropna(subset=["Category"])

    top_cats = pred_with_class["Category"].value_counts().head(8).index.tolist()
    cat_data = pred_with_class[pred_with_class["Category"].isin(top_cats)]

    fig = px.box(cat_data, x="Category", y="Recall@100", color="Method",
                 color_discrete_map=METHOD_COLORS,
                 category_orders={"Method": METHOD_ORDER})
    fig.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Augmented vs baseline ────────────────────────────────────────────
    st.subheader("Augmented Prediction: Embedding + Motif Features")

    aug_df = get_augmented_results()
    col_l, col_r = st.columns(2)

    with col_l:
        base_r = aug_df["Baseline R@100"].mean()
        aug_r = aug_df["Augmented R@100"].mean()
        pct = 100 * (aug_r - base_r) / max(base_r, 1e-10)
        n_improved = int((aug_df["Improvement"] > 0).sum())

        st.metric("Baseline R@100", f"{base_r:.4f}")
        st.metric("Augmented R@100", f"{aug_r:.4f}", delta=f"{pct:+.1f}%")
        st.metric("Diseases Improved", f"{n_improved} / {len(aug_df)}")

    with col_r:
        fig = px.scatter(aug_df, x="Baseline R@100", y="Augmented R@100",
                         hover_data=["Disease Name"], opacity=0.4,
                         color_discrete_sequence=["#4C72B0"])
        lim = max(aug_df["Baseline R@100"].max(),
                  aug_df["Augmented R@100"].max()) + 0.05
        fig.add_shape(type="line", x0=0, x1=lim, y0=0, y1=lim,
                      line=dict(dash="dash", color="gray"))
        fig.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Disease comparison ───────────────────────────────────────────────
    st.subheader("Disease Comparison")

    disease_list_sorted = sorted(
        pred_df["Disease Name"].unique().tolist()
    )
    col_a, col_b = st.columns(2)
    with col_a:
        disease_a = st.selectbox("Disease A", disease_list_sorted, index=0)
    with col_b:
        disease_b = st.selectbox("Disease B", disease_list_sorted,
                                 index=min(1, len(disease_list_sorted)-1))

    if disease_a and disease_b and disease_a != disease_b:
        from app.cache import get_disease_associations, get_computed_metrics
        dg, dn = get_disease_associations()
        metrics = get_computed_metrics()

        did_a = [did for did, n in dn.items() if n == disease_a]
        did_b = [did for did, n in dn.items() if n == disease_b]

        if did_a and did_b:
            did_a, did_b = did_a[0], did_b[0]
            genes_a, genes_b = dg[did_a], dg[did_b]
            shared = genes_a & genes_b

            c1, c2, c3 = st.columns(3)
            c1.metric(f"{disease_a} proteins", len(genes_a))
            c2.metric(f"{disease_b} proteins", len(genes_b))
            c3.metric("Shared proteins", len(shared))

            if did_a in metrics.index and did_b in metrics.index:
                compare_cols = ["Size of largest pathway component",
                                "Density of pathway", "Conductance",
                                "Num Components"]
                available = [c for c in compare_cols if c in metrics.columns]
                comp_df = metrics.loc[[did_a, did_b], available].T
                comp_df.columns = [disease_a, disease_b]
                st.dataframe(comp_df, use_container_width=True)
    elif disease_a == disease_b:
        st.info("Select two different diseases to compare.")
