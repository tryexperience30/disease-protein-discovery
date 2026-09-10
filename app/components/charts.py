"""Reusable chart components for the application."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app.config import METHOD_ORDER, METHOD_COLORS, ORBIT_SIZE_LABEL


def method_bar_chart(pred_df_row, metric="Recall@100", height=350):
    """Bar chart comparing methods for a single disease."""
    methods = [m for m in METHOD_ORDER if m in pred_df_row.columns
               or m in pred_df_row.index]
    values = [float(pred_df_row.get(m, 0)) for m in methods]
    colors = [METHOD_COLORS.get(m, "#999") for m in methods]

    fig = go.Figure(go.Bar(
        x=methods, y=values,
        marker_color=colors,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis_title=metric, height=height,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def orbit_significance_bar(pvals, height=350):
    """Bar chart of -log10(p-value) for 73 orbits of a disease."""
    orbit_nums = list(range(len(pvals)))
    neg_log_p = -np.log10(np.maximum(pvals, 1e-10))
    colors = ["#C44E52" if p < 0.01 else "#cccccc" for p in pvals]

    fig = go.Figure(go.Bar(
        x=orbit_nums, y=neg_log_p,
        marker_color=colors,
        hovertext=[f"Orbit {i} ({ORBIT_SIZE_LABEL.get(i, '?')})<br>"
                   f"p = {pvals[i]:.4f}" for i in orbit_nums],
        hoverinfo="text",
    ))
    fig.add_hline(y=-np.log10(0.01), line_dash="dash", line_color="red",
                  annotation_text="p = 0.01")
    fig.update_layout(
        xaxis_title="Orbit Position",
        yaxis_title="-log\u2081\u2080(p-value)",
        height=height, margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def protein_score_radar(scores_dict, title="Method Scores"):
    """Radar chart of per-method scores for one protein."""
    methods = list(scores_dict.keys())
    values = list(scores_dict.values())
    values.append(values[0])
    methods.append(methods[0])

    fig = go.Figure(go.Scatterpolar(
        r=values, theta=methods, fill="toself",
        line_color="#4C72B0",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values) * 1.1 + 0.01])),
        title=title, height=350,
        margin=dict(l=40, r=40, t=50, b=20),
    )
    return fig


def histogram_with_marker(data, marker_value, xlabel, color="#4C72B0",
                           marker_label="This disease", height=300):
    """Histogram with a vertical line for the current disease's value."""
    fig = px.histogram(x=data, nbins=30, color_discrete_sequence=[color])
    if marker_value is not None and not np.isnan(marker_value):
        fig.add_vline(x=marker_value, line_dash="dash", line_color="red",
                      annotation_text=marker_label)
    fig.update_layout(
        xaxis_title=xlabel, yaxis_title="Diseases",
        height=height, margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig
