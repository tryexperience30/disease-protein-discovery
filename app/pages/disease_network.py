"""Page 3: Interactive Disease Network — Physics / 3D / 2D visualization."""

import streamlit as st
import streamlit.components.v1 as components
import networkx as nx

from app.cache import (
    get_disease_list, get_disease_associations, get_disease_pathway, get_ppi_network,
)
from app.components.network_viz import build_pathway_figure
from app.components.physics_network import build_physics_html


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
    st.title("Interactive Disease Network")

    did = _disease_selector()
    disease_genes, disease_names = get_disease_associations()
    name = disease_names[did]

    Hd, Vd = get_disease_pathway(did)
    known_genes = set(Vd)

    st.markdown(f"**{name}** — {Hd.number_of_nodes()} proteins, "
                f"{Hd.number_of_edges()} interactions, "
                f"{nx.number_connected_components(Hd)} components")

    # ── Row 1: View mode + prediction controls ───────────────────────────
    r1c1, r1c2, r1c3 = st.columns([2, 1, 1])

    with r1c1:
        view_mode = st.radio(
            "View Mode",
            ["Physics (drag nodes)", "3D (rotate)", "2D (flat)"],
            horizontal=True, index=0,
            help="Physics = elastic drag-and-release; 3D = rotatable; 2D = publication-quality"
        )

    with r1c2:
        show_predicted = st.checkbox("Show predicted proteins", value=False)

    with r1c3:
        n_predicted = st.slider("Top K", 5, 50, 15, disabled=not show_predicted)

    # ── Row 2: Color pickers (always visible) ────────────────────────────
    st.markdown("**Customize Colors**")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        known_color = st.color_picker("Known proteins", "#2196F3")
    with cc2:
        predicted_color = st.color_picker("Predicted proteins", "#FF5722")
    with cc3:
        edge_color = st.color_picker("Edges", "#969696")
    with cc4:
        if view_mode.startswith("Physics"):
            bg_color = st.color_picker("Background", "#1a1a2e")
        else:
            bg_color = st.color_picker("Background", "#FAFAFC")

    colors = {
        "known": known_color,
        "predicted": predicted_color,
        "edge": edge_color,
        "bg": bg_color,
    }

    # ── Build predicted overlay ──────────────────────────────────────────
    predicted_genes = {}
    G_full = None

    if show_predicted:
        from app.utils.live_predict import predict_for_disease
        with st.spinner("Running predictions…"):
            pred_df = predict_for_disease(did)

        if not pred_df.empty:
            G_full = get_ppi_network()
            top_preds = pred_df.head(n_predicted)
            for _, row in top_preds.iterrows():
                gid = int(row["Gene ID"])
                if gid in G_full:
                    has_connection = any(
                        gid in set(G_full.neighbors(kg))
                        for kg in known_genes if kg in G_full
                    )
                    if has_connection:
                        predicted_genes[gid] = row["Combined Score"]

            if predicted_genes:
                st.caption(f"Showing {len(predicted_genes)} predicted proteins "
                           f"with direct PPI connections to the pathway")
            else:
                st.caption("Top predicted proteins don't directly connect "
                           "to the pathway — showing pathway only")

    # ── Render visualization ─────────────────────────────────────────────
    st.divider()

    if view_mode.startswith("Physics"):
        html = build_physics_html(
            Hd, known_genes=known_genes,
            predicted_genes=predicted_genes,
            G_full=G_full, colors=colors,
            height="650px",
        )
        components.html(html, height=680, scrolling=False)
        st.caption("Drag any node — it springs back. Scroll to zoom. "
                   "Double-click to focus. Navigation buttons at bottom-left.")

    elif view_mode.startswith("3D"):
        fig = build_pathway_figure(
            Hd, known_genes=known_genes,
            predicted_genes=predicted_genes,
            G_full=G_full, title=name,
            height=650, mode="3d", colors=colors,
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True,
                            config={"scrollZoom": True, "displayModeBar": True})
        else:
            st.warning("No disease proteins found in the PPI network.")

    else:
        fig = build_pathway_figure(
            Hd, known_genes=known_genes,
            predicted_genes=predicted_genes,
            G_full=G_full, title=name,
            height=550, mode="2d", colors=colors,
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True,
                            config={"scrollZoom": True, "displayModeBar": True,
                                    "modeBarButtonsToAdd": ["pan2d", "zoom2d"]})
        else:
            st.warning("No disease proteins found in the PPI network.")

    # ── Protein search ───────────────────────────────────────────────────
    st.divider()
    st.subheader("Search Protein in Pathway")
    gene_search = st.text_input("Enter Gene/Protein ID", placeholder="e.g. 7157")
    if gene_search:
        try:
            gid = int(gene_search.strip())
        except ValueError:
            st.error("Please enter a numeric Gene ID.")
            return

        if gid in Vd:
            degree = Hd.degree(gid)
            neighbors = list(Hd.neighbors(gid))
            st.success(f"Gene **{gid}** is a **known disease protein** in this pathway.")
            c1, c2 = st.columns(2)
            c1.metric("Degree in pathway", degree)
            c2.metric("Neighbors in pathway", len(neighbors))
            if neighbors:
                st.caption(f"Pathway neighbors: "
                           f"{', '.join(str(n) for n in neighbors[:20])}"
                           f"{'…' if len(neighbors) > 20 else ''}")
        elif gid in get_ppi_network():
            st.info(f"Gene **{gid}** exists in the PPI network but is **not** "
                    f"a known protein for {name}.")
        else:
            st.warning(f"Gene **{gid}** not found in the PPI network.")
