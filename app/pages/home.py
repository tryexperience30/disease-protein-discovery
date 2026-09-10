"""Home — landing page with disease search and pipeline overview."""

import streamlit as st
from app.cache import get_ppi_network, get_disease_associations, get_disease_list


def render():
    st.markdown(
        "<h1 style='text-align:center; margin-bottom:0; font-size:2.2rem'>"
        "Disease Protein Discovery Platform</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#666; font-size:1.05rem; "
        "margin-top:4px; margin-bottom:24px'>"
        "Explore disease-associated protein networks and computationally "
        "prioritize candidate disease proteins</p>",
        unsafe_allow_html=True,
    )

    # ── Disease Search (prominent) ───────────────────────────────────────
    st.markdown("### Search for a Disease")
    disease_list = get_disease_list()
    options = {f"{name} ({did})": did for did, name in disease_list}

    selected = st.selectbox(
        "Type a disease name to begin",
        [""] + list(options.keys()),
        index=0,
        placeholder="e.g. Alzheimer's Disease, Breast Cancer, Diabetes…",
        label_visibility="collapsed",
    )

    if selected and selected in options:
        did = options[selected]
        st.session_state["selected_disease"] = did

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Explore Disease", type="primary", use_container_width=True):
                st.session_state["nav"] = "Disease Explorer"
                st.rerun()
        with col_b:
            if st.button("Explore Proteins", use_container_width=True):
                st.session_state["nav"] = "Protein Explorer"
                st.rerun()

    st.divider()

    # ── Dataset stats ────────────────────────────────────────────────────
    G = get_ppi_network()
    disease_genes, _ = get_disease_associations()
    total_assoc = sum(len(v) for v in disease_genes.values())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proteins in PPI", f"{G.number_of_nodes():,}")
    c2.metric("PPI Interactions", f"{G.number_of_edges():,}")
    c3.metric("Diseases Analyzed", f"{len(disease_genes):,}")
    c4.metric("Gene-Disease Links", f"{total_assoc:,}")

    st.divider()

    # ── Pipeline ─────────────────────────────────────────────────────────
    st.markdown("### Computational Pipeline")

    steps = [
        ("PPI Network",
         "21,557 proteins connected by 342,353 experimentally validated interactions"),
        ("Disease Pathways",
         "Project disease proteins onto the PPI network to form pathway subgraphs"),
        ("Structural Analysis",
         "Measure connectivity, density, conductance, modularity, and fragmentation"),
        ("5 Prediction Methods",
         "Neighborhood, Random Walk, DIAMOnD, Neural Embeddings, Matrix Completion"),
        ("Graphlet Features",
         "73-dimensional higher-order structural signatures capture local topology"),
        ("Candidate Ranking",
         "Combined scoring prioritizes proteins as candidate disease associations"),
    ]

    cols = st.columns(len(steps))
    for col, (title, desc) in zip(cols, steps):
        with col:
            st.markdown(f"**{title}**")
            st.caption(desc)

    st.divider()

    # ── About ────────────────────────────────────────────────────────────
    with st.expander("About This Platform"):
        st.markdown("""
This platform implements the computational pipeline from:

> **Large-scale analysis of disease pathways in the human interactome**
> Agrawal, Zitnik & Leskovec — Pacific Symposium on Biocomputing, 2018

It enables interactive exploration of disease-specific protein interaction
networks, structural pathway properties, prediction results from five
network-based methods, and higher-order graphlet orbit analysis.

**Data source:** [SNAP Stanford — Disease Pathways](https://snap.stanford.edu/pathways/)
        """)

    st.caption(
        "**Research Disclaimer:** This platform provides computational prioritization "
        "of candidate disease-associated proteins. Predictions are intended for research "
        "purposes and should not be interpreted as clinical diagnoses or experimentally "
        "validated disease associations."
    )
