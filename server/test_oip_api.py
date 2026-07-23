#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        return candidate.getsockname()[1]


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as response:
        assert response.status == 200
        assert response.headers["Content-Type"].startswith("application/json")
        return json.load(response)


def fetch_json_with_headers(url: str) -> tuple[dict, dict]:
    with urllib.request.urlopen(url, timeout=15) as response:
        assert response.status == 200
        return json.load(response), {
            name.casefold(): value for name, value in response.headers.items()
        }


def main() -> int:
    port = free_port()
    environment = os.environ.copy()
    environment["OIP_API_PORT"] = str(port)
    environment["OIP_API_CACHE_ENTRIES"] = "4"
    process = subprocess.Popen(
        [sys.executable, str(REPOSITORY_ROOT / "server/oip_api.py")],
        cwd=REPOSITORY_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(300):
            if process.poll() is not None:
                raise RuntimeError(process.stdout.read())
            try:
                fetch_json(f"{base}/health")
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("API did not become ready")

        catalog = fetch_json(f"{base}/api/catalog")
        assert catalog["stats"]["prompts"] >= 14_000
        assert catalog["stats"]["images"] >= 4_000
        assert catalog["tools"] and catalog["authors"] and catalog["tags"]
        selected_tag = catalog["tags"][0]["value"]

        first = fetch_json(f"{base}/api/prompts?limit=2&offset=0")
        second = fetch_json(f"{base}/api/prompts?limit=2&offset=2")
        assert len(first["items"]) == len(second["items"]) == 2
        assert first["total"] >= 2_500
        assert {item["tweet_id"] for item in first["items"]}.isdisjoint(
            item["tweet_id"] for item in second["items"]
        )
        assert first["items"][0]["images"]

        selected_ids = [second["items"][1]["tweet_id"], first["items"][0]["tweet_id"]]
        ids_query = urllib.parse.urlencode(
            {"limit": len(selected_ids), "ids": ",".join(selected_ids)}
        )
        selected = fetch_json(f"{base}/api/prompts?{ids_query}")
        assert [item["tweet_id"] for item in selected["items"]] == selected_ids
        assert selected["total"] == len(selected_ids)

        query = urllib.parse.urlencode({"limit": 2, "q": "portrait"})
        search_url = f"{base}/api/prompts?{query}"
        searched, first_headers = fetch_json_with_headers(search_url)
        assert searched["total"] > 0
        assert first_headers["x-oip-cache"] in {"HIT", "MISS"}
        searched_again, cached_headers = fetch_json_with_headers(search_url)
        assert searched_again == searched
        assert cached_headers["x-oip-cache"] == "HIT"

        chinese_query = urllib.parse.urlencode({"limit": 2, "q": "人物肖像"})
        chinese = fetch_json(f"{base}/api/prompts?{chinese_query}")
        assert chinese["total"] > 0

        punctuation_query = urllib.parse.urlencode({"limit": 2, "q": '"portrait" OR *'})
        punctuation = fetch_json(f"{base}/api/prompts?{punctuation_query}")
        assert punctuation["total"] > 0
        punctuation_only_query = urllib.parse.urlencode({"limit": 2, "q": '!!!'})
        punctuation_only = fetch_json(f"{base}/api/prompts?{punctuation_only_query}")
        assert punctuation_only["total"] == 0

        tagged_query = urllib.parse.urlencode({"limit": 2, "tag": selected_tag})
        tagged = fetch_json(f"{base}/api/prompts?{tagged_query}")
        assert tagged["total"] > 0
        assert len(tagged["items"]) == 2
        health = fetch_json(f"{base}/health")
        assert health["query_concurrency"] >= 1
        assert health["cache_entries"] <= 4
        print("Read-only SQLite API test OK")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
