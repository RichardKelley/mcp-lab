"""Student starter: expose information about the running REST API through MCP.

Run: uv run python mcp_server.py
The MCP host launches this process and communicates over stdio. Do not print
to stdout: it is reserved for protocol messages (use stderr for debugging).
"""

import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Item API observer")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


async def fetch_json(path: str) -> dict:
    """Fetch API data. Use this helper in your tools."""
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=5.0) as client:
        response = await client.get(path)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def describe_api() -> dict:
    """Describe the REST endpoints, parameters, and request bodies available."""
    # TODO: Fetch /openapi.json and return useful information from its paths.
    # Include methods, descriptions, parameters, and request schemas.
    raise NotImplementedError("TODO: discover the API using its OpenAPI schema")


@mcp.tool()
async def get_live_metrics() -> dict:
    """Get current request counts, errors, status codes, and endpoint latency."""
    # TODO: Fetch /metrics. Return live data, not hard-coded observations.
    raise NotImplementedError("TODO: retrieve the live metrics snapshot")


@mcp.tool()
async def summarize_endpoint(method: str, path: str) -> dict:
    """Report metrics for one route, such as GET /items/{item_id}."""
    # TODO: Fetch /metrics and find the key '<UPPERCASE METHOD> <route path>'.
    # Handle an unknown route or a route that has received no requests yet.
    raise NotImplementedError("TODO: select and explain one endpoint's metrics")


if __name__ == "__main__":
    mcp.run(transport="stdio")
