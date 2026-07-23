#!/usr/bin/env python3
"""Small read-only HTTP API for the Open Image Prompts SQLite archive."""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import BoundedSemaphore, Lock
from urllib.parse import parse_qs, urlparse

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from runtime.archive_db import (
    DEFAULT_ARCHIVE_PATH,
    DEFAULT_DB_PATH,
    active_taxonomy_version,
    connect_read_only,
    ensure_working_database,
)

DB_PATH = Path(os.environ.get("OIP_DB_PATH", DEFAULT_DB_PATH))
DB_ARCHIVE_PATH = Path(os.environ.get("OIP_DB_ARCHIVE_PATH", DEFAULT_ARCHIVE_PATH))
API_HOST = os.environ.get("OIP_API_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("OIP_API_PORT", "8787"))
QUERY_CONCURRENCY = max(1, int(os.environ.get("OIP_API_QUERY_CONCURRENCY", "4")))
QUERY_WAIT_SECONDS = max(0.1, float(os.environ.get("OIP_API_QUERY_WAIT_SECONDS", "3")))
PROMPT_CACHE_ENTRIES = max(0, int(os.environ.get("OIP_API_CACHE_ENTRIES", "128")))
MAX_PAGE_SIZE = 60
_catalog_cache: dict | None = None
_catalog_lock = Lock()
_query_slots = BoundedSemaphore(QUERY_CONCURRENCY)
_prompt_cache: OrderedDict[tuple, bytes] = OrderedDict()
_prompt_cache_lock = Lock()


def connect() -> sqlite3.Connection:
    return connect_read_only(DB_PATH)


def taxonomy_version(connection: sqlite3.Connection) -> str:
    return active_taxonomy_version(connection)


def fts_expression(text: str) -> str:
    tokens = re.findall(r"[^\W_]+", text.casefold(), flags=re.UNICODE)
    tokens = list(dict.fromkeys(tokens))[:16]
    if not tokens:
        return '"__open_image_prompts_no_search_terms__"'
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens)


def prompt_parameters(query: dict[str, list[str]]) -> dict:
    limit = min(max(int(query.get("limit", ["24"])[0]), 1), MAX_PAGE_SIZE)
    offset = max(int(query.get("offset", ["0"])[0]), 0)
    text = query.get("q", [""])[0].strip()[:200]
    tool = query.get("tool", [""])[0].strip()
    author = query.get("author", [""])[0].strip()
    tag = query.get("tag", [""])[0].strip()
    ids = tuple(
        dict.fromkeys(
            value.strip()[:128]
            for value in query.get("ids", [""])[0].split(",")
            if value.strip()
        )
    )[:MAX_PAGE_SIZE]
    if tag and ":" not in tag:
        raise ValueError("tag must use dimension:value format")
    if ids and (offset or text or tool or author or tag):
        raise ValueError("ids cannot be combined with offset or archive filters")
    sort = "oldest" if query.get("sort", ["newest"])[0] == "oldest" else "newest"
    return {
        "limit": limit,
        "offset": offset,
        "q": text,
        "tool": tool,
        "author": author,
        "tag": tag,
        "ids": ids,
        "sort": sort,
    }


def prompt_cache_key(parameters: dict) -> tuple:
    return (
        parameters["limit"],
        parameters["offset"],
        parameters["sort"],
        parameters["q"].casefold(),
        parameters["tool"],
        parameters["author"],
        parameters["tag"],
        parameters["ids"],
    )


def prompt_cache_get(key: tuple) -> bytes | None:
    with _prompt_cache_lock:
        data = _prompt_cache.pop(key, None)
        if data is not None:
            _prompt_cache[key] = data
        return data


def prompt_cache_put(key: tuple, data: bytes) -> None:
    if PROMPT_CACHE_ENTRIES == 0:
        return
    with _prompt_cache_lock:
        _prompt_cache.pop(key, None)
        _prompt_cache[key] = data
        while len(_prompt_cache) > PROMPT_CACHE_ENTRIES:
            _prompt_cache.popitem(last=False)


def item_for(connection: sqlite3.Connection, row: sqlite3.Row, taxonomy: str) -> dict:
    tweet_id = str(row["tweet_id"])
    images = [
        {
            "id": str(image["id"]),
            "index": image["image_index"],
            "url": image["url"],
            "local": image["local_path"] or None,
            "tags": {},
        }
        for image in connection.execute(
            "SELECT id,image_index,url,local_path FROM images WHERE tweet_id=? ORDER BY image_index",
            (tweet_id,),
        )
    ]
    translations = {
        entry["locale"]: entry["translated_text"]
        for entry in connection.execute(
            "SELECT locale,translated_text FROM prompt_translations WHERE tweet_id=? AND translation_version=?",
            (tweet_id, taxonomy),
        )
    }
    return {
        "tweet_id": tweet_id,
        "author": row["author"],
        "tool": row["tool"] or "None",
        "prompt_text": row["prompt_text"],
        "translations": translations,
        "created_at": row["created_at"],
        "tweet_url": row["tweet_url"],
        "collected_at": row["collected_at"],
        "images": images,
        "videos": [],
        # Tag filtering and labels come from /api/catalog. Keeping the large
        # per-prompt evidence payload out makes the first gallery page smaller.
        "tags": {},
    }


def catalog(connection: sqlite3.Connection, taxonomy: str) -> dict:
    tools = [
        {"tool": row["tool"], "count": row["count"]}
        for row in connection.execute(
            """
            SELECT tool,COUNT(*) AS count FROM prompts
            WHERE tool IS NOT NULL AND tool NOT IN ('','None')
            GROUP BY tool ORDER BY count DESC,tool
            """
        )
    ]
    authors = [
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT author FROM prompts WHERE author<>'' ORDER BY author"
        )
    ]
    tags = [
        {
            "value": f"{row['dimension']}:{row['tag']}",
            "label_en": row["display_en"] or row["tag"],
            "label_zh": row["display_zh"] or row["tag"],
            "count": row["count"],
        }
        for row in connection.execute(
            """
            SELECT ld.key AS dimension,l.key AS tag,tl.display_en,tl.display_zh,
                   COUNT(DISTINCT pl.tweet_id) AS count
            FROM prompt_labels pl
            JOIN labels l ON l.id=pl.label_id
            JOIN label_dimensions ld ON ld.id=l.dimension_id
            LEFT JOIN taxonomy_labels tl
              ON tl.taxonomy_version=pl.taxonomy_version AND tl.label_id=l.id
            WHERE pl.taxonomy_version=?
            GROUP BY ld.key,l.key,tl.display_en,tl.display_zh
            ORDER BY count DESC,ld.key,l.key
            """,
            (taxonomy,),
        )
    ]
    stats = {
        "prompts": connection.execute("SELECT COUNT(*) FROM prompts").fetchone()[0],
        "images": connection.execute("SELECT COUNT(*) FROM images").fetchone()[0],
        "authors": len(authors),
        "tools": len(tools),
    }
    return {"tools": tools, "authors": authors, "tags": tags, "stats": stats}


def cached_catalog(connection: sqlite3.Connection, taxonomy: str) -> dict:
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    with _catalog_lock:
        if _catalog_cache is None:
            _catalog_cache = catalog(connection, taxonomy)
    return _catalog_cache


def prewarm_catalog() -> None:
    connection = connect()
    try:
        cached_catalog(connection, taxonomy_version(connection))
    finally:
        connection.close()


class GalleryHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 64


class Handler(BaseHTTPRequestHandler):
    server_version = "OpenImagePromptsAPI/1"

    def log_message(self, *_args) -> None:
        return

    def send_data(
        self,
        data: bytes,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            return

    def send_json(
        self,
        value: object,
        status: int = 200,
        headers: dict[str, str] | None = None,
    ) -> None:
        data = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
        self.send_data(data, status, headers)

    def do_GET(self) -> None:
        request = urlparse(self.path)
        query = parse_qs(request.query)
        if request.path == "/health":
            with _prompt_cache_lock:
                cache_entries = len(_prompt_cache)
            self.send_json(
                {
                    "ok": True,
                    "query_concurrency": QUERY_CONCURRENCY,
                    "cache_entries": cache_entries,
                }
            )
            return

        if request.path == "/api/catalog":
            connection = connect()
            try:
                taxonomy = taxonomy_version(connection)
                self.send_json(cached_catalog(connection, taxonomy))
            except sqlite3.Error as error:
                self.send_json({"error": str(error)}, 500)
            finally:
                connection.close()
            return

        if request.path != "/api/prompts":
            self.send_json({"error": "not found"}, 404)
            return

        try:
            parameters = prompt_parameters(query)
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
            return

        key = prompt_cache_key(parameters)
        cached = prompt_cache_get(key)
        if cached is not None:
            self.send_data(cached, headers={"X-OIP-Cache": "HIT"})
            return

        if not _query_slots.acquire(timeout=QUERY_WAIT_SECONDS):
            self.send_json(
                {"error": "server busy; retry shortly"},
                503,
                {"Retry-After": "1"},
            )
            return

        connection = None
        try:
            cached = prompt_cache_get(key)
            if cached is not None:
                self.send_data(cached, headers={"X-OIP-Cache": "HIT"})
                return
            connection = connect()
            taxonomy = taxonomy_version(connection)
            data = self.prompt_data(connection, taxonomy, parameters)
            prompt_cache_put(key, data)
            self.send_data(data, headers={"X-OIP-Cache": "MISS"})
        except ValueError as error:
            self.send_json({"error": str(error)}, 400)
        except sqlite3.Error as error:
            self.send_json({"error": str(error)}, 500)
        finally:
            if connection is not None:
                connection.close()
            _query_slots.release()

    def prompt_data(
        self,
        connection: sqlite3.Connection,
        taxonomy: str,
        parameters: dict,
    ) -> bytes:
        limit = parameters["limit"]
        offset = parameters["offset"]
        ids = parameters["ids"]
        if ids:
            placeholders = ",".join("?" for _ in ids)
            rows = connection.execute(
                f"""
                SELECT p.tweet_id,p.author,p.tool,p.prompt_text,p.created_at,
                       p.tweet_url,p.collected_at
                FROM prompts p
                WHERE p.tweet_id IN ({placeholders})
                """,
                ids,
            ).fetchall()
            rows_by_id = {str(row["tweet_id"]): row for row in rows}
            ordered_rows = [rows_by_id[tweet_id] for tweet_id in ids if tweet_id in rows_by_id]
            return json.dumps(
                {
                    "items": [
                        item_for(connection, row, taxonomy)
                        for row in ordered_rows[:limit]
                    ],
                    "total": len(ordered_rows),
                    "offset": 0,
                    "limit": limit,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode()

        clauses: list[str] = [
            "EXISTS (SELECT 1 FROM images visible_image WHERE visible_image.tweet_id=p.tweet_id)"
        ]
        arguments: list[object] = []

        for column, key in (("p.tool", "tool"), ("p.author", "author")):
            value = parameters[key]
            if value:
                clauses.append(f"{column}=?")
                arguments.append(value)

        text = parameters["q"]
        if text:
            clauses.append(
                """p.tweet_id IN (
                    SELECT tweet_id FROM prompt_fts
                    WHERE prompt_fts MATCH ?
                )"""
            )
            arguments.append(fts_expression(text))

        tag = parameters["tag"]
        if tag:
            dimension, label = tag.split(":", 1)
            clauses.append(
                """EXISTS (
                    SELECT 1 FROM prompt_labels pl
                    JOIN labels l ON l.id=pl.label_id
                    JOIN label_dimensions ld ON ld.id=l.dimension_id
                    WHERE pl.tweet_id=p.tweet_id AND pl.taxonomy_version=?
                      AND ld.key=? AND l.key=?
                )"""
            )
            arguments.extend((taxonomy, dimension, label))

        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        total = connection.execute(
            f"SELECT COUNT(*) FROM prompts p{where}", arguments
        ).fetchone()[0]
        order = "ASC" if parameters["sort"] == "oldest" else "DESC"
        rows = connection.execute(
            f"""
            SELECT p.tweet_id,p.author,p.tool,p.prompt_text,p.created_at,
                   p.tweet_url,p.collected_at
            FROM prompts p{where}
            ORDER BY COALESCE(p.created_at,p.collected_at) {order}
            LIMIT ? OFFSET ?
            """,
            [*arguments, limit, offset],
        ).fetchall()
        return json.dumps(
            {
                "items": [item_for(connection, row, taxonomy) for row in rows],
                "total": total,
                "offset": offset,
                "limit": limit,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()


if __name__ == "__main__":
    ensure_working_database(DB_PATH, DB_ARCHIVE_PATH)
    print("Preparing gallery filters ...", flush=True)
    prewarm_catalog()
    print(f"Open Image Prompts API listening on http://{API_HOST}:{API_PORT}", flush=True)
    with GalleryHTTPServer((API_HOST, API_PORT), Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
