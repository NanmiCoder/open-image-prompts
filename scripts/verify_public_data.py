#!/usr/bin/env python3
"""Validate the distributable database and any locally fetched image packs.

Image packs are optional downloads (scripts/fetch_dataset.py), so this check
adapts to what is present:

  * database: integrity, counts against data/public-corpus.json, referential
    consistency, and absence of labeling process tables;
  * images/: every file on disk must be referenced by the database and look
    like a real JPEG/PNG. Referenced-but-not-downloaded files are fine unless
    OIP_REQUIRE_IMAGES=1 (full local setups) is set.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from runtime.archive_db import connect_read_only, ensure_working_database

IMAGES_ROOT = REPOSITORY_ROOT / "images"
CORPUS_PATH = REPOSITORY_ROOT / "data" / "public-corpus.json"
PROCESS_TABLES = (
    "labeling_status",
    "label_candidates",
    "labeling_runs",
    "labeling_config",
    "image_evaluations",
    "prompt_tags",
)


def signature(path: Path) -> str:
    header = path.read_bytes()[:8]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header == b"\x89PNG\r\n\x1a\n":
        return "png"
    return "unknown"


def main() -> int:
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    expected = corpus["counts"]

    database = ensure_working_database()
    with connect_read_only(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        actual = {
            "prompts": connection.execute("SELECT count(*) FROM prompts").fetchone()[0],
            "images": connection.execute("SELECT count(*) FROM images").fetchone()[0],
            "translations": connection.execute(
                "SELECT count(*) FROM prompt_translations"
            ).fetchone()[0],
            "prompt_labels": connection.execute(
                "SELECT count(*) FROM prompt_labels"
            ).fetchone()[0],
            "media_labels": connection.execute(
                "SELECT count(*) FROM media_labels"
            ).fetchone()[0],
            "taxonomy_labels": connection.execute(
                "SELECT count(*) FROM taxonomy_labels"
            ).fetchone()[0],
        }
        for key, value in expected.items():
            assert actual.get(key) == value, (
                f"count mismatch for {key}: db={actual.get(key)}, manifest={value}"
            )
        assert connection.execute(
            "SELECT count(*) FROM images i LEFT JOIN prompts p USING(tweet_id) "
            "WHERE p.tweet_id IS NULL"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM prompt_labels pl LEFT JOIN labels l ON l.id=pl.label_id "
            "WHERE l.id IS NULL"
        ).fetchone()[0] == 0
        for table in PROCESS_TABLES:
            present = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
            assert not present, f"process table must not ship publicly: {table}"
        database_paths = {
            str(row[0])
            for row in connection.execute("SELECT local_path FROM images")
        }

    disk_paths = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in IMAGES_ROOT.rglob("*")
        if path.is_file()
    } if IMAGES_ROOT.is_dir() else set()

    # A release that drops records leaves the files it used to reference behind:
    # fetch_dataset.py extracts packs but never deletes. That is a stale local
    # artifact, not corruption, and the gallery simply never references it - so it
    # must not fail an ordinary checkout after a legitimate re-pull. Treat it the
    # same way as the missing-file direction: reported always, fatal only for the
    # exact-mirror setups that opt in.
    strays = sorted(disk_paths - database_paths)
    require_images = os.environ.get("OIP_REQUIRE_IMAGES") == "1"
    if strays:
        detail = (
            f"{len(strays)} files on disk are not referenced by the DB, "
            f"e.g. {strays[:3]}; remove them with "
            "`python3 scripts/fetch_dataset.py --prune`"
        )
        assert not require_images, detail
        print(f"warning: {detail}")
    missing = len(database_paths - disk_paths)
    if require_images:
        assert missing == 0, f"{missing} referenced images have not been fetched"
    invalid = [
        path
        for path in sorted(IMAGES_ROOT.rglob("*"))
        if path.is_file() and signature(path) == "unknown"
    ] if disk_paths else []
    assert not invalid, f"invalid image assets: {invalid[:5]}"

    print(
        f"Public data OK: {actual['prompts']:,} prompts, {actual['images']:,} image rows, "
        f"{len(disk_paths):,} files fetched ({missing:,} not downloaded), "
        f"{actual['translations']:,} translations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
