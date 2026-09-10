"""Live prediction endpoint uses the existing research engine."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_predictions_top_k_schema():
    r = client.get("/api/diseases/C0002395/predictions?top_k=5")
    assert r.status_code == 200
    body = r.json()
    assert body["disease_id"] == "C0002395"
    assert len(body["predictions"]) == 5
    row = body["predictions"][0]
    assert {"rank", "protein_id", "combined_score", "neighborhood", "random_walk", "diamond", "neural_embeddings", "matrix_completion"} <= set(row)
    assert row["rank"] == 1
