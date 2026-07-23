"""Bilingual intent parsing and deterministic ranking helpers.

This module deliberately performs no database writes and invokes no model.  It
turns a natural-language request into stable v2 tag constraints plus lexical
terms that the SQLite archive can score and explain.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

RETRIEVAL_VERSION = "oip-visual-v2"
CONFIG_PATH = Path(__file__).with_name(f"{RETRIEVAL_VERSION}-intent.json")
TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "taxonomy" / f"{RETRIEVAL_VERSION}.json"
HAN_RE = re.compile(r"[\u4e00-\u9fff]+")
WORD_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


@dataclass(frozen=True)
class IntentTag:
    tag: str
    mode: str
    matched_by: tuple[str, ...] = ()


@dataclass
class SearchIntent:
    query: str
    language: str
    locked_tags: list[IntentTag] = field(default_factory=list)
    must_tags: list[IntentTag] = field(default_factory=list)
    should_tags: list[IntentTag] = field(default_factory=list)
    forbidden_tags: list[IntentTag] = field(default_factory=list)
    lexical_terms: list[str] = field(default_factory=list)
    required_lexical_groups: list[list[str]] = field(default_factory=list)
    required_image_tags: list[str] = field(default_factory=list)
    verified_tweet_ids: list[str] = field(default_factory=list)
    verified_only: bool = False
    concepts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalized(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def lexical_term_present(text: str, term: str) -> bool:
    """Match Han phrases by substring and Latin terms on real word boundaries."""
    haystack = _normalized(text)
    needle = _normalized(term)
    if not needle:
        return False
    if HAN_RE.search(needle):
        return needle in haystack
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) is not None


def lexical_group_hits(text: str, group: Iterable[str]) -> list[str]:
    """Return honest lexical evidence, excluding a known rose false positive."""
    normalized = _normalized(text)
    normalized_group = {_normalized(term) for term in group}
    if normalized_group & {"rose", "roses", "玫瑰", "蔷薇"}:
        normalized = re.sub(r"(?<![a-z0-9])compass[ -]+roses?(?![a-z0-9])", " ", normalized)
        normalized = re.sub(r"(?:罗盘|指南针)(?:玫瑰|蔷薇)", " ", normalized)
    hits = []
    for term in group:
        needle = _normalized(term)
        if lexical_term_present(normalized, needle):
            hits.append(needle)
    return list(dict.fromkeys(hits))


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as source:
        config = json.load(source)
    if config.get("version") != RETRIEVAL_VERSION:
        raise ValueError(f"intent catalog must target {RETRIEVAL_VERSION}")
    return config


@lru_cache(maxsize=1)
def taxonomy_alias_entries() -> tuple[tuple[str, str, str], ...]:
    """Derive unambiguous aliases for every v2 leaf not curated explicitly."""
    config = load_config()
    with TAXONOMY_PATH.open(encoding="utf-8") as source:
        taxonomy = json.load(source)
    curated = {
        _normalized(alias)
        for spec in config["label_aliases"].values()
        for alias in spec.get("aliases", [])
    }
    candidates: dict[str, list[tuple[str, str]]] = {}
    for dimension in taxonomy.get("dimensions", []):
        dimension_key = str(dimension["key"])
        # These aliases are literal v2 leaf names. When the user says one
        # explicitly it is a constraint, regardless of dimension. Conceptual
        # inferences are added separately as `should` tags.
        mode = "must"
        for label in dimension.get("labels", []):
            canonical = f"{dimension_key}:{label['key']}"
            display = label.get("display", {})
            aliases = {
                _normalized(str(label["key"]).replace("-", " ")),
                _normalized(display.get("en", "")),
                _normalized(display.get("zh", "")),
            }
            for alias in aliases:
                if alias and alias not in curated:
                    candidates.setdefault(alias, []).append((canonical, mode))
    # Ambiguous bare words such as `editorial` and `black and white` must be
    # resolved by the curated catalog, never expanded into several hard tags.
    return tuple(
        (alias, values[0][0], values[0][1])
        for alias, values in candidates.items()
        if len({canonical for canonical, _ in values}) == 1
    )


def _append_tag(target: dict[str, IntentTag], canonical: str, mode: str, matched_by: str) -> None:
    existing = target.get(canonical)
    priority = {"should": 1, "must": 2, "locked": 3}
    if existing:
        strongest = mode if priority[mode] > priority[existing.mode] else existing.mode
        aliases = tuple(dict.fromkeys([*existing.matched_by, matched_by]))
        target[canonical] = IntentTag(canonical, strongest, aliases)
    else:
        target[canonical] = IntentTag(canonical, mode, (matched_by,))


def _unmatched_han_terms(query: str, matched_aliases: Iterable[str], stopwords: set[str]) -> list[str]:
    masked = query
    for alias in sorted((value for value in matched_aliases if HAN_RE.search(value)), key=len, reverse=True):
        masked = masked.replace(alias, " ")
    for stopword in sorted(stopwords, key=len, reverse=True):
        masked = masked.replace(stopword, " ")
    # Never emit a single Han character: it has near-zero retrieval precision.
    return [part for part in HAN_RE.findall(masked) if len(part) >= 2]


def parse_intent(query: str, explicit_tags: Iterable[str] = ()) -> SearchIntent:
    config = load_config()
    normalized = _normalized(query)
    positive_text = normalized
    language = "zh-Hans" if HAN_RE.search(normalized) else "en"
    tags: dict[str, IntentTag] = {}
    lexical: list[str] = []
    matched_aliases: list[str] = []
    concepts: list[str] = []
    required_lexical_groups: list[list[str]] = []
    required_image_tags: list[str] = []
    verified_tweet_ids: list[str] = []
    verified_only = False
    forbidden: dict[str, IntentTag] = {}

    negative_matches: list[str] = []
    for canonical, aliases in config.get("negative_aliases", {}).items():
        for raw_alias in aliases:
            alias = _normalized(raw_alias)
            if lexical_term_present(normalized, alias):
                _append_tag(forbidden, canonical, "must", alias)
                negative_matches.append(alias)
    for alias in sorted(set(negative_matches), key=len, reverse=True):
        positive_text = positive_text.replace(alias, " ")

    for canonical in explicit_tags:
        value = _normalized(canonical)
        if value:
            _append_tag(tags, value, "locked", value)

    alias_entries: list[tuple[str, str, str]] = list(taxonomy_alias_entries())
    for canonical, spec in config["label_aliases"].items():
        for alias in spec.get("aliases", []):
            alias_entries.append((_normalized(alias), canonical, "must"))
    # Longest phrases first makes `product photography` more informative than
    # the contained word `product`, while still allowing both distinct tags.
    for alias, canonical, mode in sorted(alias_entries, key=lambda item: len(item[0]), reverse=True):
        if lexical_term_present(positive_text, alias):
            _append_tag(tags, canonical, mode, alias)
            matched_aliases.append(alias)
            lexical.append(alias)

    for concept in config.get("concepts", []):
        aliases = [_normalized(value) for value in concept.get("aliases", [])]
        matches = [alias for alias in aliases if lexical_term_present(positive_text, alias)]
        if not matches:
            continue
        concepts.append(str(concept["id"]))
        matched_aliases.extend(matches)
        concept_lexical = [_normalized(value) for value in concept.get("lexical", []) if _normalized(value)]
        lexical.extend(concept_lexical)
        if concept.get("require_lexical") and concept_lexical:
            required_lexical_groups.append(concept_lexical)
        for group in concept.get("required_lexical_groups", []):
            normalized_group = [_normalized(value) for value in group if _normalized(value)]
            if normalized_group:
                required_lexical_groups.append(normalized_group)
        required_image_tags.extend(_normalized(value) for value in concept.get("required_image_tags", []))
        verified_tweet_ids.extend(str(value) for value in concept.get("verified_tweet_ids", []))
        verified_only = verified_only or bool(concept.get("verified_only"))
        for canonical in concept.get("must", []):
            _append_tag(tags, canonical, "must", f"concept:{concept['id']}")
        for canonical in concept.get("should", []):
            _append_tag(tags, canonical, "should", f"concept:{concept['id']}")
        for canonical in concept.get("forbidden", []):
            _append_tag(forbidden, canonical, "must", f"concept:{concept['id']}")

    english_stopwords = {_normalized(value) for value in config.get("english_stopwords", [])}
    chinese_stopwords = {_normalized(value) for value in config.get("chinese_stopwords", [])}
    lexical.extend(
        word for word in WORD_RE.findall(positive_text)
        if len(word) >= 2 and word not in english_stopwords
    )
    lexical.extend(_unmatched_han_terms(positive_text, matched_aliases, chinese_stopwords))
    lexical = [term for term in dict.fromkeys(_normalized(value) for value in lexical) if term]
    lexical = [term for term in lexical if not (len(term) == 1 and HAN_RE.fullmatch(term))]

    # Explicit people and paired motifs are semantic content constraints, not
    # merely ranking hints. Keep them as lexical evidence groups so a male
    # portrait or a compass rose cannot satisfy the user's brief.
    female_terms = ["female", "woman", "women", "girl", "lady", "女性", "女人", "女孩", "女生", "女士"]
    if any(lexical_term_present(positive_text, term) for term in female_terms):
        required_lexical_groups.append(female_terms)
    snake_terms = ["snake", "serpent", "蛇", "蛇纹"]
    rose_terms = ["rose", "roses", "玫瑰", "蔷薇"]
    if (
        any(lexical_term_present(positive_text, term) for term in snake_terms)
        and any(lexical_term_present(positive_text, term) for term in rose_terms)
    ):
        required_lexical_groups.extend([snake_terms, rose_terms])

    required_lexical_groups = [
        list(dict.fromkeys(group))
        for group in required_lexical_groups
        if group
    ]
    if "childrens-book" in concepts:
        required_image_tags.extend(
            item.tag for item in tags.values() if item.tag.startswith("scene:")
        )

    # Resolve two common natural-language ambiguities before retrieval. A
    # fashion editorial already has a fashion subject; keeping both `fashion`
    # and `editorial` as render styles can exceed visual_style.max=2 once the
    # user also asks for surrealism. Likewise bare "neon" in an abstract
    # graphic brief describes palette more reliably than a visible light
    # source, so lighting remains a preference rather than a hard constraint.
    if (
        "subject_type:fashion-person" in tags
        and "visual_style:editorial" in tags
        and "visual_style:fashion" in tags
    ):
        item = tags["visual_style:fashion"]
        tags["visual_style:fashion"] = IntentTag(item.tag, "should", item.matched_by)
    elif "subject_type:fashion-person" in tags and "visual_style:fashion" in tags:
        item = tags["visual_style:fashion"]
        explicit_style_aliases = {"fashion photography", "时尚摄影"}
        if not (set(item.matched_by) & explicit_style_aliases):
            tags["visual_style:fashion"] = IntentTag(item.tag, "should", item.matched_by)
    if (
        "color_palette:neon" in tags
        and "lighting:neon-light" in tags
        and ({"subject_type:abstract", "subject_type:graphic-design", "visual_style:graphic-design"} & set(tags))
    ):
        item = tags["lighting:neon-light"]
        tags["lighting:neon-light"] = IntentTag(item.tag, "should", item.matched_by)

    ordered = sorted(tags.values(), key=lambda item: item.tag)
    return SearchIntent(
        query=str(query or ""),
        language=language,
        locked_tags=[item for item in ordered if item.mode == "locked"],
        must_tags=[item for item in ordered if item.mode == "must"],
        should_tags=[item for item in ordered if item.mode == "should"],
        forbidden_tags=sorted(forbidden.values(), key=lambda item: item.tag),
        lexical_terms=lexical,
        required_lexical_groups=required_lexical_groups,
        required_image_tags=list(dict.fromkeys(value for value in required_image_tags if value)),
        verified_tweet_ids=list(dict.fromkeys(value for value in verified_tweet_ids if value)),
        verified_only=verified_only,
        concepts=list(dict.fromkeys(concepts)),
    )


def weighted_tag_similarity(left: set[str], right: set[str]) -> float:
    """Weighted-Jaccard proxy for result diversification."""
    if not left or not right:
        return 0.0
    important = {"subject_type", "visual_style", "composition", "lighting", "color_palette", "mood", "scene"}
    union = left | right
    intersection = left & right
    weight = lambda tag: 2.0 if tag.partition(":")[0] in important else 1.0
    return sum(weight(tag) for tag in intersection) / sum(weight(tag) for tag in union)
