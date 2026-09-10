"""Metric display cards with optional tooltip explanations."""

import streamlit as st
from app.config import METRIC_DESCRIPTIONS


def metric_card(label, value, description_key=None):
    """Display a single metric with an optional info tooltip."""
    desc = METRIC_DESCRIPTIONS.get(description_key or label)
    if desc:
        st.metric(label, value, help=desc)
    else:
        st.metric(label, value)


def metric_table(metrics_dict, columns=3):
    """Display a grid of metrics from a dict {label: value}."""
    items = list(metrics_dict.items())
    for row_start in range(0, len(items), columns):
        cols = st.columns(columns)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx < len(items):
                label, value = items[idx]
                with col:
                    metric_card(label, value, description_key=label)
