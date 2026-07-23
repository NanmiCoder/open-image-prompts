#!/usr/bin/env python3
"""Validate the distributable DB and approved local image subset."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from runtime.archive_db import connect_read_only, ensure_working_database

IMAGES_ROOT = REPOSITORY_ROOT / "images"


def signature(path: Path) -> str:
    header = path.read_bytes()[:8]
    if header.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if header == b"\x89PNG\r\n\x1a\n":
        return "png"
    if header.startswith(b"version "):
        return "lfs"
    return "unknown"


def main() -> int:
    database = ensure_working_database()
    with connect_read_only(database) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        prompt_count = connection.execute("SELECT count(*) FROM prompts").fetchone()[0]
        image_count = connection.execute("SELECT count(*) FROM images").fetchone()[0]
        translation_count = connection.execute(
            "SELECT count(*) FROM prompt_translations WHERE translation_version='oip-visual-v2'"
        ).fetchone()[0]
        assert prompt_count >= 14_000
        assert image_count >= 1
        assert translation_count >= 28_000
        assert connection.execute(
            "SELECT count(*) FROM images i LEFT JOIN prompts p USING(tweet_id) "
            "WHERE p.tweet_id IS NULL"
        ).fetchone()[0] == 0
        database_paths = {
            str(row[0])
            for row in connection.execute("SELECT local_path FROM images ORDER BY local_path")
        }

    disk_paths = {
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in IMAGES_ROOT.rglob("*")
        if path.is_file()
    }
    assert database_paths == disk_paths, (
        f"DB/files mismatch: missing={len(database_paths - disk_paths)}, "
        f"unreferenced={len(disk_paths - database_paths)}"
    )
    invalid = [
        path for path in sorted(IMAGES_ROOT.rglob("*"))
        if path.is_file() and signature(path) not in {"jpg", "png", "lfs"}
    ]
    assert not invalid, f"invalid image assets: {invalid[:5]}"
    print(
        f"Public data OK: {prompt_count} prompts, {image_count} approved images, "
        f"{translation_count} translations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
