from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_liveness_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["n_diseases"] == 519
    assert body["n_ppi_nodes"] > 20000


def test_list_diseases():
    r = client.get("/api/diseases?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 5
    assert "id" in body["diseases"][0]


def test_search_alzheimer():
    r = client.get("/api/search?q=Alzheimer")
    assert r.status_code == 200
    labels = [h["label"] for h in r.json()["results"]]
    assert any("Alzheimer" in label for label in labels)


def test_disease_detail_and_metrics():
    r = client.get(" /api/diseases/C0002395".replace(" ", ""))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "C0002395"
    assert "Alzheimer" in body["name"]
    assert body["n_associated_proteins"] > 0

    m = client.get("/api/diseases/C0002395/metrics")
    assert m.status_code == 200
    keys = {x["key"] for x in m.json()["metrics"]}
    assert keys == {
        "relative_lcc",
        "density",
        "component_distance",
        "conductance",
        "spatial_association",
        "modularity",
    }


def test_unknown_disease():
    r = client.get("/api/diseases/NOT_A_DISEASE")
    assert r.status_code == 404
    assert "Unknown disease" in r.json()["detail"]


def test_disease_network_schema():
    r = client.get("/api/diseases/C0002395/network")
    assert r.status_code == 200
    graph = r.json()
    assert "nodes" in graph and "edges" in graph
    assert graph["n_associated"] > 0
    node = graph["nodes"][0]
    assert {"id", "label", "type", "degree"} <= set(node)


def test_unknown_protein():
    r = client.get("/api/proteins/not-an-id")
    assert r.status_code == 400
    r = client.get("/api/proteins/999999999")
    assert r.status_code == 404


def test_protein_in_network():
    r = client.get("/api/proteins/7157")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "7157"
    assert body["in_ppi"] is True
    assert body["degree"] > 0
    d = client.get("/api/proteins/7157/diseases")
    assert d.status_code == 200


def test_models_performance():
    r = client.get("/api/models/performance")
    assert r.status_code == 200
    body = r.json()
    assert "Recall@25" in body["metrics_available"]
    assert "ROC-AUC" in body["metrics_not_computed"]
    assert "NMF" in body["nmf_leakage_note"]
    methods = [p["method"] for p in body["performance"]]
    assert methods == [
        "Neighborhood",
        "Random Walk",
        "DIAMOnD",
        "Neural Embeddings",
        "Matrix Completion",
    ]


def test_graphlets():
    r = client.get("/api/diseases/C0002395/graphlets")
    assert r.status_code == 200
    body = r.json()
    assert len(body["orbits"]) == 73


def test_predictions_unknown_disease():
    r = client.get("/api/diseases/NOT_A_DISEASE/predictions")
    assert r.status_code == 404


def test_similarity_not_fabricated():
    r = client.get("/api/diseases/C0002395/similar")
    assert r.status_code == 200
    assert r.json()["available"] is False
