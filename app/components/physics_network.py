"""Physics-based interactive network using pyvis / vis.js.

Nodes can be grabbed, dragged, and released — they spring back
into place via force-directed simulation (elastic behavior).
"""

import tempfile
import networkx as nx
from pyvis.network import Network


def build_physics_html(Hd, known_genes=None, predicted_genes=None,
                       G_full=None, colors=None, height="650px"):
    """Build an interactive HTML string with elastic physics network.

    Returns an HTML string that can be embedded via st.components.v1.html.
    """
    known_genes = known_genes or set(Hd.nodes())
    predicted_genes = predicted_genes or {}

    kc = (colors or {}).get("known", "#2196F3")
    pc = (colors or {}).get("predicted", "#FF5722")
    ec = (colors or {}).get("edge", "#969696")
    bg = (colors or {}).get("bg", "#1a1a2e")

    net = Network(height=height, width="100%", bgcolor=bg,
                  font_color="white", directed=False)

    net.barnes_hut(
        gravity=-3000,
        central_gravity=0.3,
        spring_length=120,
        spring_strength=0.04,
        damping=0.09,
    )

    for n in Hd.nodes():
        degree = Hd.degree(n)
        size = max(8, min(30, 6 + degree * 1.5))
        net.add_node(
            n,
            label=str(n),
            title=f"Gene {n} (Known)\nDegree: {degree}",
            color=kc,
            size=size,
            shape="dot",
            font={"size": 8, "color": "white"},
        )

    if G_full is not None:
        all_pathway_nodes = set(Hd.nodes())
        for g, score in predicted_genes.items():
            if g in G_full:
                has_conn = any(g in set(G_full.neighbors(k))
                              for k in all_pathway_nodes if k in G_full)
                if has_conn:
                    degree = G_full.degree(g)
                    size = max(6, min(25, 5 + score * 30))
                    net.add_node(
                        g,
                        label=str(g),
                        title=f"Gene {g} (Predicted)\nScore: {score:.4f}\nDegree: {degree}",
                        color=pc,
                        size=size,
                        shape="diamond",
                        font={"size": 8, "color": "white"},
                    )

    current_nodes = set(net.get_nodes())

    for u, v in Hd.edges():
        if u in current_nodes and v in current_nodes:
            net.add_edge(u, v, color=ec, width=1)

    if G_full is not None:
        for g in predicted_genes:
            if g in current_nodes and g in G_full:
                for nbr in G_full.neighbors(g):
                    if nbr in current_nodes:
                        try:
                            net.add_edge(g, nbr, color=pc, width=0.8, dashes=True)
                        except Exception:
                            pass

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "navigationButtons": true
      },
      "physics": {
        "enabled": true,
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.09
        },
        "stabilization": {
          "enabled": true,
          "iterations": 150,
          "fit": true
        }
      }
    }
    """)

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w")
    net.save_graph(tmp.name)
    tmp.close()

    with open(tmp.name, "r") as f:
        html = f.read()

    return html
