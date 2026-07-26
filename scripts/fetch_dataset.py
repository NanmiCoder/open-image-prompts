#!/usr/bin/env python3
"""Download the public dataset (SQLite archive + image packs) for this repo.

Data no longer travels through Git LFS: every asset lives on GitHub
Releases and data/dataset-manifest.json records, per asset, the release tag
it was published under plus its sha256. This script makes the local checkout
match the manifest and is safe to re-run any time (verified assets are
skipped).

    python3 scripts/fetch_dataset.py             # database + all image packs
    python3 scripts/fetch_dataset.py --db-only   # database only
    OIP_FETCH_SKIP_IMAGES=1 ...                  # same as --db-only (CI)
    python3 scripts/fetch_dataset.py --assets-dir DIR   # offline: copy from DIR

Everything it writes (db/prompts.db.gz, images/**) is gitignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "data" / "dataset-manifest.json"
MARKER_DIR = REPOSITORY_ROOT / ".oip" / "packs"
CHUNK = 1024 * 1024
# Pin the extraction filter rather than relying on the default, which warns on
# Python 3.12/3.13 and changed in 3.14. The member checks in safe_extract already
# reject everything the "data" filter would. tarfile.data_filter exists exactly in
# the versions that accept the keyword, so this stays compatible with 3.10.0.
EXTRACT_KWARGS: dict[str, str] = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path, expected_bytes: int) -> None:
    partial = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "oip-fetch/1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as out:
            done = 0
            next_mark = 0
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if expected_bytes and done >= next_mark:
                    percent = done * 100 // expected_bytes
                    print(f"    {done:,}/{expected_bytes:,} bytes ({percent}%)", flush=True)
                    next_mark = done + max(expected_bytes // 10, 50 * CHUNK)
    except urllib.error.URLError as error:
        partial.unlink(missing_ok=True)
        raise SystemExit(
            f"download failed: {url}\n  {error}\n"
            "Check network access to github.com, or pass --assets-dir with "
            "locally provided assets."
        )
    partial.replace(target)


def obtain(entry: dict, target: Path, release_repo: str, assets_dir: Path | None) -> None:
    """Place the asset at `target`, verifying its sha256."""
    if target.is_file() and sha256_file(target) == entry["sha256"]:
        print(f"  {entry['asset']:26s} already present, sha verified")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if assets_dir is not None:
        source = assets_dir / entry["asset"]
        if not source.is_file():
            raise SystemExit(f"asset not found in --assets-dir: {source}")
        print(f"  {entry['asset']:26s} copying from {assets_dir}")
        shutil.copyfile(source, target)
    else:
        url = (
            f"https://github.com/{release_repo}/releases/download/"
            f"{entry['tag']}/{entry['asset']}"
        )
        print(f"  {entry['asset']:26s} downloading ({entry['bytes']:,} bytes)")
        download(url, target, entry.get("bytes", 0))
    actual = sha256_file(target)
    if actual != entry["sha256"]:
        target.unlink(missing_ok=True)
        raise SystemExit(
            f"sha256 mismatch for {entry['asset']}: expected {entry['sha256']}, got {actual}"
        )


def safe_extract(archive: Path, root: Path) -> int:
    """Extract a pack, accepting only regular files under images/."""
    count = 0
    with tarfile.open(archive, mode="r:gz") as tar:
        for member in tar:
            name = member.name
            if not member.isreg():
                continue
            if name.startswith(("/", "\\")) or ".." in Path(name).parts:
                raise SystemExit(f"refusing unsafe path in pack: {name!r}")
            if not name.startswith("images/"):
                raise SystemExit(f"unexpected path outside images/ in pack: {name!r}")
            member.mode = 0o644
            tar.extract(member, path=root, **EXTRACT_KWARGS)
            count += 1
    return count


def prune_unreferenced_images() -> int:
    """Delete images/ files the current database no longer references.

    A release that drops records leaves its files behind, because extraction never
    deletes. Deleting is opt-in rather than automatic: the files are re-downloadable
    but a user may be holding on to an older corpus on purpose.
    """
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))
    from runtime.archive_db import connect_read_only, ensure_working_database

    images_root = REPOSITORY_ROOT / "images"
    if not images_root.is_dir():
        print("prune: images/ is absent, nothing to do")
        return 0
    database = ensure_working_database()
    with connect_read_only(database) as connection:
        referenced = {str(row[0]) for row in connection.execute("SELECT local_path FROM images")}
    removed = 0
    for path in sorted(images_root.rglob("*")):
        if not path.is_file():
            continue
        if path.relative_to(REPOSITORY_ROOT).as_posix() in referenced:
            continue
        path.unlink()
        removed += 1
    for directory in sorted(images_root.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    print(f"prune: removed {removed:,} unreferenced files from images/")
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db-only", action="store_true", help="skip image packs")
    parser.add_argument("--assets-dir", type=Path, help="offline mode: copy assets from this directory instead of downloading")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="after fetching, delete images/ files the database no longer references",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.is_file():
        raise SystemExit(f"dataset manifest missing: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    release_repo = manifest.get("release_repo", "NanmiCoder/open-image-prompts")
    assets_dir = args.assets_dir.resolve() if args.assets_dir else None
    skip_images = args.db_only or os.environ.get("OIP_FETCH_SKIP_IMAGES") == "1"

    print(f"dataset {manifest['dataset_version']} ({manifest['taxonomy_version']})")
    print("[1/2] database archive")
    obtain(manifest["db"], REPOSITORY_ROOT / "db" / "prompts.db.gz", release_repo, assets_dir)

    if skip_images:
        print("[2/2] image packs skipped (--db-only)")
        if args.prune:
            prune_unreferenced_images()
        return 0

    packs = manifest.get("image_packs", [])
    print(f"[2/2] image packs ({len(packs)})")
    MARKER_DIR.mkdir(parents=True, exist_ok=True)
    for entry in packs:
        marker = MARKER_DIR / f"{entry['asset']}.sha256"
        if marker.is_file() and marker.read_text(encoding="utf-8").strip() == entry["sha256"]:
            print(f"  {entry['asset']:26s} already extracted")
            continue
        archive = MARKER_DIR / entry["asset"]
        obtain(entry, archive, release_repo, assets_dir)
        extracted = safe_extract(archive, REPOSITORY_ROOT)
        marker.write_text(entry["sha256"] + "\n", encoding="utf-8")
        archive.unlink()
        print(f"  {entry['asset']:26s} extracted {extracted:,} files")

    if args.prune:
        prune_unreferenced_images()
    total = sum(1 for path in (REPOSITORY_ROOT / "images").rglob("*") if path.is_file())
    print(f"done: images/ now holds {total:,} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
