"""Interactive 2D and 3D Plotly network visualizations for disease pathways.

Uses actual PPI edges and prediction scores — no synthetic structures.
3D is the default exploratory view; 2D is the analytical/publication alternative.
User-selectable colors for known proteins, predicted proteins, edges, and background.
"""

import numpy as np
import networkx as nx
import plotly.graph_objects as go

_DEFAULT_COLORS = {
    "known": "#2196F3",
    "predicted": "#FF5722",
    "edge": "#969696",
    "bg": "#FAFAFC",
}


# ─────────────────────────────────────────────────────────────────────────
#  Shared helpers
# ─────────────────────────────────────────────────────────────────────────

def _merge_colors(colors):
    c = dict(_DEFAULT_COLORS)
    if colors:
        c.update(colors)
    return c


def _prepare_display_graph(Hd, known_genes, predicted_genes, G_full=None):
    display = Hd.copy()
    for g in predicted_genes:
        if g not in display:
            display.add_node(g)
    if G_full is not None:
        all_display_nodes = set(display.nodes())
        for g in predicted_genes:
            if g in G_full:
                for nbr in G_full.neighbors(g):
                    if nbr in all_display_nodes and not display.has_edge(g, nbr):
                        display.add_edge(g, nbr)
    return display


def _compute_component_map(Hd):
    comp_map = {}
    for ci, comp in enumerate(nx.connected_components(Hd)):
        for n in comp:
            comp_map[n] = ci
    return comp_map


def _node_hover(n, known_genes, predicted_genes, comp_map, display_graph):
    degree = display_graph.degree(n)
    if n in known_genes:
        comp_label = comp_map.get(n, "—")
        return (
            max(7, min(18, 5 + degree * 0.6)),
            f"<b>Gene {n}</b><br>"
            f"Status: Known disease protein<br>"
            f"Degree: {degree}<br>"
            f"Component: {comp_label}",
        )
    elif n in predicted_genes:
        score = predicted_genes[n]
        return (
            max(6, min(15, 4 + score * 25)),
            f"<b>Gene {n}</b><br>"
            f"Status: Predicted candidate<br>"
            f"Combined Score: {score:.4f}<br>"
            f"Degree: {degree}",
        )
    else:
        return (5, f"Gene {n}<br>Degree: {degree}")


# ─────────────────────────────────────────────────────────────────────────
#  3D Network
# ─────────────────────────────────────────────────────────────────────────

def build_3d_figure(Hd, known_genes=None, predicted_genes=None,
                    G_full=None, title="Disease Pathway (3D)", height=650,
                    colors=None):
    if Hd.number_of_nodes() == 0:
        return None

    c = _merge_colors(colors)
    known_genes = known_genes or set(Hd.nodes())
    predicted_genes = predicted_genes or {}

    display = _prepare_display_graph(Hd, known_genes, predicted_genes, G_full)
    comp_map = _compute_component_map(Hd)

    pos = nx.spring_layout(display, dim=3, seed=42,
                           k=3.0 / max(display.number_of_nodes() ** 0.33, 1),
                           iterations=60)

    edge_x, edge_y, edge_z = [], [], []
    for u, v in display.edges():
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
        edge_z += [z0, z1, None]

    edge_alpha = f"rgba({int(c['edge'][1:3],16)},{int(c['edge'][3:5],16)},{int(c['edge'][5:7],16)},0.3)"

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode="lines",
        line=dict(width=1.2, color=edge_alpha),
        hoverinfo="none",
    )

    kn_x, kn_y, kn_z, kn_size, kn_text = [], [], [], [], []
    pr_x, pr_y, pr_z, pr_size, pr_text, pr_score = [], [], [], [], [], []

    for n in display.nodes():
        x, y, z = pos[n]
        size, text = _node_hover(n, known_genes, predicted_genes, comp_map, display)

        if n in known_genes:
            kn_x.append(x); kn_y.append(y); kn_z.append(z)
            kn_size.append(size); kn_text.append(text)
        elif n in predicted_genes:
            pr_x.append(x); pr_y.append(y); pr_z.append(z)
            pr_size.append(size); pr_text.append(text)
            pr_score.append(predicted_genes[n])

    known_trace = go.Scatter3d(
        x=kn_x, y=kn_y, z=kn_z, mode="markers",
        name="Known disease proteins",
        marker=dict(size=kn_size, color=c["known"], opacity=0.9,
                    line=dict(width=0.5, color="white")),
        text=kn_text, hoverinfo="text",
    )

    traces = [edge_trace, known_trace]

    if pr_x:
        pred_trace = go.Scatter3d(
            x=pr_x, y=pr_y, z=pr_z, mode="markers",
            name="Predicted candidates",
            marker=dict(size=pr_size, color=pr_score, colorscale=[
                [0, "#FFCCBC"], [1, c["predicted"]]
            ], showscale=True,
                colorbar=dict(title="Score", len=0.5, x=1.02),
                opacity=0.9, symbol="diamond",
                line=dict(width=0.5, color="white")),
            text=pr_text, hoverinfo="text",
        )
        traces.append(pred_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title, height=height, showlegend=True,
        legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.7)"),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor=c["bg"],
        ),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────
#  2D Network
# ─────────────────────────────────────────────────────────────────────────

def build_2d_figure(Hd, known_genes=None, predicted_genes=None,
                    G_full=None, title="Disease Pathway (2D)", height=550,
                    colors=None):
    if Hd.number_of_nodes() == 0:
        return None

    c = _merge_colors(colors)
    known_genes = known_genes or set(Hd.nodes())
    predicted_genes = predicted_genes or {}

    display = _prepare_display_graph(Hd, known_genes, predicted_genes, G_full)
    comp_map = _compute_component_map(Hd)

    pos = nx.spring_layout(display, seed=42,
                           k=2.5 / max(display.number_of_nodes() ** 0.5, 1))

    edge_x, edge_y = [], []
    for u, v in display.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_alpha = f"rgba({int(c['edge'][1:3],16)},{int(c['edge'][3:5],16)},{int(c['edge'][5:7],16)},0.5)"

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=0.8, color=edge_alpha),
        hoverinfo="none", showlegend=False,
    )

    kn_x, kn_y, kn_size, kn_text = [], [], [], []
    pr_x, pr_y, pr_size, pr_text, pr_score = [], [], [], [], []

    for n in display.nodes():
        x, y = pos[n]
        size, text = _node_hover(n, known_genes, predicted_genes, comp_map, display)

        if n in known_genes:
            kn_x.append(x); kn_y.append(y)
            kn_size.append(size); kn_text.append(text)
        elif n in predicted_genes:
            pr_x.append(x); pr_y.append(y)
            pr_size.append(size); pr_text.append(text)
            pr_score.append(predicted_genes[n])

    known_trace = go.Scatter(
        x=kn_x, y=kn_y, mode="markers",
        name="Known disease proteins",
        marker=dict(size=kn_size, color=c["known"],
                    line=dict(width=0.5, color="white")),
        text=kn_text, hoverinfo="text",
    )

    traces = [edge_trace, known_trace]

    if pr_x:
        pred_trace = go.Scatter(
            x=pr_x, y=pr_y, mode="markers",
            name="Predicted candidates",
            marker=dict(size=pr_size, color=pr_score, colorscale=[
                [0, "#FFCCBC"], [1, c["predicted"]]
            ], showscale=True,
                colorbar=dict(title="Score", len=0.5),
                symbol="diamond",
                line=dict(width=0.5, color="white")),
            text=pr_text, hoverinfo="text",
        )
        traces.append(pred_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title, showlegend=True,
        legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0.7)"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=height, margin=dict(l=5, r=5, t=40, b=5),
        dragmode="pan", plot_bgcolor=c["bg"],
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────
#  Convenience dispatcher
# ─────────────────────────────────────────────────────────────────────────

def build_pathway_figure(Hd, known_genes=None, predicted_genes=None,
                         G_full=None, title="Disease Pathway", height=550,
                         mode="3d", colors=None):
    """Build either 2D or 3D figure. mode='3d' (default) or '2d'."""
    if mode == "3d":
        return build_3d_figure(Hd, known_genes, predicted_genes, G_full,
                               title=f"{title} (3D)", height=height, colors=colors)
    else:
        return build_2d_figure(Hd, known_genes, predicted_genes, G_full,
                               title=f"{title} (2D)", height=height, colors=colors)
