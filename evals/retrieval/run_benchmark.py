#!/usr/bin/env python3
"""Deterministic bilingual benchmark for exact and related retrieval channels.

Exact relevance is checked against labeled constraints. Related relevance is
fail-closed against image IDs that were manually reviewed for the query.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_DIR = Path(__file__).resolve().parents[2]
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from retrieval.engine import RETRIEVAL_VERSION, parse_intent
from runtime.archive_db import DEFAULT_DB_PATH, connect_read_only
from scripts import prompt_library


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def percentile(values: list[float], position: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * position))]


def tag_ids(item: dict[str, Any]) -> set[str]:
    return {str(tag["id"]) for tag in item.get("tags") or []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--intents", type=Path, default=Path(__file__).with_name("intents.jsonl"))
    parser.add_argument("--out", type=Path)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    details = []
    durations = []
    strict_relevant = strict_returned = 0
    related_relevant = related_returned = 0
    strict_capacity = 0
    parser_expected = parser_found = 0
    zero_exact_queries = zero_queries_recovered = 0
    queries_with_related = related_hard_violations = related_unjudged = 0
    locale_strict_relevant = {"zh-Hans": 0, "en": 0}
    locale_capacity = {"zh-Hans": 0, "en": 0}

    with connect_read_only(args.db) as conn:
        for case in load_cases(args.intents):
            for locale, query in case["intent"].items():
                expected = set(case["must_tags_all"])
                forbidden = set(case["forbidden_tags"])
                intent = parse_intent(query)
                parsed_tags = {
                    item.tag for item in [*intent.locked_tags, *intent.must_tags]
                }
                parser_expected += len(expected)
                parser_found += len(expected & parsed_tags)

                started = time.perf_counter()
                result = prompt_library.run_search(
                    conn,
                    SimpleNamespace(
                        query=query,
                        tag=None,
                        author=None,
                        tool=None,
                        limit=args.limit,
                        max_prompt_chars=400,
                        max_tags=100,
                        taxonomy=RETRIEVAL_VERSION,
                    ),
                )
                durations.append(time.perf_counter() - started)

                exact_rows = []
                for item in result["results"]:
                    tags = tag_ids(item)
                    relevant = expected.issubset(tags) and not (forbidden & tags)
                    strict_relevant += int(relevant)
                    locale_strict_relevant[locale] += int(relevant)
                    exact_rows.append({
                        "tweet_id": item["tweet_id"],
                        "relevant": relevant,
                    })

                related_rows = []
                reviewed_related_ids = set(
                    (case.get("related_relevant_ids") or {}).get(locale) or []
                )
                for item in result["related_results"]:
                    tags = tag_ids(item)
                    missing = expected - tags
                    hard_violations = sorted(forbidden & tags)
                    reviewed_relevant = item["tweet_id"] in reviewed_related_ids
                    unjudged = not reviewed_relevant
                    relevant = reviewed_relevant and len(missing) <= 1 and not hard_violations
                    related_relevant += int(relevant)
                    related_unjudged += int(unjudged)
                    related_hard_violations += len(hard_violations)
                    related_rows.append({
                        "tweet_id": item["tweet_id"],
                        "relevant": relevant,
                        "visually_reviewed": reviewed_relevant,
                        "missing_expected": sorted(missing),
                        "declared_missing": item["missing_constraints"],
                        "hard_violations": hard_violations,
                    })

                exact_count = len(exact_rows)
                related_count = len(related_rows)
                strict_returned += exact_count
                related_returned += related_count
                strict_capacity += args.limit
                locale_capacity[locale] += args.limit
                zero_exact_queries += int(exact_count == 0)
                zero_queries_recovered += int(exact_count == 0 and related_count > 0)
                queries_with_related += int(related_count > 0)
                details.append({
                    "id": case["id"],
                    "locale": locale,
                    "query": query,
                    "exact": exact_rows,
                    "related": related_rows,
                })

    strict_precision = strict_relevant / strict_returned if strict_returned else 0.0
    related_precision = related_relevant / related_returned if related_returned else 1.0
    strict_yield = strict_relevant / strict_capacity if strict_capacity else 0.0
    combined_yield = (
        (strict_relevant + related_relevant) / strict_capacity
        if strict_capacity else 0.0
    )
    summary = {
        "schema_version": "oip-retrieval-benchmark-v2",
        "taxonomy_version": RETRIEVAL_VERSION,
        "queries": len(details),
        "parser_must_coverage": round(parser_found / parser_expected, 4),
        "strict": {
            "precision_on_returned": round(strict_precision, 4),
            "yield_adjusted_p_at_5": round(strict_yield, 4),
            "average_results": round(strict_returned / len(details), 2),
            "zero_result_queries": zero_exact_queries,
        },
        "related": {
            "human_judged_precision": round(related_precision, 4),
            "results": related_returned,
            "queries_supplemented": queries_with_related,
            "zero_queries_recovered": zero_queries_recovered,
            "unjudged_results": related_unjudged,
            "hard_violations": related_hard_violations,
        },
        "combined_useful_at_5": round(combined_yield, 4),
        "relative_useful_gain": (
            round((combined_yield - strict_yield) / strict_yield, 4)
            if strict_yield else 0.0
        ),
        "locale_strict_p_at_5": {
            locale: round(locale_strict_relevant[locale] / locale_capacity[locale], 4)
            for locale in locale_capacity
        },
        "latency_ms": {
            "median": round(statistics.median(durations) * 1000, 2),
            "p95": round(percentile(durations, 0.95) * 1000, 2),
            "max": round(max(durations) * 1000, 2),
        },
    }
    report = {"summary": summary, "details": details}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    passed = (
        summary["parser_must_coverage"] == 1.0
        and strict_precision >= 0.93
        and related_precision >= 0.95
        and related_unjudged == 0
        and related_hard_violations == 0
        and combined_yield > strict_yield
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
