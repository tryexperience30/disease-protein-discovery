"""API-level journey covering the product path without fabricating results."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_end_to_end_disease_protein_path():
    search = client.get("/api/search?q=Alzheimer")
    assert search.status_code == 200
    hit = next(h for h in search.json()["results"] if h["type"] == "disease")
    did = hit["id"]

    disease = client.get(f"/api/diseases/{did}")
    assert disease.status_code == 200
    assert disease.json()["n_network_nodes"] > 0

    metrics = client.get(f"/api/diseases/{did}/metrics")
    assert metrics.status_code == 200
    assert len(metrics.json()["metrics"]) == 6

    network = client.get(f"/api/diseases/{did}/network")
    assert network.status_code == 200
    node_id = network.json()["nodes"][0]["id"]

    protein = client.get(f"/api/proteins/{node_id}")
    assert protein.status_code == 200
    diseases = client.get(f"/api/proteins/{node_id}/diseases")
    assert diseases.status_code == 200
    ids = [d["disease_id"] for d in diseases.json()["diseases"]]
    assert did in ids
