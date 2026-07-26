#!/usr/bin/env python3
"""Guard the documentation against drifting away from the shipped dataset.

Both README files quote dataset counts in prose, and the Skills describe how to
obtain the data. Neither is covered by the database checks in
scripts/verify_public_data.py, so a dataset release or a distribution change can
leave the docs stating something that is no longer true. This check needs no
database and no network, so it can run on every platform in CI.

    python3 scripts/verify_docs.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = REPOSITORY_ROOT / "data" / "public-corpus.json"

# Prose label in each README -> key in data/public-corpus.json.
COUNT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("README.md", "prompts", r"\*\*([\d,]+) source prompts\*\*"),
    ("README.md", "images", r"\*\*([\d,]+) images\*\*"),
    ("README.md", "translations", r"\*\*([\d,]+) translations\*\*"),
    ("README.md", "prompt_labels", r"\*\*([\d,]+) active v2 prompt labels\*\*"),
    ("README.md", "taxonomy_labels", r"closed taxonomy of \*\*([\d,]+) visual labels\*\*"),
    ("README.zh-CN.md", "prompts", r"\*\*([\d,]+) 条来源提示词\*\*"),
    ("README.zh-CN.md", "images", r"\*\*([\d,]+) 张图片\*\*"),
    ("README.zh-CN.md", "translations", r"\*\*([\d,]+) 条翻译\*\*"),
    ("README.zh-CN.md", "prompt_labels", r"\*\*([\d,]+) 条有效 v2 提示词标签\*\*"),
    ("README.zh-CN.md", "taxonomy_labels", r"\*\*([\d,]+) 个封闭视觉标签\*\*"),
)

# Dataset assets moved from Git LFS to GitHub Releases. Documenting that history
# is fine ("instead of Git LFS"); telling a reader to obtain an LFS corpus is a
# stale instruction that sends people and agents down a dead path.
STALE_PHRASES: tuple[str, ...] = (
    "LFS corpus",
    "LFS image corpus",
    "Git LFS images",
    "git lfs pull",
)
STALE_SEARCH_GLOBS: tuple[str, ...] = (
    "README.md",
    "README.zh-CN.md",
    "DATASET.md",
    "web/README.md",
    "skills/**/*.md",
    "skills/**/*.py",
    "scripts/*.py",
    "server/*.py",
    "runtime/*.py",
)


def check_counts(problems: list[str]) -> None:
    expected = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))["counts"]
    for filename, key, pattern in COUNT_PATTERNS:
        path = REPOSITORY_ROOT / filename
        text = path.read_text(encoding="utf-8")
        match = re.search(pattern, text)
        if match is None:
            problems.append(
                f"{filename}: no prose count matched /{pattern}/; update "
                "scripts/verify_docs.py together with the wording"
            )
            continue
        stated = int(match.group(1).replace(",", ""))
        if stated != expected[key]:
            problems.append(
                f"{filename}: states {stated:,} for {key}, but "
                f"data/public-corpus.json has {expected[key]:,}"
            )


def check_stale_phrases(problems: list[str]) -> None:
    this_file = Path(__file__).resolve()
    for pattern in STALE_SEARCH_GLOBS:
        for path in sorted(REPOSITORY_ROOT.glob(pattern)):
            # This file necessarily spells out the phrases it forbids.
            if not path.is_file() or path.resolve() == this_file:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                folded = line.casefold()
                for phrase in STALE_PHRASES:
                    if phrase.casefold() in folded:
                        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
                        problems.append(
                            f"{relative}:{number}: stale distribution wording "
                            f"{phrase!r}; assets ship through GitHub Releases"
                        )


def check_style_cards(problems: list[str]) -> None:
    """Every style card must expose one unique id, and SKILL.md must count them.

    The reference files use two layouts - a prose heading with an explicit id
    field, and the card id itself as the heading - so an agent asked for
    `style_card_id` needs one dependable place to read it from.
    """
    references = REPOSITORY_ROOT / "skills" / "img-gen-taste" / "references"
    heading = re.compile(r"^## (.+)$")
    id_field = re.compile(r"^- `id`: `([a-z0-9-]+)`$")
    ids: dict[str, str] = {}
    total = 0
    for path in sorted(references.glob("*.md")):
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        current: str | None = None
        current_line = 0
        seen_id = False

        def close(card: str | None, line: int, has_id: bool) -> None:
            if card is not None and not has_id:
                problems.append(f"{relative}:{line}: card {card!r} has no `- `id`:` field")

        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = heading.match(line)
            if match:
                title = match.group(1).strip()
                if title == "目录":  # table of contents, not a card
                    close(current, current_line, seen_id)
                    current, seen_id = None, False
                    continue
                close(current, current_line, seen_id)
                current, current_line, seen_id = title, number, False
                total += 1
                continue
            found = id_field.match(line)
            if found and current is not None:
                seen_id = True
                card_id = found.group(1)
                if card_id in ids:
                    problems.append(
                        f"{relative}:{number}: duplicate card id {card_id!r}, "
                        f"already defined in {ids[card_id]}"
                    )
                ids[card_id] = f"{relative}:{number}"
        close(current, current_line, seen_id)

    if len(ids) != total:
        problems.append(f"{total} style cards but {len(ids)} unique ids")
    skill_path = REPOSITORY_ROOT / "skills" / "img-gen-taste" / "SKILL.md"
    stated = re.search(r"The (\d+) cards are", skill_path.read_text(encoding="utf-8"))
    if stated is None:
        problems.append("skills/img-gen-taste/SKILL.md: card count sentence not found")
    elif int(stated.group(1)) != total:
        problems.append(
            f"skills/img-gen-taste/SKILL.md: claims {stated.group(1)} cards, "
            f"references define {total}"
        )


def main() -> int:
    problems: list[str] = []
    check_counts(problems)
    check_stale_phrases(problems)
    check_style_cards(problems)
    if problems:
        for problem in problems:
            print(f"  {problem}")
        raise SystemExit(f"documentation check failed with {len(problems)} problem(s)")
    print(
        "Docs OK: README counts match data/public-corpus.json, style cards all "
        "expose a unique id, no stale LFS instructions"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
