"""Disease Explorer — the primary page.

Tabs: Overview | Network | Predictions | Graphlet Orbits
All sections for the selected disease in one place.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import networkx as nx

from app.config import METHOD_ORDER, METHOD_COLORS, METRIC_DESCRIPTIONS
from app.cache import (
    get_disease_list, get_disease_associations, get_disease_classes,
    get_computed_metrics, get_pathway_features, get_disease_motifs,
    get_disease_pathway, get_ppi_network,
)
from app.components.metric_cards import metric_table
from app.components.charts import (
    histogram_with_marker, orbit_significance_bar, protein_score_radar,
)
from app.components.network_viz import build_pathway_figure
from app.components.physics_network import build_physics_html
from app.components.prediction_table import render_prediction_table


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
    selected = st.selectbox("Select Disease", list(options.keys()),
                            index=default_idx)
    did = options[selected]
    st.session_state["selected_disease"] = did
    return did


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 1: Overview
# ═══════════════════════════════════════════════════════════════════════════

def _render_overview(did, name, genes, category, Hd, Vd):
    metrics_df = get_computed_metrics()
    paper_df = get_pathway_features()

    # Header metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Disease ID", did)
    c2.metric("Category", category)
    c3.metric("Known Genes", len(genes))
    c4.metric("Genes in PPI", len(Vd))
    c5.metric("Components", nx.number_connected_components(Hd))

    st.divider()

    # Structural metrics
    st.markdown("#### Structural Metrics")

    if did in metrics_df.index:
        row = metrics_df.loc[did]
        metrics = {
            "Num Internal Edges": f"{int(row.get('Num Internal Edges', 0))}",
            "Size of largest pathway component": f"{row.get('Size of largest pathway component', 0):.3f}",
            "Density of pathway": f"{row.get('Density of pathway', 0):.4f}",
            "Conductance": f"{row.get('Conductance', 0):.3f}",
            "Network Modularity": f"{row.get('Network Modularity', 0):.2e}",
        }
        dist = row.get("Distance of Pathway Components")
        if pd.notna(dist):
            metrics["Distance of Pathway Components"] = f"{dist:.2f}"
        else:
            metrics["Distance of Pathway Components"] = "N/A"

        if did in paper_df.index:
            sp = paper_df.loc[did, "Spatial Network Association"]
            metrics["Spatial Network Association (p-value)"] = (
                f"{sp:.4f}" if pd.notna(sp) else "—"
            )

        metric_table(metrics, columns=4)

        # Context histograms
        st.markdown("#### This Disease vs All 519 Diseases")
        h1, h2, h3 = st.columns(3)
        with h1:
            val = row.get("Size of largest pathway component")
            fig = histogram_with_marker(
                metrics_df["Size of largest pathway component"].dropna(),
                val, "LCC Fraction", color="#4C72B0",
                marker_label=f"This disease: {val:.3f}"
            )
            st.plotly_chart(fig, use_container_width=True)
        with h2:
            val = row.get("Density of pathway")
            fig = histogram_with_marker(
                metrics_df["Density of pathway"].dropna(),
                val, "Pathway Density", color="#55A868",
                marker_label=f"This disease: {val:.4f}"
            )
            st.plotly_chart(fig, use_container_width=True)
        with h3:
            val = row.get("Conductance")
            fig = histogram_with_marker(
                metrics_df["Conductance"].dropna(),
                val, "Conductance", color="#8172B2",
                marker_label=f"This disease: {val:.3f}"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No pre-computed structural metrics for this disease.")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 2: Network
# ═══════════════════════════════════════════════════════════════════════════

def _render_network(did, name, Hd, Vd):
    known_genes = set(Vd)

    st.markdown(f"**{Hd.number_of_nodes()}** proteins · "
                f"**{Hd.number_of_edges()}** interactions · "
                f"**{nx.number_connected_components(Hd)}** components")

    r1, r2, r3 = st.columns([2, 1, 1])
    with r1:
        view_mode = st.radio(
            "View", ["Physics (drag nodes)", "3D (rotate)", "2D (flat)"],
            horizontal=True, index=0,
        )
    with r2:
        show_predicted = st.checkbox("Show predicted proteins", value=False)
    with r3:
        n_predicted = st.slider("Top K", 5, 50, 15, disabled=not show_predicted)

    with st.expander("Customize Colors", expanded=False):
        cc1, cc2, cc3, cc4 = st.columns(4)
        with cc1:
            known_color = st.color_picker("Known proteins", "#2196F3")
        with cc2:
            predicted_color = st.color_picker("Predicted proteins", "#FF5722")
        with cc3:
            edge_color = st.color_picker("Edges", "#969696")
        with cc4:
            bg_default = "#1a1a2e" if view_mode.startswith("Physics") else "#FAFAFC"
            bg_color = st.color_picker("Background", bg_default)

    colors = {"known": known_color, "predicted": predicted_color,
              "edge": edge_color, "bg": bg_color}

    predicted_genes = {}
    G_full = None
    if show_predicted:
        from app.utils.live_predict import predict_for_disease
        with st.spinner("Running 5 prediction methods…"):
            pred_df = predict_for_disease(did)
        if not pred_df.empty:
            G_full = get_ppi_network()
            for _, row in pred_df.head(n_predicted).iterrows():
                gid = int(row["Gene ID"])
                if gid in G_full:
                    if any(gid in set(G_full.neighbors(kg))
                           for kg in known_genes if kg in G_full):
                        predicted_genes[gid] = row["Combined Score"]
            if predicted_genes:
                st.caption(f"Showing {len(predicted_genes)} predicted proteins "
                           f"with direct PPI connections to the pathway")

    if view_mode.startswith("Physics"):
        html = build_physics_html(Hd, known_genes=known_genes,
                                   predicted_genes=predicted_genes,
                                   G_full=G_full, colors=colors, height="620px")
        components.html(html, height=650, scrolling=False)
        st.caption("Drag any node — it springs back. Scroll to zoom. "
                   "Double-click to focus.")
    elif view_mode.startswith("3D"):
        fig = build_pathway_figure(Hd, known_genes=known_genes,
                                    predicted_genes=predicted_genes,
                                    G_full=G_full, title=name,
                                    height=620, mode="3d", colors=colors)
        if fig:
            st.plotly_chart(fig, use_container_width=True,
                            config={"scrollZoom": True, "displayModeBar": True})
    else:
        fig = build_pathway_figure(Hd, known_genes=known_genes,
                                    predicted_genes=predicted_genes,
                                    G_full=G_full, title=name,
                                    height=520, mode="2d", colors=colors)
        if fig:
            st.plotly_chart(fig, use_container_width=True,
                            config={"scrollZoom": True, "displayModeBar": True})

    if Hd.number_of_nodes() == 0:
        st.warning("No disease proteins found in the PPI network.")

    # Protein search
    st.markdown("#### Search Protein in Pathway")
    gene_search = st.text_input("Gene ID", placeholder="e.g. 7157",
                                key="net_search")
    if gene_search:
        try:
            gid = int(gene_search.strip())
        except ValueError:
            st.error("Enter a numeric Gene ID.")
            return
        if gid in Vd:
            degree = Hd.degree(gid)
            nbrs = list(Hd.neighbors(gid))
            st.success(f"Gene **{gid}** — known disease protein. "
                       f"Degree: {degree}, Neighbors: {len(nbrs)}")
        elif gid in get_ppi_network():
            st.info(f"Gene **{gid}** exists in the PPI network but is not "
                    f"a known protein for {name}.")
        else:
            st.warning(f"Gene **{gid}** not found in the PPI network.")


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 3: Predictions
# ═══════════════════════════════════════════════════════════════════════════

def _render_predictions(did, name):
    from app.utils.live_predict import predict_for_disease, get_protein_network_stats
    import plotly.express as px

    with st.spinner(f"Running 5 prediction methods for {name}…"):
        pred_df = predict_for_disease(did)

    if pred_df.empty:
        st.warning("No predictions could be generated for this disease.")
        return

    st.markdown(f"**{len(pred_df):,}** candidate proteins ranked by combined score")

    render_prediction_table(pred_df, name)

    st.divider()

    # Score distribution
    st.markdown("#### Method Score Distribution (Top 50)")
    top50 = pred_df.head(50)
    melted = top50[["Gene ID"] + METHOD_ORDER].melt(
        id_vars="Gene ID", var_name="Method", value_name="Score"
    )
    fig = px.box(melted, x="Method", y="Score", color="Method",
                 color_discrete_map=METHOD_COLORS)
    fig.update_layout(showlegend=False, height=320,
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Prediction evidence
    st.markdown("#### Prediction Evidence")
    st.caption("Select a candidate protein to view model inputs and "
               "supporting network evidence.")

    top_genes = pred_df.head(100)["Gene ID"].tolist()
    selected_gene = st.selectbox(
        "Select protein", top_genes,
        format_func=lambda g: f"Gene {g} — Rank {pred_df[pred_df['Gene ID']==g].index[0]}, "
                              f"Score {pred_df[pred_df['Gene ID']==g]['Combined Score'].values[0]:.4f}",
        key="pred_explain",
    )

    if selected_gene:
        row = pred_df[pred_df["Gene ID"] == selected_gene].iloc[0]
        col_l, col_r = st.columns([2, 3])

        with col_l:
            st.markdown(f"**Gene ID:** {selected_gene}")
            st.markdown(f"**Rank:** {row.name}")
            st.markdown(f"**Combined Score:** {row['Combined Score']:.4f}")
            st.divider()
            for method in METHOD_ORDER:
                val = row.get(method, 0)
                st.markdown(f"- {method}: `{val:.4f}`")
            stats = get_protein_network_stats(int(selected_gene))
            if stats:
                st.divider()
                st.markdown(f"- Degree: `{stats['Degree']}`")
                st.markdown(f"- Clustering: `{stats['Clustering Coefficient']:.4f}`")
                st.markdown(f"- Triangles: `{stats['Triangles']}`")

        with col_r:
            scores_dict = {m: float(row.get(m, 0)) for m in METHOD_ORDER}
            fig = protein_score_radar(scores_dict, title=f"Gene {selected_gene}")
            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Scores represent each method's assessment based on network position "
            "relative to known disease proteins. These are model input features, "
            "not causal explanations."
        )


# ═══════════════════════════════════════════════════════════════════════════
#  TAB 4: Graphlet Orbits
# ═══════════════════════════════════════════════════════════════════════════

def _render_orbits(did, name):
    motifs_df = get_disease_motifs()
    if did not in motifs_df.index:
        st.info("No motif data available for this disease.")
        return

    orbit_cols = [c for c in motifs_df.columns if c.startswith("orbit_")]
    pvals = motifs_df.loc[did, orbit_cols].values.astype(float)
    n_sig = int((pvals < 0.01).sum())

    st.markdown(f"**{n_sig}** of 73 orbits significantly over-represented (p < 0.01)")

    fig = orbit_significance_bar(pvals, height=380)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Graphlet orbit signatures describe the local structural patterns "
        "surrounding disease proteins. Orbits 0-3 correspond to 2-3 node "
        "graphlets, 4-14 to 4-node graphlets, and 15-72 to 5-node graphlets. "
        "Red bars indicate statistically significant over-representation "
        "(p < 0.01 vs random protein sets of equal size)."
    )

    # Orbit detail table
    with st.expander("Orbit p-value details"):
        orbit_data = pd.DataFrame({
            "Orbit": range(73),
            "p-value": pvals,
            "Significant": ["Yes" if p < 0.01 else "No" for p in pvals],
        })
        st.dataframe(orbit_data, hide_index=True, use_container_width=True,
                     height=300)


# ═══════════════════════════════════════════════════════════════════════════
#  Main render
# ═══════════════════════════════════════════════════════════════════════════

def render():
    st.title("Disease Explorer")

    did = _disease_selector()

    disease_genes, disease_names = get_disease_associations()
    disease_classes = get_disease_classes()

    name = disease_names[did]
    genes = disease_genes[did]
    category = disease_classes.get(did, "Not classified")

    Hd, Vd = get_disease_pathway(did)

    # ── Tabs ─────────────────────────────────────────────────────────────
    tab_overview, tab_network, tab_predictions, tab_orbits = st.tabs([
        "Overview", "Disease Network", "Predictions", "Graphlet Orbits"
    ])

    with tab_overview:
        _render_overview(did, name, genes, category, Hd, Vd)

    with tab_network:
        _render_network(did, name, Hd, Vd)

    with tab_predictions:
        _render_predictions(did, name)

    with tab_orbits:
        _render_orbits(did, name)
