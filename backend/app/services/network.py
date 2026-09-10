"""Disease and protein network subsets from the real PPI graph."""

from __future__ import annotations

from typing import Optional

import networkx as nx

from ..schemas import NetworkEdge, NetworkGraph, NetworkNode
from ..store import store
from .prediction import predict_for_disease


def _node_type(nid: int, associated: set[int], predicted: dict[int, float]) -> str:
    if nid in associated:
        return "associated"
    if nid in predicted:
        return "predicted"
    return "other"


def _serialize(
    display: nx.Graph,
    associated: set[int],
    predicted: dict[int, float],
    *,
    disease_id: Optional[str] = None,
    protein_id: Optional[str] = None,
    hops: int = 0,
    truncated: bool = False,
    truncation_note: Optional[str] = None,
) -> NetworkGraph:
    comp_map = {}
    if display.number_of_nodes():
        for ci, comp in enumerate(nx.connected_components(display)):
            for n in comp:
                comp_map[n] = ci

    nodes = []
    n_associated = n_predicted = n_other = 0
    for n in display.nodes():
        ntype = _node_type(int(n), associated, predicted)
        if ntype == "associated":
            n_associated += 1
        elif ntype == "predicted":
            n_predicted += 1
        else:
            n_other += 1
        score = predicted.get(int(n))
        nodes.append(
            NetworkNode(
                id=str(n),
                label=str(n),
                type=ntype,
                score=None if score is None else float(score),
                degree=int(display.degree(n)),
                component=comp_map.get(n),
            )
        )
    edges = [
        NetworkEdge(source=str(u), target=str(v))
        for u, v in display.edges()
        if u != v
    ]
    return NetworkGraph(
        disease_id=disease_id,
        protein_id=protein_id,
        hops=hops,
        truncated=truncated,
        truncation_note=truncation_note,
        nodes=nodes,
        edges=edges,
        n_associated=n_associated,
        n_predicted=n_predicted,
        n_other=n_other,
    )


def disease_network(
    disease_id: str,
    *,
    include_predicted: bool = False,
    top_k: int = 15,
    hops: int = 0,
    max_extra_nodes: int = 200,
) -> NetworkGraph:
    G = store.require_graph()
    Hd, Vd = store.pathway(disease_id)
    associated = set(int(n) for n in Vd)
    predicted: dict[int, float] = {}
    display = Hd.copy()
    truncated = False
    note = None

    if include_predicted and top_k > 0:
        pred_df = predict_for_disease(disease_id)
        if not pred_df.empty:
            for _, row in pred_df.head(int(top_k)).iterrows():
                gid = int(row["Gene ID"])
                if gid not in G:
                    continue
                if any(nbr in associated for nbr in G.neighbors(gid)):
                    predicted[gid] = float(row["Combined Score"])
                    if gid not in display:
                        display.add_node(gid)

    if hops >= 1:
        extras: list[tuple[int, int]] = []
        for seed in list(display.nodes()):
            if seed not in G:
                continue
            for nbr in G.neighbors(seed):
                if nbr in display:
                    continue
                extras.append((int(G.degree(nbr)), int(nbr)))
        extras.sort(reverse=True)
        cap = max(0, int(max_extra_nodes))
        chosen = extras[:cap]
        if len(extras) > cap:
            truncated = True
            note = (
                f"1-hop expansion limited to {cap} additional proteins "
                f"(highest degree first). {len(extras) - cap} neighbors omitted."
            )
        for _, nbr in chosen:
            display.add_node(nbr)

    all_nodes = set(display.nodes())
    for n in list(all_nodes):
        if n not in G:
            continue
        for nbr in G.neighbors(n):
            if nbr in all_nodes and not display.has_edge(n, nbr):
                display.add_edge(n, nbr)

    if hops >= 2:
        truncated = True
        extra = (
            "Full 2-hop expansion of a disease pathway can exceed tens of thousands "
            "of nodes. This API returns 1-hop with a cap instead of rendering the "
            "entire interactome."
        )
        note = f"{note} {extra}".strip() if note else extra

    return _serialize(
        display,
        associated,
        predicted,
        disease_id=disease_id,
        hops=min(hops, 1) if hops < 2 else 1,
        truncated=truncated,
        truncation_note=note,
    )


def protein_network(gene_id: int, hops: int = 1, limit: int = 80) -> NetworkGraph:
    G = store.require_graph()
    if gene_id not in G:
        raise KeyError(gene_id)

    associated_all = set()
    for genes in store.disease_genes.values():
        if gene_id in genes:
            associated_all.update(genes)

    nodes = {gene_id}
    truncated = False
    note = None
    if hops >= 1:
        neighbors = list(G.neighbors(gene_id))
        if hops >= 2:
            extra = []
            for nbr in neighbors:
                extra.extend(G.neighbors(nbr))
            neighbors = list(dict.fromkeys(neighbors + extra))
        if len(neighbors) > limit:
            truncated = True
            note = f"Neighborhood limited to {limit} of {len(neighbors)} proteins."
            neighbors = sorted(neighbors, key=lambda n: G.degree(n), reverse=True)[:limit]
        nodes.update(int(n) for n in neighbors)

    display = G.subgraph(nodes).copy()
    associated = {n for n in display.nodes() if n in associated_all and n != gene_id}
    # Center protein is highlighted as associated if it has any known disease link.
    if gene_id in store.protein_to_diseases:
        associated.add(gene_id)
    return _serialize(
        display,
        associated,
        {},
        protein_id=str(gene_id),
        hops=hops,
        truncated=truncated,
        truncation_note=note,
    )
