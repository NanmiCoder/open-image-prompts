"""Cross-platform hydration and read-only access for the public SQLite archive."""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = REPOSITORY_ROOT / ".oip" / "runtime" / "prompts.db"
DEFAULT_ARCHIVE_PATH = REPOSITORY_ROOT / "db" / "prompts.db.gz"


def _fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def ensure_working_database(
    db_path: Path = DEFAULT_DB_PATH,
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
) -> Path:
    """Expand the versioned archive once and refresh it when the archive changes."""
    db_path = Path(db_path)
    archive_path = Path(archive_path)
    if not archive_path.is_file():
        raise SystemExit(
            f"SQLite archive not found at {archive_path}. "
            "Run `npm run setup` from the repository root."
        )
    with archive_path.open("rb") as archive:
        if archive.read(32).startswith(b"version https://git-lfs"):
            raise SystemExit(
                "The SQLite archive is still a Git LFS pointer. "
                "Run `npm run setup` from the repository root."
            )

    fingerprint = _fingerprint(archive_path)
    stamp_path = db_path.with_suffix(f"{db_path.suffix}.source")
    try:
        if db_path.is_file() and stamp_path.read_text(encoding="utf-8").strip() == fingerprint:
            return db_path
    except OSError:
        pass

    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = db_path.with_name(f"{db_path.name}.{os.getpid()}.tmp")
    temporary_stamp = stamp_path.with_name(f"{stamp_path.name}.{os.getpid()}.tmp")
    try:
        with gzip.open(archive_path, "rb") as source, temporary.open("wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
        with sqlite3.connect(temporary) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise RuntimeError("expanded SQLite archive failed integrity_check")
        os.replace(temporary, db_path)
        temporary_stamp.write_text(f"{fingerprint}\n", encoding="utf-8")
        os.replace(temporary_stamp, stamp_path)
    finally:
        temporary.unlink(missing_ok=True)
        temporary_stamp.unlink(missing_ok=True)
    return db_path


def connect_read_only(path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(
        f"file:{Path(path).resolve().as_posix()}?mode=ro&immutable=1",
        uri=True,
        timeout=5,
    )
    connection.row_factory = sqlite3.Row
    return connection


def table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def active_taxonomy_version(connection: sqlite3.Connection) -> str:
    if not table_exists(connection, "archive_config"):
        return "legacy"
    row = connection.execute(
        "SELECT value FROM archive_config WHERE key='active_taxonomy_version'"
    ).fetchone()
    return str(row[0]) if row else "legacy"
