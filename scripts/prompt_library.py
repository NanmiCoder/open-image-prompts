#!/usr/bin/env python3
"""Read-only retrieval CLI for the Open Image Prompts archive.

The CLI is deliberately deterministic: it never invokes a model, changes the
database, or prints credentials. It gives an agent a bounded set of bilingual,
copyable source prompts plus their active controlled tags and representative
media, which is the hand-off point for prompt improvement or image ideation.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

REPO_DIR = Path(__file__).resolve().parents[1]
if str(REPO_DIR) not in sys.path:
    sys.path.insert(0, str(REPO_DIR))

from runtime.archive_db import (
    DEFAULT_ARCHIVE_PATH,
    DEFAULT_DB_PATH,
    active_taxonomy_version,
    connect_read_only,
    ensure_working_database,
    table_exists,
)
from retrieval.engine import (
    IntentTag,
    RETRIEVAL_VERSION,
    SearchIntent,
    lexical_group_hits,
    lexical_term_present,
    parse_intent,
    weighted_tag_similarity,
)

SCHEMA_VERSION = "oip-retrieval-v1"


def json_array(value: object) -> list[str]:
    try:
        parsed = json.loads(str(value or "[]"))
        return [str(item) for item in parsed] if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return table_exists(conn, table) and any(row[1] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def current_version(conn: sqlite3.Connection) -> str:
    return active_taxonomy_version(conn)


def require_v2_active(conn: sqlite3.Connection) -> None:
    actual = current_version(conn)
    if actual != RETRIEVAL_VERSION:
        raise RuntimeError(
            f"retrieval is not ready: active taxonomy is {actual!r}, expected {RETRIEVAL_VERSION!r}"
        )


def search_terms(query: str) -> list[str]:
    """Compatibility helper backed by the v2 intent parser.

    In particular, this never emits individual Han characters.  A one-character
    match recalls most of a Chinese archive and was the main source of false
    positives in the previous search implementation.
    """
    return parse_intent(query).lexical_terms


def trim(text: object, maximum: int) -> str:
    value = str(text or "").strip()
    return value if len(value) <= maximum else f"{value[:maximum - 1].rstrip()}…"


def bounded_int(minimum: int, maximum: int):
    def parse(value: str) -> int:
        try:
            parsed = int(value)
        except ValueError as error:
            raise argparse.ArgumentTypeError(f"must be an integer from {minimum} to {maximum}") from error
        if not minimum <= parsed <= maximum:
            raise argparse.ArgumentTypeError(f"must be from {minimum} to {maximum}")
        return parsed
    return parse


def label_rows(conn: sqlite3.Connection, *, media: bool, taxonomy_version: str, tweet_ids: set[str] | None = None) -> Iterable[sqlite3.Row]:
    table = "media_labels" if media else "prompt_labels"
    if not (table_exists(conn, table) and table_exists(conn, "labels") and table_exists(conn, "label_dimensions")):
        return []
    alias = "ml" if media else "pl"
    owner = "ml.tweet_id" if media else "pl.tweet_id"
    versioned = column_exists(conn, table, "taxonomy_version")
    catalog = table_exists(conn, "taxonomy_labels") and versioned
    catalog_join = (
        f"LEFT JOIN taxonomy_labels tl ON tl.taxonomy_version={alias}.taxonomy_version AND tl.label_id=l.id"
        if catalog else ""
    )
    where: list[str] = []
    params: list[str] = []
    if media:
        where.append("ml.media_type='image'")
    if versioned:
        where.append(f"{alias}.taxonomy_version=?")
        params.append(taxonomy_version)
    if tweet_ids is not None:
        if not tweet_ids:
            return []
        where.append(f"{owner} IN ({','.join('?' for _ in tweet_ids)})")
        params.extend(sorted(tweet_ids))
    return conn.execute(
        f"""
        SELECT {owner} AS tweet_id, ld.key AS dimension_key, l.key AS label_key,
               l.name AS fallback_name, {alias}.confidence, '' AS evidence,
               {"tl.display_en, tl.display_zh, tl.aliases_en_json, tl.aliases_zh_json" if catalog else "NULL AS display_en, NULL AS display_zh, NULL AS aliases_en_json, NULL AS aliases_zh_json"}
        FROM {table} {alias}
        JOIN labels l ON l.id={alias}.label_id
        JOIN label_dimensions ld ON ld.id=l.dimension_id
        {catalog_join}
        WHERE {' AND '.join(where)}
        ORDER BY {owner}, ld.key, {alias}.confidence DESC, l.key
        """,
        params,
    )


def tags_by_tweet(conn: sqlite3.Connection, taxonomy_version: str, tweet_ids: set[str] | None = None) -> dict[str, list[dict[str, Any]]]:
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for media in (False, True):
        for row in label_rows(conn, media=media, taxonomy_version=taxonomy_version, tweet_ids=tweet_ids):
            tweet_id = str(row["tweet_id"])
            canonical = f"{row['dimension_key']}:{row['label_key']}"
            item = {
                "id": canonical,
                "dimension": row["dimension_key"],
                "key": row["label_key"],
                "display": {
                    "en": row["display_en"] or row["fallback_name"] or row["label_key"],
                    "zh-Hans": row["display_zh"] or row["display_en"] or row["fallback_name"] or row["label_key"],
                },
                "aliases": {
                    "en": json_array(row["aliases_en_json"]),
                    "zh-Hans": json_array(row["aliases_zh_json"]),
                },
                "confidence": float(row["confidence"] or 0),
                "evidence": row["evidence"] or "",
                "scope": "image" if media else "prompt",
                "scopes": ["image" if media else "prompt"],
            }
            key = (tweet_id, canonical)
            if key not in best:
                best[key] = item
            else:
                existing = best[key]
                existing["scopes"] = sorted(set([*existing.get("scopes", []), *item["scopes"]]))
                if item["confidence"] > existing["confidence"]:
                    item["scopes"] = existing["scopes"]
                    best[key] = item
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (tweet_id, _), item in best.items():
        grouped[tweet_id].append(item)
    for tags in grouped.values():
        tags.sort(key=lambda tag: (tag["dimension"], tag["key"]))
    return grouped


def translations_by_tweet(conn: sqlite3.Connection, taxonomy_version: str, tweet_ids: set[str] | None = None) -> dict[str, dict[str, str]]:
    if not table_exists(conn, "prompt_translations"):
        return {}
    if tweet_ids is not None and not tweet_ids:
        return {}
    where = "translation_version=?"
    params: list[str] = [taxonomy_version]
    if tweet_ids is not None:
        where += f" AND tweet_id IN ({','.join('?' for _ in tweet_ids)})"
        params.extend(sorted(tweet_ids))
    rows = conn.execute(
        f"SELECT tweet_id, locale, translated_text FROM prompt_translations WHERE {where}",
        params,
    )
    translated: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        translated[str(row["tweet_id"])][str(row["locale"])] = str(row["translated_text"])
    return translated


def image_summary_by_tweet(conn: sqlite3.Connection, tweet_ids: set[str] | None = None) -> dict[str, dict[str, Any]]:
    if not table_exists(conn, "images"):
        return {}
    id_column = "id" if column_exists(conn, "images", "id") else "NULL"
    if tweet_ids is not None and not tweet_ids:
        return {}
    where = ""
    params: list[str] = []
    if tweet_ids is not None:
        where = f"WHERE tweet_id IN ({','.join('?' for _ in tweet_ids)})"
        params.extend(sorted(tweet_ids))
    rows = conn.execute(
        f"""
        SELECT {id_column} AS image_id, tweet_id, image_index, url, local_path
        FROM images {where} ORDER BY tweet_id, image_index, {id_column if id_column != 'NULL' else 'url'}
        """,
        params,
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["tweet_id"])].append({
            "id": str(row["image_id"]) if row["image_id"] is not None else None,
            "index": int(row["image_index"]),
            "url": row["url"],
            "local_path": row["local_path"],
        })
    return {
        tweet_id: {
            "count": len(items),
            "representative": items[0],
            "items": items,
            "paths": [item["local_path"] for item in items if item["local_path"]],
        }
        for tweet_id, items in grouped.items()
    }


def recipe_by_tweet(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not table_exists(conn, "prompt_recipes"):
        return {}
    rows = conn.execute(
        """
        SELECT recipe.tweet_id, recipe.recipe_text_en, recipe.recipe_text_zh
        FROM prompt_recipes recipe
        JOIN (
          SELECT tweet_id, max(updated_at) AS updated_at FROM prompt_recipes
          WHERE status='generated' GROUP BY tweet_id
        ) latest ON latest.tweet_id=recipe.tweet_id AND latest.updated_at=recipe.updated_at
        """
    )
    return {
        str(row["tweet_id"]): {"en": row["recipe_text_en"], "zh-Hans": row["recipe_text_zh"]}
        for row in rows
    }


def searchable_text(prompt: sqlite3.Row, tags: list[dict[str, Any]], translations: dict[str, str]) -> str:
    tag_text = " ".join(
        " ".join([
            tag["id"], tag["display"]["en"], tag["display"]["zh-Hans"],
            *tag["aliases"]["en"], *tag["aliases"]["zh-Hans"], tag["evidence"],
        ])
        for tag in tags
    )
    return " ".join([
        str(prompt["prompt_text"] or ""), str(prompt["author"] or ""), str(prompt["tool"] or ""),
        *translations.values(), tag_text,
    ]).casefold()


def score_match(query: str, terms: list[str], text: str, tag_ids: set[str]) -> float:
    phrase = query.casefold().strip()
    score = 14.0 if phrase and phrase in text else 0.0
    for term in terms:
        folded = term.casefold()
        if folded in tag_ids:
            score += 9
        elif folded in text:
            score += 2 if len(folded) == 1 else 4
    return score


def record_for(prompt: sqlite3.Row, tags: list[dict[str, Any]], translations: dict[str, str], images: dict[str, Any], recipes: dict[str, dict[str, Any]], *, score: float, maximum: int, max_tags: int, match_reasons: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    tweet_id = str(prompt["tweet_id"])
    matched_ids = {
        str(reason["value"])
        for reason in (match_reasons or [])
        if reason.get("type") in {"locked_tag", "must_tag", "should_tag"} and reason.get("value")
    }
    ranked_tags = sorted(tags, key=lambda tag: (tag["id"] not in matched_ids, -tag["confidence"], tag["id"]))
    image_data = images.get(tweet_id, {"count": 0, "representative": None, "items": [], "paths": []})
    return {
        "tweet_id": tweet_id,
        "score": round(score, 2),
        "author": prompt["author"],
        "tool": prompt["tool"] or "None",
        "created_at": prompt["created_at"] or prompt["collected_at"],
        "tweet_url": prompt["tweet_url"],
        "prompt_text": trim(prompt["prompt_text"], maximum),
        "source_prompt": str(prompt["prompt_text"] or ""),
        "source_url": prompt["tweet_url"],
        "translations": translations,
        "tag_count": len(tags),
        "tags": ranked_tags[:max_tags],
        "images": image_data,
        "image_paths": image_data.get("paths", []),
        "match_reasons": match_reasons or [],
        "recipe": recipes.get(tweet_id),
    }


def archive(conn: sqlite3.Connection, taxonomy_version: str | None = None, tweet_ids: set[str] | None = None) -> tuple[dict[str, sqlite3.Row], dict[str, list[dict[str, Any]]], dict[str, dict[str, str]], dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    # Retrieval is a v2-only product surface.  Legacy and partially inferred
    # free-form labels are intentionally never a fallback.
    require_v2_active(conn)
    version = RETRIEVAL_VERSION
    if tweet_ids is not None and not tweet_ids:
        return {}, {}, {}, {}, {}, version
    prompt_where = ""
    prompt_params: list[str] = []
    if tweet_ids is not None:
        prompt_where = f" WHERE tweet_id IN ({','.join('?' for _ in tweet_ids)})"
        prompt_params.extend(sorted(tweet_ids))
    prompts = {
        str(row["tweet_id"]): row
        for row in conn.execute(
            "SELECT tweet_id, author, tool, prompt_text, created_at, tweet_url, collected_at FROM prompts" + prompt_where,
            prompt_params,
        )
    }
    tags = tags_by_tweet(conn, version, tweet_ids)
    translations = translations_by_tweet(conn, version, tweet_ids)
    # A named staging version must never fall through to unlabeled legacy
    # prompts merely because their raw source text happens to match a query.
    prompts = {tweet_id: prompt for tweet_id, prompt in prompts.items() if tweet_id in tags}
    return prompts, tags, translations, image_summary_by_tweet(conn, tweet_ids), recipe_by_tweet(conn), version


def fts_rank_percentiles(conn: sqlite3.Connection, intent: SearchIntent, limit: int = 500) -> dict[str, float]:
    """Return a bounded lexical rank boost when native SQLite FTS5 is present."""
    if not intent.lexical_terms or not table_exists(conn, "prompt_fts"):
        return {}
    phrases = []
    for term in intent.lexical_terms:
        escaped = term.replace('"', '""').strip()
        if escaped:
            phrases.append(f'"{escaped}"')
    if not phrases:
        return {}
    expression = " OR ".join(dict.fromkeys(phrases))
    try:
        rows = list(conn.execute(
            """
            SELECT tweet_id, bm25(prompt_fts, 0.0, 1.0, 0.05, 0.1, 1.8) AS rank
            FROM prompt_fts WHERE prompt_fts MATCH ?
            ORDER BY rank LIMIT ?
            """,
            (expression, limit),
        ))
    except sqlite3.OperationalError:
        return {}
    count = max(1, len(rows))
    return {str(row["tweet_id"]): 1.0 - (index / count) for index, row in enumerate(rows)}


def candidate_tweet_ids(
    conn: sqlite3.Connection,
    intent: SearchIntent,
    *,
    fts_scores: dict[str, float],
    author: str | None,
    tool: str | None,
    require_images: bool,
    limit: int = 1500,
) -> set[str]:
    """Use indexed v2 label assignments to bound hydration to a small pool."""
    required = sorted({item.tag for item in [*intent.locked_tags, *intent.must_tags]})
    candidates = set(fts_scores)
    if required:
        label_rows = list(conn.execute(
            f"""
            SELECT label_id FROM taxonomy_labels
            WHERE taxonomy_version=? AND (dimension_key || ':' || key) IN ({','.join('?' for _ in required)})
            """,
            [RETRIEVAL_VERSION, *required],
        ))
        label_ids = sorted({int(row[0]) for row in label_rows})
        if len(label_ids) != len(required):
            return set()
        placeholders = ",".join("?" for _ in label_ids)
        where = []
        params: list[Any] = [RETRIEVAL_VERSION, *label_ids, RETRIEVAL_VERSION, *label_ids]
        if require_images:
            where.append("EXISTS (SELECT 1 FROM images image WHERE image.tweet_id=p.tweet_id)")
        if author:
            where.append("lower(p.author) LIKE ?")
            params.append(f"%{author.casefold()}%")
        if tool:
            where.append("lower(COALESCE(p.tool,'')) LIKE ?")
            params.append(f"%{tool.casefold()}%")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        params.extend([len(label_ids), limit])
        rows = conn.execute(
            f"""
            WITH fact AS (
              SELECT tweet_id,label_id,max(confidence) confidence
              FROM prompt_labels
              WHERE taxonomy_version=? AND label_id IN ({placeholders})
              GROUP BY tweet_id,label_id
              UNION ALL
              SELECT tweet_id,label_id,max(confidence) confidence
              FROM media_labels
              WHERE taxonomy_version=? AND media_type='image' AND label_id IN ({placeholders})
              GROUP BY tweet_id,label_id
            ), aggregated AS (
              SELECT tweet_id,label_id,max(confidence) confidence
              FROM fact GROUP BY tweet_id,label_id
            )
            SELECT p.tweet_id,sum(aggregated.confidence) confidence
            FROM prompts p JOIN aggregated ON aggregated.tweet_id=p.tweet_id
            {where_sql}
            GROUP BY p.tweet_id
            HAVING count(DISTINCT aggregated.label_id)=?
            ORDER BY confidence DESC,p.tweet_id
            LIMIT ?
            """,
            params,
        )
        candidates.update(str(row[0]) for row in rows)
    elif not candidates:
        where = []
        params: list[Any] = []
        if require_images:
            where.append("EXISTS (SELECT 1 FROM images image WHERE image.tweet_id=p.tweet_id)")
        if author:
            where.append("lower(p.author) LIKE ?")
            params.append(f"%{author.casefold()}%")
        if tool:
            where.append("lower(COALESCE(p.tool,'')) LIKE ?")
            params.append(f"%{tool.casefold()}%")
        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        params.append(limit)
        candidates.update(str(row[0]) for row in conn.execute(
            f"""
            SELECT p.tweet_id FROM prompts p {where_sql}
            ORDER BY COALESCE(p.created_at,p.collected_at) DESC LIMIT ?
            """,
            params,
        ))
    return candidates


def tag_evidence(tag: dict[str, Any]) -> tuple[float, str]:
    scopes = set(tag.get("scopes") or [tag.get("scope", "prompt")])
    if scopes == {"image", "prompt"}:
        return 1.0, "prompt+image"
    if "image" in scopes:
        return 0.9, "image"
    return 0.55, "prompt"


def score_candidate(intent: SearchIntent, prompt: sqlite3.Row, prompt_tags: list[dict[str, Any]], translations: dict[str, str], image_data: dict[str, Any], fts_percentile: float) -> tuple[float, list[dict[str, Any]]] | None:
    by_id = {tag["id"].casefold(): tag for tag in prompt_tags}
    reasons: list[dict[str, Any]] = []
    score = 0.0

    forbidden_hits = [constraint.tag for constraint in intent.forbidden_tags if constraint.tag.casefold() in by_id]
    if forbidden_hits:
        return None

    if intent.verified_only and str(prompt["tweet_id"]) not in intent.verified_tweet_ids:
        return None

    for required_image_tag in intent.required_image_tags:
        tag = by_id.get(required_image_tag.casefold())
        if (
            (not tag or "image" not in set(tag.get("scopes") or [tag.get("scope", "prompt")]))
            and str(prompt["tweet_id"]) not in intent.verified_tweet_ids
        ):
            return None
    if str(prompt["tweet_id"]) in intent.verified_tweet_ids:
        score += 30.0
        reasons.append({"type": "human_verified", "value": str(prompt["tweet_id"])})

    for constraint in [*intent.locked_tags, *intent.must_tags]:
        tag = by_id.get(constraint.tag.casefold())
        if not tag:
            return None
        evidence, scope = tag_evidence(tag)
        weight = 22.0 if constraint.mode == "locked" else 15.0
        score += weight * evidence
        reasons.append({
            "type": f"{constraint.mode}_tag",
            "value": constraint.tag,
            "scope": scope,
            "matched_by": list(constraint.matched_by),
        })

    for constraint in intent.should_tags:
        tag = by_id.get(constraint.tag.casefold())
        if not tag:
            continue
        evidence, scope = tag_evidence(tag)
        score += 6.0 * evidence
        reasons.append({
            "type": "should_tag",
            "value": constraint.tag,
            "scope": scope,
            "matched_by": list(constraint.matched_by),
        })

    text = searchable_text(prompt, prompt_tags, translations)
    requested = {tag.tag for tag in [*intent.locked_tags, *intent.must_tags, *intent.should_tags]}
    if (
        "sneaker" in intent.concepts
        and {"subject_type:product", "usage:ecommerce", "color_palette:white-minimal"}.issubset(requested)
    ):
        clean_product_conflicts = {
            "subject_type:fashion-person",
            "subject_type:portrait",
            "quality_flags:embedded-text",
            "quality_flags:typography-heavy",
            "quality_flags:multi-panel-layout",
            "quality_flags:screenshot-ui",
        }
        if clean_product_conflicts & set(by_id):
            return None
    if (
        "perfume" in intent.concepts
        and {"visual_style:minimal", "color_palette:dark-moody", "usage:ad-campaign"}.issubset(requested)
    ):
        restrained_product_conflicts = {
            "subject_type:fashion-person",
            "subject_type:portrait",
            "quality_flags:embedded-text",
            "quality_flags:typography-heavy",
            "quality_flags:multi-panel-layout",
            "mood:energetic",
            "composition:dynamic-diagonal",
        }
        if restrained_product_conflicts & set(by_id):
            return None
        if lexical_group_hits(text, ["splash", "splashing", "burst", "explosion", "飞溅", "喷溅", "爆炸"]):
            return None
    if "jewelry-product" in intent.concepts:
        jewelry_product_conflicts = {
            "subject_type:portrait",
            "subject_type:fashion-person",
            "subject_type:beauty-closeup",
            "subject_type:diagram-document",
            "quality_flags:embedded-text",
            "quality_flags:typography-heavy",
            "quality_flags:multi-panel-layout",
            "quality_flags:screenshot-ui",
            "quality_flags:logo-watermark",
        }
        if jewelry_product_conflicts & set(by_id):
            return None
        if lexical_group_hits(text, ["keychain", "key chain", "key ring", "钥匙扣", "钥匙链"]):
            return None
    if "tech-product" in intent.concepts:
        tech_product_conflicts = {
            "subject_type:graphic-design",
            "subject_type:fashion-person",
            "subject_type:portrait",
            "subject_type:food-drink",
            "subject_type:character",
            "quality_flags:typography-heavy",
            "quality_flags:multi-panel-layout",
            "quality_flags:screenshot-ui",
            "quality_flags:logo-watermark",
            "usage:poster",
        }
        if tech_product_conflicts & set(by_id):
            return None
    if "rain-race-car" in intent.concepts:
        race_car_conflicts = {
            "subject_type:character",
            "subject_type:diagram-document",
            "subject_type:ui-screen",
            "quality_flags:embedded-text",
            "quality_flags:typography-heavy",
            "quality_flags:multi-panel-layout",
            "quality_flags:screenshot-ui",
            "quality_flags:logo-watermark",
        }
        if race_car_conflicts & set(by_id):
            return None
    hard_constraint_count = len(intent.locked_tags) + len(intent.must_tags)
    lexical_weight = 1.0 if hard_constraint_count < 2 else 0.75
    lexical_cap = 18.0 if hard_constraint_count < 2 else 4.0
    phrase_weight = 10.0 if hard_constraint_count < 2 else 2.0
    bm25_weight = 12.0 if hard_constraint_count < 2 else 2.0
    for required_group in intent.required_lexical_groups:
        group_hits = lexical_group_hits(text, required_group)
        if not group_hits:
            return None
        score += 10.0
        reasons.append({"type": "required_lexical", "values": group_hits})
    phrase = intent.query.casefold().strip()
    if phrase and lexical_term_present(text, phrase):
        score += phrase_weight
        reasons.append({"type": "exact_phrase", "value": intent.query})
    lexical_hits = [term for term in intent.lexical_terms if lexical_term_present(text, term)]
    if lexical_hits:
        score += min(lexical_cap, lexical_weight * len(lexical_hits))
        reasons.append({"type": "lexical", "values": lexical_hits})
    if fts_percentile:
        score += bm25_weight * fts_percentile
        reasons.append({"type": "bm25", "percentile": round(fts_percentile, 3)})

    if image_data.get("count", 0):
        score += 3.0
        reasons.append({"type": "image_available", "count": image_data["count"]})

    quality_ids = set(by_id)
    if "quality_flags:needs-review" in quality_ids:
        score -= 12.0
    if "quality_flags:visible-artifacts" in quality_ids:
        score -= 8.0
    if "quality_flags:screenshot-ui" in quality_ids and "subject_type:ui-screen" not in {tag.tag for tag in [*intent.locked_tags, *intent.must_tags, *intent.should_tags]}:
        score -= 5.0
    requested = {tag.tag for tag in [*intent.locked_tags, *intent.must_tags]}
    if "lighting:neon-light" in requested:
        if "color_palette:neon" in quality_ids:
            score += 8.0
        if "color_palette:dark-moody" in quality_ids:
            score += 4.0
        if "visual_style:black-and-white" in quality_ids or "color_palette:black-and-white" in quality_ids:
            score -= 20.0
        if "color_palette:warm-tones" in quality_ids:
            score -= 8.0

    if intent.query.strip() and not any(reason["type"] not in {"image_available"} for reason in reasons):
        return None
    return score, reasons


def relaxation_plan(intent: SearchIntent) -> list[str]:
    """Explicit constraints are never relaxed; inferred preferences are `should`."""
    return []


def intent_with_relaxations(intent: SearchIntent, relaxed: list[str]) -> SearchIntent:
    relaxed_set = set(relaxed)
    moved = [item for item in intent.must_tags if item.tag in relaxed_set]
    kept = [item for item in intent.must_tags if item.tag not in relaxed_set]
    should_by_tag = {item.tag: item for item in intent.should_tags}
    for item in moved:
        should_by_tag[item.tag] = IntentTag(item.tag, "should", item.matched_by)
    return SearchIntent(
        query=intent.query,
        language=intent.language,
        locked_tags=list(intent.locked_tags),
        must_tags=kept,
        should_tags=sorted(should_by_tag.values(), key=lambda item: item.tag),
        forbidden_tags=list(intent.forbidden_tags),
        lexical_terms=list(intent.lexical_terms),
        required_lexical_groups=[list(group) for group in intent.required_lexical_groups],
        required_image_tags=list(intent.required_image_tags),
        verified_tweet_ids=list(intent.verified_tweet_ids),
        verified_only=intent.verified_only,
        concepts=list(intent.concepts),
    )


def search_hits(
    conn: sqlite3.Connection,
    intent: SearchIntent,
    *,
    fts_scores: dict[str, float],
    require_images: bool,
    author_filter: str | None,
    tool_filter: str | None,
    max_prompt_chars: int,
    max_tags: int,
    relaxed: list[str],
) -> tuple[list[dict[str, Any]], str]:
    candidate_ids = candidate_tweet_ids(
        conn, intent, fts_scores=fts_scores, author=author_filter, tool=tool_filter,
        require_images=require_images,
    )
    prompts, tags, translations, images, recipes, version = archive(
        conn, RETRIEVAL_VERSION, candidate_ids,
    )
    hits = []
    for tweet_id, prompt in prompts.items():
        if author_filter and author_filter.casefold() not in str(prompt["author"] or "").casefold():
            continue
        if tool_filter and tool_filter.casefold() not in str(prompt["tool"] or "").casefold():
            continue
        prompt_tags = tags.get(tweet_id, [])
        image_data = images.get(tweet_id, {"count": 0, "representative": None, "items": [], "paths": []})
        if require_images and not image_data["count"]:
            continue
        scored = score_candidate(
            intent, prompt, prompt_tags, translations.get(tweet_id, {}), image_data,
            fts_scores.get(tweet_id, 0.0),
        )
        if scored is None:
            continue
        score, reasons = scored
        if relaxed:
            reasons.append({"type": "relaxation", "constraints": list(relaxed)})
        item = record_for(
            prompt, prompt_tags, translations.get(tweet_id, {}), images, recipes,
            score=score, maximum=max_prompt_chars, max_tags=max_tags,
            match_reasons=reasons,
        )
        item["relaxation_level"] = len(relaxed)
        item["relaxed_constraints"] = list(relaxed)
        item["_tag_ids"] = {tag["id"] for tag in prompt_tags}
        item["_prompt_key"] = re.sub(r"\s+", " ", str(prompt["prompt_text"] or "").casefold()).strip()[:1000]
        hits.append(item)
    hits.sort(key=lambda item: (-item["score"], item["tweet_id"]), reverse=False)
    return hits, version


def diversify_tiers(
    tiers: list[list[dict[str, Any]]], limit: int, *, finalize: bool = True,
) -> list[dict[str, Any]]:
    chosen: list[dict[str, Any]] = []
    author_counts: dict[str, int] = defaultdict(int)
    prompt_keys: set[str] = set()
    tweet_ids: set[str] = set()
    for hits in tiers:
        pool = [item for item in hits[:max(100, limit * 15)] if item["tweet_id"] not in tweet_ids]
        maximum = max((float(item["score"]) for item in pool), default=1.0) or 1.0
        while pool and len(chosen) < limit:
            best_index = None
            best_value = float("-inf")
            for index, item in enumerate(pool):
                author = str(item.get("author") or "")
                if item["tweet_id"] in tweet_ids or author_counts[author] >= 2 or item["_prompt_key"] in prompt_keys:
                    continue
                similarity = max(
                    (weighted_tag_similarity(item["_tag_ids"], previous["_tag_ids"]) for previous in chosen),
                    default=0.0,
                )
                value = 0.82 * (float(item["score"]) / maximum) - 0.18 * similarity
                if author_counts[author]:
                    value -= 0.08
                if value > best_value:
                    best_value = value
                    best_index = index
            if best_index is None:
                break
            item = pool.pop(best_index)
            chosen.append(item)
            tweet_ids.add(item["tweet_id"])
            author_counts[str(item.get("author") or "")] += 1
            prompt_keys.add(item["_prompt_key"])
        if len(chosen) >= limit:
            break
    if finalize:
        for rank, item in enumerate(chosen, 1):
            item["rank"] = rank
            item.pop("_tag_ids", None)
            item.pop("_prompt_key", None)
    return chosen


def run_search(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    require_v2_active(conn)
    selected_tag = str(getattr(args, "tag", "") or "").casefold().strip()
    intent = parse_intent(args.query, [selected_tag] if selected_tag else [])
    fts_scores = fts_rank_percentiles(conn, intent)
    require_images = not bool(getattr(args, "allow_no_image", False))
    author_filter = getattr(args, "author", None)
    tool_filter = getattr(args, "tool", None)
    tiers: list[list[dict[str, Any]]] = []
    tier_summaries = []
    relaxed: list[str] = []
    plan = relaxation_plan(intent)
    version = RETRIEVAL_VERSION
    while True:
        tier_intent = intent_with_relaxations(intent, relaxed)
        hits, version = search_hits(
            conn, tier_intent, fts_scores=fts_scores, require_images=require_images,
            author_filter=author_filter, tool_filter=tool_filter,
            max_prompt_chars=args.max_prompt_chars, max_tags=args.max_tags,
            relaxed=relaxed,
        )
        tiers.append(hits)
        tier_summaries.append({
            "level": len(relaxed), "relaxed_constraints": list(relaxed),
            "match_count": len(hits),
        })
        selectable_count = len(diversify_tiers(tiers, args.limit, finalize=False))
        if selectable_count >= args.limit or len(relaxed) >= len(plan):
            break
        relaxed.append(plan[len(relaxed)])
    exact_match_count = len(tiers[0]) if tiers else 0
    total_matches = len({item["tweet_id"] for tier in tiers for item in tier})
    selected = diversify_tiers(tiers, args.limit)
    used_relaxations = list(dict.fromkeys(
        constraint for item in selected for constraint in item.get("relaxed_constraints", [])
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "query": args.query,
        "active_taxonomy_version": current_version(conn),
        "taxonomy_version": version,
        "parsed_intent": intent.as_dict(),
        "relaxed_constraints": used_relaxations,
        "search_tiers": tier_summaries,
        "result_count": len(selected),
        "exact_match_count": exact_match_count,
        "total_matches": total_matches,
        "results": selected,
    }


def run_get(conn: sqlite3.Connection, args: argparse.Namespace) -> dict[str, Any]:
    require_v2_active(conn)
    prompts, tags, translations, images, recipes, version = archive(conn, RETRIEVAL_VERSION, {str(args.tweet_id)})
    prompt = prompts.get(args.tweet_id)
    if not prompt:
        raise SystemExit(f"No prompt found for tweet_id={args.tweet_id}")
    item = record_for(
        prompt, tags.get(args.tweet_id, []), translations.get(args.tweet_id, {}), images, recipes,
        score=0, maximum=args.max_prompt_chars, max_tags=args.max_tags,
    )
    item["rank"] = 1
    return {
        "schema_version": SCHEMA_VERSION,
        "active_taxonomy_version": current_version(conn),
        "taxonomy_version": version,
        "result": item,
    }


def run_status(conn: sqlite3.Connection) -> dict[str, Any]:
    version = RETRIEVAL_VERSION
    actual = current_version(conn)
    return {
        "schema_version": SCHEMA_VERSION,
        "active_taxonomy_version": actual,
        "required_taxonomy_version": version,
        "ready": actual == version,
        "prompts": conn.execute("SELECT count(*) FROM prompts").fetchone()[0],
        "images": conn.execute("SELECT count(*) FROM images").fetchone()[0] if table_exists(conn, "images") else 0,
        "translations": conn.execute("SELECT count(*) FROM prompt_translations WHERE translation_version=?", (version,)).fetchone()[0] if table_exists(conn, "prompt_translations") else 0,
        "prompt_labels": conn.execute("SELECT count(*) FROM prompt_labels" + (" WHERE taxonomy_version=?" if column_exists(conn, "prompt_labels", "taxonomy_version") else ""), (version,) if column_exists(conn, "prompt_labels", "taxonomy_version") else ()).fetchone()[0] if table_exists(conn, "prompt_labels") else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only bilingual retrieval for Open Image Prompts")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="working SQLite archive; never modified")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE_PATH, help="gzip archive used only if --db is missing")
    parser.add_argument("--taxonomy", choices=[RETRIEVAL_VERSION], default=RETRIEVAL_VERSION, help="v2 is the only searchable taxonomy")
    subparsers = parser.add_subparsers(dest="command", required=True)
    search = subparsers.add_parser("search", help="find prompts by bilingual visual intent and controlled tags")
    search.add_argument("query")
    search.add_argument("--tag", help="exact canonical tag: dimension:key")
    search.add_argument("--author")
    search.add_argument("--tool")
    search.add_argument("--allow-no-image", action="store_true", help="include text-only prompts; image references are required by default")
    search.add_argument("--limit", type=bounded_int(1, 50), default=8)
    search.add_argument("--max-prompt-chars", type=bounded_int(200, 20000), default=1600)
    search.add_argument("--max-tags", type=bounded_int(1, 50), default=12)
    get = subparsers.add_parser("get", help="return a source prompt by stable tweet ID")
    get.add_argument("tweet_id")
    get.add_argument("--max-prompt-chars", type=bounded_int(200, 30000), default=20000)
    get.add_argument("--max-tags", type=bounded_int(1, 100), default=50)
    subparsers.add_parser("status", help="show active searchable coverage")
    args = parser.parse_args()

    db_path = args.db
    if not db_path.is_file():
        db_path = ensure_working_database(db_path, args.archive)
    with connect_read_only(db_path) as conn:
        if args.command == "search":
            result = run_search(conn, args)
        elif args.command == "get":
            result = run_get(conn, args)
        else:
            result = run_status(conn)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
