#!/usr/bin/env python3
"""Export validated research outputs to compact JSON for the static website.

Uses the existing FastAPI store, pathway builder, and predict_for_disease
engine. Does not reimplement scoring, metrics, or graphlet definitions.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.services import (  # noqa: E402
    disease_story,
    get_disease,
    get_metrics,
    list_diseases,
)
from app.services.models import models_payload  # noqa: E402
from app.services.network import disease_network  # noqa: E402
from app.services.protein import disease_graphlets  # noqa: E402
from app.services.rankings import get_predictions  # noqa: E402
from app.store import store  # noqa: E402


OUT = ROOT / "frontend" / "public" / "generated"


def log(msg: str) -> None:
    print(msg, flush=True)


def _sanitize(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(_sanitize(payload), ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    tmp.replace(path)


def valid_json(path: Path, required: tuple[str, ...]) -> bool:
    if not path.exists() or path.stat().st_size < 2:
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and all(key in data for key in required)


def export_catalog() -> None:
    store.load()
    listing = list_diseases(limit=519)
    details = []
    metrics_map = {}
    orbits_map = {}
    stories_map = {}
    proteins: dict[str, dict] = {}
    G = store.require_graph()

    for item in listing.diseases:
        did = item.id
        detail = get_disease(did)
        details.append(detail.model_dump())
        metrics_map[did] = {
            "disease_id": did,
            "metrics": [m.model_dump() for m in get_metrics(did)],
        }
        orbits_map[did] = disease_graphlets(did).model_dump()
        stories_map[did] = disease_story(did).model_dump()
        for gid in detail.associated_protein_ids:
            rec = proteins.setdefault(
                gid,
                {
                    "id": gid,
                    "label": f"Gene {gid}",
                    "in_ppi": int(gid) in G,
                    "degree": int(G.degree(int(gid))) if int(gid) in G else 0,
                    "disease_ids": [],
                    "graphlet_note": (
                        "Per-protein 73-orbit ORCA signatures are not computed in this project. "
                        "Disease-level 73-orbit p-values are available for associated diseases. "
                        "Per-protein structure uses the 12-dimensional motif-signature proxy "
                        "from motif_analysis.py, which is computed by the live FastAPI backend."
                    ),
                },
            )
            rec["disease_ids"].append(did)

    for rec in proteins.values():
        rec["n_associated_diseases"] = len(rec["disease_ids"])

    write_json(
        OUT / "diseases.json",
        {
            "count": len(details),
            "disclaimer": details[0]["disclaimer"] if details else "",
            "diseases": details,
        },
    )
    write_json(OUT / "metrics.json", metrics_map)
    write_json(OUT / "orbits.json", orbits_map)
    write_json(OUT / "stories.json", stories_map)
    write_json(OUT / "models.json", models_payload().model_dump())
    write_json(OUT / "proteins.json", {"count": len(proteins), "proteins": proteins})
    log(f"Catalog: {len(details)} diseases, {len(proteins)} associated proteins")


def export_pathways(force: bool = False) -> None:
    store.load()
    ids = sorted(store.disease_names)
    net_dir = OUT / "networks"
    net_dir.mkdir(parents=True, exist_ok=True)
    for i, did in enumerate(ids, 1):
        path = net_dir / f"{did}.json"
        if not force and valid_json(path, ("nodes", "edges")):
            log(f"[{i}/{len(ids)}] {did} pathway exists, skip")
            continue
        graph = disease_network(did, include_predicted=False, top_k=15, hops=0)
        write_json(path, graph.model_dump())
        log(
            f"[{i}/{len(ids)}] {store.disease_names[did]} pathway "
            f"({graph.n_associated} nodes, {len(graph.edges)} edges)"
        )


def _prediction_payload(did: str) -> dict:
    payload = get_predictions(did, top_k=100).model_dump()
    G = store.require_graph()
    _, Vd = store.pathway(did)
    seeds = set(Vd)
    for item in payload["predictions"]:
        gid = int(item["protein_id"])
        neighbors = []
        if gid in G:
            neighbors = [str(n) for n in G.neighbors(gid) if n in seeds]
        item["pathway_neighbors"] = neighbors
        item["degree"] = int(G.degree(gid)) if gid in G else 0
    return payload


def _enrich_proteins_from_predictions() -> None:
    proteins_path = OUT / "proteins.json"
    if not proteins_path.exists():
        return
    data = json.loads(proteins_path.read_text(encoding="utf-8"))
    proteins = data.get("proteins") or {}
    G = store.require_graph()
    pred_dir = OUT / "predictions"
    if not pred_dir.exists():
        return
    added = 0
    for pred_file in sorted(pred_dir.glob("*.json")):
        try:
            payload = json.loads(pred_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        did = str(payload.get("disease_id") or pred_file.stem)
        for row in payload.get("predictions") or []:
            pid = str(row.get("protein_id") or "")
            if not pid or pid in proteins:
                continue
            gid = int(pid)
            proteins[pid] = {
                "id": pid,
                "label": f"Gene {pid}",
                "in_ppi": gid in G,
                "degree": int(row.get("degree") or (G.degree(gid) if gid in G else 0)),
                "disease_ids": [],
                "n_associated_diseases": 0,
                "graphlet_note": (
                    "This protein appears as a computational candidate in static prediction "
                    "export. It has no known disease association in this dataset. "
                    "Per-protein 73-orbit ORCA signatures are not computed in this project."
                ),
            }
            added += 1
    data["proteins"] = proteins
    data["count"] = len(proteins)
    write_json(proteins_path, data)
    if added:
        log(f"Proteins index: added {added} candidate-only proteins from predictions")


def export_predictions(force: bool = False) -> tuple[int, int, list[str]]:
    store.load()
    ids = sorted(store.disease_names)
    pred_dir = OUT / "predictions"
    pred_dir.mkdir(parents=True, exist_ok=True)
    ok = skipped = 0
    failures: list[str] = []
    t0 = time.time()
    log("Preparing prediction engine (one-time)…")
    store.get_engine()
    log(f"Engine ready in {time.time() - t0:.1f}s")

    for i, did in enumerate(ids, 1):
        name = store.disease_names[did]
        path = pred_dir / f"{did}.json"
        if not force and valid_json(path, ("disease_id", "predictions")):
            log(f"[{i}/{len(ids)}] {name} predictions exist, skip")
            skipped += 1
            continue
        try:
            payload = _prediction_payload(did)
            write_json(path, payload)
            ok += 1
            log(
                f"[{i}/{len(ids)}] {name}  top-{payload['top_k']}  "
                f"candidates={payload['n_candidates']}"
            )
        except Exception as exc:
            failures.append(f"{did} ({name}): {exc}")
            log(f"[{i}/{len(ids)}] FAILED {did} {name}: {exc}")
            traceback.print_exc()
    _enrich_proteins_from_predictions()
    return ok, skipped, failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Export static JSON from the validated pipeline")
    parser.add_argument("--pathways-only", action="store_true")
    parser.add_argument("--predictions-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite existing JSON files")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    failures: list[str] = []

    if not args.predictions_only:
        log("=== Catalog, metrics, orbits, models ===")
        export_catalog()
        log("=== Pathway networks ===")
        export_pathways(force=args.force)

    if not args.pathways_only:
        log("=== Top-100 predictions (existing engine) ===")
        ok, skipped, failures = export_predictions(force=args.force)
        log(f"Predictions written={ok} skipped={skipped} failed={len(failures)}")
        if failures:
            log("Failure summary:")
            for line in failures:
                log(f"  {line}")

    log(f"Done in {time.time() - t0:.1f}s → {OUT}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
