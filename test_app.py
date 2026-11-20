from fastapi.testclient import TestClient

from app import create_app


def test_items_and_metrics():
    with TestClient(create_app()) as client:
        assert client.get("/metrics").json()["total_requests"] == 0
        created = client.post("/items", json={"name": "Pencil", "price": 1.25})
        assert created.status_code == 201
        item = created.json()
        assert client.get(f"/items/{item['id']}").json() == item
        assert item in client.get("/items").json()
        assert client.get("/items/999").status_code == 404
        assert client.get("/items/not-an-int").status_code == 422
        assert client.post("/items", json={"name": "", "price": -1}).status_code == 422
        client.get("/docs")
        assert "/items" in client.get("/openapi.json").json()["paths"]
        snapshot = client.get("/metrics").json()
        assert snapshot["total_requests"] == 6
        route = snapshot["endpoints"]["GET /items/{item_id}"]
        assert route["requests"] == 3
        assert route["errors"] == 2
        assert route["status_codes"] == {"200": 1, "404": 1, "422": 1}
        assert route["error_rate"] == 0.6667
        assert client.get("/metrics").json()["endpoints"] == snapshot["endpoints"]


def test_latency_and_unhandled_errors():
    app = create_app()

    @app.get("/broken")
    async def broken():
        raise RuntimeError("Test failure")

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/slow?delay_ms=30").status_code == 200
        assert client.get("/slow?delay_ms=2001").status_code == 422
        assert client.get("/missing").status_code == 404
        assert client.get("/broken").status_code == 500
        metrics = client.get("/metrics").json()["endpoints"]
        assert metrics["GET /slow"]["max_latency_ms"] >= 25
        assert metrics["GET <unmatched>"]["errors"] == 1
        assert metrics["GET /broken"]["status_codes"] == {"500": 1}

    with TestClient(create_app()) as fresh:
        assert fresh.get("/metrics").json()["total_requests"] == 0
