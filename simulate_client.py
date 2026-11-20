"""Send random traffic to the lab API until Ctrl+C (or --count requests)."""

import argparse
from collections import Counter
import math
import os
import random
import time

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--count", type=int, default=0, help="Number of requests; 0 runs until Ctrl+C")
    parser.add_argument("--interval", type=float, default=0.5, help="Average pause between requests in seconds")
    parser.add_argument("--seed", type=int, help="Seed for repeatable request choices")
    args = parser.parse_args()
    if args.count < 0:
        parser.error("--count must be nonnegative")
    if not math.isfinite(args.interval) or args.interval < 0:
        parser.error("--interval must be finite and nonnegative")

    rng = random.Random(args.seed)
    known_ids = [1]
    statuses = Counter()
    attempted = 0
    connection_errors = 0
    # Reads are more common than writes; some traffic deliberately produces errors.
    actions = ["health", "list", "get", "create", "slow", "missing", "invalid"]
    weights = [10, 25, 25, 10, 15, 10, 5]

    print(f"Sending traffic to {args.base_url}. Press Ctrl+C to stop.", flush=True)
    try:
        with httpx.Client(base_url=args.base_url, timeout=5.0) as client:
            while args.count == 0 or attempted < args.count:
                action = rng.choices(actions, weights=weights, k=1)[0]
                method, path, payload = "GET", "/health", None
                if action == "list":
                    path = "/items"
                elif action == "get":
                    path = f"/items/{rng.choice(known_ids)}"
                elif action == "create":
                    method, path = "POST", "/items"
                    payload = {
                        "name": rng.choice(["Notebook", "Pencil", "Folder", "Marker"]),
                        "price": round(rng.uniform(0.50, 20.0), 2),
                    }
                elif action == "slow":
                    path = f"/slow?delay_ms={rng.randint(50, 750)}"
                elif action == "missing":
                    path = f"/items/{-rng.randint(1, 1000)}"
                elif action == "invalid":
                    method, path = "POST", "/items"
                    payload = {"name": "", "price": -1}

                attempted += 1
                started = time.perf_counter()
                try:
                    response = client.request(method, path, json=payload)
                    elapsed_ms = (time.perf_counter() - started) * 1000
                    statuses[response.status_code] += 1
                    if action == "create" and response.status_code == 201:
                        known_ids.append(response.json()["id"])
                    elif action == "list" and response.status_code == 200:
                        known_ids = [item["id"] for item in response.json()] or [1]
                    print(
                        f"{attempted:5d}  {method:4s} {path:30s} "
                        f"{response.status_code}  {elapsed_ms:7.1f} ms",
                        flush=True,
                    )
                except httpx.RequestError as exc:
                    connection_errors += 1
                    print(f"{attempted:5d}  {method} {path}: {exc}", flush=True)
                    # Avoid a tight retry loop when the server is unavailable.
                    if args.count == 0 or attempted < args.count:
                        time.sleep(max(1.0, args.interval))
                    continue

                if args.count == 0 or attempted < args.count:
                    time.sleep(rng.uniform(0.5, 1.5) * args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        print(f"Attempts: {attempted}; responses: {dict(sorted(statuses.items()))}; connection errors: {connection_errors}")


if __name__ == "__main__":
    main()
