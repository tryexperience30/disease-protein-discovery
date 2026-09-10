"""Page 4: Predictions — ranked protein table, method comparison, explanation."""

import streamlit as st
import pandas as pd
import numpy as np

from app.config import METHOD_ORDER, METHOD_COLORS
from app.cache import get_disease_list, get_disease_associations
from app.utils.live_predict import predict_for_disease, get_protein_network_stats
from app.components.prediction_table import render_prediction_table
from app.components.charts import method_bar_chart, protein_score_radar


def _disease_selector():
    disease_list = get_disease_list()
    options = {f"{name} ({did})": did for did, name in disease_list}
    preselect = st.session_state.get("selected_disease")
    default_idx = 0
    if preselect:
        for i, (label, did) in enumerate(options.items()):
            if did == preselect:
                default_idx = i
                break
    selected = st.selectbox("Select Disease", list(options.keys()), index=default_idx)
    did = options[selected]
    st.session_state["selected_disease"] = did
    return did


def render():
    st.title("Prediction Results")

    did = _disease_selector()
    _, disease_names = get_disease_associations()
    name = disease_names[did]

    # ── Run live predictions ─────────────────────────────────────────────
    with st.spinner(f"Running 5 prediction methods for {name}…"):
        pred_df = predict_for_disease(did)

    if pred_df.empty:
        st.warning("No predictions could be generated for this disease.")
        return

    st.markdown(f"**{name}** — {len(pred_df):,} candidate proteins ranked by combined score")

    # ── Ranked prediction table ──────────────────────────────────────────
    st.subheader("Ranked Candidate Proteins")
    render_prediction_table(pred_df, name)

    st.divider()

    # ── Method score distribution for top candidates ─────────────────────
    st.subheader("Method Score Distribution (Top 50)")
    top50 = pred_df.head(50)
    import plotly.express as px
    melted = top50[["Gene ID"] + METHOD_ORDER].melt(
        id_vars="Gene ID", var_name="Method", value_name="Score"
    )
    fig = px.box(melted, x="Method", y="Score", color="Method",
                 color_discrete_map=METHOD_COLORS)
    fig.update_layout(showlegend=False, height=350,
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── Explain prediction for a selected protein ────────────────────────
    st.subheader("Explain Prediction")
    st.markdown("Select a predicted protein to view the evidence contributing "
                "to its prioritization.")

    top_genes = pred_df.head(100)["Gene ID"].tolist()
    selected_gene = st.selectbox(
        "Select a predicted protein",
        top_genes,
        format_func=lambda g: f"Gene {g} (Rank {pred_df[pred_df['Gene ID'] == g].index[0]})"
    )

    if selected_gene:
        row = pred_df[pred_df["Gene ID"] == selected_gene].iloc[0]

        col_left, col_right = st.columns([2, 3])

        with col_left:
            st.markdown("##### Prediction Evidence")
            st.markdown(f"**Gene ID:** {selected_gene}")
            st.markdown(f"**Rank:** {row.name}")
            st.markdown(f"**Combined Score:** {row['Combined Score']:.4f}")
            st.divider()

            st.markdown("**Per-method scores:**")
            for method in METHOD_ORDER:
                val = row.get(method, 0)
                st.markdown(f"- {method}: `{val:.4f}`")

            stats = get_protein_network_stats(int(selected_gene))
            if stats:
                st.divider()
                st.markdown("**Network properties:**")
                st.markdown(f"- Degree in PPI: `{stats['Degree']}`")
                st.markdown(f"- Clustering coefficient: `{stats['Clustering Coefficient']:.4f}`")
                st.markdown(f"- Triangles: `{stats['Triangles']}`")

        with col_right:
            st.markdown("##### Method Score Profile")
            scores_dict = {m: float(row.get(m, 0)) for m in METHOD_ORDER}
            fig = protein_score_radar(scores_dict, title=f"Gene {selected_gene}")
            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "These scores represent each method's assessment of how likely this protein "
            "is to be associated with the disease, based on its position in the PPI network "
            "relative to known disease proteins. They are supporting evidence features, "
            "not causal explanations."
        )
