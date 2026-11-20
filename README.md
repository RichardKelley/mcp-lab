# FastAPI + MCP lab

In this project, you'll create an MCP server to answer questions about a FastAPI server. 

The FastAPI server tracks metrics related to usage. Your goal will be to create an MCP server that can answer questions about the server's state 

## Run the API

```sh
uv sync
uv run uvicorn app:app --reload
```

Metrics are cumulative since startup, grouped by HTTP method and route template.
Each observed endpoint reports request count, error count, error rate (0–1),
average and maximum latency in milliseconds, and counts by status code.
Errors mean HTTP status >= 400, including validation failures. Unmatched paths
share the `<unmatched>` bucket. Routes appear only after their first request.
Latency measures server processing until the response is available to middleware,
not network transfer time. Metrics and items live in memory and reset on restart
or reload; run one worker. Documentation, schema, and metrics requests are excluded.

## Simulated client

With the API running, start random traffic in another terminal:

```sh
uv run python simulate_client.py
```

The client randomly checks health, lists and looks up items, creates items, and
calls the slow endpoint. Some requests intentionally cause 404 and 422 responses
so the error metrics change too. Each request prints its status and latency.
Requests run sequentially with a random pause averaging 0.5 seconds; stop with
Ctrl+C to see a summary. Created items remain in the API until it restarts.

For a fixed run or faster traffic:

```sh
uv run python simulate_client.py --count 50 --interval 0.1 --seed 42
```

Use `--base-url http://127.0.0.1:8001` (or `API_BASE_URL`) to target another
address. `--count 0` runs indefinitely. Inspect `/metrics` or ask your MCP host
questions while the simulator runs.

## The Exercise

Fill in the three tools in `mcp_server.py`. The server, tool decorators, and HTTP
helper are provided; the tool bodies intentionally raise `NotImplementedError`.

1. Discover the REST API from `/openapi.json` in `describe_api`.
2. Retrieve current observations from `/metrics` in `get_live_metrics`.
3. Select one route's metrics in `summarize_endpoint`, handling missing data.
4. Handle connection failures and HTTP errors with useful tool error messages.

Connect your server using the Pi instructions below. `API_BASE_URL` optionally
changes the API address. Pi's language model uses your tools to answer questions;
the MCP server itself does not call a model.

Try asking:

- What endpoints does this API expose, and how do I create an item?
- Which endpoint has received the most requests?
- Which endpoint has the highest average latency?
- How many requests to `GET /items/{item_id}` failed?

Generate additional traffic and ask again to verify the answers change. Before
traffic exists, report that there is no observed data instead of inventing values.

## Connect to the Pi coding agent

Current Pi supports MCP over stdio, which matches this project's starter.
With Pi installed, run these commands from this project directory in separate
terminals:

```sh
# Terminal 1: start the REST API
uv run uvicorn app:app --reload

# Terminal 2: generate traffic
uv run python simulate_client.py

# Terminal 3: register the MCP server for this project and launch Pi
pi mcp add --local item-api -- uv --directory "$PWD" run python mcp_server.py
pi mcp list
pi
```

If the API and simulator are already running, only the third terminal is needed.
Pi launches the MCP process itself. Inside Pi, use `/mcp` to inspect the
connection. If you register the server while Pi is already open, run `/reload`.

The starter can connect and advertise its tools, but tool calls return TODO
errors until you implement the student exercise. Once completed, try asking:

> Use the item-api MCP tools to identify the endpoint with the highest average latency.

See the [Pi MCP documentation](https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/mcp.md)
for configuration details.
