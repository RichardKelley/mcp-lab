"""A tiny REST API with process-local, cumulative request metrics."""

import asyncio
from collections import Counter
from dataclasses import dataclass, field
from time import perf_counter

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field


class ItemInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0, allow_inf_nan=False)


class Item(ItemInput):
    id: int


@dataclass
class EndpointMetrics:
    requests: int = 0
    errors: int = 0
    total_ms: float = 0
    max_ms: float = 0
    statuses: Counter = field(default_factory=Counter)

    def record(self, status: int, elapsed_ms: float) -> None:
        self.requests += 1
        self.errors += int(status >= 400)
        self.total_ms += elapsed_ms
        self.max_ms = max(self.max_ms, elapsed_ms)
        self.statuses[str(status)] += 1


def create_app() -> FastAPI:
    app = FastAPI(title="Item API", description="A small API for the MCP lab.")
    started = perf_counter()
    items = {1: Item(id=1, name="Notebook", price=4.50)}
    next_id = 2
    metrics: dict[str, EndpointMetrics] = {}
    excluded = {"/metrics", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}

    @app.middleware("http")
    async def measure(request: Request, call_next):
        if request.url.path in excluded:
            return await call_next(request)
        start = perf_counter()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            # Group IDs together (e.g. /items/{item_id}), not by raw URL.
            route = request.scope.get("route")
            path = getattr(route, "path", "<unmatched>")
            key = f"{request.method} {path}"
            # No await here: updates are atomic within this app's event loop.
            metrics.setdefault(key, EndpointMetrics()).record(
                status, (perf_counter() - start) * 1000
            )

    @app.get("/health")
    async def health() -> dict:
        """Check whether the API is running."""
        return {"status": "ok"}

    @app.get("/items")
    async def list_items() -> list[Item]:
        """List all items."""
        return list(items.values())

    @app.get("/items/{item_id}")
    async def get_item(item_id: int) -> Item:
        """Look up an item; unknown IDs return 404."""
        if item_id not in items:
            raise HTTPException(404, "Item not found")
        return items[item_id]

    @app.post("/items", status_code=201)
    async def add_item(item: ItemInput) -> Item:
        """Create an item in memory."""
        nonlocal next_id
        created = Item(id=next_id, **item.model_dump())
        items[next_id] = created
        next_id += 1
        return created

    @app.get("/slow")
    async def slow(delay_ms: int = Query(default=200, ge=0, le=2000)) -> dict:
        """Simulate a slow endpoint to make latency visible."""
        await asyncio.sleep(delay_ms / 1000)
        return {"delay_ms": delay_ms}

    @app.get("/metrics")
    async def get_metrics() -> dict:
        """Return a live snapshot; polling this endpoint does not count as traffic."""
        return {
            "uptime_seconds": round(perf_counter() - started, 3),
            "total_requests": sum(m.requests for m in metrics.values()),
            "endpoints": {
                key: {
                    "requests": m.requests,
                    "errors": m.errors,
                    "error_rate": round(m.errors / m.requests, 4),
                    "avg_latency_ms": round(m.total_ms / m.requests, 3),
                    "max_latency_ms": round(m.max_ms, 3),
                    "status_codes": dict(m.statuses),
                }
                for key, m in sorted(metrics.items())
            },
        }

    return app


app = create_app()
