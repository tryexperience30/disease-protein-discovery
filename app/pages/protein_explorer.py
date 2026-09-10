"""Protein Explorer — search and inspect individual proteins."""

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx

from app.cache import (
    get_ppi_network, get_disease_associations, get_disease_classes,
    get_disease_motifs,
)
from app.utils.live_predict import get_protein_network_stats
from app.components.charts import orbit_significance_bar


def render():
    st.title("Protein Explorer")
    st.markdown("Search for a protein to view its network properties, "
                "disease associations, and graphlet features.")

    gene_input = st.text_input(
        "Enter Entrez Gene ID",
        placeholder="e.g. 7157 (TP53), 672 (BRCA1), 4790 (NFKB1)",
    )

    if not gene_input:
        st.info("Enter a numeric Entrez Gene ID above to explore a protein.")
        return

    try:
        gene_id = int(gene_input.strip())
    except ValueError:
        st.error("Please enter a valid numeric Gene ID.")
        return

    G = get_ppi_network()
    if gene_id not in G:
        st.error(
            f"Gene **{gene_id}** not found in the PPI network "
            f"({G.number_of_nodes():,} proteins). "
            f"Check the ID or try another gene."
        )
        return

    disease_genes, disease_names = get_disease_associations()
    disease_classes = get_disease_classes()

    # ── Network stats ────────────────────────────────────────────────────
    st.markdown(f"### Gene {gene_id}")
    stats = get_protein_network_stats(gene_id)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Degree", stats["Degree"],
              help="Number of direct PPI interactions")
    c2.metric("Clustering", f"{stats['Clustering Coefficient']:.4f}",
              help="Fraction of neighbor pairs that are also connected")
    c3.metric("Triangles", stats["Triangles"],
              help="Number of closed triangles involving this protein")
    c4.metric("PPI Network", "Present",
              help="This protein is in the largest connected component")

    st.divider()

    # ── Known disease associations ───────────────────────────────────────
    st.markdown("#### Known Disease Associations")

    associated_diseases = []
    for did, genes in disease_genes.items():
        if gene_id in genes:
            associated_diseases.append({
                "Disease ID": did,
                "Disease Name": disease_names[did],
                "Category": disease_classes.get(did, "—"),
                "Pathway Size": len(genes),
            })

    if associated_diseases:
        st.markdown(f"This protein is associated with **{len(associated_diseases)}** "
                    f"diseases in the dataset:")
        st.dataframe(
            pd.DataFrame(associated_diseases),
            hide_index=True, use_container_width=True,
            height=min(35 * len(associated_diseases) + 38, 400),
        )
    else:
        st.info(
            "This protein has no known disease associations in the dataset. "
            "It may still appear as a predicted candidate for diseases."
        )

    st.divider()

    # ── Graphlet orbit profile ───────────────────────────────────────────
    st.markdown("#### Graphlet Orbit Context")

    motifs_df = get_disease_motifs()

    if associated_diseases:
        st.caption(
            "Graphlet orbit significance for diseases this protein is "
            "associated with. Select a disease to view its 73-orbit profile."
        )
        orbit_cols = [c for c in motifs_df.columns if c.startswith("orbit_")]

        sel_disease = st.selectbox(
            "Select disease for orbit profile",
            [d["Disease ID"] for d in associated_diseases],
            format_func=lambda did: disease_names[did],
        )

        if sel_disease in motifs_df.index:
            pvals = motifs_df.loc[sel_disease, orbit_cols].values.astype(float)
            n_sig = int((pvals < 0.01).sum())
            st.markdown(f"**{n_sig}** of 73 orbits significant (p < 0.01) "
                        f"for {disease_names[sel_disease]}")
            fig = orbit_significance_bar(pvals)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No motif data available for this disease.")
    else:
        st.info("No disease associations — cannot show orbit profiles.")

    st.divider()

    # ── PPI Neighbors ────────────────────────────────────────────────────
    st.markdown("#### PPI Neighborhood")

    neighbors = list(G.neighbors(gene_id))
    if neighbors:
        st.markdown(f"**{len(neighbors)}** direct PPI neighbors")

        nbr_data = []
        for nbr in neighbors[:100]:
            diseases_for_nbr = [disease_names[did]
                                for did, gs in disease_genes.items() if nbr in gs]
            nbr_data.append({
                "Gene ID": nbr,
                "Degree": G.degree(nbr),
                "Disease Associations": len(diseases_for_nbr),
                "Example Diseases": (", ".join(diseases_for_nbr[:3])
                                     if diseases_for_nbr else "—"),
            })

        st.dataframe(
            pd.DataFrame(nbr_data), hide_index=True,
            use_container_width=True, height=400,
        )
        if len(neighbors) > 100:
            st.caption(f"Showing 100 of {len(neighbors)} neighbors.")
    else:
        st.info("This protein has no neighbors in the PPI network.")
