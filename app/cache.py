"""Centralized cached data loading.

Wraps existing load_data.py and pre-computed result CSVs behind Streamlit
caching decorators so every page shares the same in-memory copies.
All raw data is loaded read-only.
"""

import sys
import os
import numpy as np
import pandas as pd
import networkx as nx
import streamlit as st

from app.config import PROJECT_ROOT, DATA_DIR, RESULTS_DIR

sys.path.insert(0, PROJECT_ROOT)
from load_data import (
    load_ppi_network      as _load_ppi,
    load_disease_associations as _load_assoc,
    load_disease_classes   as _load_classes,
    load_pathway_features  as _load_features,
    load_disease_motifs    as _load_motifs,
)
from build_pathways import build_disease_pathway as _build_pathway


# ── PPI Network (cached as resource — mutable graph) ────────────────────

@st.cache_resource(show_spinner="Loading PPI network…")
def get_ppi_network():
    G = _load_ppi()
    largest_cc = max(nx.connected_components(G), key=len)
    return G.subgraph(largest_cc).copy()


# ── Disease associations & names ────────────────────────────────────────

@st.cache_data(show_spinner="Loading disease associations…")
def get_disease_associations():
    genes, names = _load_assoc()
    return genes, names


@st.cache_data(show_spinner=False)
def get_disease_names_dict():
    _, names = get_disease_associations()
    return names


@st.cache_data(show_spinner=False)
def get_disease_list():
    _, names = get_disease_associations()
    return sorted(names.items(), key=lambda x: x[1])


# ── Disease classes ─────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_disease_classes():
    return _load_classes()


# ── Paper pathway features ──────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_pathway_features():
    return _load_features()


# ── Motif p-values ──────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def get_disease_motifs():
    return _load_motifs()


# ── Pre-computed result CSVs ────────────────────────────────────────────

@st.cache_data(show_spinner="Loading computed metrics…")
def get_computed_metrics():
    path = os.path.join(RESULTS_DIR, "computed_pathway_metrics.csv")
    return pd.read_csv(path, index_col="Disease ID")


@st.cache_data(show_spinner="Loading prediction results…")
def get_prediction_results():
    return pd.read_csv(os.path.join(RESULTS_DIR, "prediction_results.csv"))


@st.cache_data(show_spinner="Loading augmented results…")
def get_augmented_results():
    return pd.read_csv(os.path.join(RESULTS_DIR, "augmented_results.csv"))


# ── Derived: build pathway for a single disease ────────────────────────

def get_disease_pathway(disease_id):
    G = get_ppi_network()
    genes, _ = get_disease_associations()
    return _build_pathway(G, genes[disease_id])
