# Retrieval contract

## Product boundary

This Skill is read-only and serves only the active `oip-visual-v2` corpus. It
must fail closed when another taxonomy is active. Labeling, provider routing,
queue recovery, taxonomy activation, database publication, and archive writes
belong to repository operations, not this user-facing Skill.

## Search pipeline

1. Pass the user's original wording to search. Do not silently enrich it with
   guessed subjects, styles, props, or negative constraints.
2. Treat an explicit `--tag` as locked. Literal request terms and core subject
   concepts may become must constraints; inferred preferences remain should
   constraints. Inspect `parsed_intent` instead of assuming which mode was used.
3. Recall from both prompt labels and image labels. Prefer image-confirmed
   evidence and default to records with local images.
4. Penalize objective quality flags such as `needs-review` and
   `visible-artifacts`. Do not invent a subjective “beauty score”.
5. Diversify near-duplicate tags and authors after relevance ranking.
6. Preserve fail-closed exact results in `results`. If the exact channel cannot
   fill the requested limit, search independent one-facet fallback tiers and
   expose visually confirmed candidates only in `related_results`.
7. Explain matched and missing constraints for every result.

## Stable output

Search output uses schema `oip-retrieval-v1` and includes:

- exact taxonomy version;
- raw and parsed intent;
- ranked result score and match reasons;
- `match_kind` (`exact` or `related`) and declared `missing_constraints`;
- unchanged source prompt and bilingual translations;
- canonical tags and all image paths;
- author and source URL.

Results without a real image, source prompt, author/source provenance, or stable
tweet ID are invalid.

`source_prompt` is the unchanged source text stored by the archive. When that
text is commentary, an announcement, or post copy rather than an executable
generation prompt, disclose the distinction instead of relabeling it.

## Exact, related, and empty results

Zero exact results are better than unrelated examples. The exact `results`
channel never relaxes a constraint. The separate `related_results` channel may
omit exactly one safe aesthetic facet such as composition, lighting, palette,
mood, minimal styling, or a long-exposure preference.

A related candidate is valid only when every remaining visual constraint has
image-side evidence. Unrequested screenshots, document/UI graphics, heavy
text, multi-panel layouts, visible artifacts, and watermarks are rejected.
Subject, scene, explicit style/use, locked tags, user invariants, and forbidden
constraints are never relaxed. If both channels are empty, report the corpus
gap and hand off to first-principles prompting without fabricated provenance.
